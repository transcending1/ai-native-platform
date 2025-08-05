import json
import os
from pprint import pprint

import allure
import django
from django.core.cache import cache

from core.models.extractor.tool_generator import tool_generator_llm, tool_generator_examples_to_messages
from core.models.utils import from_examples_to_messages

# 设置Django环境
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "llm_api.settings.dev_settings")
django.setup()

from core.models.llm import llm


def test_normal_llm():
    with allure.step("调用大语言模型调试"):
        # 调用大语言模型
        res = llm.invoke(
            "你是谁？",
            config={
                "configurable": {
                    "global_model": "Qwen3-30B-A3B-FP8",  # 模型ID
                    "global_model_provider": "openai",  # 模型提供商
                    "global_temperature": 0.1,  # 固定写死
                    "global_base_url": os.getenv('CHAT_MODEL_DEFAULT_BASE_URL'),  # 基础URL
                    "global_api_key": os.getenv('CHAT_MODEL_DEFAULT_API_KEY'),  # API密钥
                }
            }
        )
        # res.content是一个字符串，大模型返回的内容
        print(res.content)


def test_global_llm():
    """测试从Redis获取配置的功能"""
    with allure.step("配置文件存储到redis里面"):
        new_config = {
            "global_temperature": 0.1,
            # "global_max_tokens": 35000,
            "global_base_url": os.getenv('CHAT_MODEL_DEFAULT_BASE_URL'),
            "global_api_key": os.getenv('CHAT_MODEL_DEFAULT_API_KEY'),
            "global_model": "Qwen3-30B-A3B-FP8",
            "global_model_provider": "openai",
        }

        # 将配置存储到Redis 缓存永不过期
        cache.set('code_model', json.dumps(new_config), timeout=None)
    with allure.step("更新配置"):
        # 更新配置
        cache.set('code_model', json.dumps(new_config), timeout=None)
    with allure.step("从redis中获取配置"):
        # 从Redis获取配置
        config_json = json.loads(cache.get('code_model'))
    with allure.step("调用大语言模型调试"):
        # 调用大语言模型
        res = llm.invoke(
            "你是谁？",
            config={
                "configurable": config_json
            }
        )
        # res.content是一个字符串，大模型返回的内容
        print(res.content)


def test_tool_generation_llm():
    """测试工具生成大语言模型"""
    with allure.step("调用工具生成大语言模型"):
        messages = from_examples_to_messages(
            user_question="请帮我写一个请假的函数，输入请假天数，哪时候开始请假即可。",
            examples=tool_generator_examples_to_messages
        )
        config_json = json.loads(cache.get('code_model'))
        res = tool_generator_llm.invoke(
            messages,
            config={
                "configurable": config_json
            }
        )
        pprint(res)
