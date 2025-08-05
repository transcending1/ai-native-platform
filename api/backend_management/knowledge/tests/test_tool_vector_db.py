"""
工具知识向量数据库CRUD测试
"""
import json
import pytest
import allure
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from unittest.mock import patch, AsyncMock

from knowledge.models import Namespace, KnowledgeDocument
from knowledge.utils.async_helper import VectorDBAsyncWrapper, AsyncHandler
from core.indexing.de_duplication import de_duplicator
from core.indexing.index import index, update_meta_data, delete


User = get_user_model()


class TestToolVectorDBCRUD(TestCase):
    """
    工具知识向量数据库CRUD测试类
    """

    def setUp(self):
        """测试初始化"""
        # 创建测试用户
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # 创建测试命名空间
        self.namespace = Namespace.objects.create(
            name='测试命名空间',
            description='用于测试的命名空间',
            creator=self.user
        )
        
        # 创建API客户端
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
        # 测试工具数据
        self.tool_data = {
            'name': 'jms跳板机机器申请',
            'description': '公司内部开发人员申请内部jms跳板机里面对应ip的机器的时候使用',
            'input_schema': {
                "type": "object",
                "properties": {
                    "ip_address": {"type": "string", "description": "IP地址"},
                    "time": {"type": "string", "description": "申请时长"}
                },
                "required": ["ip_address", "time"]
            },
            'output_schema': {
                "type": "object",
                "properties": {
                    "is_success": {"type": "boolean", "description": "申请是否成功"},
                    "ip_address": {"type": "string", "description": "申请的IP地址"},
                    "time": {"type": "string", "description": "申请的时长"}
                }
            },
            'output_schema_jinja2_template': '机器申请结果：{% if is_success %}成功{% else %}失败{% endif %}。IP地址：{{ ip_address }}，申请时长：{{ time }}。',
            'html_template': '<p>机器申请结果：{{ is_success }}</p><p>IP地址：{{ ip_address }}</p><p>申请时长：{{ time }}</p>',
            'few_shots': [
                "我要申请一台192.168.3.211的机器,周期1个月。",
                "jms来一台机器",
                "jms机器192.168.9.100来一台，周期1周",
                "我要申请一台jms的机器"
            ],
            'tool_type': 'dynamic',
            'extra_params': {
                'code': '''def main(
    ip_address: str,
    time: str = "一周",
    state=None,
    config=None,
    run_manager=None
):
    # 在此处进行各种工具包的导入
    if not ip_address.startswith("192.168"):
        # 如果不符合规范就主动抛出异常，告知机器人返回结果通知人类
        raise ToolException(f"IP地址不合法,必须以192.168开头,当前ip地址为{ip_address}")
    return {
        "is_success": True,
        "ip_address": ip_address,
        "time": time,
    }'''
            }
        }

    @pytest.mark.asyncio
    @patch('knowledge.utils.async_helper.index')
    async def test_add_tool_to_vector_db(self, mock_index):
        """测试添加工具到向量数据库"""
        with allure.step("创建工具文档"):
            document = KnowledgeDocument.objects.create(
                title='测试工具',
                doc_type='tool',
                namespace=self.namespace,
                creator=self.user,
                last_editor=self.user
            )
            document.set_tool_data(self.tool_data)
            document.save()

        with allure.step("调用添加工具到向量数据库方法"):
            # 配置mock
            mock_index.return_value = AsyncMock()
            
            # 调用添加方法
            result = VectorDBAsyncWrapper.add_tool_to_vector_db(
                document, self.tool_data, self.user
            )
            
            # 验证调用
            assert result is not None
            mock_index.assert_called_once()
            
            # 验证调用参数
            call_args = mock_index.call_args
            assert call_args[1]['document_id'] == str(document.id)
            assert call_args[1]['tenant'] == str(self.user.id)
            assert call_args[1]['namespace'] == str(self.namespace.id)
            assert call_args[1]['knowledge_type'] == 'tool'
            
            # 验证文档元数据
            doc_arg = call_args[1]['doc']
            metadata = doc_arg.metadata
            assert metadata['name'] == self.tool_data['name']
            assert metadata['description'] == self.tool_data['description']
            assert json.loads(metadata['input_schema']) == self.tool_data['input_schema']

    @pytest.mark.asyncio
    @patch('knowledge.utils.async_helper.update_meta_data')
    async def test_update_tool_in_vector_db(self, mock_update):
        """测试更新向量数据库中的工具"""
        with allure.step("创建工具文档"):
            document = KnowledgeDocument.objects.create(
                title='测试工具',
                doc_type='tool',
                namespace=self.namespace,
                creator=self.user,
                last_editor=self.user
            )
            document.set_tool_data(self.tool_data)
            document.save()

        with allure.step("更新工具数据"):
            updated_tool_data = self.tool_data.copy()
            updated_tool_data['description'] = '更新后的工具描述'

        with allure.step("调用更新工具向量数据库方法"):
            # 配置mock
            mock_update.return_value = AsyncMock()
            
            # 调用更新方法
            result = VectorDBAsyncWrapper.update_tool_in_vector_db(
                document, updated_tool_data, self.user
            )
            
            # 验证调用
            assert result is not None
            mock_update.assert_called_once()
            
            # 验证调用参数
            call_args = mock_update.call_args
            assert call_args[1]['document_id'] == str(document.id)
            assert call_args[1]['tenant'] == str(self.user.id)
            assert call_args[1]['namespace'] == str(self.namespace.id)
            assert call_args[1]['knowledge_type'] == 'tool'
            
            # 验证更新的元数据
            meta_data_map = call_args[1]['meta_data_map']
            assert meta_data_map['description'] == '更新后的工具描述'

    @pytest.mark.asyncio
    @patch('knowledge.utils.async_helper.delete')
    async def test_delete_tool_from_vector_db(self, mock_delete):
        """测试从向量数据库删除工具"""
        with allure.step("创建工具文档"):
            document = KnowledgeDocument.objects.create(
                title='测试工具',
                doc_type='tool',
                namespace=self.namespace,
                creator=self.user,
                last_editor=self.user
            )
            document.set_tool_data(self.tool_data)
            document.save()

        with allure.step("调用删除工具向量数据库方法"):
            # 配置mock
            mock_delete.return_value = AsyncMock()
            
            # 调用删除方法
            result = VectorDBAsyncWrapper.delete_tool_from_vector_db(
                document, self.user
            )
            
            # 验证调用
            assert result is not None
            mock_delete.assert_called_once()
            
            # 验证调用参数
            call_args = mock_delete.call_args
            assert call_args[1]['document_id'] == str(document.id)
            assert call_args[1]['tenant'] == str(self.user.id)
            assert call_args[1]['namespace'] == str(self.namespace.id)
            assert call_args[1]['knowledge_type'] == 'tool'

    def test_create_tool_via_api_with_vector_db_integration(self):
        """测试通过API创建工具并集成向量数据库"""
        with allure.step("准备创建工具请求数据"):
            data = {
                'title': '测试API工具',
                'summary': '通过API创建的测试工具',
                'doc_type': 'tool',
                'status': 'published',
                'tool_data': self.tool_data
            }

        with allure.step("发送创建工具请求"):
            with patch('knowledge.utils.async_helper.VectorDBAsyncWrapper.add_tool_to_vector_db') as mock_add:
                response = self.client.post(
                    f'/api/knowledge/namespaces/{self.namespace.id}/documents/',
                    data=data,
                    format='json'
                )
                
                # 验证API响应
                assert response.status_code == 201
                assert response.data['title'] == '测试API工具'
                assert response.data['doc_type'] == 'tool'
                
                # 验证向量数据库集成被调用
                mock_add.assert_called_once()

    def test_update_tool_via_api_with_vector_db_integration(self):
        """测试通过API更新工具并集成向量数据库"""
        with allure.step("创建初始工具文档"):
            document = KnowledgeDocument.objects.create(
                title='原始工具',
                doc_type='tool',
                namespace=self.namespace,
                creator=self.user,
                last_editor=self.user
            )
            document.set_tool_data(self.tool_data)
            document.save()

        with allure.step("准备更新工具请求数据"):
            updated_data = {
                'title': '更新后的工具',
                'tool_data': {
                    **self.tool_data,
                    'description': '这是更新后的工具描述'
                }
            }

        with allure.step("发送更新工具请求"):
            with patch('knowledge.utils.async_helper.VectorDBAsyncWrapper.update_tool_in_vector_db') as mock_update:
                response = self.client.put(
                    f'/api/knowledge/namespaces/{self.namespace.id}/documents/{document.id}/',
                    data=updated_data,
                    format='json'
                )
                
                # 验证API响应
                assert response.status_code == 200
                assert response.data['title'] == '更新后的工具'
                
                # 验证向量数据库更新被调用
                mock_update.assert_called_once()

    def test_delete_tool_via_api_with_vector_db_integration(self):
        """测试通过API删除工具并集成向量数据库"""
        with allure.step("创建工具文档"):
            document = KnowledgeDocument.objects.create(
                title='待删除工具',
                doc_type='tool',
                namespace=self.namespace,
                creator=self.user,
                last_editor=self.user
            )
            document.set_tool_data(self.tool_data)
            document.save()

        with allure.step("发送删除工具请求"):
            with patch('knowledge.views.knowledge_management.AsyncHandler.safe_run') as mock_cleanup:
                response = self.client.delete(
                    f'/api/knowledge/namespaces/{self.namespace.id}/documents/{document.id}/'
                )
                
                # 验证API响应
                assert response.status_code == 204
                
                # 验证文档被软删除
                document.refresh_from_db()
                assert not document.is_active
                
                # 验证资源清理被调用（包括向量数据库删除）
                mock_cleanup.assert_called_once()

    def test_async_handler_safe_run(self):
        """测试异步处理器的安全运行方法"""
        async def test_coro():
            return "测试结果"

        with allure.step("测试异步操作成功情况"):
            with patch('knowledge.utils.async_helper.run_async_in_sync', return_value="测试结果") as mock_run:
                result = AsyncHandler.safe_run(test_coro(), "测试操作")
                assert result == "测试结果"
                mock_run.assert_called_once()

    def test_async_handler_with_fallback(self):
        """测试异步处理器的fallback机制"""
        async def failing_coro():
            raise Exception("测试异常")

        with allure.step("测试异步操作失败时的fallback"):
            with patch('knowledge.utils.async_helper.run_async_in_sync', side_effect=Exception("测试异常")):
                result = AsyncHandler.run_with_fallback(
                    failing_coro(), 
                    fallback_value="fallback结果", 
                    error_message="操作失败"
                )
                assert result == "fallback结果"

    def tearDown(self):
        """清理测试数据"""
        # 清理创建的测试数据
        KnowledgeDocument.objects.filter(namespace=self.namespace).delete()
        self.namespace.delete()
        self.user.delete()


