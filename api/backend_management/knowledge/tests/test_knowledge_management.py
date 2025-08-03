import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from unittest.mock import patch

from knowledge.models import (
    Namespace,
    NamespaceCollaborator,
    KnowledgeDocument,
    FormDataEntry,
    ToolExecution
)

User = get_user_model()


@pytest.mark.django_db
class KnowledgeManagementBaseTest(APITestCase):
    """
    知识管理测试基类
    """
    
    def setUp(self):
        """测试数据准备"""
        # 创建测试用户
        self.user1 = User.objects.create_user(
            username='testuser1',
            email='testuser1@example.com',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='testuser2',
            email='testuser2@example.com',
            password='testpass123'
        )
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpass123',
            role='admin'
        )
        
        # 创建测试知识库
        self.namespace = Namespace.objects.create(
            name='测试知识库',
            description='用于测试的知识库',
            creator=self.user1,
            access_type='collaborators'
        )
        
        # 添加协作者
        self.collaborator = NamespaceCollaborator.objects.create(
            namespace=self.namespace,
            user=self.user2,
            role='readonly',
            added_by=self.user1
        )
        
        # API客户端
        self.client = APIClient()
        
    def authenticate_user(self, user):
        """认证用户"""
        self.client.force_authenticate(user=user)


class KnowledgeCategoryTestCase(KnowledgeManagementBaseTest):
    """
    知识分类测试用例
    """
    
    def test_create_category_success(self):
        """测试创建分类成功"""
        self.authenticate_user(self.user1)
        
        url = reverse('namespace-categories-list', kwargs={'namespace_pk': self.namespace.id})
        data = {
            'name': '技术文档',
            'description': '技术相关的文档分类',
            'color': '#1890ff',
            'sort_order': 1
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], '技术文档')
        self.assertEqual(KnowledgeDocument.objects.count(), 1)
        
        category = KnowledgeDocument.objects.first()
        self.assertEqual(category.creator, self.user1)
        self.assertEqual(category.namespace, self.namespace)
    
    def test_create_category_permission_denied(self):
        """测试无权限创建分类"""
        self.authenticate_user(self.user2)  # readonly权限
        
        url = reverse('namespace-categories-list', kwargs={'namespace_pk': self.namespace.id})
        data = {
            'name': '技术文档',
            'description': '技术相关的文档分类'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(KnowledgeDocument.objects.count(), 0)
    
    def test_list_categories(self):
        """测试获取分类列表"""
        # 创建测试分类
        category1 = KnowledgeDocument.objects.create(
            name='技术文档',
            namespace=self.namespace,
            creator=self.user1,
            sort_order=1
        )
        category2 = KnowledgeDocument.objects.create(
            name='产品文档',
            namespace=self.namespace,
            creator=self.user1,
            sort_order=2
        )
        
        self.authenticate_user(self.user2)  # 协作者可以查看
        
        url = reverse('namespace-categories-list', kwargs={'namespace_pk': self.namespace.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]['name'], '技术文档')  # 按sort_order排序
    
    def test_update_category(self):
        """测试更新分类"""
        category = KnowledgeDocument.objects.create(
            name='技术文档',
            namespace=self.namespace,
            creator=self.user1
        )
        
        self.authenticate_user(self.user1)
        
        url = reverse('namespace-categories-detail', kwargs={
            'namespace_pk': self.namespace.id,
            'pk': category.id
        })
        data = {
            'name': '技术文档-更新',
            'description': '更新后的描述',
            'color': '#52c41a'
        }
        
        response = self.client.put(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], '技术文档-更新')
        
        category.refresh_from_db()
        self.assertEqual(category.name, '技术文档-更新')
    
    def test_delete_category(self):
        """测试删除分类"""
        category = KnowledgeDocument.objects.create(
            name='技术文档',
            namespace=self.namespace,
            creator=self.user1
        )
        
        self.authenticate_user(self.user1)
        
        url = reverse('namespace-categories-detail', kwargs={
            'namespace_pk': self.namespace.id,
            'pk': category.id
        })
        
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        category.refresh_from_db()
        self.assertFalse(category.is_active)  # 软删除


