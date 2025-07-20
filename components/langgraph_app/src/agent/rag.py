import asyncio

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from typing_extensions import List

from agent.configuration import Configuration
from agent.state import State
from ai_native_core.model import knowledge_rerank_model
from ai_native_core.rerank import reranker
from ai_native_core.utils.vector_store import get_vector_stores


class RAGAnswer(BaseModel):
    """回答问题的格式"""

    answer: str = Field(..., description="用markdown的格式回答问题的答案")
    source_ids: List[int] = Field(
        ..., description="命中的知识编号列表",
    )


rag_prompt_template = ChatPromptTemplate.from_messages(
    [
        {
            "role": "system",
            "content": '''{prompt},你的背景知识编号如下\n
{context}\n
你可以使用上面的这些知识来回答用户的问题\n
''',
        }
    ]
)


def get_rag_knowledge_context(context: list) -> str:
    """根据知识生成提示"""
    prompt = ""
    for idx, doc in enumerate(context):
        prompt += f"知识编号:{idx}\n知识内容:{doc.page_content}\n"
    return prompt


knowledge_rerank_prompt_template = ChatPromptTemplate.from_messages(
    [
        {
            "role": "system",
            "content": '''你是问题知识相关性分析专家,帮助用户找出和用户问题非常相关的知识编号id列表.
要求:
标记出与用户问题最相关的知识列表id编号

知识列表如下:
{context}
用户的问题如下:
{question}
请你给出和用户问题相关的知识编号
''',
        }
    ]
)


class QuotedAnswer(BaseModel):
    """标注和用户问题相关的知识列表"""
    source_ids: List[int] = Field(
        ..., description="命中的知识编号列表",
    )


async def common_knowledge_retrieve(state: State, config):
    """
    通用知识召回器
    :param state:
    :param config:
    :return:
    """
    configuration = Configuration.from_runnable_config(config)
    question = state["question"]
    if not configuration.rag_config.is_rag:
        return {"context": []}
    # TODO:内置的weaviate需要改成async
    vector_store_list = get_vector_stores(
        tenant=configuration.sys_config.tenant_id,
        namespace_list=configuration.rag_config.namespace_list
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
        doc for doc, score in retrieved_docs if score >= configuration.rag_config.retrieve_threshold
    ]
    return {"context": filtered_docs}


async def common_knowledge_rerank(state: State, config):
    """
    通用知识重排序器
    :param state:
    :param config:
    :return:
    """
    configuration = Configuration.from_runnable_config(config)
    context = state["context"]
    if not configuration.rag_config.is_rag:
        return {"context": []}
    if not configuration.rag_config.is_rerank:
        return {"context": context}
    if not context:
        return {"context": []}

    context = await reranker.rerank(
        query=state["question"],
        texts=context,
        topn=configuration.rag_config.rerank_top_n,
        rerank_threshold=configuration.rag_config.rerank_threshold
    )
    return {"context": context}


async def common_knowledge_llm_rerank(state: State, config):
    configuration = Configuration.from_runnable_config(config)
    context = state["context"]
    if not configuration.rag_config.is_rag:
        return {"context": []}
    if not configuration.rag_config.is_llm_rerank:
        return {"context": context}
    if not context:
        return {"context": []}
    llm_rerank_model_with_structured_output = knowledge_rerank_model.with_structured_output(
        QuotedAnswer,
    )
    res = knowledge_rerank_prompt_template.invoke(
        {
            "context": get_rag_knowledge_context(context),
            "question": state["question"]
        }
    )
    response = await llm_rerank_model_with_structured_output.ainvoke(res)
    new_context = [
        context[citation] for citation in response.source_ids
    ]
    return {"context": new_context}
