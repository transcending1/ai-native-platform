import ast
import json
import os
import subprocess
import tempfile
from typing import Annotated
from typing import Optional

from django.core.cache import cache
from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import BaseTool
from langchain_core.tools.base import ArgsSchema
from langgraph.prebuilt import InjectedState
from langgraph.prebuilt import create_react_agent
from langgraph.prebuilt.chat_agent_executor import AgentState
from pydantic import BaseModel, Field

from core.models.llm import llm as code_generation_llm


class CodeExecutionInput(BaseModel):
    code: str = Field(
        description="根据代码模版生成的要执行的Python代码和测试用例代码（放在一起）",
    )


class CodeExecutionTool(BaseTool):
    name: str = "python_code_executor"
    description: str = "执行Python代码并返回结果（每次生成代码之后都要调用代码执行工具去运行直到成功运行为止）"
    args_schema: Optional[ArgsSchema] = CodeExecutionInput.model_json_schema()
    return_direct: bool = False
    handle_tool_error: bool = True

    def _run(
            self,
            code: str,
            state: Annotated[AgentState, InjectedState] = None,
            config: RunnableConfig = None,
            run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """执行Python代码并返回结果"""
        try:
            # 创建临时文件来执行代码
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                # 写入主代码
                f.write(code)
                f.write('\n')

                temp_file = f.name

            try:
                result = subprocess.run(
                    [
                        "python", "-m", "pytest", temp_file, '-k',
                        'test_case', '--tb=native', '--no-header',
                        '--color=no', '-p', 'no:warnings'
                    ],
                    capture_output=True,
                    text=True,
                    timeout=60
                )

                output = {
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "return_code": result.returncode,
                    "success": result.returncode == 0
                }

            except subprocess.TimeoutExpired:
                output = {
                    "stdout": "",
                    "stderr": "Test timed out after 60 seconds",
                    "return_code": -1,
                    "success": False
                }
            finally:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)

            if "FAILED" in output["stdout"]:
                return f"代码执行失败！\n错误信息: {output['stdout']}，请继续修改代码迭代"
            else:
                return f"代码执行成功！\n输出: {output['stdout']}，直接返回给用户"

        except subprocess.TimeoutExpired:
            return "代码执行超时（超过30秒）"
        except Exception as e:
            return f"执行器异常: {str(e)}"


def extract_function_body(code_str: str, class_name: str, function_name: str) -> Optional[str]:
    """
    从代码字符串中提取指定类的指定函数的源代码

    :param code_str: 包含完整代码的字符串
    :param class_name: 要提取的类名
    :param function_name: 要提取的函数名
    :return: 函数的源代码字符串，如果未找到则返回None
    """
    # 解析代码为AST
    tree = ast.parse(code_str)

    # 查找目标类
    target_class = None
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            target_class = node
            break

    if not target_class:
        return None

    # 在类中查找目标函数
    target_function = None
    for item in target_class.body:
        if isinstance(item, ast.FunctionDef) and item.name == function_name:
            target_function = item
            break

    if not target_function:
        return None

    # 获取函数的源代码
    lines = code_str.splitlines()
    start_line = target_function.lineno - 1  # AST的行号从1开始
    end_line = target_function.end_lineno if hasattr(target_function, 'end_lineno') else start_line

    # 处理可能的多行装饰器
    while start_line > 0 and lines[start_line - 1].strip().startswith('@'):
        start_line -= 1

    # 提取函数代码
    function_lines = lines[start_line:end_line]

    # 计算最小缩进（去除空行）
    min_indent = None
    for line in function_lines:
        stripped = line.lstrip()
        if stripped:  # 非空行
            indent = len(line) - len(stripped)
            if min_indent is None or indent < min_indent:
                min_indent = indent

    # 统一去除最小缩进
    if min_indent is not None and min_indent > 0:
        function_lines = [line[min_indent:] if line.strip() else line for line in function_lines]

    return '\n'.join(function_lines)


