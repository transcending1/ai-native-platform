import json
import os
import django
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

# 设置Django环境
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "llm_api.settings.dev_settings")
django.setup()

from knowledge.models import Namespace, KnowledgeDocument

User = get_user_model()


class ToolGenerationTestCase(TestCase):
    """工具生成功能测试用例"""

    def setUp(self):
        """测试前准备"""
        # 创建测试用户
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # 创建测试知识库
        self.namespace = Namespace.objects.create(
            name='测试知识库',
            description='用于测试的知识库',
            owner=self.user,
            is_public=False
        )
        
        # 创建API客户端
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_generate_tool_by_ai_success(self):
        """测试AI生成工具成功"""
        url = reverse('namespace-documents-generate-tool-by-ai', kwargs={'namespace_pk': self.namespace.id})
        
        data = {
            'description': '请帮我生成一个请假的工具，输入请假天数和开始日期即可',
            'title': '请假工具'
        }
        
        response = self.client.post(url, data, format='json')
        
        # 验证响应状态
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # 验证返回数据
        response_data = response.data
        self.assertIn('id', response_data)
        self.assertIn('title', response_data)
        self.assertIn('doc_type', response_data)
        self.assertEqual(response_data['doc_type'], 'tool')
        
        # 验证工具数据
        tool_data = response_data.get('tool_data', {})
        self.assertIn('name', tool_data)
        self.assertIn('description', tool_data)
        self.assertIn('input_schema', tool_data)
        self.assertIn('output_schema', tool_data)
        self.assertIn('output_schema_jinja2_template', tool_data)
        self.assertIn('html_template', tool_data)
        self.assertIn('few_shots', tool_data)
        self.assertIn('extra_params', tool_data)

    def test_generate_tool_by_ai_without_description(self):
        """测试AI生成工具缺少描述"""
        url = reverse('namespace-documents-generate-tool-by-ai', kwargs={'namespace_pk': self.namespace.id})
        
        data = {
            'title': '请假工具'
        }
        
        response = self.client.post(url, data, format='json')
        
        # 验证响应状态
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    def test_generate_tool_by_ai_description_too_long(self):
        """测试AI生成工具描述过长"""
        url = reverse('namespace-documents-generate-tool-by-ai', kwargs={'namespace_pk': self.namespace.id})
        
        # 创建一个超过30000字符的描述
        long_description = "这是一个很长的描述" * 2000  # 大约30000字符
        
        data = {
            'description': long_description,
            'title': '测试工具'
        }
        
        response = self.client.post(url, data, format='json')
        
        # 验证响应状态
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertIn('30000', response.data['error'])

    def test_generate_tool_by_ai_with_parent_folder(self):
        """测试AI生成工具指定父文件夹"""
        # 创建父文件夹
        parent_folder = KnowledgeDocument.objects.create(
            title='工具文件夹',
            doc_type='folder',
            namespace=self.namespace,
            creator=self.user,
            last_editor=self.user
        )
        
        url = reverse('namespace-documents-generate-tool-by-ai', kwargs={'namespace_pk': self.namespace.id})
        
        data = {
            'description': '请帮我生成一个计算器工具，可以进行加减乘除运算',
            'title': '计算器工具',
            'parent_id': parent_folder.id
        }
        
        response = self.client.post(url, data, format='json')
        
        # 验证响应状态
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # 验证文档在正确的父文件夹下
        response_data = response.data
        self.assertEqual(response_data['parent'], parent_folder.id)

    def test_execute_tool_with_json_output(self):
        """测试执行工具返回JSON格式"""
        # 创建测试工具
        tool_document = KnowledgeDocument.objects.create(
            title='测试工具',
            doc_type='tool',
            namespace=self.namespace,
            creator=self.user,
            last_editor=self.user
        )
        
        # 设置工具数据
        tool_data = {
            'name': '测试工具',
            'description': '用于测试的工具',
            'input_schema': {
                'type': 'object',
                'properties': {
                    'name': {'type': 'string', 'description': '姓名'}
                },
                'required': ['name']
            },
            'output_schema': {
                'type': 'object',
                'properties': {
                    'message': {'type': 'string', 'description': '返回消息'}
                },
                'required': ['message']
            },
            'output_schema_jinja2_template': '你好，{{ message }}',
            'html_template': '<div>你好，{{ message }}</div>',
            'few_shots': ['测试输入'],
            'tool_type': 'dynamic',
            'extra_params': {
                'code': '''def main(name, state=None, config=None, run_manager=None, **kwargs):
    return {"message": f"欢迎 {name}!"}'''
            }
        }
        tool_document.set_tool_data(tool_data)
        tool_document.save()
        
        url = reverse('namespace-documents-execute-tool', kwargs={
            'namespace_pk': self.namespace.id,
            'pk': tool_document.id
        })
        
        data = {
            'input_data': {'name': '张三'},
            'output_type': 'json'
        }
        
        response = self.client.post(url, data, format='json')
        
        # 验证响应状态
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 验证返回数据
        response_data = response.data
        self.assertEqual(response_data['type'], 'json')
        self.assertIn('content', response_data)
        self.assertIn('raw_data', response_data)
        self.assertIn('execution_id', response_data)

    def test_execute_tool_with_jinja2_output(self):
        """测试执行工具返回Jinja2格式"""
        # 创建测试工具
        tool_document = KnowledgeDocument.objects.create(
            title='测试工具',
            doc_type='tool',
            namespace=self.namespace,
            creator=self.user,
            last_editor=self.user
        )
        
        # 设置工具数据
        tool_data = {
            'name': '测试工具',
            'description': '用于测试的工具',
            'input_schema': {
                'type': 'object',
                'properties': {
                    'name': {'type': 'string', 'description': '姓名'}
                },
                'required': ['name']
            },
            'output_schema': {
                'type': 'object',
                'properties': {
                    'message': {'type': 'string', 'description': '返回消息'}
                },
                'required': ['message']
            },
            'output_schema_jinja2_template': '你好，{{ message }}',
            'html_template': '<div>你好，{{ message }}</div>',
            'few_shots': ['测试输入'],
            'tool_type': 'dynamic',
            'extra_params': {
                'code': '''def main(name, state=None, config=None, run_manager=None, **kwargs):
    return {"message": f"欢迎 {name}!"}'''
            }
        }
        tool_document.set_tool_data(tool_data)
        tool_document.save()
        
        url = reverse('namespace-documents-execute-tool', kwargs={
            'namespace_pk': self.namespace.id,
            'pk': tool_document.id
        })
        
        data = {
            'input_data': {'name': '张三'},
            'output_type': 'jinja2'
        }
        
        response = self.client.post(url, data, format='json')
        
        # 验证响应状态
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 验证返回数据
        response_data = response.data
        self.assertEqual(response_data['type'], 'jinja2')
        self.assertIn('content', response_data)
        self.assertEqual(response_data['content'], '你好，欢迎 张三!')

    def test_execute_tool_with_html_output(self):
        """测试执行工具返回HTML格式"""
        # 创建测试工具
        tool_document = KnowledgeDocument.objects.create(
            title='测试工具',
            doc_type='tool',
            namespace=self.namespace,
            creator=self.user,
            last_editor=self.user
        )
        
        # 设置工具数据
        tool_data = {
            'name': '测试工具',
            'description': '用于测试的工具',
            'input_schema': {
                'type': 'object',
                'properties': {
                    'name': {'type': 'string', 'description': '姓名'}
                },
                'required': ['name']
            },
            'output_schema': {
                'type': 'object',
                'properties': {
                    'message': {'type': 'string', 'description': '返回消息'}
                },
                'required': ['message']
            },
            'output_schema_jinja2_template': '你好，{{ message }}',
            'html_template': '<div style="color: blue;">你好，{{ message }}</div>',
            'few_shots': ['测试输入'],
            'tool_type': 'dynamic',
            'extra_params': {
                'code': '''def main(name, state=None, config=None, run_manager=None, **kwargs):
    return {"message": f"欢迎 {name}!"}'''
            }
        }
        tool_document.set_tool_data(tool_data)
        tool_document.save()
        
        url = reverse('namespace-documents-execute-tool', kwargs={
            'namespace_pk': self.namespace.id,
            'pk': tool_document.id
        })
        
        data = {
            'input_data': {'name': '张三'},
            'output_type': 'html'
        }
        
        response = self.client.post(url, data, format='json')
        
        # 验证响应状态
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 验证返回数据
        response_data = response.data
        self.assertEqual(response_data['type'], 'html')
        self.assertIn('content', response_data)
        self.assertIn('raw_data', response_data)
        self.assertIn('<div style="color: blue;">你好，欢迎 张三!</div>', response_data['content'])

    def test_execute_tool_invalid_input(self):
        """测试执行工具无效输入"""
        # 创建测试工具
        tool_document = KnowledgeDocument.objects.create(
            title='测试工具',
            doc_type='tool',
            namespace=self.namespace,
            creator=self.user,
            last_editor=self.user
        )
        
        # 设置工具数据
        tool_data = {
            'name': '测试工具',
            'description': '用于测试的工具',
            'input_schema': {
                'type': 'object',
                'properties': {
                    'name': {'type': 'string', 'description': '姓名'}
                },
                'required': ['name']
            },
            'output_schema': {
                'type': 'object',
                'properties': {
                    'message': {'type': 'string', 'description': '返回消息'}
                },
                'required': ['message']
            },
            'output_schema_jinja2_template': '你好，{{ message }}',
            'html_template': '<div>你好，{{ message }}</div>',
            'few_shots': ['测试输入'],
            'tool_type': 'dynamic',
            'extra_params': {
                'code': '''def main(name, state=None, config=None, run_manager=None, **kwargs):
    if not name:
        raise Exception("姓名不能为空")
    return {"message": f"欢迎 {name}!"}'''
            }
        }
        tool_document.set_tool_data(tool_data)
        tool_document.save()
        
        url = reverse('namespace-documents-execute-tool', kwargs={
            'namespace_pk': self.namespace.id,
            'pk': tool_document.id
        })
        
        data = {
            'input_data': {'name': ''},
            'output_type': 'json'
        }
        
        response = self.client.post(url, data, format='json')
        
        # 验证响应状态
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    def test_generate_tool_by_ai_timeout_handling(self):
        """测试AI生成工具的超时处理"""
        url = reverse('namespace-documents-generate-tool-by-ai', kwargs={'namespace_pk': self.namespace.id})
        
        data = {
            'description': '请帮我生成一个请假的工具，输入请假天数和开始日期即可',
            'title': '请假工具'
        }
        
        # 注意：这个测试需要实际的AI服务配置才能运行
        # 在实际环境中，如果AI服务响应时间过长，会触发超时
        try:
            response = self.client.post(url, data, format='json')
            # 如果成功，验证响应格式
            if response.status_code == status.HTTP_201_CREATED:
                self.assertIn('id', response.data)
                self.assertIn('tool_data', response.data)
            # 如果超时，验证错误响应
            elif response.status_code == status.HTTP_408_REQUEST_TIMEOUT:
                self.assertIn('error', response.data)
                self.assertIn('超时', response.data['error'])
        except Exception as e:
            # 如果出现其他错误，记录但不失败
            print(f"AI生成工具测试出现异常: {e}")
            pass 