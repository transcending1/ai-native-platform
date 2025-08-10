import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient
from datetime import timedelta
from unittest.mock import patch, MagicMock

from summary.models.summary import UserSummary, PlatformSummary


User = get_user_model()


@pytest.fixture
def user():
    """创建测试用户"""
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )


@pytest.fixture
def authenticated_client(user):
    """创建已认证的API客户端"""
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def user_summary(user):
    """创建用户统计数据"""
    return UserSummary.objects.create(
        user=user,
        total_llm_models=5,
        total_namespaces=10,
        created_namespaces=8,
        collaborated_namespaces=2,
        total_documents=50,
        normal_documents=30,
        tool_documents=20,
        created_bots=3,
        collaborated_bots=1
    )


@pytest.fixture
def platform_summary():
    """创建平台统计数据"""
    return PlatformSummary.objects.create(
        date=timezone.now().date(),
        total_users=100,
        active_users=80,
        total_llm_models=10,
        total_namespaces=200,
        total_documents=1000,
        total_bots=50
    )


@pytest.mark.django_db
class TestUserSummaryModel:
    """用户统计模型测试"""
    
    def test_create_user_summary(self, user):
        """测试创建用户统计"""
        summary = UserSummary.objects.create(
            user=user,
            total_llm_models=5,
            total_namespaces=10
        )
        
        assert summary.user == user
        assert summary.total_llm_models == 5
        assert summary.total_namespaces == 10
        assert str(summary) == f"{user.username}的统计数据"
    
    @patch('summary.models.summary.LLMModel')
    @patch('summary.models.summary.Namespace')
    @patch('summary.models.summary.KnowledgeDocument')
    @patch('summary.models.summary.Bot')
    def test_refresh_statistics(self, mock_bot, mock_doc, mock_namespace, mock_llm, user):
        """测试刷新统计数据"""
        # 模拟模型查询返回值
        mock_llm.objects.filter.return_value.count.return_value = 5
        mock_namespace.objects.filter.return_value.count.return_value = 8
        mock_namespace.objects.filter.return_value.exclude.return_value.count.return_value = 2
        mock_doc.objects.filter.return_value.count.return_value = 50
        mock_doc.objects.filter.return_value.filter.return_value.count.side_effect = [30, 20]
        mock_bot.objects.filter.return_value.count.return_value = 3
        
        summary = UserSummary.objects.create(user=user)
        result = summary.refresh_statistics()
        
        assert result == summary
        assert summary.total_llm_models == 5
        assert summary.created_namespaces == 8
        assert summary.collaborated_namespaces == 2
        assert summary.total_namespaces == 10
        assert summary.total_documents == 50
        assert summary.normal_documents == 30
        assert summary.tool_documents == 20
        assert summary.created_bots == 3


@pytest.mark.django_db
class TestPlatformSummaryModel:
    """平台统计模型测试"""
    
    def test_create_platform_summary(self):
        """测试创建平台统计"""
        today = timezone.now().date()
        summary = PlatformSummary.objects.create(
            date=today,
            total_users=100,
            active_users=80
        )
        
        assert summary.date == today
        assert summary.total_users == 100
        assert summary.active_users == 80
        assert str(summary) == f"{today}的平台统计"
    
    @patch('summary.models.summary.Bot')
    @patch('summary.models.summary.KnowledgeDocument')
    @patch('summary.models.summary.Namespace')
    @patch('summary.models.summary.LLMModel')
    def test_generate_daily_summary(self, mock_llm, mock_namespace, mock_doc, mock_bot):
        """测试生成每日统计"""
        # 模拟查询返回值
        User.objects.create_user(username='test1', email='test1@example.com')
        User.objects.create_user(username='test2', email='test2@example.com')
        
        mock_llm.objects.filter.return_value.count.return_value = 10
        mock_namespace.objects.count.return_value = 200
        mock_doc.objects.count.return_value = 1000
        mock_bot.objects.count.return_value = 50
        
        today = timezone.now().date()
        summary = PlatformSummary.generate_daily_summary(today)
        
        assert summary.date == today
        assert summary.total_users == 2
        assert summary.total_llm_models == 10
        assert summary.total_namespaces == 200
        assert summary.total_documents == 1000
        assert summary.total_bots == 50


