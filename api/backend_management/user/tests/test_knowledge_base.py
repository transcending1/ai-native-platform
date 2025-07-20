import allure
import pytest
import uuid
from unittest.mock import patch, MagicMock
from django.urls import reverse
from django.contrib.auth.models import User as DjangoUser
from rest_framework.test import APIClient
from rest_framework import status
from django.core.files.uploadedfile import SimpleUploadedFile

from user.models.knowledge_base import KnowledgeBase, Document, KnowledgeBaseCollaborator
from user.models.book_manager import User


@pytest.fixture
def api_client():
    """创建API客户端"""
    return APIClient()


@pytest.fixture
def test_user():
    """创建测试用户"""
    return User.objects.create(
        name='测试用户',
        email='test@example.com'
    )


@pytest.fixture
def authenticated_client(test_user):
    """创建已认证的客户端"""
    client = APIClient()
    # 创建Django用户用于认证
    django_user = DjangoUser.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )
    client.force_authenticate(user=django_user)
    return client


@pytest.fixture
def test_knowledge_base(test_user):
    """创建测试知识库"""
    return KnowledgeBase.objects.create(
        name='测试知识库',
        desc='这是一个测试知识库',
        owner=test_user
    )


@allure.feature('知识库管理')
@allure.story('创建知识库')
@pytest.mark.django_db
def test_create_knowledge_base_with_owner(authenticated_client, test_user):
    """测试创建知识库（带用户绑定）"""
    url = reverse('knowledgebase-list')
    
    with allure.step("创建知识库 - 包含名称、描述和设置"):
        data = {
            'name': '测试知识库',
            'desc': '这是一个测试知识库',
            'doc_width': 'standard',
            'enable_comments': True,
            'auto_publish': False,
            'doc_create_position': 'top'
        }
        response = authenticated_client.post(url, data, format='json')
        
    with allure.step("验证创建成功"):
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['success'] is True
        assert response.data['message'] == '知识库创建成功'
        assert response.data['data']['name'] == '测试知识库'
        
    with allure.step("验证数据库中存在该知识库"):
        kb = KnowledgeBase.objects.get(id=response.data['data']['kbId'])
        assert kb.name == '测试知识库'
        assert kb.desc == '这是一个测试知识库'
        assert kb.owner == test_user
        assert kb.doc_width == 'standard'
        assert kb.enable_comments is True


@allure.feature('知识库管理')
@allure.story('创建知识库')
@pytest.mark.django_db
def test_create_knowledge_base_empty_name(authenticated_client):
    """测试创建知识库时名称为空"""
    url = reverse('knowledgebase-list')
    
    with allure.step("尝试创建名称为空的知识库"):
        data = {
            'name': '',
            'desc': '描述信息'
        }
        response = authenticated_client.post(url, data, format='json')
        
    with allure.step("验证创建失败"):
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['success'] is False
        assert response.data['message'] == '知识库创建失败'


@allure.feature('知识库管理')
@allure.story('查询知识库列表')
@pytest.mark.django_db
def test_list_knowledge_base_with_owner(authenticated_client, test_user):
    """测试查询知识库列表（仅显示用户拥有的）"""
    url = reverse('knowledgebase-list')
    
    with allure.step("创建测试数据"):
        # 创建其他用户和知识库
        other_user = User.objects.create(name='其他用户', email='other@example.com')
        
        kb1 = KnowledgeBase.objects.create(name='我的知识库1', desc='描述1', owner=test_user)
        kb2 = KnowledgeBase.objects.create(name='我的知识库2', desc='描述2', owner=test_user)
        other_kb = KnowledgeBase.objects.create(name='其他知识库', desc='其他描述', owner=other_user)
        
        # 为知识库1添加文档
        Document.objects.create(knowledge_base=kb1, title='文档1', content='内容1')
        Document.objects.create(knowledge_base=kb1, title='文档2', content='内容2')
        
    with allure.step("获取知识库列表"):
        response = authenticated_client.get(url)
        
    with allure.step("验证只返回当前用户的知识库"):
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert len(response.data['data']['results']) == 2  # 只显示当前用户的知识库
        
        # 验证返回的知识库都属于当前用户
        for kb_data in response.data['data']['results']:
            assert kb_data['owner_name'] == '测试用户'


