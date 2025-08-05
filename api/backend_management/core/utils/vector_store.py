from functools import lru_cache

from langchain_weaviate import WeaviateVectorStore

from core.extensions.ext_weaviate import weaviate_client
from core.models.embedding import embedding


@lru_cache(maxsize=1000)
def get_vector_store(
        tenant: str,
        namespace: str,
        knowledge_type: str
):
    if knowledge_type == "common":
        return WeaviateVectorStore(
            client=weaviate_client,
            index_name=f"common_knowledge_{tenant}_{namespace}",  # 数据库index，纵向隔离
            text_key='text',  # 文本字段
            embedding=embedding,
            attributes=[
                'text',
                'tenant',
                'owner',
                'namespace',
                'source',
                'document_id',
                'title',
            ],
        )
    elif knowledge_type == "tool":
        return WeaviateVectorStore(
            client=weaviate_client,
            index_name=f"tool_knowledge_{tenant}_{namespace}",  # 数据库index，纵向隔离
            text_key='text',  # 文本字段
            embedding=embedding,
            attributes=[
                'text',
                'tenant',
                'owner',
                'namespace',
                'source',
                'document_id',
                'input_schema',
                'few_shots',
                'name',
                'description',
                'tool_type',
                'output_schema',
                'jinja2_template',
                'html_template',
                'extra_params',
            ],
        )
    else:
        raise ValueError(f"Unsupported knowledge type: {knowledge_type}")


def get_vector_stores(
        tenant: str,
        namespace_list: list,
        knowledge_type: str = "common"
):
    """
    一个机器人学习多个namespace
    :param tenant: 租户
    :param namespace_list: 多个namespace
    :param knowledge_type: 知识类型：1.常规知识 2.工具知识
    :return:
    """
    return [
        get_vector_store(tenant=tenant, namespace=namespace, knowledge_type=knowledge_type)
        for namespace in namespace_list
    ]