@pytest.mark.django_db
class TestUserSummaryViewSet:
    """用户统计视图集测试"""
    
    def test_list_user_summary_success(self, authenticated_client, user_summary):
        """测试获取用户统计数据成功"""
        url = reverse('user-summary-list')
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['username'] == user_summary.user.username
        assert data['total_llm_models'] == user_summary.total_llm_models
        assert data['total_namespaces'] == user_summary.total_namespaces
    
    def test_list_user_summary_auto_create(self, authenticated_client, user):
        """测试自动创建用户统计数据"""
        url = reverse('user-summary-list')
        
        # 确保没有统计数据
        assert not UserSummary.objects.filter(user=user).exists()
        
        with patch.object(UserSummary, 'refresh_statistics') as mock_refresh:
            response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert UserSummary.objects.filter(user=user).exists()
        mock_refresh.assert_called_once()
    
    def test_dashboard_success(self, authenticated_client, user_summary, platform_summary):
        """测试获取仪表板数据成功"""
        url = reverse('user-summary-dashboard')
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert 'user_stats' in data
        assert 'platform_stats' in data
        assert 'growth_stats' in data
        
        assert data['user_stats']['total_namespaces'] == user_summary.total_namespaces
        assert data['platform_stats']['total_users'] == platform_summary.total_users
    
    def test_dashboard_auto_create_platform_stats(self, authenticated_client, user_summary):
        """测试仪表板自动创建平台统计"""
        url = reverse('user-summary-dashboard')
        
        # 确保没有平台统计数据
        PlatformSummary.objects.all().delete()
        
        with patch.object(PlatformSummary, 'generate_daily_summary') as mock_generate:
            mock_generate.return_value = MagicMock()
            response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        mock_generate.assert_called_once()
    
    @patch('summary.views.summary.summaryAPI')
    def test_refresh_user_stats_success(self, mock_api, authenticated_client, user_summary):
        """测试刷新用户统计数据成功"""
        url = reverse('user-summary-refresh')
        
        with patch.object(user_summary, 'refresh_statistics') as mock_refresh:
            mock_refresh.return_value = user_summary
            response = authenticated_client.post(url)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data['message'] == '统计数据已刷新'
        assert 'updated_at' in data
        assert 'user_stats' in data
        mock_refresh.assert_called_once()
    
    def test_unauthorized_access(self):
        """测试未认证访问"""
        client = APIClient()
        url = reverse('user-summary-list')
        response = client.get(url)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestPlatformSummaryViewSet:
    """平台统计视图集测试"""
    
    def test_list_platform_summary(self, authenticated_client, platform_summary):
        """测试获取平台统计列表"""
        url = reverse('platform-summary-list')
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert 'results' in data
        assert len(data['results']) >= 1
        assert data['results'][0]['total_users'] == platform_summary.total_users
    
    def test_latest_platform_summary(self, authenticated_client, platform_summary):
        """测试获取最新平台统计"""
        url = reverse('platform-summary-latest')
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data['total_users'] == platform_summary.total_users
        assert data['total_namespaces'] == platform_summary.total_namespaces
    
    def test_latest_auto_generate(self, authenticated_client):
        """测试自动生成最新统计"""
        url = reverse('platform-summary-latest')
        
        # 确保没有统计数据
        PlatformSummary.objects.all().delete()
        
        with patch.object(PlatformSummary, 'generate_daily_summary') as mock_generate:
            mock_summary = MagicMock()
            mock_generate.return_value = mock_summary
            response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        mock_generate.assert_called_once()
    
    def test_generate_today_summary(self, authenticated_client):
        """测试生成今日统计"""
        url = reverse('platform-summary-generate-today')
        
        with patch.object(PlatformSummary, 'generate_daily_summary') as mock_generate:
            mock_summary = MagicMock()
            mock_generate.return_value = mock_summary
            response = authenticated_client.post(url)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data['message'] == '今日平台统计已生成'
        assert 'data' in data
        mock_generate.assert_called_once()


@pytest.mark.django_db
class TestSummaryIntegration:
    """统计功能集成测试"""
    
    def test_complete_dashboard_workflow(self, authenticated_client, user):
        """测试完整的仪表板工作流程"""
        # 1. 获取仪表板数据（应该自动创建统计记录）
        dashboard_url = reverse('user-summary-dashboard')
        
        with patch.object(UserSummary, 'refresh_statistics'), \
             patch.object(PlatformSummary, 'generate_daily_summary') as mock_generate:
            
            mock_generate.return_value = MagicMock(
                total_users=100,
                active_users=80,
                date=timezone.now().date()
            )
            
            response = authenticated_client.get(dashboard_url)
        
        assert response.status_code == status.HTTP_200_OK
        
        # 验证用户统计记录已创建
        assert UserSummary.objects.filter(user=user).exists()
        
        # 2. 刷新统计数据
        refresh_url = reverse('user-summary-refresh')
        
        with patch.object(UserSummary.objects.get(user=user), 'refresh_statistics'):
            response = authenticated_client.post(refresh_url)
        
        assert response.status_code == status.HTTP_200_OK
        
        # 3. 再次获取仪表板数据
        response = authenticated_client.get(dashboard_url)
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert all(key in data for key in ['user_stats', 'platform_stats', 'growth_stats'])
    
    def test_error_handling(self, authenticated_client, user):
        """测试错误处理"""
        url = reverse('user-summary-dashboard')
        
        # 模拟数据库错误
        with patch('summary.models.summary.UserSummary.objects.get_or_create') as mock_get:
            mock_get.side_effect = Exception("Database error")
            response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        data = response.json()
        assert 'error' in data
        assert data['error'] == '获取仪表板数据失败'
