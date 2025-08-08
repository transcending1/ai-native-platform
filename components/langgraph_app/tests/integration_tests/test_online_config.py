from pprint import pprint

import pytest
from langgraph_sdk import get_sync_client

from agent import graph
from ai_native_core.utils.vector_store import get_vector_stores

_config = {
    "configurable": {
        "last_model": "Qwen3-30B-A3B-FP8",
        "rag_config": {
            "is_rag": True,
            "is_rerank": True,
            "rerank_top_n": 3,
            "is_llm_rerank": False,
            "namespace_list": [
                "5"
            ],
            "retrieve_top_n": 5,
            "rerank_threshold": 0.4,
            "retrieve_threshold": 0.2,
            "is_structured_output": False
        },
        "sys_config": {
            "owner": "1"
        },
        "tool_config": {
            "is_rag": True,
            "is_rerank": True,
            "rerank_top_n": 3,
            "is_llm_rerank": False,
            "max_iterations": 3,
            "namespace_list": [
                "5"
            ],
            "retrieve_top_n": 5,
            "rerank_threshold": 0.4,
            "retrieve_threshold": 0.2
        },
        "last_api_key": "aB3fG7kL9mN1pQ5rS8tU2vW4xYz0Aa",
        "last_base_url": "http://222.186.32.152:10000/v1",
        "memory_config": {
            "max_tokens": 2560
        },
        "chat_bot_config": {
            "prompt": "你是门禁机器人，专注于帮助来公司门口回复各种各样的问题。"
        },
        "last_extra_body": {
            "chat_template_kwargs": {
                "enable_thinking": False
            }
        },
        "last_max_tokens": 5120,
        "last_temperature": 0,
        "last_model_provider": "openai",
        "knowledge_rerank_model": "",
        "knowledge_rerank_api_key": "aB3fG7kL9mN1pQ5rS8tU2vW4xYz0Aa",
        "knowledge_rerank_base_url": "http://222.186.32.152:10000/v1",
        "knowledge_rerank_extra_body": {
            "chat_template_kwargs": {
                "enable_thinking": False
            }
        },
        "knowledge_rerank_max_tokens": 5120,
        "knowledge_rerank_temperature": 0,
        "knowledge_rerank_model_provider": ""
    }
}

GRAPH_ID = "agent"


@pytest.mark.asyncio
async def test_retriever() -> None:
    vector_store_list = get_vector_stores(
        tenant="none",
        namespace_list=['5']
    )
    vector_store = vector_store_list[0]
    res = await vector_store.asimilarity_search_with_score(
        "爱因斯坦会议室密码是多少?",
        k=5,
    )
    pprint(res)


@pytest.mark.asyncio
async def test_only_rag_in_graph() -> None:
    langgraph_client = get_sync_client(url="http://222.186.32.152:32710", api_key=None)

    assistant = langgraph_client.assistants.get(
        assistant_id='cd398240-8244-4762-98d4-6d43bfdb3df7'
    )
    input_params = {
        "question": "徐鹏的职责是啥？",
    }
    # streaming非常灵活，可以从里面获取任何自己想要的信息
    async for message, metadata in graph.astream(
            input_params,
            config=assistant['config'],
            stream_mode="messages"
    ):
        if "last_model" in metadata.get('tags', []):
            print(message.content, end="")


@pytest.mark.asyncio
async def test_only_tool_in_graph() -> None:
    langgraph_client = get_sync_client(url="http://222.186.32.152:32710", api_key=None)

    assistant = langgraph_client.assistants.get(
        assistant_id='cd398240-8244-4762-98d4-6d43bfdb3df7'
    )
    input_params = {
        "question": "上海的天气咋样？",
    }
    # streaming非常灵活，可以从里面获取任何自己想要的信息
    async for stream_mode, chuck in graph.astream(
            input_params,
            config=assistant['config'],
            stream_mode=["updates", "messages"]
    ):
        # 最终大模型产生的消息可以展示给用户
        if stream_mode == "messages":
            message, metadata = chuck
            print(stream_mode, chuck)
        # 具体的调用过程可以展示给用户
        elif stream_mode == "updates":
            print(stream_mode, chuck)
