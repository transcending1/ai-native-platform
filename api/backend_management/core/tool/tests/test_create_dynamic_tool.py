import os
from pprint import pprint

import django
from langgraph.prebuilt import create_react_agent

from ai_native_core.model import knowledge_rerank_model
from langchain_core.tools import ToolException

from agent.utils import create_dynamic_tool

# 设置Django环境
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "llm_api.settings.dev_settings")
django.setup()


def main(
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
    return {'status': '成功', 'message': f'机器申请成功，IP: {ip}, 申请时间: {days}天'}


def test_dynamic_tool():
    # 定义工具元数据
    tool_metadata = {
        "name": "jms跳板机机器申请",
        "description": "公司内部开发人员申请内部jms跳板机里面对应ip的机器的时候使用",
        "input_schema": {
            "type": "object",
            "properties": {
                "ip_address": {"type": "string", "description": "IP地址"},
                "time": {"type": "string", "description": "申请时长", "default": "一周"}
            },
            "required": ["ip_address", "time"]
        },
        "output_schema": {
            "type": "object",
            "properties": {
                "is_success": {"type": "boolean", "description": "申请是否成功"},
                "ip_address": {"type": "string", "description": "申请的IP地址"},
                "time": {"type": "string", "description": "申请的时长"}
            }
        },
        "jinja2_template": "机器申请结果：{% if is_success %}成功{% else %}失败{% endif %}。IP地址：{{ ip_address }}，申请时长：{{ time }}。",
        "function_code": """def main(
        ip_address: str,
        time: str = "一周",
        state=None,
        config=None,
        run_manager=None
):
    # 在此处进行各种工具包的导入
    if not ip_address.startswith("192.168"):
        # 如果不符合规范就主动抛出异常，告知机器人返回结果通知人类
        raise ToolException(f"IP地址不合法,必须以192.168开头,当前ip地址为{ip_address}")
    return {
        "is_success": True,
        "ip_address": ip_address,
        "time": time,
    }"""

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
        function_code=tool_metadata["function_code"],
        output_schema=tool_metadata["output_schema"],
        jinja2_template=tool_metadata["jinja2_template"],
        # 人类使用模式。
        is_jinja2_template=False
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
    # 输出: 机器申请结果：成功。IP地址：192.168.1.1，申请时长：2h。

    agent = create_react_agent(
        model=knowledge_rerank_model,
        tools=[tool],
        prompt=f"你是情感伴侣，请使用工具获取服务器状态。",
    )


    # # # 测试大模型调度Tool
    # for chunk in knowledge_rerank_model.bind_tools([
    #     tool
    # ]).stream(
    #     [
    #         {
    #             "role": "system",
    #             "content": "你是超级助手"
    #         },
    #         {
    #             "role": "user",
    #             "content": "我要申请一个月ip为192.168.3.4的机器"
    #         }
    #     ],
    #     config=_config
    # ):
    #     pprint(chunk)


def test_html_template():
    """测试HTML模板渲染功能"""
    # 定义带HTML模板的工具元数据
    html_tool_metadata = {
        "name": "服务器状态监控",
        "description": "监控服务器状态并生成HTML报告",
        "input_schema": {
            "type": "object",
            "properties": {
                "server_name": {"type": "string", "description": "服务器名称"},
                "check_type": {"type": "string", "description": "检查类型", "default": "basic"}
            },
            "required": ["server_name"]
        },
        "output_schema": {
            "type": "object",
            "properties": {
                "server_name": {"type": "string", "description": "服务器名称"},
                "status": {"type": "string", "description": "服务器状态"},
                "cpu_usage": {"type": "number", "description": "CPU使用率"},
                "memory_usage": {"type": "number", "description": "内存使用率"},
                "disk_usage": {"type": "number", "description": "磁盘使用率"},
                "uptime": {"type": "string", "description": "运行时间"}
            }
        },
        "jinja2_template": "服务器 {{ server_name }} 状态：{{ status }}，CPU使用率：{{ cpu_usage }}%，内存使用率：{{ memory_usage }}%",
        "html_template": """
        <div class="server-status-card" style="border: 1px solid #ddd; border-radius: 8px; padding: 16px; margin: 8px; background: white;">
            <h3 style="color: #333; margin-top: 0;">🖥️ {{ server_name }} 服务器状态</h3>
            <div style="margin: 12px 0;">
                <span class="status-badge" style="
                    padding: 4px 12px; 
                    border-radius: 20px; 
                    font-weight: bold;
                    {% if status == 'online' %}
                        background: #e7f5e7; color: #2d8f2d;
                    {% elif status == 'warning' %}
                        background: #fff3cd; color: #856404;
                    {% else %}
                        background: #f8d7da; color: #721c24;
                    {% endif %}
                ">{{ status.upper() }}</span>
            </div>
            <div class="metrics" style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin: 16px 0;">
                <div class="metric">
                    <div style="font-size: 12px; color: #666; margin-bottom: 4px;">CPU使用率</div>
                    <div class="progress-bar" style="background: #f0f0f0; border-radius: 4px; height: 8px; position: relative;">
                        <div style="
                            background: {% if cpu_usage > 80 %}#dc3545{% elif cpu_usage > 60 %}#ffc107{% else %}#28a745{% endif %}; 
                            height: 100%; 
                            border-radius: 4px; 
                            width: {{ cpu_usage }}%;
                        "></div>
                    </div>
                    <div style="font-size: 14px; font-weight: bold; margin-top: 4px;">{{ cpu_usage }}%</div>
                </div>
                <div class="metric">
                    <div style="font-size: 12px; color: #666; margin-bottom: 4px;">内存使用率</div>
                    <div class="progress-bar" style="background: #f0f0f0; border-radius: 4px; height: 8px; position: relative;">
                        <div style="
                            background: {% if memory_usage > 80 %}#dc3545{% elif memory_usage > 60 %}#ffc107{% else %}#28a745{% endif %}; 
                            height: 100%; 
                            border-radius: 4px; 
                            width: {{ memory_usage }}%;
                        "></div>
                    </div>
                    <div style="font-size: 14px; font-weight: bold; margin-top: 4px;">{{ memory_usage }}%</div>
                </div>
            </div>
            <div style="font-size: 12px; color: #666; margin-top: 12px;">
                📈 磁盘使用率: {{ disk_usage }}% | ⏱️ 运行时间: {{ uptime }}
            </div>
        </div>
        """,
        "function_code": """def main(
        server_name: str,
        check_type: str = "basic",
        state=None,
        config=None,
        run_manager=None
):
    import random
    
    # 模拟服务器监控数据
    statuses = ["online", "warning", "offline"]
    status = random.choice(statuses[:2])  # 避免offline状态以便展示
    
    return {
        "server_name": server_name,
        "status": status,
        "cpu_usage": round(random.uniform(20, 95), 1),
        "memory_usage": round(random.uniform(30, 85), 1), 
        "disk_usage": round(random.uniform(40, 90), 1),
        "uptime": f"{random.randint(1, 30)}天{random.randint(1, 23)}小时"
    }"""
    }

    _config = {
        "configurable": {
            "sys_config": {
                "tenant_id": "tenant1",
                "user_id": "user1",
            },
            "chat_bot_config": {
                "prompt": "你是系统监控助手",
            },
            "memory_config": {
                "max_tokens": 256,
            },
        }
    }

    print("\n=== 测试HTML模板渲染 ===")

    # 创建带HTML模板的工具
    html_tool = create_dynamic_tool(
        name=html_tool_metadata["name"],
        description=html_tool_metadata["description"],
        input_schema=html_tool_metadata["input_schema"],
        function_code=html_tool_metadata["function_code"],
        output_schema=html_tool_metadata["output_schema"],
        jinja2_template=html_tool_metadata["jinja2_template"],
        is_jinja2_template=False,  # 关闭Jinja2模板
        html_template=html_tool_metadata["html_template"],
        is_html_template=True  # 开启HTML模板
    )

    # 测试HTML渲染
    html_result = html_tool._run(
        server_name="Web-Server-01",
        check_type="detailed",
        state="xxx",
        config=_config
    )

    print("HTML渲染结果类型:", html_result.get("type"))
    print("原始数据:", html_result.get("raw_data"))
    print("HTML内容预览 (前200字符):", html_result.get("content", "")[:200])
    # save to temp.html
    with open("temp.html", "w", encoding="utf-8") as f:
        f.write(html_result.get("content", ""))

    # 创建对比的Jinja2模板工具
    print("\n=== 对比Jinja2模板渲染 ===")
    jinja2_tool = create_dynamic_tool(
        name=html_tool_metadata["name"],
        description=html_tool_metadata["description"],
        input_schema=html_tool_metadata["input_schema"],
        function_code=html_tool_metadata["function_code"],
        output_schema=html_tool_metadata["output_schema"],
        jinja2_template=html_tool_metadata["jinja2_template"],
        is_jinja2_template=True,  # 开启Jinja2模板
        html_template=html_tool_metadata["html_template"],
        is_html_template=False  # 关闭HTML模板
    )

    jinja2_result = jinja2_tool._run(
        server_name="Web-Server-01",
        check_type="detailed",
        state="xxx",
        config=_config
    )

    print("Jinja2渲染结果:", jinja2_result)

    agent = create_react_agent(
        model=knowledge_rerank_model,
        tools=[jinja2_tool],
        prompt="你是系统监控助手，请使用工具获取服务器状态。",
    )




if __name__ == "__main__":
    test_dynamic_tool()
    test_html_template()