@allure.feature('知识库管理')
@allure.story('更新知识库设置')
@pytest.mark.django_db
def test_update_knowledge_base_settings(authenticated_client, test_knowledge_base):
    """测试更新知识库设置"""
    url = reverse('knowledgebase-update-settings', kwargs={'pk': test_knowledge_base.id})
    
    with allure.step("更新知识库设置"):
        data = {
            'doc_width': 'wide',
            'enable_comments': False,
            'auto_publish': True,
            'doc_create_position': 'bottom'
        }
        response = authenticated_client.patch(url, data, format='json')
        
    with allure.step("验证更新成功"):
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert response.data['message'] == '设置更新成功'
        
    with allure.step("验证数据库中的更新"):
        test_knowledge_base.refresh_from_db()
        assert test_knowledge_base.doc_width == 'wide'
        assert test_knowledge_base.enable_comments is False
        assert test_knowledge_base.auto_publish is True
        assert test_knowledge_base.doc_create_position == 'bottom'


@allure.feature('知识库管理')
@allure.story('上传知识库封面')
@pytest.mark.django_db
@patch('user.utils.cos_storage.cos_upload_service.upload_image')
def test_upload_cover_image(mock_upload, authenticated_client, test_knowledge_base):
    """测试上传知识库封面"""
    url = reverse('knowledgebase-upload-cover', kwargs={'pk': test_knowledge_base.id})
    
    with allure.step("准备图片文件"):
        image_content = b"fake image content"
        image_file = SimpleUploadedFile(
            "test_cover.jpg", 
            image_content, 
            content_type="image/jpeg"
        )
        
    with allure.step("模拟上传成功"):
        mock_upload.return_value = {
            'success': True,
            'message': '上传成功',
            'url': 'https://example.com/test_cover.jpg',
            'path': 'knowledge-base-covers/2025/01/01/test_cover.jpg'
        }
        
    with allure.step("上传封面图片"):
        response = authenticated_client.post(
            url, 
            {'cover_image': image_file}, 
            format='multipart'
        )
        
    with allure.step("验证上传成功"):
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert response.data['data']['cover_image'] == 'https://example.com/test_cover.jpg'
        
    with allure.step("验证数据库更新"):
        test_knowledge_base.refresh_from_db()
        assert test_knowledge_base.cover_image == 'https://example.com/test_cover.jpg'


@allure.feature('知识库协作')
@allure.story('添加协作者')
@pytest.mark.django_db
def test_add_collaborator(authenticated_client, test_knowledge_base):
    """测试添加协作者"""
    url = reverse('knowledgebase-collaborators', kwargs={'pk': test_knowledge_base.id})
    
    with allure.step("创建协作者用户"):
        collaborator_user = User.objects.create(
            name='协作者',
            email='collaborator@example.com'
        )
        
    with allure.step("添加协作者"):
        data = {
            'user_email': 'collaborator@example.com',
            'permission': 'edit'
        }
        response = authenticated_client.post(url, data, format='json')
        
    with allure.step("验证添加成功"):
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['success'] is True
        assert response.data['message'] == '协作者添加成功'
        
    with allure.step("验证数据库中的协作者"):
        collaborator = KnowledgeBaseCollaborator.objects.get(
            knowledge_base=test_knowledge_base,
            user=collaborator_user
        )
        assert collaborator.permission == 'edit'
        assert collaborator.invite_token is not None


@allure.feature('知识库协作')
@allure.story('获取协作者列表')
@pytest.mark.django_db
def test_get_collaborators(authenticated_client, test_knowledge_base):
    """测试获取协作者列表"""
    url = reverse('knowledgebase-collaborators', kwargs={'pk': test_knowledge_base.id})
    
    with allure.step("创建协作者"):
        collaborator_user = User.objects.create(
            name='协作者',
            email='collaborator@example.com'
        )
        KnowledgeBaseCollaborator.objects.create(
            knowledge_base=test_knowledge_base,
            user=collaborator_user,
            permission='read'
        )
        
    with allure.step("获取协作者列表"):
        response = authenticated_client.get(url)
        
    with allure.step("验证协作者信息"):
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert len(response.data['data']) == 1
        
        collaborator_data = response.data['data'][0]
        assert collaborator_data['user_name'] == '协作者'
        assert collaborator_data['user_email'] == 'collaborator@example.com'
        assert collaborator_data['permission'] == 'read'


