from typing import List

from pydantic import BaseModel, Field

from core.models.llm import llm
from core.models.utils import from_examples_to_messages


class PropertySchema(BaseModel):
    """工具函数的输入输出参数的JSON Schema中的属性"""
    type: str = Field(
        'string', description="属性的类型,枚举值:1.string,2.int,3.bool,4.float",
    )
    description: str = Field(
        ..., description="属性的描述,用于帮助用户理解该属性的含义",
    )
    default: object = Field(
        ...,
        description="属性的默认值,为type中对应类型的默认值，非必填字段,如string类型的默认值为''(空字符串),int类型的默认值为0,boolean类型的默认值为false, float类型的默认值为0.0",
    )


class InputOutputSchema(BaseModel):
    """工具函数的输入参数的JSON Schema"""
    type: str = Field(
        "object", description="输入输出参数的类型，固定为object",
    )
    properties: dict = Field(
        ..., description="输入输出参数的属性,如字段名和类型等",
    )
    required: List[str] = Field(
        ..., description="输入输出必填字段列表",
    )


class ToolGeneration(BaseModel):
    """根据用户的问题生成工具函数,工具的输入输出schema,工具的名称，描述等信息"""
    name: str = Field(
        ..., description="工具名称",
    )
    description: str = Field(
        ..., description="工具描述,用于帮助用户理解工具的功能",
    )
    input_schema: InputOutputSchema = Field(
        ..., description="工具的输入参数的JSON Schema,用于验证用户输入",
    )
    few_shots: List[str] = Field(
        ..., description="工具的触发示例,用于帮助用户理解如何使用该工具",
    )
    output_schema: InputOutputSchema = Field(
        ..., description="工具的输出参数的JSON Schema,用于验证工具返回值",
    )
    output_schema_jinja2_template: str = Field(
        ...,
        description='Jinja2模板,用于将工具的输出参数output_schema渲染为人类可读的字符串。'
                    '比如在加法计算的场景下函数输出的output json字符串为:{"result": 3}'
                    '那么输出可以是"计算结果为{{ result }}"，渲染后输出"计算结果为3"',
    )
    html_template: str = Field(
        ...,
        description="HTML模板,用于在Web前端优雅展示工具结果,为了展示到界面上,需要将工具的输出参数渲染为人类可读的html",
    )
    function_code: str = Field(
        ...,
        description="工具函数的代码,用于执行工具的具体逻辑,如调用API等.且函数名必须为main，"
                    "传参必须与input_schema中的属性一致并且都是关键字参数，"
                    "返回值必须是一个字典，且字典的键必须与output_schema中的属性一致"
    )


tool_generator_examples_to_messages = [
    (
        "请帮我生成一个JMS申请机器的工具函数:IP地址不合法,必须以192.168开头,申请可以有时间以天为单位,默认一周（7d）.",
        ToolGeneration(
            name='申请JMS机器',
            description='申请JMS机器的工具',
            input_schema=InputOutputSchema(
                type='object',
                properties={
                    'ip': {'type': 'string', 'description': '要申请的机器IP地址'},
                    'days': {'type': 'integer', 'description': '申请时间（天），默认为7天'}
                },
                required=['ip']
            ),
            few_shots=[
                '申请机器，IP地址为192.168.1.100，申请时间3天',
                '申请机器，IP地址为192.168.0.5'
            ],
            output_schema=InputOutputSchema(
                type='object',
                properties={
                    'status': {'type': 'string', 'description': '申请状态（成功/失败）'},
                    'message': {'type': 'string', 'description': '申请结果信息'}
                },
                required=['status', 'message']
            ),
            output_schema_jinja2_template="申请{{ '成功' if status == '成功' else '失败' if status == '失败' else '未知状态' }} - {{ message }}",
            html_template="""{% set status_class = 'success' if status == '成功' else 'error' if status == '失败' else 'info' %}
<div class="result-card result-{{ status_class }}">
  <div class="result-status">申请{{ status }}</div>
  <div class="result-message">{{ message }}</div>
</div>

<style>
.result-card {
  padding: 16px;
  border-radius: 8px;
  margin: 12px 0;
  border-left: 4px solid;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.result-success {
  background-color: #f0f9eb;
  border-color: #67c23a;
  color: #67c23a;
}

.result-error {
  background-color: #fef0f0;
  border-color: #f56c6c;
  color: #f56c6c;
}

.result-info {
  background-color: #f4f4f5;
  border-color: #909399;
  color: #909399;
}

.result-status {
  font-weight: bold;
  margin-bottom: 8px;
}

.result-message {
  color: #333;
}
</style>""",
            function_code="""def main(
        ip="", 
        days=7,
        state=None,
        config=None,
        run_manager=None,
        **kwargs
):
    if not ip.startswith('192.168'):
        return {'status': '失败', 'message': 'IP地址不合法，必须以192.168开头'}
    if days < 1:
        return {'status': '失败', 'message': '申请时间必须大于等于1天'}
    return {'status': '成功', 'message': f'机器申请成功，IP: {ip}, 申请时间: {days}天'}""")

    )
]

tool_generator_llm = llm.with_structured_output(
    ToolGeneration
)
