from pprint import pprint

from langchain_core.tools import ToolException

from agent.utils import create_dynamic_tool
from ai_native_core.model import knowledge_rerank_model


def test_dynamic_tool():
    # 定义工具元数据
    tool_metadata = {
        "name": "jms跳板机机器申请",
        "description": "公司内部开发人员申请内部jms跳板机里面对应ip的机器的时候使用",
        "input_schema": {
            "type": "object",
            "properties": {
                "ip_address": {"type": "string", "description": "IP地址"},
                "time": {"type": "string", "description": "申请时长"}
            },
            "required": ["ip_address", "time"]
        },
        "function_code": """
if not ip_address.startswith("192.168"):
    raise ToolException(f"IP地址不合法,必须以192.168开头,当前ip地址为{ip_address}")
result = f"申请机器成功,ip地址为{ip_address},申请时长为{time}"
print(state)
print(config)
    """
    }

    _config = {
        "configurable": {
            "sys_config": {
                "tenant_id": "tenant1",
                "user_id": "user1",
            },
            "chat_bot_config": {
                "prompt": "你是情感伴侣",
            },
            "memory_config": {
                "max_tokens": 256,
            },
        }
    }

    # 创建动态工具类
    tool = create_dynamic_tool(
        name=tool_metadata["name"],
        description=tool_metadata["description"],
        input_schema=tool_metadata["input_schema"],
        function_code=tool_metadata["function_code"]
    )

    # 使用示例
    print(tool.name)  # 输出: jms跳板机机器申请
    print(tool.description)

    # 测试_run方法
    try:
        # 测试非法IP
        print(
            tool._run(
                # 用户/Bot传入的参数,保证最大限度提升决策能力
                ip_address="10.0.0.1",
                time="2h",
                # 状态图参数，最大限度复用图状态，动态决策
                state="xxx",
                # 运行时配置参数，最大限度提升灵活度，注入画像等内容
                config=_config
            )
        )
    except ToolException as e:
        print(e)  # 输出: IP地址不合法,必须以192.168开头,当前ip地址为10.0.0.1

    # 测试合法IP
    print(tool._run(ip_address="192.168.1.1", time="2h", state="xxx", config=_config))
    # 输出: 申请机器成功,ip地址为192.168.1.1,申请时长为2h

    # 测试大模型调度Tool
    for chunk in knowledge_rerank_model.bind_tools([
        tool
    ]).stream(
        [
            {
                "role": "system",
                "content": "你是超级助手"
            },
            {
                "role": "user",
                "content": "我要申请一个月ip为192.168.3.4的机器"
            }
        ],
        config=_config
    ):
        pprint(chunk)
