import os

import pytest

from agent import graph


def get_input_config(
        thread_id,
        is_common_rag=True,
        is_tool_rag=True
):
    return {
        "configurable": {
            "sys_config": {
                "tenant_id": "tenant1",
                "user_id": "user1",
            },
            "chat_bot_config": {
                "prompt": "你是情感伴侣",
            },
            "rag_config": {
                "prompt": "你是情感伴侣",
                "is_rag": is_common_rag,
                "retrieve_top_n": 5,
                "retrieve_threshold": 0.2,
                "is_rerank": True,
                "rerank_top_n": 3,
                "rerank_threshold": 0.4,
                "is_llm_rerank": True,
                "namespace_list": ["namespace1"],
                "is_structured_output": True
            },
            "tool_config": {
                "is_rag": is_tool_rag,
                "retrieve_top_n": 5,
                "retrieve_threshold": 0.2,
                "is_rerank": True,
                "rerank_top_n": 3,
                "rerank_threshold": 0.4,
                "is_llm_rerank": True,
                "max_iterations": 3,
                "namespace_list": ["namespace1"],
            },
            "memory_config": {
                "max_tokens": 256,
            },
            "last_temperature": 0,
            "last_max_tokens": 512,
            "last_api_key": os.getenv('CHAT_MODEL_DEFAULT_API_KEY'),
            "last_extra_body": {
                "chat_template_kwargs": {
                    "enable_thinking": False
                }
            },
            "knowledge_rerank_temperature": 0,
            "knowledge_rerank_max_tokens": 512,
            "knowledge_rerank_api_key": os.getenv('CHAT_MODEL_DEFAULT_API_KEY'),
            "knowledge_rerank_extra_body": {
                "chat_template_kwargs": {
                    "enable_thinking": False
                }
            },
            # between different tenants and users 会话session
            "thread_id": thread_id
        }
    }


@pytest.mark.asyncio
async def test_only_rag_in_graph() -> None:
    input_params = {
        "question": "法拉第会议室号码是啥?",
    }
    input_config = get_input_config(
        "abc123",
        is_common_rag=True,
        is_tool_rag=False
    )
    # streaming非常灵活，可以从里面获取任何自己想要的信息
    async for message, metadata in graph.astream(
            input_params,
            config=input_config,
            stream_mode="messages"  # 会执行graph中所有产生messages的消息。graph中只要定义同步的invoke即可
    ):
        if "last_model" in metadata.get('tags', []):
            print(message.content, end="")
    # state1_messages = graph.get_state(input_config).values['messages']
    # pprint(state1_messages)
    # 第二轮对话
    # input_params = {
    #     "question": "我前面说了啥?",
    # }
    # input_config = get_input_config("abc123")
    # # 第二轮对话,对话内部的messages会reduce叠加
    # async for message, metadata in graph.astream(
    #         input_params,
    #         config=input_config,
    #         stream_mode="messages"
    # ):
    #     if "last_model" in metadata.get('tags', []):
    #         print(message.content, end="")
    # state2_messages = graph.get_state(input_config).values['messages']
    # pprint(state2_messages)


@pytest.mark.asyncio
async def test_only_tool_in_graph() -> None:
    input_params = {
        "question": "我要使用jms去申请一台机器，192.168.3.1，一周时长"
    }
    input_config = get_input_config(
        "abc123",
        is_common_rag=False,
        is_tool_rag=True
    )
    # streaming非常灵活，可以从里面获取任何自己想要的信息
    async for stream_mode, chuck in graph.astream(
            input_params,
            config=input_config,
            stream_mode=["updates", "messages"]  # 会执行graph中所有产生messages的消息。graph中只要定义同步的invoke即可
    ):
        # 最终大模型产生的消息可以展示给用户
        if stream_mode == "messages":
            message, metadata = chuck
            print(stream_mode, chuck)
        # 具体的调用过程可以展示给用户
        elif stream_mode == "updates":
            print(stream_mode, chuck)


@pytest.mark.asyncio
async def test_tool_and_rag_in_graph() -> None:
    input_params = {
        "question": "我要使用jms去申请一台机器，192.168.3.1，一周时长.另外我们公司的法拉第会议室号是多少?"
    }
    input_config = get_input_config(
        "abc123",
        is_common_rag=True,
        is_tool_rag=True
    )
    # streaming非常灵活，可以从里面获取任何自己想要的信息
    async for stream_mode, chuck in graph.astream(
            input_params,
            config=input_config,
            stream_mode=["updates", "messages"]  # 会执行graph中所有产生messages的消息。graph中只要定义同步的invoke即可
    ):
        # 最终大模型产生的消息可以展示给用户
        if stream_mode == "messages":
            message, metadata = chuck
            print(stream_mode, chuck)
        # 具体的调用过程可以展示给用户
        elif stream_mode == "updates":
            print(stream_mode, chuck)