class KnowledgeTagTestCase(KnowledgeManagementBaseTest):
    """
    知识标签测试用例
    """
    
    def test_create_tag_success(self):
        """测试创建标签成功"""
        self.authenticate_user(self.user1)
        
        url = reverse('namespace-tags-list', kwargs={'namespace_pk': self.namespace.id})
        data = {
            'name': 'Python',
            'color': '#f5f5f5'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Python')
        self.assertEqual(KnowledgeDocument.objects.count(), 1)
        
        tag = KnowledgeDocument.objects.first()
        self.assertEqual(tag.creator, self.user1)
        self.assertEqual(tag.namespace, self.namespace)
    
    def test_list_tags(self):
        """测试获取标签列表"""
        # 创建测试标签
        tag1 = KnowledgeDocument.objects.create(
            name='Python',
            namespace=self.namespace,
            creator=self.user1,
            usage_count=5
        )
        tag2 = KnowledgeDocument.objects.create(
            name='Django',
            namespace=self.namespace,
            creator=self.user1,
            usage_count=3
        )
        
        self.authenticate_user(self.user2)
        
        url = reverse('namespace-tags-list', kwargs={'namespace_pk': self.namespace.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]['name'], 'Python')  # 按usage_count倒序


class KnowledgeDocumentTestCase(KnowledgeManagementBaseTest):
    """
    知识文档测试用例
    """
    
    def setUp(self):
        super().setUp()
        
        # 创建测试分类和标签
        self.category = KnowledgeDocument.objects.create(
            name='技术文档',
            namespace=self.namespace,
            creator=self.user1
        )
        self.tag1 = KnowledgeDocument.objects.create(
            name='Python',
            namespace=self.namespace,
            creator=self.user1
        )
        self.tag2 = KnowledgeDocument.objects.create(
            name='Django',
            namespace=self.namespace,
            creator=self.user1
        )
    
    def test_create_folder_success(self):
        """测试创建文件夹成功"""
        self.authenticate_user(self.user1)
        
        url = reverse('namespace-documents-list', kwargs={'namespace_pk': self.namespace.id})
        data = {
            'title': '开发文档',
            'doc_type': 'folder',
            'summary': '开发相关的文档文件夹',
            'sort_order': 1,
            'is_public': True
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], '开发文档')
        self.assertEqual(response.data['doc_type'], 'folder')
        self.assertEqual(KnowledgeDocument.objects.count(), 1)
        
        document = KnowledgeDocument.objects.first()
        self.assertEqual(document.creator, self.user1)
        self.assertEqual(document.namespace, self.namespace)
        self.assertTrue(document.is_folder)
    
    def test_create_document_with_category_and_tags(self):
        """测试创建带分类和标签的文档"""
        self.authenticate_user(self.user1)
        
        url = reverse('namespace-documents-list', kwargs={'namespace_pk': self.namespace.id})
        data = {
            'title': 'Django开发指南',
            'content': '# Django开发指南\n\n这是一个Django开发指南...',
            'summary': 'Django开发的最佳实践',
            'doc_type': 'document',
            'status': 'published',
            'category_id': self.category.id,
            'tag_ids': [self.tag1.id, self.tag2.id],
            'is_public': True
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], 'Django开发指南')
        self.assertEqual(response.data['category']['id'], self.category.id)
        self.assertEqual(len(response.data['tags']), 2)
        
        document = KnowledgeDocument.objects.first()
        self.assertEqual(document.category, self.category)
        self.assertEqual(document.tags.count(), 2)
    
    def test_create_document_with_parent(self):
        """测试在文件夹下创建文档"""
        # 先创建父文件夹
        parent_folder = KnowledgeDocument.objects.create(
            title='开发文档',
            doc_type='folder',
            namespace=self.namespace,
            creator=self.user1,
            last_editor=self.user1
        )
        
        self.authenticate_user(self.user1)
        
        url = reverse('namespace-documents-list', kwargs={'namespace_pk': self.namespace.id})
        data = {
            'title': '子文档',
            'content': '这是子文档的内容',
            'doc_type': 'document',
            'parent': parent_folder.id
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['parent'], parent_folder.id)
        
        document = KnowledgeDocument.objects.get(title='子文档')
        self.assertEqual(document.parent, parent_folder)
        self.assertEqual(document.depth, 1)
    
    def test_list_documents_with_filters(self):
        """测试文档列表过滤功能"""
        # 创建测试文档
        folder = KnowledgeDocument.objects.create(
            title='开发文档',
            doc_type='folder',
            namespace=self.namespace,
            creator=self.user1,
            last_editor=self.user1
        )
        doc1 = KnowledgeDocument.objects.create(
            title='Python基础',
            content='Python基础教程',
            doc_type='document',
            namespace=self.namespace,
            creator=self.user1,
            category=self.category,
            parent=folder
        )
        doc1.tags.set([self.tag1])
        
        doc2 = KnowledgeDocument.objects.create(
            title='Django进阶',
            content='Django进阶教程',
            doc_type='document',
            namespace=self.namespace,
            creator=self.user1,
            last_editor=self.user1
        )
        doc2.tags.set([self.tag2])
        
        self.authenticate_user(self.user2)
        
        # 测试父文档过滤
        url = reverse('namespace-documents-list', kwargs={'namespace_pk': self.namespace.id})
        response = self.client.get(url, {'parent_id': folder.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], 'Python基础')
        
        # 测试搜索
        response = self.client.get(url, {'search': 'Python'})
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], 'Python基础')
        
        # 测试分类过滤
        response = self.client.get(url, {'category_id': self.category.id})
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], 'Python基础')
        
        # 测试标签过滤
        response = self.client.get(url, {'tag_ids': f'{self.tag1.id},{self.tag2.id}'})
        self.assertEqual(len(response.data), 2)
    
    def test_retrieve_document_with_permission(self):
        """测试获取文档详情和权限检查"""
        document = KnowledgeDocument.objects.create(
            title='私有文档',
            content='这是私有文档内容',
            doc_type='document',
            namespace=self.namespace,
            creator=self.user1,
            is_public=False
        )
        
        # 创建者可以访问
        self.authenticate_user(self.user1)
        url = reverse('namespace-documents-detail', kwargs={
            'namespace_pk': self.namespace.id,
            'pk': document.id
        })
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 协作者无法访问私有文档
        self.authenticate_user(self.user2)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # 设置为公开文档
        document.is_public = True
        document.save()
        
        # 协作者现在可以访问
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 检查浏览次数增加
        document.refresh_from_db()
        self.assertEqual(document.view_count, 2)  # 两次访问
    
    def test_update_document(self):
        """测试更新文档"""
        document = KnowledgeDocument.objects.create(
            title='原始标题',
            content='原始内容',
            doc_type='document',
            namespace=self.namespace,
            creator=self.user1,
            last_editor=self.user1
        )
        
        self.authenticate_user(self.user1)
        
        url = reverse('namespace-documents-detail', kwargs={
            'namespace_pk': self.namespace.id,
            'pk': document.id
        })
        data = {
            'title': '更新标题',
            'content': '更新内容',
            'summary': '更新摘要',
            'category_id': self.category.id,
            'tag_ids': [self.tag1.id]
        }
        
        response = self.client.put(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], '更新标题')
        
        document.refresh_from_db()
        self.assertEqual(document.title, '更新标题')
        self.assertEqual(document.last_editor, self.user1)
        self.assertEqual(document.category, self.category)
    
    def test_delete_document_recursive(self):
        """测试递归删除文档"""
        # 创建层次结构
        folder = KnowledgeDocument.objects.create(
            title='文件夹',
            doc_type='folder',
            namespace=self.namespace,
            creator=self.user1,
            last_editor=self.user1
        )
        subfolder = KnowledgeDocument.objects.create(
            title='子文件夹',
            doc_type='folder',
            namespace=self.namespace,
            creator=self.user1,
            parent=folder
        )
        document = KnowledgeDocument.objects.create(
            title='文档',
            doc_type='document',
            namespace=self.namespace,
            creator=self.user1,
            parent=subfolder
        )
        
        self.authenticate_user(self.user1)
        
        url = reverse('namespace-documents-detail', kwargs={
            'namespace_pk': self.namespace.id,
            'pk': folder.id
        })
        
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # 检查所有文档都被软删除
        folder.refresh_from_db()
        subfolder.refresh_from_db()
        document.refresh_from_db()
        
        self.assertFalse(folder.is_active)
        self.assertFalse(subfolder.is_active)
        self.assertFalse(document.is_active)
    
    def test_get_document_tree(self):
        """测试获取文档树"""
        # 创建层次结构
        folder1 = KnowledgeDocument.objects.create(
            title='文件夹1',
            doc_type='folder',
            namespace=self.namespace,
            creator=self.user1,
            sort_order=1
        )
        folder2 = KnowledgeDocument.objects.create(
            title='文件夹2',
            doc_type='folder',
            namespace=self.namespace,
            creator=self.user1,
            sort_order=2
        )
        subfolder = KnowledgeDocument.objects.create(
            title='子文件夹',
            doc_type='folder',
            namespace=self.namespace,
            creator=self.user1,
            parent=folder1
        )
        document = KnowledgeDocument.objects.create(
            title='文档',
            doc_type='document',
            namespace=self.namespace,
            creator=self.user1,
            parent=subfolder
        )
        
        self.authenticate_user(self.user2)
        
        url = reverse('namespace-documents-tree', kwargs={'namespace_pk': self.namespace.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # 两个根文件夹
        
        # 检查嵌套结构
        folder1_data = response.data[0]
        self.assertEqual(folder1_data['title'], '文件夹1')
        self.assertEqual(len(folder1_data['children']), 1)
        
        subfolder_data = folder1_data['children'][0]
        self.assertEqual(subfolder_data['title'], '子文件夹')
        self.assertEqual(len(subfolder_data['children']), 1)
        
        document_data = subfolder_data['children'][0]
        self.assertEqual(document_data['title'], '文档')
        self.assertEqual(len(document_data['children']), 0)
    
    def test_move_document(self):
        """测试移动文档"""
        folder1 = KnowledgeDocument.objects.create(
            title='文件夹1',
            doc_type='folder',
            namespace=self.namespace,
            creator=self.user1,
            last_editor=self.user1
        )
        folder2 = KnowledgeDocument.objects.create(
            title='文件夹2',
            doc_type='folder',
            namespace=self.namespace,
            creator=self.user1,
            last_editor=self.user1
        )
        document = KnowledgeDocument.objects.create(
            title='文档',
            doc_type='document',
            namespace=self.namespace,
            creator=self.user1,
            parent=folder1
        )
        
        self.authenticate_user(self.user1)
        
        url = reverse('namespace-documents-move', kwargs={
            'namespace_pk': self.namespace.id,
            'pk': document.id
        })
        data = {
            'target_parent_id': folder2.id,
            'sort_order': 5
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        document.refresh_from_db()
        self.assertEqual(document.parent, folder2)
        self.assertEqual(document.sort_order, 5)

    def test_create_tool_with_type_specific_data(self):
        """测试通过type_specific_data字段创建工具知识"""
        url = reverse('namespace-documents-list', kwargs={'namespace_pk': self.namespace.id})
        
        data = {
            'title': '电瓶车',
            'doc_type': 'tool',
            'parent': None,
            'is_public': True,
            'type_specific_data': {
                'name': '电瓶车',
                'description': '电瓶车工具描述'
            }
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # 验证创建成功
        document = KnowledgeDocument.objects.get(id=response.data['id'])
        self.assertEqual(document.title, '电瓶车')
        self.assertEqual(document.doc_type, 'tool')
        
        # 验证工具数据被正确保存
        tool_data = document.get_tool_data()
        self.assertEqual(tool_data['name'], '电瓶车')
        self.assertEqual(tool_data['description'], '电瓶车工具描述')
        
        # 验证GET请求能获取到正确的数据
        detail_url = reverse('namespace-documents-detail', kwargs={
            'namespace_pk': self.namespace.id,
            'pk': document.id
        })
        detail_response = self.client.get(detail_url)
        self.assertEqual(detail_response.status_code, status.HTTP_200_OK)
        
        # 验证返回的工具数据正确
        returned_tool_data = detail_response.data['tool_data']
        self.assertEqual(returned_tool_data['name'], '电瓶车')
        self.assertEqual(returned_tool_data['description'], '电瓶车工具描述')

    def test_create_form_with_type_specific_data(self):
        """测试通过type_specific_data字段创建表单知识"""
        url = reverse('namespace-documents-list', kwargs={'namespace_pk': self.namespace.id})
        
        data = {
            'title': '用户信息表',
            'doc_type': 'form',
            'parent': None,
            'is_public': True,
            'type_specific_data': {
                'table_name': 'user_info',
                'table_description': '用户信息收集表单',
                'fields': [
                    {
                        'name': 'name',
                        'field_type': 'String',
                        'required': True,
                        'default_value': ''
                    }
                ]
            }
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # 验证创建成功
        document = KnowledgeDocument.objects.get(id=response.data['id'])
        self.assertEqual(document.title, '用户信息表')
        self.assertEqual(document.doc_type, 'form')
        
        # 验证表单数据被正确保存
        form_data = document.get_form_data()
        self.assertEqual(form_data['table_name'], 'user_info')
        self.assertEqual(form_data['table_description'], '用户信息收集表单')
        self.assertEqual(len(form_data['fields']), 1)
        self.assertEqual(form_data['fields'][0]['name'], 'name')


class KnowledgeVersionTestCase(KnowledgeManagementBaseTest):
    """
    知识版本测试用例
    """
    
    def setUp(self):
        super().setUp()
        
        self.document = KnowledgeDocument.objects.create(
            title='版本测试文档',
            content='原始内容',
            doc_type='document',
            namespace=self.namespace,
            creator=self.user1,
            last_editor=self.user1
        )
    
    def test_create_version(self):
        """测试创建版本"""
        self.authenticate_user(self.user1)
        
        url = reverse('document-versions-list', kwargs={
            'namespace_pk': self.namespace.id,
            'document_pk': self.document.id
        })
        data = {
            'version_number': 'v1.0',
            'title': '版本1.0标题',
            'content': '版本1.0内容',
            'summary': '版本1.0摘要',
            'change_log': '初始版本'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['version_number'], 'v1.0')
        self.assertEqual(KnowledgeDocument.objects.count(), 1)
        
        version = KnowledgeDocument.objects.first()
        self.assertEqual(version.document, self.document)
        self.assertEqual(version.creator, self.user1)
    
    def test_list_versions(self):
        """测试获取版本列表"""
        # 创建测试版本
        version1 = KnowledgeDocument.objects.create(
            document=self.document,
            version_number='v1.0',
            title='版本1.0',
            content='版本1.0内容',
            creator=self.user1
        )
        version2 = KnowledgeDocument.objects.create(
            document=self.document,
            version_number='v1.1',
            title='版本1.1',
            content='版本1.1内容',
            creator=self.user1
        )
        
        self.authenticate_user(self.user2)  # 协作者可以查看版本
        
        url = reverse('document-versions-list', kwargs={
            'namespace_pk': self.namespace.id,
            'document_pk': self.document.id
        })
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        # 按创建时间倒序
        self.assertEqual(response.data[0]['version_number'], 'v1.1')


class KnowledgeCommentTestCase(KnowledgeManagementBaseTest):
    """
    知识评论测试用例
    """
    
    def setUp(self):
        super().setUp()
        
        self.document = KnowledgeDocument.objects.create(
            title='评论测试文档',
            content='文档内容',
            doc_type='document',
            namespace=self.namespace,
            creator=self.user1,
            is_public=True
        )
    
    def test_create_comment(self):
        """测试创建评论"""
        self.authenticate_user(self.user2)
        
        url = reverse('document-comments-list', kwargs={
            'namespace_pk': self.namespace.id,
            'document_pk': self.document.id
        })
        data = {
            'content': '这是一个测试评论'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['content'], '这是一个测试评论')
        self.assertEqual(KnowledgeDocument.objects.count(), 1)
        
        comment = KnowledgeDocument.objects.first()
        self.assertEqual(comment.document, self.document)
        self.assertEqual(comment.creator, self.user2)
    
    def test_create_reply_comment(self):
        """测试创建回复评论"""
        # 创建父评论
        parent_comment = KnowledgeDocument.objects.create(
            document=self.document,
            content='父评论',
            creator=self.user1
        )
        
        self.authenticate_user(self.user2)
        
        url = reverse('document-comments-list', kwargs={
            'namespace_pk': self.namespace.id,
            'document_pk': self.document.id
        })
        data = {
            'content': '这是一个回复',
            'parent': parent_comment.id
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['parent'], parent_comment.id)
        
        reply = KnowledgeDocument.objects.get(parent=parent_comment)
        self.assertEqual(reply.content, '这是一个回复')
    
    def test_list_comments_with_replies(self):
        """测试获取评论列表（包含回复）"""
        # 创建评论和回复
        comment1 = KnowledgeDocument.objects.create(
            document=self.document,
            content='评论1',
            creator=self.user1
        )
        comment2 = KnowledgeDocument.objects.create(
            document=self.document,
            content='评论2',
            creator=self.user2
        )
        reply1 = KnowledgeDocument.objects.create(
            document=self.document,
            content='回复1',
            creator=self.user2,
            parent=comment1
        )
        reply2 = KnowledgeDocument.objects.create(
            document=self.document,
            content='回复2',
            creator=self.user1,
            parent=comment1
        )
        
        self.authenticate_user(self.user2)
        
        url = reverse('document-comments-list', kwargs={
            'namespace_pk': self.namespace.id,
            'document_pk': self.document.id
        })
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # 只返回顶级评论
        
        # 检查回复嵌套
        comment1_data = next(c for c in response.data if c['content'] == '评论1')
        self.assertEqual(len(comment1_data['replies']), 2)
        
        comment2_data = next(c for c in response.data if c['content'] == '评论2')
        self.assertEqual(len(comment2_data['replies']), 0)


@pytest.mark.django_db
class SimpleDocumentUpdateTestCase(APITestCase):
    """
    简单的文档更新测试用例
    """
    
    def setUp(self):
        """测试数据准备"""
        # 创建测试用户
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='testpass123'
        )
        
        # 创建测试知识库
        self.namespace = Namespace.objects.create(
            name='测试知识库',
            description='用于测试的知识库',
            creator=self.user,
            access_type='collaborators'
        )
        
        # 创建测试文档
        self.document = KnowledgeDocument.objects.create(
            title='原始标题',
            content='原始内容',
            summary='原始摘要',
            doc_type='document',
            namespace=self.namespace,
            creator=self.user,
            last_editor=self.user
        )
        
        # API客户端
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
    
    def test_update_document_content_only(self):
        """测试只更新文档内容"""
        url = reverse('namespace-documents-detail', kwargs={
            'namespace_pk': self.namespace.id,
            'pk': self.document.id
        })
        
        data = {
            'title': self.document.title,  # 保持原有标题
            'content': '更新后的内容',
            'summary': '更新后的摘要'
        }
        
        response = self.client.put(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['content'], '更新后的内容')
        self.assertEqual(response.data['summary'], '更新后的摘要')
        
        # 验证数据库中的更新
        self.document.refresh_from_db()
        self.assertEqual(self.document.content, '更新后的内容')
        self.assertEqual(self.document.summary, '更新后的摘要')
        self.assertEqual(self.document.last_editor, self.user)
    
    def test_update_document_frontend_style(self):
        """测试前端风格的更新请求（只包含content和summary）"""
        url = reverse('namespace-documents-detail', kwargs={
            'namespace_pk': self.namespace.id,
            'pk': self.document.id
        })
        
        # 模拟前端发送的数据（只包含content和summary）
        data = {
            'content': '前端更新的内容',
            'summary': '前端更新的摘要'
        }
        
        response = self.client.put(url, data, format='json')
        
        # 应该返回400错误，因为缺少必需的title字段
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('title', response.data['details'])
        
        # 现在测试修复后的前端请求（包含title）
        data_with_title = {
            'title': self.document.title,  # 包含原有标题
            'content': '前端更新的内容',
            'summary': '前端更新的摘要'
        }
        
        response = self.client.put(url, data_with_title, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['content'], '前端更新的内容')
        self.assertEqual(response.data['summary'], '前端更新的摘要')
        
        # 验证数据库中的更新
        self.document.refresh_from_db()
        self.assertEqual(self.document.content, '前端更新的内容')
        self.assertEqual(self.document.summary, '前端更新的摘要')


if __name__ == '__main__':
    pytest.main([__file__]) 