# 针对真实向量数据库的集成测试（需要启动向量数据库服务）
@pytest.mark.integration
class TestToolVectorDBIntegration(TestCase):
    """
    工具知识向量数据库集成测试（需要真实向量数据库环境）
    """

    def setUp(self):
        """测试初始化"""
        self.user = User.objects.create_user(
            username='integrationuser',
            email='integration@example.com',
            password='testpass123'
        )
        
        self.namespace = Namespace.objects.create(
            name='集成测试命名空间',
            description='用于集成测试的命名空间',
            creator=self.user
        )

    @pytest.mark.asyncio
    async def test_real_vector_db_operations(self):
        """测试真实向量数据库操作（需要向量数据库服务运行）"""
        with allure.step("准备测试数据"):
            document_id = "integration_test_tool_001"
            tenant = str(self.user.id)
            namespace = str(self.namespace.id)
            
            tool_data = {
                'name': '集成测试工具',
                'description': '用于集成测试的工具',
                'input_schema': {
                    "type": "object",
                    "properties": {
                        "test_param": {"type": "string", "description": "测试参数"}
                    }
                },
                'few_shots': ["测试示例1", "测试示例2"],
                'tool_type': 'dynamic'
            }

        with allure.step("清理可能存在的测试数据"):
            try:
                await delete(
                    document_id=document_id,
                    tenant=tenant,
                    namespace=namespace,
                    knowledge_type="tool"
                )
            except:
                pass  # 忽略清理错误

        with allure.step("测试添加工具到向量数据库"):
            from langchain_core.documents import Document
            
            vector_doc = Document(
                page_content="",
                metadata={
                    "tenant": tenant,
                    "owner": tenant,
                    "namespace": namespace,
                    "source": "integration_test",
                    "document_id": document_id,
                    "name": tool_data['name'],
                    "description": tool_data['description'],
                    "input_schema": json.dumps(tool_data['input_schema']),
                    "few_shots": json.dumps(tool_data['few_shots']),
                    "tool_type": tool_data['tool_type']
                }
            )

            result = await index(
                document_id=document_id,
                tenant=tenant,
                namespace=namespace,
                doc=vector_doc,
                knowledge_type="tool"
            )
            
            # 验证添加成功
            source_ids = await de_duplicator.get_all_source_ids(document_id)
            assert len(source_ids) > 0

        with allure.step("测试更新工具元数据"):
            updated_meta_data = {
                "name": "更新后的集成测试工具",
                "description": "这是更新后的描述"
            }
            
            await update_meta_data(
                document_id=document_id,
                tenant=tenant,
                namespace=namespace,
                meta_data_map=updated_meta_data,
                knowledge_type="tool"
            )

        with allure.step("测试删除工具"):
            await delete(
                document_id=document_id,
                tenant=tenant,
                namespace=namespace,
                knowledge_type="tool"
            )
            
            # 验证删除成功
            source_ids = await de_duplicator.get_all_source_ids(document_id)
            assert len(source_ids) == 0

    def tearDown(self):
        """清理测试数据"""
        self.namespace.delete()
        self.user.delete()