import asyncio
import json
from collections import defaultdict
from typing import List

from langchain_core.prompts import ChatPromptTemplate
from langgraph.prebuilt import create_react_agent
from pydantic import BaseModel, Field

from agent.configuration import Configuration
from agent.state import State
from agent.utils import create_dynamic_tool
from ai_native_core.model import knowledge_rerank_model, last_model
from ai_native_core.rerank import reranker
from ai_native_core.utils.vector_store import get_vector_stores


def get_tool_context(context: list) -> str:
    """根据知识生成提示"""
    prompt = ""
    for idx, doc in enumerate(context):
        prompt += f"工具编号:{idx}\n工具描述:{doc.page_content}\n"
    return prompt


tool_rerank_prompt_template = ChatPromptTemplate.from_messages(
    [
        {
            "role": "system",
            "content": '''你是问题知识相关性分析专家,帮助用户找出和用户问题非常相关的工具编号id列表.
要求:
分析出用户最可能使用的一系列工具并标记出与用户问题最相关的工具编号id列表

工具列表如下:
{context}
用户的问题如下:
{question}
请你给出和用户问题相关的工具编号
''',
        }
    ]
)


class QuotedTool(BaseModel):
    """根据用户问题判断最相关的工具编号"""
    source_ids: List[int] = Field(
        ..., description="命中的知识编号列表",
    )


def get_agent(
        state,
        prompt_prefix,
        response_format=None
):
    tools = []
    for tool_doc in state['tool_context']:
        # TODO:根据不同的Tool类型通过适配器构建不同的Tool用来被编排。
        if tool_doc.metadata['tool_type'] == 'dynamic':
            tool_name = tool_doc.metadata['name']
            tool_few_shots = tool_doc.metadata['tool_trigger_selected_examples']
            tool = create_dynamic_tool(
                name=tool_name,
                description=tool_doc.metadata['description'] + f"类似下面的问题:{tool_few_shots}\n可以使用这个工具",
                input_schema=json.loads(tool_doc.metadata['input_schema']),
                function_code=json.loads(tool_doc.metadata['extra_params'])['code']
            )
            tools.append(tool)
    agent = create_react_agent(
        model=last_model,
        tools=tools,
        prompt=f"{prompt_prefix}",
        response_format=response_format
    )
    return agent


async def tool_knowledge_retrieve(state: State, config):
    """
    工具知识检索
    :param state:
    :param config:
    :return:
    """
    configuration = Configuration.from_runnable_config(config)
    question = state["question"]
    if not configuration.tool_config.is_rag:
        return {"tool_context": []}
    # TODO:内置的weaviate需要改成async
    vector_store_list = get_vector_stores(
        tenant=configuration.sys_config.tenant_id,
        namespace_list=configuration.tool_config.namespace_list,
        knowledge_type="tool"
    )
    tasks = [
        vector_store.asimilarity_search_with_score(
            question,
            k=configuration.tool_config.retrieve_top_n
        )
        for vector_store in vector_store_list
    ]
    results = await asyncio.gather(*tasks)
    retrieved_docs = [item for sublist in results for item in sublist]
    # score to meta data
    for rank, (doc, score) in enumerate(retrieved_docs):
        doc.metadata["embedding_rank"] = rank
        doc.metadata["embedding_score"] = score
    filtered_docs = [
        doc for doc, score in retrieved_docs if score >= configuration.tool_config.retrieve_threshold
    ]
    return {"tool_context": filtered_docs}


async def tool_knowledge_rerank(state: State, config):
    """
    工具知识重排序器
    :param state:
    :param config:
    :return:
    """
    configuration = Configuration.from_runnable_config(config)
    context = state["tool_context"]
    if not configuration.tool_config.is_rag:
        return {"tool_context": []}
    if not configuration.tool_config.is_rerank:
        return {"tool_context": context}

    context = await reranker.rerank(
        query=state["question"],
        texts=context,
        topn=configuration.tool_config.rerank_top_n,
        rerank_threshold=configuration.tool_config.rerank_threshold
    )
    return {"tool_context": context}


def merge_tools(context):
    tool_map = defaultdict(list)
    for doc in context:
        tool_map[doc.metadata['document_id']].append(doc)
    tool_context = []
    for doc_id, doc_list in tool_map.items():
        base_doc = doc_list[0]
        few_shots = ""
        for doc in doc_list:
            few_shots += f"{doc.metadata['tool_trigger_selected_examples']}\n"
        base_doc.metadata['tool_trigger_selected_examples'] = few_shots
        tool_context.append(base_doc)
    return tool_context


async def tool_knowledge_llm_rerank(state: State, config):
    configuration = Configuration.from_runnable_config(config)
    context = state["tool_context"]
    if not configuration.tool_config.is_rag:
        return {"tool_context": []}
    if not configuration.tool_config.is_llm_rerank:
        new_context = merge_tools(context)
        return {"tool_context": new_context}
    if not context:
        return {"tool_context": []}
    llm_rerank_model_with_structured_output = knowledge_rerank_model.with_structured_output(
        QuotedTool,
    )
    res = tool_rerank_prompt_template.invoke(
        {
            "context": get_tool_context(context),
            "question": state["question"]
        }
    )
    response = await llm_rerank_model_with_structured_output.ainvoke(res)
    new_context = [
        context[citation] for citation in response.source_ids
    ]
    tool_context = merge_tools(new_context)
    return {"tool_context": tool_context}
