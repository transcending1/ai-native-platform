import os
import django

from core.agent.coding.embedding import embedding_code_generator

# os.environ["LANGSMITH_TRACING"] = "true"
# os.environ["LANGSMITH_API_KEY"] = "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"
# 设置Django环境
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "llm_api.settings.dev_settings")
django.setup()


def test_embedding_coding():
    user_demand = """
    headers = {
                "Content-Type": "application/json",
            }
    请求头：Authorization：Bearer xxxxxxxxxxxxxxxxxxxxxxx 用户的Token
    请求体：inputs 内嵌套文本  ['文本1','文本2']
    接口：http://222.186.32.152:10001/embed

    实现一波Embedding的请求示例
    Token为 aB3fG7kL9mN1pQ5rS8tU2vW4xYz0Aa
    """
    # 更具用户需求生成底代码
    is_success, code = embedding_code_generator.generation(user_demand, redis_key="global_embedding")
    # is_success 代表代码生成是否运行单元测试成功
    print(is_success)
    # code 代表单元测试用例代码
    print(code)