@allure.feature('知识库协作')
@allure.story('接受协作邀请')
@pytest.mark.django_db
def test_accept_collaboration_invite(authenticated_client, test_user):
    """测试接受协作邀请"""
    with allure.step("创建知识库和邀请"):
        other_user = User.objects.create(name='拥有者', email='owner@example.com')
        kb = KnowledgeBase.objects.create(
            name='协作知识库',
            desc='测试协作',
            owner=other_user
        )
        
        # 创建协作邀请
        collaborator = KnowledgeBaseCollaborator.objects.create(
            knowledge_base=kb,
            user=test_user,
            permission='read'
        )
        
    with allure.step("接受邀请"):
        url = reverse(
            'knowledgebase-accept-invite', 
            kwargs={'invite_token': collaborator.invite_token}
        )
        response = authenticated_client.post(url)
        
    with allure.step("验证接受成功"):
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert response.data['message'] == '成功加入知识库'
        
    with allure.step("验证邀请状态更新"):
        collaborator.refresh_from_db()
        assert collaborator.accepted_at is not None


@allure.feature('文档管理')
@allure.story('创建文档（根据知识库设置）')
@pytest.mark.django_db
def test_create_document_with_position_setting(test_user):
    """测试根据知识库设置创建文档位置"""
    with allure.step("创建知识库（文档创建位置：顶部）"):
        kb = KnowledgeBase.objects.create(
            name='文档测试库',
            desc='用于测试文档位置',
            owner=test_user,
            doc_create_position='top'
        )
        
        # 先创建一个文档
        existing_doc = Document.objects.create(
            knowledge_base=kb,
            title='现有文档',
            content='现有内容',
            position=0
        )
        
    with allure.step("创建新文档"):
        new_doc = Document.objects.create(
            knowledge_base=kb,
            title='新文档',
            content='新内容'
        )
        
    with allure.step("验证新文档位置在顶部"):
        # 刷新现有文档
        existing_doc.refresh_from_db()
        assert new_doc.position == 0  # 新文档在顶部
        assert existing_doc.position == 1  # 现有文档位置+1


@allure.feature('文档管理')
@allure.story('自动发布功能')
@pytest.mark.django_db
def test_document_auto_publish(test_user):
    """测试文档自动发布功能"""
    with allure.step("创建知识库（开启自动发布）"):
        kb = KnowledgeBase.objects.create(
            name='自动发布测试库',
            desc='测试自动发布',
            owner=test_user,
            auto_publish=True
        )
        
    with allure.step("创建文档"):
        document = Document.objects.create(
            knowledge_base=kb,
            title='自动发布文档',
            content='测试自动发布内容'
        )
        
    with allure.step("验证文档自动发布"):
        assert document.is_published is True
        assert document.published_at is not None


@allure.feature('权限管理')
@allure.story('权限验证')
@pytest.mark.django_db
def test_permission_check(authenticated_client, test_user):
    """测试权限验证"""
    with allure.step("创建其他用户的知识库"):
        other_user = User.objects.create(name='其他用户', email='other@example.com')
        other_kb = KnowledgeBase.objects.create(
            name='其他用户的知识库',
            desc='测试权限',
            owner=other_user
        )
        
    with allure.step("尝试删除其他用户的知识库"):
        url = reverse('knowledgebase-detail', kwargs={'pk': other_kb.id})
        response = authenticated_client.delete(url)
        
    with allure.step("验证权限被拒绝"):
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data['success'] is False
        assert '只有知识库拥有者可以删除知识库' in response.data['message']


@allure.feature('数据完整性')
@allure.story('级联删除')
@pytest.mark.django_db
def test_cascade_delete_with_collaborators(authenticated_client, test_knowledge_base):
    """测试删除知识库时级联删除协作者"""
    with allure.step("添加协作者和文档"):
        collaborator_user = User.objects.create(
            name='协作者',
            email='collaborator@example.com'
        )
        KnowledgeBaseCollaborator.objects.create(
            knowledge_base=test_knowledge_base,
            user=collaborator_user,
            permission='read'
        )
        
        Document.objects.create(
            knowledge_base=test_knowledge_base,
            title='测试文档',
            content='测试内容'
        )
        
    with allure.step("删除知识库"):
        url = reverse('knowledgebase-detail', kwargs={'pk': test_knowledge_base.id})
        response = authenticated_client.delete(url)
        
    with allure.step("验证级联删除"):
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        
        # 验证协作者记录被删除
        assert not KnowledgeBaseCollaborator.objects.filter(
            knowledge_base_id=test_knowledge_base.id
        ).exists()
        
        # 验证文档被删除
        assert not Document.objects.filter(
            knowledge_base_id=test_knowledge_base.id
        ).exists() 