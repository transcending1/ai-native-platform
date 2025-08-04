from langchain.chat_models import init_chat_model

# 创建默认的LLM实例
llm = init_chat_model(
    model="gpt-3.5-turbo",  # 添加默认模型（可以是任意有效模型名）
    extra_body={
        "chat_template_kwargs": {
            "enable_thinking": False
        }
    },
    configurable_fields=(  # 可以动态配置传入的参数
        "model",
        "model_provider",
        "temperature",
        "max_tokens",
        "api_key",
        "base_url",
        "extra_body"
    ),
    config_prefix="global",
    tags=["global_model"],
)