class CodeGeneration:
    def __init__(
            self,
            code_template,
            system_prompt_patch,
            to_extract_class_name,
            to_extract_function_list,
            max_iterations=3
    ):
        # 创建工具实例
        code_executor = CodeExecutionTool()
        # 创建工具列表
        self.tools = [code_executor]
        self.code_template = code_template
        self.system_prompt_patch = system_prompt_patch
        self.max_iterations = max_iterations
        self.to_extract_class_name = to_extract_class_name
        self.to_extract_function_list = to_extract_function_list

    def parse_generation_code(self, code_str, redis_key):
        function_code_mapping = {}
        for func_name in self.to_extract_function_list:
            function_body = extract_function_body(code_str, self.to_extract_class_name, func_name)
            function_code_mapping[func_name] = function_body
        # 原始代码也写入缓存，供下一次迭代使用。
        function_code_mapping['__raw_code__'] = code_str
        # 把代码存储进入缓存。
        cache.set(key=redis_key, value=json.dumps(function_code_mapping), timeout=None)
        return function_code_mapping

    def generation(self, user_demand, redis_key) -> tuple[bool, str]:
        code_model_config = json.loads(cache.get('code_model'))
        # 获取上一次生成的代码，基于上一次生成的内容可以进一步迭代
        last_round_code = ""
        _code = cache.get(redis_key)
        # if _code:
        #     _code_json = json.loads(_code)
        #     last_round_code = _code_json.get("__raw_code__", "")
        prompt = f"""你是一个专业的Python编程助手，具有以下能力：

                1. 业务代码生成：根据用户需求生成高质量的Python业务代码
                2. 测试生成：为生成的代码创建完整的单元测试（如果测试用例固定就不用生成测试用例了）
                3. 代码执行：执行代码并捕获错误信息
                4. 自动修复：根据错误信息自动修复代码问题

                请始终确保：
                - 碰到异常信息必须抛出，并且必须抛出得完善（比如一个Http请求，必须把响应体里面的内容全部携带进入异常，这样方便后续代码生成）
                - 测试用例覆盖主要功能，测试用例和主代码写在一起，一口气生成即可
                - 由于生成的代码会写到一个py文件里面，所以需要保证 “pytest xxxx.py -k test_case” 这个命令可以执行成功。所以生成的代码一定要规范

                需要生成的代码模版如下:
                {self.code_template}\n
                额外的重点内容的说明:
                {self.system_prompt_patch}\n
                上一次生成的代码为如下（如果存在你可以参考一波，可能用户想基于上一轮代码继续迭代）：
                {last_round_code}

                工作流程：
                1. 理解用户需求
                2. 生成用户需求初始代码
                3. 生成对应的测试用例（如果测试用例固定就不用生成测试用例了）
                4. 执行测试用例
                5. 如果出现错误，分析错误信息并修复代码，并再次调用代码执行工具去看看是否还有异常
                6. 重复步骤3-5直到代码完全正确

                注意：
                - 最后成功运行通过的代码只返回代码的字符串内容即可(注意：不需要```python xxxx ``` 进行包装)
                - 每次生成代码之后都要调用代码执行工具去运行直到成功为止，不能生成完了代码就结束直接返回结果了
                """

        # 创建智能体
        agent = create_react_agent(
            model=code_generation_llm.with_config(config=code_model_config),
            tools=self.tools,
            prompt=prompt,
        )
        is_success = False
        code = ""
        # noinspection PyTypeChecker
        for stream_mode, chunk in agent.stream(
                {
                    "messages": [
                        {"role": "user", "content": user_demand}
                    ]
                },
                {
                    "recursion_limit": 2 * self.max_iterations + 1
                },
                stream_mode=["updates", "messages"],
        ):
            if stream_mode == "updates":
                # 显示工具调用过程
                if chunk.get('agent'):
                    try:
                        code = json.loads(
                            chunk['agent']['messages'][0].additional_kwargs['tool_calls'][0]['function']['arguments']
                        )['code']
                    except (KeyError, TypeError, json.JSONDecodeError):
                        is_success = True
                        try:
                            # 代码有错误纠正之后的结果
                            code = chunk['agent']['messages'][0].additional_kwargs['tool_calls'][0]['function'][
                                'arguments']
                        except Exception:
                            # Tool里面单元测试运行成功
                            code = chunk['agent']['messages'][0].content
        self.parse_generation_code(code_str=code, redis_key=redis_key)
        return is_success, code
