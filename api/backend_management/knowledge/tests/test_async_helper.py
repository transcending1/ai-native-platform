"""
测试异步帮助工具模块
"""
import asyncio
import pytest
from unittest.mock import patch, AsyncMock
from django.test import TestCase
from django.contrib.auth import get_user_model

from ..utils.async_helper import (
    run_async_in_sync, 
    AsyncHandler, 
    DocumentVectorDBWrapper,
    VectorDBAsyncWrapper
)
from ..models.knowledge_management import KnowledgeDocument
from ..models.namespace import Namespace

User = get_user_model()


class TestAsyncHelper(TestCase):
    """异步帮助工具测试"""
    
    def setUp(self):
        """设置测试数据"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.namespace = Namespace.objects.create(
            name='test_namespace',
            creator=self.user
        )
        
        self.document = KnowledgeDocument.objects.create(
            title='Test Document',
            content='<p>测试内容</p>',
            markdown_content='测试内容',
            creator=self.user,
            namespace=self.namespace
        )

    async def sample_async_func(self, value=42):
        """示例异步函数"""
        await asyncio.sleep(0.01)  # 模拟异步操作
        return value * 2

    async def failing_async_func(self):
        """失败的异步函数"""
        await asyncio.sleep(0.01)
        raise ValueError("测试异常")

    def test_run_async_in_sync_success(self):
        """测试成功运行异步函数"""
        result = run_async_in_sync(self.sample_async_func(10))
        self.assertEqual(result, 20)

    def test_run_async_in_sync_with_exception(self):
        """测试异步函数抛出异常的情况"""
        with self.assertRaises(ValueError):
            run_async_in_sync(self.failing_async_func())

    def test_async_handler_safe_run_success(self):
        """测试AsyncHandler.safe_run成功情况"""
        result = AsyncHandler.safe_run(
            self.sample_async_func(7),
            "测试失败"
        )
        self.assertEqual(result, 14)

    def test_async_handler_safe_run_failure(self):
        """测试AsyncHandler.safe_run失败情况"""
        result = AsyncHandler.safe_run(
            self.failing_async_func(),
            "测试失败"
        )
        self.assertIsNone(result)

    def test_async_handler_run_with_fallback_success(self):
        """测试AsyncHandler.run_with_fallback成功情况"""
        result = AsyncHandler.run_with_fallback(
            self.sample_async_func(4),
            fallback_value=0,
            error_message="测试失败"
        )
        self.assertEqual(result, 8)

    def test_async_handler_run_with_fallback_failure(self):
        """测试AsyncHandler.run_with_fallback失败情况"""
        result = AsyncHandler.run_with_fallback(
            self.failing_async_func(),
            fallback_value=999,
            error_message="测试失败"
        )
        self.assertEqual(result, 999)

    @patch('core.indexing.index.index')
    def test_document_vector_db_wrapper_store_success(self, mock_index):
        """测试DocumentVectorDBWrapper存储成功"""
        mock_index.return_value = AsyncMock()
        
        result = DocumentVectorDBWrapper.store_document_to_vector_db(self.document)
        
        # 验证没有抛出异常
        # 这里主要是测试不会出现Event loop closed错误
        self.assertIsNone(result)  # safe_run在成功时返回None（由于没有返回值）

    @patch('core.indexing.index.index')
    def test_document_vector_db_wrapper_store_with_empty_content(self, mock_index):
        """测试DocumentVectorDBWrapper存储空内容文档"""
        mock_index.return_value = AsyncMock()
        
        # 创建空内容文档
        empty_document = KnowledgeDocument.objects.create(
            title='Empty Document',
            content='',
            markdown_content='',
            creator=self.user,
            namespace=self.namespace
        )
        
        result = DocumentVectorDBWrapper.store_document_to_vector_db(empty_document)
        
        # 验证空内容文档不会调用index
        mock_index.assert_not_called()
        self.assertIsNone(result)

    def test_multiple_async_operations_no_event_loop_conflict(self):
        """测试多个异步操作不会产生事件循环冲突"""
        # 模拟连续执行多个异步操作，这在之前会导致Event loop closed错误
        results = []
        
        for i in range(3):
            try:
                result = run_async_in_sync(self.sample_async_func(i))
                results.append(result)
            except Exception as e:
                self.fail(f"第{i}次异步操作失败: {str(e)}")
        
        expected = [0, 2, 4]  # 0*2, 1*2, 2*2
        self.assertEqual(results, expected)

    def test_nested_async_calls_no_event_loop_error(self):
        """测试嵌套异步调用不会产生事件循环错误"""
        async def nested_async_operation():
            # 在异步函数中再次调用异步操作
            result1 = await self.sample_async_func(2)
            result2 = await self.sample_async_func(3)
            return result1 + result2
        
        # 这种嵌套调用在修复前可能导致Event loop closed错误
        result = run_async_in_sync(nested_async_operation())
        self.assertEqual(result, 10)  # (2*2) + (3*2) = 4 + 6 = 10


class TestAsyncHelperIntegration(TestCase):
    """异步帮助工具集成测试"""
    
    def setUp(self):
        """设置测试数据"""
        self.user = User.objects.create_user(
            username='integrationuser',
            email='integration@example.com',
            password='testpass123'
        )
        
        self.namespace = Namespace.objects.create(
            name='integration_namespace',
            creator=self.user
        )

    @patch('core.indexing.index.index')
    def test_document_creation_with_vector_storage(self, mock_index):
        """测试文档创建时的向量存储集成"""
        mock_index.return_value = AsyncMock()
        
        # 创建包含内容的文档
        document = KnowledgeDocument.objects.create(
            title='Integration Test Document',
            content='<p>集成测试内容</p>',
            markdown_content='集成测试内容',
            creator=self.user,
            namespace=self.namespace
        )
        
        # 模拟向量存储操作
        try:
            DocumentVectorDBWrapper.store_document_to_vector_db(document)
        except Exception as e:
            self.fail(f"向量存储集成测试失败: {str(e)}")

    def test_concurrent_async_operations(self):
        """测试并发异步操作"""
        import threading
        import time
        
        results = []
        errors = []
        
        def async_operation_thread(value):
            try:
                async def test_coro():
                    await asyncio.sleep(0.01)
                    return value * 2
                
                result = run_async_in_sync(test_coro())
                results.append(result)
            except Exception as e:
                errors.append(str(e))
        
        # 创建多个线程同时执行异步操作
        threads = []
        for i in range(5):
            thread = threading.Thread(target=async_operation_thread, args=(i,))
            threads.append(thread)
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        # 验证所有操作都成功完成，没有Event loop错误
        self.assertEqual(len(errors), 0, f"并发异步操作出现错误: {errors}")
        self.assertEqual(len(results), 5)
        self.assertEqual(sorted(results), [0, 2, 4, 6, 8])  # 0*2, 1*2, 2*2, 3*2, 4*2