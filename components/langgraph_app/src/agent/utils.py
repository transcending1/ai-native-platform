from typing import Optional, Any, Dict, Type

from langchain.tools import BaseTool
from langchain_core.tools import ToolException, ArgsSchema


def create_dynamic_tool(
        name: str,
        description: str,
        input_schema: Dict[str, Any],
        function_code: str,
) -> Type[BaseTool]:
    """
    动态创建工具类及其_run方法

    :param name: 工具名称
    :param description: 工具描述
    :param input_schema: 输入参数的JSON Schema
    :param function_code: _run函数的执行代码字符串
    :return: 动态生成的工具类
    """

    # 1. 创建_run函数
    def _run_function(*args, **kwargs):
        # 动态执行函数代码
        # 固定的参数
        local_vars = {
            "state": kwargs.get("state"),
            "config": kwargs.get("config"),
            "run_manager": kwargs.get("run_manager"),
            "ToolException": ToolException  # 确保异常类型可用
        }
        # 动态参数
        for param in input_schema["properties"]:
            local_vars[param] = kwargs.get(param)

        try:
            exec(function_code, globals(), local_vars)
        except Exception as e:
            raise ToolException(f"执行错误: {str(e)}")
        # 返回函数的结果给大模型
        return local_vars.get("result", "No result returned")

    # 设置函数签名
    _run_function.__name__ = "_run"

    # 2. 动态创建工具类 - 修复点：添加类型注解
    annotations = {
        "name": str,
        "description": str,
        "args_schema": Optional[ArgsSchema],
        "return_direct": bool,
        "handle_tool_error": bool,
    }
    tool_class = type(
        f"{name}Tool",
        (BaseTool,),
        {
            "__annotations__": annotations,
            # 添加类型注解
            "name": name,
            "description": description,
            "args_schema": input_schema,
            "return_direct": False,
            "handle_tool_error": True,
            "_run": _run_function
        }
    )

    return tool_class()
