"""
Django异步操作兼容性工具
"""
import json

from langchain_core.documents import Document
from langchain_core.documents import Document as LangchainDocument

from core.indexing.index import index
from llm_api.settings.base import info_logger


# 向量数据库操作的异步包装器
class ToolVectorDBWrapper:
    """向量数据库异步操作包装器"""

    @staticmethod
    def add_tool_to_vector_db(document, tool_data, user):
        """同步方式添加工具到向量数据库"""

        vector_doc = Document(
            page_content="",  # 工具知识不需要内容，主要靠元数据
            metadata={
                "tenant": str(user.id),
                "owner": str(user.id),
                "namespace": str(document.namespace.id),
                "source": "knowledge_system",
                "document_id": str(document.id),
                "name": tool_data.get('name', ''),
                "description": tool_data.get('description', ''),
                "input_schema": json.dumps(tool_data.get('input_schema', {})),
                "output_schema": json.dumps(tool_data.get('output_schema', {})),
                "output_schema_jinja2_template": tool_data.get('output_schema_jinja2_template', ''),
                "html_template": tool_data.get('html_template', ''),
                "few_shots": json.dumps(tool_data.get('few_shots', [])),
                "tool_type": tool_data.get('tool_type', 'dynamic'),
                "extra_params": json.dumps(tool_data.get('extra_params', {}))
            }
        )

        # 添加到向量数据库
        index(
            document_id=str(document.id),
            tenant=str(user.id),
            namespace=str(document.namespace.id),
            doc=vector_doc,
            knowledge_type="tool"
        )

        info_logger(f"工具 {document.title} 已成功添加到向量数据库")

    @staticmethod
    def delete_tool_from_vector_db(document, user):
        """同步方式从向量数据库中删除工具"""
        from core.indexing.index import delete
        delete(
            document_id=str(document.id),
            tenant=str(user.id),
            namespace=str(document.namespace.id),
            knowledge_type="tool"
        )

        info_logger(f"工具 {document.title} 已成功从向量数据库删除")


class DocumentVectorDBWrapper:
    """文档向量数据库异步操作包装器"""

    @staticmethod
    def store_document_to_vector_db(document):
        """同步方式存储文档到向量数据库"""
        # 创建文档对象
        doc = LangchainDocument(
            page_content=document.markdown_content,
            metadata={
                "tenant": str(document.creator.id),
                "owner": str(document.creator.id),
                "namespace": str(document.namespace.id),
                "source": f"document_{document.id}",
                "document_id": str(document.id),
                "title": document.title,
                "H1": "",
                "H2": "",
                "H3": "",
                "H4": "",
                "H5": "",
                "H6": "",
            }
        )

        # 存储到向量数据库
        index(
            document_id=str(document.id),
            tenant=str(document.creator.id),
            namespace=str(document.namespace.id),
            doc=doc,
        )

        info_logger(f"文档 {document.title} 已成功存储到向量数据库")
