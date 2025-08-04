from typing import Optional, Any, Dict, Type

from langchain.tools import BaseTool
from langchain_core.tools import ToolException, ArgsSchema
from jinja2 import Template


def create_dynamic_tool(
        name: str,
        description: str,
        input_schema: Dict[str, Any],
        function_code: str,
        output_schema: Optional[Dict[str, Any]],
        jinja2_template: Optional[str],
        is_jinja2_template: bool = True,
        html_template: Optional[str] = None,
        is_html_template: bool = False
) -> Type[BaseTool]:
    """
    动态创建工具类及其_run方法

    :param name: 工具名称
    :param description: 工具描述
    :param input_schema: 输入参数的JSON Schema
    :param function_code: _run函数的执行代码字符串
    :param output_schema: 函数返回值的JSON Schema
    :param jinja2_template: Jinja2模板，用于将output_schema扁平化为人类可读的字符串
    :param is_jinja2_template: 是否使用Jinja2模板格式化输出,默认开启为了对接Agent,关闭情况下就是对接Workflow
    :param html_template: HTML模板，用于在Web前端优雅展示工具结果
    :param is_html_template: 是否使用HTML模板渲染输出，用于Web前端展示
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
        function_kwargs = {}
        for param in input_schema["properties"]:
            function_kwargs[param] = kwargs.get(param)
        
        # 添加固定参数到函数调用参数中
        function_kwargs.update({
            "state": kwargs.get("state"),
            "config": kwargs.get("config"),
            "run_manager": kwargs.get("run_manager"),
        })

        try:
            # 执行函数定义代码
            exec(function_code, globals(), local_vars)
            
            # 调用定义的main函数
            if 'main' in local_vars:
                result = local_vars['main'](**function_kwargs)
                
                # 优先使用HTML模板渲染（用于Web前端展示）
                if is_html_template and html_template and result:
                    try:
                        template = Template(html_template)
                        html_result = template.render(result)
                        return {
                            "type": "html",
                            "content": html_result,
                            "raw_data": result
                        }
                    except Exception as template_error:
                        # 如果HTML模板渲染失败，返回原始结果并添加警告
                        return {
                            "type": "error",
                            "message": f"HTML模板渲染失败: {str(template_error)}",
                            "raw_data": result
                        }
                
                # 如果提供了jinja2模板，则使用模板格式化返回结果
                elif is_jinja2_template and jinja2_template and result:
                    try:
                        template = Template(jinja2_template)
                        formatted_result = template.render(result)
                        return formatted_result
                    except Exception as template_error:
                        # 如果模板渲染失败，返回原始结果并添加警告
                        return f"模板渲染失败: {str(template_error)}\n原始结果: {result}"
                
                return result
            else:
                raise ToolException("函数代码中未找到main函数")
                
        except Exception as e:
            raise ToolException(f"执行错误，异常信息：{str(e)}")

    # 设置函数签名
    _run_function.__name__ = "_run"

    # 2. 动态创建工具类 - 修复点：添加类型注解
    annotations = {
        "name": str,
        "description": str,
        "args_schema": Optional[ArgsSchema],
        "return_direct": bool,
        "handle_tool_error": bool,
        "output_schema": Optional[Dict[str, Any]],
        "jinja2_template": Optional[str],
        "html_template": Optional[str],
        "is_html_template": bool,
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
            "output_schema": output_schema,
            "jinja2_template": jinja2_template,
            "html_template": html_template,
            "is_html_template": is_html_template,
            "_run": _run_function
        }
    )

    return tool_class()
