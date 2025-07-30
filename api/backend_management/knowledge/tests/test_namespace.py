import allure
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from knowledge.models.namespace import Namespace, NamespaceCollaborator

User = get_user_model()


@allure.feature('知识库管理')
@allure.story('知识库模型测试')
@pytest.mark.django_db
class TestNamespaceModel:
    """知识库模型测试"""

    def test_create_namespace(self):
        """测试创建知识库"""
        with allure.step("创建用户"):
            user = User.objects.create_user(username='testuser', password='testpass123')
        
        with allure.step("创建知识库"):
            namespace = Namespace.objects.create(
                name='测试知识库',
                description='这是一个测试知识库',
                creator=user
            )
        
        with allure.step("验证知识库信息"):
            assert namespace.name == '测试知识库'
            assert namespace.description == '这是一个测试知识库'
            assert namespace.creator == user
            assert namespace.access_type == 'collaborators'  # 默认值
            assert namespace.is_active is True
            assert namespace.slug is not None  # 自动生成
            assert str(namespace) == '测试知识库'

    def test_namespace_permissions(self):
        """测试知识库权限检查"""
        with allure.step("创建用户"):
            creator = User.objects.create_user(username='creator', password='pass123')
            user1 = User.objects.create_user(username='user1', password='pass123')
            user2 = User.objects.create_user(username='user2', password='pass123')
        
        with allure.step("创建知识库"):
            namespace = Namespace.objects.create(
                name='权限测试知识库',
                creator=creator,
                access_type='collaborators'
            )
        
        with allure.step("测试创建者权限"):
            assert namespace.can_access(creator) is True
            assert namespace.can_edit(creator) is True
        
        with allure.step("测试普通用户权限"):
            assert namespace.can_access(user1) is False
            assert namespace.can_edit(user1) is False
        
        with allure.step("添加协作者"):
            NamespaceCollaborator.objects.create(
                namespace=namespace,
                user=user1,
                can_edit=True,
                added_by=creator
            )
        
        with allure.step("测试协作者权限"):
            assert namespace.can_access(user1) is True
            assert namespace.can_edit(user1) is True
        
        with allure.step("测试公开知识库"):
            namespace.access_type = 'public'
            namespace.save()
            assert namespace.can_access(user2) is True
            assert namespace.can_edit(user2) is False  # 仍然不能编辑

    def test_collaborator_count(self):
        """测试协作者数量统计"""
        with allure.step("创建用户和知识库"):
            creator = User.objects.create_user(username='creator', password='pass123')
            user1 = User.objects.create_user(username='user1', password='pass123')
            user2 = User.objects.create_user(username='user2', password='pass123')
            
            namespace = Namespace.objects.create(
                name='协作者测试知识库',
                creator=creator
            )
        
        with allure.step("验证初始协作者数量"):
            assert namespace.collaborator_count == 0
        
        with allure.step("添加协作者"):
            NamespaceCollaborator.objects.create(
                namespace=namespace,
                user=user1,
                added_by=creator
            )
            NamespaceCollaborator.objects.create(
                namespace=namespace,
                user=user2,
                added_by=creator
            )
        
        with allure.step("验证协作者数量"):
            assert namespace.collaborator_count == 2


