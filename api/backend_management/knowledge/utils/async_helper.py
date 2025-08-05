"""
Django异步操作兼容性工具
"""
import asyncio
import functools
from typing import Any, Callable, Coroutine
from llm_api.settings.base import error_logger, info_logger


def run_async_in_sync(coro: Coroutine) -> Any:
    """
    在Django同步视图中安全地运行异步协程
    
    Args:
        coro: 异步协程对象
        
    Returns:
        协程的执行结果
        
    Raises:
        Exception: 协程执行过程中的异常
    """
    try:
        # 尝试获取当前事件循环
        try:
            loop = asyncio.get_running_loop()
            # 如果已经在事件循环中，使用asyncio.create_task
            return asyncio.create_task(coro)
        except RuntimeError:
            # 没有运行中的事件循环，创建新的事件循环
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(coro)
                return result
            finally:
                loop.close()
                # 清理事件循环
                asyncio.set_event_loop(None)
    except Exception as e:
        error_logger(f"异步操作执行失败: {str(e)}")
        raise


def async_to_sync_decorator(func: Callable) -> Callable:
    """
    装饰器：将异步函数转换为同步函数，用于Django视图中
    
    Args:
        func: 异步函数
        
    Returns:
        同步包装函数
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        coro = func(*args, **kwargs)
        return run_async_in_sync(coro)
    
    return wrapper


class AsyncHandler:
    """异步操作处理器"""
    
    @staticmethod
    def safe_run(coro: Coroutine, error_message: str = "异步操作失败") -> Any:
        """
        安全地运行异步协程，带有错误处理
        
        Args:
            coro: 异步协程对象
            error_message: 错误信息前缀
            
        Returns:
            协程的执行结果或None（如果失败）
        """
        try:
            return run_async_in_sync(coro)
        except Exception as e:
            error_logger(f"{error_message}: {str(e)}")
            return None
    
    @staticmethod
    def run_with_fallback(coro: Coroutine, fallback_value: Any = None, error_message: str = "异步操作失败") -> Any:
        """
        运行异步协程，失败时返回fallback值
        
        Args:
            coro: 异步协程对象
            fallback_value: 失败时的默认返回值
            error_message: 错误信息前缀
            
        Returns:
            协程的执行结果或fallback_value
        """
        try:
            return run_async_in_sync(coro)
        except Exception as e:
            error_logger(f"{error_message}: {str(e)}")
            return fallback_value


# 向量数据库操作的异步包装器
class VectorDBAsyncWrapper:
    """向量数据库异步操作包装器"""
    
    @staticmethod
    def add_tool_to_vector_db(document, tool_data, user):
        """同步方式添加工具到向量数据库"""
        from core.indexing.index import index
        from langchain_core.documents import Document
        import json
        
        async def _add_tool():
            # 构建向量数据库文档
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
            await index(
                document_id=str(document.id),
                tenant=str(user.id),
                namespace=str(document.namespace.id),
                doc=vector_doc,
                knowledge_type="tool"
            )
            
            info_logger(f"工具 {document.title} 已成功添加到向量数据库")
        
        return AsyncHandler.safe_run(_add_tool(), f"添加工具 {document.title} 到向量数据库失败")
    
    @staticmethod
    def update_tool_in_vector_db(document, tool_data, user):
        """同步方式更新向量数据库中的工具"""
        from core.indexing.index import update_meta_data
        import json
        
        async def _update_tool():
            # 构建更新的元数据
            meta_data_map = {
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

            # 更新向量数据库
            await update_meta_data(
                document_id=str(document.id),
                tenant=str(user.id),
                namespace=str(document.namespace.id),
                meta_data_map=meta_data_map,
                knowledge_type="tool"
            )
            
            info_logger(f"工具 {document.title} 已成功更新到向量数据库")
        
        return AsyncHandler.safe_run(_update_tool(), f"更新工具 {document.title} 到向量数据库失败")
    
    @staticmethod
    def delete_tool_from_vector_db(document, user):
        """同步方式从向量数据库中删除工具"""
        from core.indexing.index import delete
        
        async def _delete_tool():
            await delete(
                document_id=str(document.id),
                tenant=str(user.id),
                namespace=str(document.namespace.id),
                knowledge_type="tool"
            )
            
            info_logger(f"工具 {document.title} 已成功从向量数据库删除")
        
        return AsyncHandler.safe_run(_delete_tool(), f"从向量数据库删除工具 {document.title} 失败")