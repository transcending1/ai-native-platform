import json
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status

from knowledge.models import (
    Namespace, 
    KnowledgeDocument, 
    FormDataEntry, 
    ToolExecution
)

User = get_user_model()


class KnowledgeTypesTestCase(APITestCase):
    """
    测试不同类型的知识功能
    """

    def setUp(self):
        """设置测试数据"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # 使用登录API获取JWT token
        login_data = {
            'username': 'testuser',
            'password': 'testpass123'
        }
        login_response = self.client.post('/api/user/auth/login/', login_data)
        if login_response.status_code == 200:
            access_token = login_response.data['data']['access']
            self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        else:
            # 如果登录失败，直接设置用户认证（用于测试）
            self.client.force_authenticate(user=self.user)
        
        # 创建测试知识库
        self.namespace = Namespace.objects.create(
            name='测试知识库',
            description='用于测试的知识库',
            creator=self.user,
            access_type='collaborators'
        )

    def test_create_tool_knowledge(self):
        """测试创建工具知识"""
        url = reverse('namespace-documents-list', kwargs={'namespace_pk': self.namespace.id})
        
        tool_data = {
            'name': '测试工具',
            'description': '这是一个测试工具',
            'input_schema': {
                'type': 'object',
                'properties': {
                    'ip_address': {'type': 'string', 'description': 'IP地址'},
                    'time': {'type': 'string', 'description': '申请时长'}
                },
                'required': ['ip_address', 'time']
            },
            'few_shots': [
                '我要申请一台192.168.3.211的机器,周期1个月。',
                'jms来一台机器'
            ],
            'tool_type': 'dynamic',
            'extra_params': {
                'code': '''if not ip_address.startswith("192.168"):
    raise ToolException(f"IP地址不合法,必须以192.168开头,当前ip地址为{ip_address}")
result = f"申请机器成功,ip地址为{ip_address},申请时长为{time}"'''
            }
        }
        
        data = {
            'title': '测试工具知识',
            'doc_type': 'tool',
            'tool_data': tool_data
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # 验证创建的工具知识
        tool_doc = KnowledgeDocument.objects.get(id=response.data['id'])
        self.assertEqual(tool_doc.doc_type, 'tool')
        self.assertTrue(tool_doc.is_tool)
        self.assertIsNotNone(tool_doc.type_specific_data)
        self.assertEqual(tool_doc.get_tool_data()['name'], '测试工具')

    def test_create_form_knowledge(self):
        """测试创建表单知识"""
        url = reverse('namespace-documents-list', kwargs={'namespace_pk': self.namespace.id})
        
        form_data = {
            'table_name': 'user_info',
            'table_description': '用户信息表',
            'fields': [
                {
                    'name': 'name',
                    'field_type': 'String',
                    'description': '姓名',
                    'is_required': True,
                    'default_value': ''
                },
                {
                    'name': 'age',
                    'field_type': 'Integer',
                    'description': '年龄',
                    'is_required': False,
                    'default_value': '0'
                }
            ]
        }
        
        data = {
            'title': '测试表单知识',
            'doc_type': 'form',
            'form_data': form_data
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # 验证创建的表单知识
        form_doc = KnowledgeDocument.objects.get(id=response.data['id'])
        self.assertEqual(form_doc.doc_type, 'form')
        self.assertTrue(form_doc.is_form)
        self.assertIsNotNone(form_doc.type_specific_data)
        self.assertEqual(form_doc.get_form_data()['table_name'], 'user_info')

    def test_create_document_knowledge(self):
        """测试创建文档知识"""
        url = reverse('namespace-documents-list', kwargs={'namespace_pk': self.namespace.id})
        
        data = {
            'title': '测试文档知识',
            'doc_type': 'document',
            'content': '# 这是一个测试文档\n\n这是文档的内容。'
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # 验证创建的文档知识
        doc = KnowledgeDocument.objects.get(id=response.data['id'])
        self.assertEqual(doc.doc_type, 'document')
        self.assertTrue(doc.is_document)
        self.assertIsNotNone(doc.content)

    def test_update_tool_knowledge(self):
        """测试更新工具知识"""
        # 先创建工具知识
        tool_doc = KnowledgeDocument.objects.create(
            title='原始工具',
            doc_type='tool',
            namespace=self.namespace,
            creator=self.user,
            last_editor=self.user
        )
        
        url = reverse('namespace-documents-detail', kwargs={
            'namespace_pk': self.namespace.id,
            'pk': tool_doc.id
        })
        
        updated_tool_data = {
            'name': '更新后的工具',
            'description': '这是更新后的工具描述',
            'input_schema': {
                'type': 'object',
                'properties': {
                    'param1': {'type': 'string', 'description': '参数1'}
                },
                'required': ['param1']
            },
            'few_shots': ['示例1'],
            'tool_type': 'dynamic',
            'extra_params': {}
        }
        
        data = {
            'title': '更新后的工具知识',
            'tool_data': updated_tool_data
        }
        
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 验证更新
        tool_doc.refresh_from_db()
        self.assertEqual(tool_doc.get_tool_data()['name'], '更新后的工具')

    def test_execute_tool(self):
        """测试执行工具"""
        # 创建工具知识
        tool_doc = KnowledgeDocument.objects.create(
            title='可执行工具',
            doc_type='tool',
            namespace=self.namespace,
            creator=self.user,
            last_editor=self.user,
            type_specific_data={
                'name': '测试工具',
                'description': '测试工具描述',
                'input_schema': {
                    'type': 'object',
                    'properties': {
                        'ip_address': {'type': 'string', 'description': 'IP地址'}
                    },
                    'required': ['ip_address']
                },
                'few_shots': [],
                'tool_type': 'dynamic',
                'extra_params': {}
            }
        )
        
        url = reverse('namespace-documents-execute-tool', kwargs={
            'namespace_pk': self.namespace.id,
            'pk': tool_doc.id
        })
        
        data = {
            'input_data': {
                'ip_address': '192.168.1.100'
            }
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # 验证执行记录
        execution = ToolExecution.objects.get(id=response.data['id'])
        self.assertEqual(execution.tool_document, tool_doc)
        self.assertEqual(execution.executor, self.user)
        self.assertEqual(execution.input_data['ip_address'], '192.168.1.100')

    def test_submit_form_data(self):
        """测试提交表单数据"""
        # 创建表单知识
        form_doc = KnowledgeDocument.objects.create(
            title='用户信息表单',
            doc_type='form',
            namespace=self.namespace,
            creator=self.user,
            last_editor=self.user,
            type_specific_data={
                'table_name': 'user_info',
                'table_description': '用户信息表',
                'fields': [
                    {
                        'name': 'name',
                        'field_type': 'String',
                        'description': '姓名',
                        'is_required': True
                    },
                    {
                        'name': 'age',
                        'field_type': 'Integer',
                        'description': '年龄',
                        'is_required': False
                    }
                ]
            }
        )
        
        url = reverse('namespace-documents-submit-form-data', kwargs={
            'namespace_pk': self.namespace.id,
            'pk': form_doc.id
        })
        
        data = {
            'data': {
                'name': '张三',
                'age': 25
            }
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # 验证表单数据条目
        entry = FormDataEntry.objects.get(id=response.data['id'])
        self.assertEqual(entry.form_document, form_doc)
        self.assertEqual(entry.submitter, self.user)
        self.assertEqual(entry.data['name'], '张三')
        self.assertEqual(entry.data['age'], 25)

    def test_get_form_data(self):
        """测试获取表单数据"""
        # 创建表单知识和数据条目
        form_doc = KnowledgeDocument.objects.create(
            title='测试表单',
            doc_type='form',
            namespace=self.namespace,
            creator=self.user,
            last_editor=self.user
        )
        
        FormDataEntry.objects.create(
            form_document=form_doc,
            submitter=self.user,
            data={'name': '测试用户', 'age': 30}
        )
        
        url = reverse('namespace-documents-form-data', kwargs={
            'namespace_pk': self.namespace.id,
            'pk': form_doc.id
        })
        
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['data']['name'], '测试用户')

    def test_get_tool_executions(self):
        """测试获取工具执行历史"""
        # 创建工具知识和执行记录
        tool_doc = KnowledgeDocument.objects.create(
            title='测试工具',
            doc_type='tool',
            namespace=self.namespace,
            creator=self.user,
            last_editor=self.user
        )
        
        ToolExecution.objects.create(
            tool_document=tool_doc,
            executor=self.user,
            input_data={'param': 'value'},
            status='success'
        )
        
        url = reverse('namespace-documents-tool-executions', kwargs={
            'namespace_pk': self.namespace.id,
            'pk': tool_doc.id
        })
        
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['status'], 'success')

    def test_invalid_tool_input_schema(self):
        """测试无效的工具输入模式"""
        url = reverse('namespace-documents-list', kwargs={'namespace_pk': self.namespace.id})
        
        invalid_tool_data = {
            'name': '无效工具',
            'description': '测试无效的输入模式',
            'input_schema': {
                'type': 'invalid',  # 无效的类型
                'properties': {}
            }
        }
        
        data = {
            'title': '无效工具知识',
            'doc_type': 'tool',
            'tool_data': invalid_tool_data
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_form_fields(self):
        """测试无效的表单字段"""
        url = reverse('namespace-documents-list', kwargs={'namespace_pk': self.namespace.id})
        
        invalid_form_data = {
            'table_name': 'test_table',
            'table_description': '测试表',
            'fields': [
                {
                    'name': 'field1',
                    'field_type': 'String',
                    'is_required': True
                },
                {
                    'name': 'field1',  # 重复的字段名
                    'field_type': 'Integer',
                    'is_required': False
                }
            ]
        }
        
        data = {
            'title': '无效表单知识',
            'doc_type': 'form',
            'form_data': invalid_form_data
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_tool_with_type_specific_data_field(self):
        """测试通过type_specific_data字段创建工具知识（兼容性测试）"""
        url = reverse('namespace-documents-list', kwargs={'namespace_pk': self.namespace.id})
        
        # 使用type_specific_data字段（模拟前端发送的数据结构）
        data = {
            'title': '电瓶车管理工具',
            'doc_type': 'tool',
            'parent': None,
            'is_public': True,
            'type_specific_data': {
                'name': '电瓶车',
                'description': '电瓶车管理工具描述',
                'input_schema': {
                    'type': 'object',
                    'properties': {
                        'license_plate': {
                            'type': 'string',
                            'description': '车牌号'
                        }
                    },
                    'required': ['license_plate']
                },
                'few_shots': ['查询A12345车牌的电瓶车信息'],
                'tool_type': 'dynamic',
                'extra_params': {
                    'code': 'print(f"查询车牌: {license_plate}")'
                }
            }
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # 验证创建成功
        document = KnowledgeDocument.objects.get(id=response.data['id'])
        self.assertEqual(document.title, '电瓶车管理工具')
        self.assertEqual(document.doc_type, 'tool')
        self.assertTrue(document.is_tool)
        
        # 验证工具数据被正确保存
        tool_data = document.get_tool_data()
        self.assertEqual(tool_data['name'], '电瓶车')
        self.assertEqual(tool_data['description'], '电瓶车管理工具描述')
        self.assertEqual(tool_data['tool_type'], 'dynamic')
        self.assertEqual(len(tool_data['few_shots']), 1)
        self.assertEqual(tool_data['few_shots'][0], '查询A12345车牌的电瓶车信息')
        
        # 验证输入参数结构
        input_schema = tool_data['input_schema']
        self.assertEqual(input_schema['type'], 'object')
        self.assertIn('license_plate', input_schema['properties'])
        self.assertEqual(input_schema['required'], ['license_plate'])
        
        # 验证额外参数
        extra_params = tool_data['extra_params']
        self.assertIn('code', extra_params)
        self.assertEqual(extra_params['code'], 'print(f"查询车牌: {license_plate}")')
        
        # 验证GET请求能获取到正确的数据
        detail_url = reverse('namespace-documents-detail', kwargs={
            'namespace_pk': self.namespace.id,
            'pk': document.id
        })
        detail_response = self.client.get(detail_url)
        self.assertEqual(detail_response.status_code, status.HTTP_200_OK)
        
        # 验证返回的工具数据正确（应该在tool_data字段中）
        returned_tool_data = detail_response.data['tool_data']
        self.assertEqual(returned_tool_data['name'], '电瓶车')
        self.assertEqual(returned_tool_data['description'], '电瓶车管理工具描述')
        self.assertEqual(returned_tool_data['tool_type'], 'dynamic')

    def test_create_tool_with_minimal_data(self):
        """测试使用最少字段创建工具知识（模拟简化界面）"""
        url = reverse('namespace-documents-list', kwargs={'namespace_pk': self.namespace.id})
        
        # 模拟用户界面发送的简化数据（只有基本字段）
        data = {
            'title': '电瓶车测试',
            'doc_type': 'tool',
            'parent': None,
            'is_public': True,
            'type_specific_data': {
                'name': '电瓶车测试',
                'description': '电瓶车测试'
                # 注意：没有提供 input_schema 字段
            }
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # 验证创建成功
        document = KnowledgeDocument.objects.get(id=response.data['id'])
        self.assertEqual(document.title, '电瓶车测试')
        self.assertEqual(document.doc_type, 'tool')
        self.assertTrue(document.is_tool)
        
        # 验证工具数据被正确保存，缺失的字段使用默认值
        tool_data = document.get_tool_data()
        self.assertEqual(tool_data['name'], '电瓶车测试')
        self.assertEqual(tool_data['description'], '电瓶车测试')
        self.assertEqual(tool_data['tool_type'], 'dynamic')
        
        # 验证input_schema使用了默认值
        input_schema = tool_data['input_schema']
        self.assertEqual(input_schema['type'], 'object')
        self.assertEqual(input_schema['properties'], {})
        self.assertEqual(input_schema['required'], [])
        
        # 验证其他字段的默认值
        self.assertEqual(tool_data['few_shots'], [])
        self.assertEqual(tool_data['extra_params'], {})
        
        # 验证GET请求能获取到正确的数据
        detail_url = reverse('namespace-documents-detail', kwargs={
            'namespace_pk': self.namespace.id,
            'pk': document.id
        })
        detail_response = self.client.get(detail_url)
        self.assertEqual(detail_response.status_code, status.HTTP_200_OK)
        
        # 验证返回的工具数据正确
        returned_tool_data = detail_response.data['tool_data']
        self.assertEqual(returned_tool_data['name'], '电瓶车测试')
        self.assertEqual(returned_tool_data['description'], '电瓶车测试')
        self.assertEqual(returned_tool_data['tool_type'], 'dynamic')

    def test_update_tool_data_only(self):
        """测试只更新工具数据（不包含其他基础字段）"""
        # 先创建工具知识
        tool_doc = KnowledgeDocument.objects.create(
            title='原始工具',
            doc_type='tool',
            namespace=self.namespace,
            creator=self.user,
            last_editor=self.user
        )
        
        # 设置初始工具数据
        initial_tool_data = {
            'name': '原始工具名',
            'description': '原始工具描述',
            'input_schema': {
                'type': 'object',
                'properties': {},
                'required': []
            },
            'few_shots': [],
            'tool_type': 'dynamic',
            'extra_params': {}
        }
        tool_doc.set_tool_data(initial_tool_data)
        tool_doc.save()
        
        url = reverse('namespace-documents-detail', kwargs={
            'namespace_pk': self.namespace.id,
            'pk': tool_doc.id
        })
        
        # 只更新工具数据（模拟用户报告的场景）
        update_data = {
            "tool_data": {
                "name": "更新后的电瓶车",
                "description": "更新后的电瓶车描述",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "名字"
                        },
                        "age": {
                            "type": "integer", 
                            "description": "年龄"
                        }
                    },
                    "required": []
                },
                "few_shots": ["电瓶车往前走一步", "电瓶车往后走一步"],
                "tool_type": "dynamic",
                "extra_params": {"code": ""}
            }
        }
        
        response = self.client.put(url, update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 验证工具数据被正确更新
        tool_doc.refresh_from_db()
        updated_tool_data = tool_doc.get_tool_data()
        
        self.assertEqual(updated_tool_data['name'], "更新后的电瓶车")
        self.assertEqual(updated_tool_data['description'], "更新后的电瓶车描述")
        self.assertEqual(len(updated_tool_data['few_shots']), 2)
        self.assertEqual(updated_tool_data['few_shots'][0], "电瓶车往前走一步")
        self.assertEqual(updated_tool_data['few_shots'][1], "电瓶车往后走一步")
        
        # 验证input_schema正确更新
        input_schema = updated_tool_data['input_schema']
        self.assertEqual(input_schema['type'], 'object')
        self.assertIn('name', input_schema['properties'])
        self.assertIn('age', input_schema['properties'])
        self.assertEqual(input_schema['properties']['name']['type'], 'string')
        self.assertEqual(input_schema['properties']['age']['type'], 'integer')
        
        # 验证基础字段没有被改变
        self.assertEqual(tool_doc.title, '原始工具')  # 标题应该保持不变
        self.assertEqual(tool_doc.doc_type, 'tool')   # 文档类型应该保持不变


class KnowledgeDocumentModelTestCase(TestCase):
    """
    测试知识文档模型的功能
    """

    def setUp(self):
        """设置测试数据"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.namespace = Namespace.objects.create(
            name='测试知识库',
            creator=self.user
        )

    def test_tool_data_methods(self):
        """测试工具数据相关方法"""
        tool_doc = KnowledgeDocument.objects.create(
            title='测试工具',
            doc_type='tool',
            namespace=self.namespace,
            creator=self.user,
            last_editor=self.user
        )
        
        # 测试默认数据
        default_data = tool_doc.get_tool_data()
        self.assertIsNotNone(default_data)
        self.assertEqual(default_data['tool_type'], 'dynamic')
        
        # 测试设置数据
        new_data = {
            'name': '新工具',
            'description': '新工具描述',
            'input_schema': {'type': 'object', 'properties': {}},
            'few_shots': [],
            'tool_type': 'dynamic',
            'extra_params': {}
        }
        tool_doc.set_tool_data(new_data)
        tool_doc.save()
        
        # 验证数据设置成功
        tool_doc.refresh_from_db()
        self.assertEqual(tool_doc.get_tool_data()['name'], '新工具')

    def test_form_data_methods(self):
        """测试表单数据相关方法"""
        form_doc = KnowledgeDocument.objects.create(
            title='测试表单',
            doc_type='form',
            namespace=self.namespace,
            creator=self.user,
            last_editor=self.user
        )
        
        # 测试默认数据
        default_data = form_doc.get_form_data()
        self.assertIsNotNone(default_data)
        self.assertEqual(default_data['fields'], [])
        
        # 测试设置数据
        new_data = {
            'table_name': 'test_table',
            'table_description': '测试表',
            'fields': [
                {
                    'name': 'field1',
                    'field_type': 'String',
                    'is_required': True
                }
            ]
        }
        form_doc.set_form_data(new_data)
        form_doc.save()
        
        # 验证数据设置成功
        form_doc.refresh_from_db()
        self.assertEqual(form_doc.get_form_data()['table_name'], 'test_table')

    def test_dynamic_table_name(self):
        """测试动态表名生成"""
        form_doc = KnowledgeDocument.objects.create(
            title='测试表单',
            doc_type='form',
            namespace=self.namespace,
            creator=self.user,
            last_editor=self.user
        )
        
        expected_name = f"form_data_{self.namespace.id}_{form_doc.id}"
        self.assertEqual(form_doc.get_dynamic_table_name(), expected_name)
        
        # 非表单类型返回None
        doc = KnowledgeDocument.objects.create(
            title='普通文档',
            doc_type='document',
            namespace=self.namespace,
            creator=self.user,
            last_editor=self.user
        )
        
        self.assertIsNone(doc.get_dynamic_table_name())

    def test_save_method_initialization(self):
        """测试保存方法的初始化逻辑"""
        # 工具类型自动初始化
        tool_doc = KnowledgeDocument(
            title='新工具',
            doc_type='tool',
            namespace=self.namespace,
            creator=self.user,
            last_editor=self.user
        )
        tool_doc.save()
        
        self.assertIsNotNone(tool_doc.type_specific_data)
        self.assertEqual(tool_doc.type_specific_data['tool_type'], 'dynamic')
        
        # 表单类型自动初始化
        form_doc = KnowledgeDocument(
            title='新表单',
            doc_type='form',
            namespace=self.namespace,
            creator=self.user,
            last_editor=self.user
        )
        form_doc.save()
        
        self.assertIsNotNone(form_doc.type_specific_data)
        self.assertEqual(form_doc.type_specific_data['fields'], [])
        
        # 文件夹类型清空数据
        folder_doc = KnowledgeDocument(
            title='文件夹',
            doc_type='folder',
            namespace=self.namespace,
            creator=self.user,
            last_editor=self.user,
            type_specific_data={'test': 'data'}
        )
        folder_doc.save()
        
        self.assertIsNone(folder_doc.type_specific_data) 