@allure.feature('知识库管理')
@allure.story('知识库API测试')
@pytest.mark.django_db
class TestNamespaceAPI:
    """知识库API测试"""

    def setup_method(self):
        """测试前准备"""
        self.client = APIClient()
        self.user1 = User.objects.create_user(username='user1', password='pass123')
        self.user2 = User.objects.create_user(username='user2', password='pass123')
        self.user3 = User.objects.create_user(username='user3', password='pass123')

    def test_create_namespace(self):
        """测试创建知识库API"""
        with allure.step("用户登录"):
            self.client.force_authenticate(user=self.user1)
        
        with allure.step("创建知识库"):
            data = {
                'name': 'API测试知识库',
                'description': '通过API创建的知识库',
                'access_type': 'collaborators'
            }
            response = self.client.post('/knowledge/namespaces/', data)
        
        with allure.step("验证响应"):
            assert response.status_code == status.HTTP_201_CREATED
            assert response.data['name'] == 'API测试知识库'
            assert response.data['creator']['username'] == 'user1'
            assert response.data['can_access'] is True
            assert response.data['can_edit'] is True

    def test_list_namespaces(self):
        """测试获取知识库列表API"""
        with allure.step("创建测试数据"):
            # 用户1创建的知识库
            namespace1 = Namespace.objects.create(
                name='用户1的知识库',
                creator=self.user1
            )
            
            # 用户2创建的私有知识库
            Namespace.objects.create(
                name='用户2的私有知识库',
                creator=self.user2,
                access_type='collaborators'
            )
            
            # 用户2创建的公开知识库
            Namespace.objects.create(
                name='用户2的公开知识库',
                creator=self.user2,
                access_type='public'
            )
            
            # 用户1被邀请协作的知识库
            namespace4 = Namespace.objects.create(
                name='协作知识库',
                creator=self.user2
            )
            NamespaceCollaborator.objects.create(
                namespace=namespace4,
                user=self.user1,
                added_by=self.user2
            )
        
        with allure.step("用户1登录并获取知识库列表"):
            self.client.force_authenticate(user=self.user1)
            response = self.client.get('/knowledge/namespaces/')
        
        with allure.step("验证响应"):
            assert response.status_code == status.HTTP_200_OK
            assert len(response.data['results']) == 3  # 自己的 + 公开的 + 协作的
            
            namespace_names = [ns['name'] for ns in response.data['results']]
            assert '用户1的知识库' in namespace_names
            assert '用户2的公开知识库' in namespace_names
            assert '协作知识库' in namespace_names
            assert '用户2的私有知识库' not in namespace_names

    def test_search_namespaces(self):
        """测试搜索知识库API"""
        with allure.step("创建测试数据"):
            Namespace.objects.create(
                name='Django学习知识库',
                creator=self.user1
            )
            Namespace.objects.create(
                name='Python编程指南',
                creator=self.user1
            )
            Namespace.objects.create(
                name='前端开发笔记',
                creator=self.user1
            )
        
        with allure.step("用户登录并搜索"):
            self.client.force_authenticate(user=self.user1)
            response = self.client.get('/knowledge/namespaces/?search=Python')
        
        with allure.step("验证搜索结果"):
            assert response.status_code == status.HTTP_200_OK
            assert len(response.data['results']) == 1
            assert response.data['results'][0]['name'] == 'Python编程指南'

    def test_add_collaborator(self):
        """测试添加协作者API"""
        with allure.step("创建知识库"):
            namespace = Namespace.objects.create(
                name='协作测试知识库',
                creator=self.user1
            )
        
        with allure.step("用户1登录并添加协作者"):
            self.client.force_authenticate(user=self.user1)
            data = {
                'username': 'user2',
                'can_edit': True
            }
            response = self.client.post(f'/knowledge/namespaces/{namespace.id}/add_collaborator/', data)
        
        with allure.step("验证响应"):
            assert response.status_code == status.HTTP_201_CREATED
            assert response.data['user']['username'] == 'user2'
            assert response.data['can_edit'] is True
        
        with allure.step("验证数据库中的协作关系"):
            collaborator = NamespaceCollaborator.objects.get(
                namespace=namespace,
                user=self.user2
            )
            assert collaborator.can_edit is True
            assert collaborator.added_by == self.user1

    def test_remove_collaborator(self):
        """测试移除协作者API"""
        with allure.step("创建知识库和协作关系"):
            namespace = Namespace.objects.create(
                name='移除协作者测试',
                creator=self.user1
            )
            NamespaceCollaborator.objects.create(
                namespace=namespace,
                user=self.user2,
                added_by=self.user1
            )
        
        with allure.step("用户1登录并移除协作者"):
            self.client.force_authenticate(user=self.user1)
            response = self.client.delete(f'/knowledge/namespaces/{namespace.id}/collaborators/{self.user2.id}/')
        
        with allure.step("验证响应"):
            assert response.status_code == status.HTTP_204_NO_CONTENT
        
        with allure.step("验证协作关系已删除"):
            assert not NamespaceCollaborator.objects.filter(
                namespace=namespace,
                user=self.user2
            ).exists()

    def test_update_namespace_basic_info(self):
        """测试更新知识库基本信息API"""
        with allure.step("创建知识库"):
            namespace = Namespace.objects.create(
                name='原始名称',
                description='原始描述',
                creator=self.user1,
                access_type='collaborators'
            )
        
        with allure.step("用户1登录并更新基本信息"):
            self.client.force_authenticate(user=self.user1)
            data = {
                'name': '更新后的名称',
                'description': '更新后的描述',
                'access_type': 'public'
            }
            response = self.client.patch(f'/knowledge/namespaces/{namespace.id}/update_basic/', data)
        
        with allure.step("验证响应"):
            assert response.status_code == status.HTTP_200_OK
            assert response.data['name'] == '更新后的名称'
            assert response.data['description'] == '更新后的描述'
            assert response.data['access_type'] == 'public'
        
        with allure.step("验证数据库中的更新"):
            namespace.refresh_from_db()
            assert namespace.name == '更新后的名称'
            assert namespace.description == '更新后的描述'
            assert namespace.access_type == 'public'

    def test_unauthorized_access(self):
        """测试未授权访问"""
        with allure.step("创建知识库"):
            namespace = Namespace.objects.create(
                name='私有知识库',
                creator=self.user1,
                access_type='collaborators'
            )
        
        with allure.step("用户2尝试访问用户1的私有知识库"):
            self.client.force_authenticate(user=self.user2)
            response = self.client.get(f'/knowledge/namespaces/{namespace.id}/')
        
        with allure.step("验证访问被拒绝"):
            # 在实际的权限控制中，这里应该返回403或404
            # 具体行为取决于视图集的权限实现
            assert response.status_code in [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND]

    @allure.story("Base64图片上传")
    def test_base64_image_upload(self):
        """测试base64图片上传"""
        with allure.step("创建知识库"):
            namespace = Namespace.objects.create(
                name='测试知识库',
                creator=self.user1
            )
        
        with allure.step("准备base64图片数据"):
            # 一个简单的1x1像素PNG图片的base64编码
            base64_image = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
        
        with allure.step("通过API更新知识库封面"):
            self.client.force_authenticate(user=self.user1)
            data = {
                'name': '更新后的知识库',
                'description': '测试base64图片上传',
                'cover': base64_image,
                'access_type': 'collaborators'
            }
            response = self.client.patch(f'/knowledge/namespaces/{namespace.id}/update_basic/', data)
        
        with allure.step("验证更新成功"):
            assert response.status_code == status.HTTP_200_OK
            assert response.data['name'] == '更新后的知识库'
            assert response.data['description'] == '测试base64图片上传'
            assert 'cover' in response.data
            # 更新后的对象应该有封面文件
            namespace.refresh_from_db()
            assert namespace.cover is not None
            assert namespace.cover.name != ''

    @allure.story("协作者权限系统")
    def test_collaborator_role_system(self):
        """测试新的协作者角色权限系统"""
        with allure.step("创建知识库"):
            namespace = Namespace.objects.create(
                name='权限测试知识库',
                creator=self.user1
            )
        
        with allure.step("添加管理权限协作者"):
            self.client.force_authenticate(user=self.user1)
            data = {
                'username': self.user2.username,
                'role': 'admin'
            }
            response = self.client.post(f'/knowledge/namespaces/{namespace.id}/add_collaborator/', data)
        
        with allure.step("验证添加管理员成功"):
            assert response.status_code == status.HTTP_201_CREATED
            assert response.data['user']['username'] == self.user2.username
            assert response.data['role'] == 'admin'
            assert response.data['can_edit'] == True
            assert response.data['can_read'] == True
        
        with allure.step("添加只读权限协作者"):
            data = {
                'username': self.user3.username,
                'role': 'readonly'
            }
            response = self.client.post(f'/knowledge/namespaces/{namespace.id}/add_collaborator/', data)
        
        with allure.step("验证添加只读用户成功"):
            assert response.status_code == status.HTTP_201_CREATED
            assert response.data['user']['username'] == self.user3.username
            assert response.data['role'] == 'readonly'
            assert response.data['can_edit'] == False
            assert response.data['can_read'] == True
        
        with allure.step("测试管理员权限"):
            # 管理员应该可以编辑知识库
            self.client.force_authenticate(user=self.user2)
            data = {'name': '管理员修改的名称'}
            response = self.client.patch(f'/knowledge/namespaces/{namespace.id}/update_basic/', data)
            assert response.status_code == status.HTTP_200_OK
        
        with allure.step("测试只读用户权限"):
            # 只读用户不应该可以编辑知识库
            self.client.force_authenticate(user=self.user3)
            data = {'name': '只读用户尝试修改'}
            response = self.client.patch(f'/knowledge/namespaces/{namespace.id}/update_basic/', data)
            assert response.status_code == status.HTTP_403_FORBIDDEN

    @allure.story("权限兼容性测试")
    def test_can_edit_compatibility(self):
        """测试can_edit字段的向后兼容性"""
        with allure.step("创建知识库"):
            namespace = Namespace.objects.create(
                name='兼容性测试知识库',
                creator=self.user1
            )
        
        with allure.step("使用旧的can_edit字段添加协作者"):
            self.client.force_authenticate(user=self.user1)
            data = {
                'username': self.user2.username,
                'can_edit': True  # 使用旧字段
            }
            response = self.client.post(f'/knowledge/namespaces/{namespace.id}/add_collaborator/', data)
        
        with allure.step("验证兼容性转换"):
            assert response.status_code == status.HTTP_201_CREATED
            assert response.data['role'] == 'admin'  # 应该转换为admin角色
            assert response.data['can_edit'] == True
        
        with allure.step("使用旧字段更新权限"):
            collaborator_id = response.data['user']['id']
            data = {'can_edit': False}
            response = self.client.patch(
                f'/knowledge/namespaces/{namespace.id}/collaborators/{collaborator_id}/',
                data
            )
        
        with allure.step("验证权限更新"):
            assert response.status_code == status.HTTP_200_OK
            assert response.data['role'] == 'readonly'  # 应该转换为readonly角色
            assert response.data['can_edit'] == False 