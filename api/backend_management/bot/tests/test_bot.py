import pytest
import allure
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch, MagicMock

from bot.models.bot import Bot, BotCollaborator
from core.extensions.ext_langgraph import GRAPH_ID

User = get_user_model()


class BotModelTest(TestCase):
    """Bot模型测试"""

    def setUp(self):
        self.user1 = User.objects.create_user(
            username='testuser1',
            email='test1@example.com',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password='testpass123'
        )

    @allure.step("测试Bot模型创建和基本属性")
    def test_bot_creation(self):
        """测试Bot创建和基本属性"""
        bot = Bot.objects.create(
            name="测试Bot",
            description="这是一个测试Bot",
            creator=self.user1,
            access_type='collaborators'
        )
        
        self.assertEqual(bot.name, "测试Bot")
        self.assertEqual(bot.description, "这是一个测试Bot")
        self.assertEqual(bot.creator, self.user1)
        self.assertEqual(bot.access_type, 'collaborators')
        self.assertIsNotNone(bot.slug)
        self.assertTrue(bot.is_active)
        self.assertFalse(bot.is_public)

    @allure.step("测试Bot权限检查")
    def test_bot_permissions(self):
        """测试Bot权限检查方法"""
        bot = Bot.objects.create(
            name="测试Bot",
            creator=self.user1,
            access_type='collaborators'
        )
        
        # 创建者应该可以访问和编辑
        self.assertTrue(bot.can_access(self.user1))
        self.assertTrue(bot.can_edit(self.user1))
        
        # 其他用户不能访问非公开Bot
        self.assertFalse(bot.can_access(self.user2))
        self.assertFalse(bot.can_edit(self.user2))
        
        # 公开Bot所有用户都可以访问
        bot.access_type = 'public'
        bot.save()
        self.assertTrue(bot.can_access(self.user2))
        self.assertFalse(bot.can_edit(self.user2))

    @allure.step("测试Bot协作者")
    def test_bot_collaborator(self):
        """测试Bot协作者功能"""
        bot = Bot.objects.create(
            name="测试Bot",
            creator=self.user1
        )
        
        # 添加协作者
        collaborator = BotCollaborator.objects.create(
            bot=bot,
            user=self.user2,
            role='admin',
            added_by=self.user1
        )
        
        # 检查协作者权限
        self.assertTrue(bot.can_access(self.user2))
        self.assertTrue(bot.can_edit(self.user2))
        self.assertTrue(collaborator.can_edit)
        self.assertTrue(collaborator.can_read)
        
        # 修改为只读权限
        collaborator.role = 'readonly'
        collaborator.save()
        
        self.assertTrue(bot.can_access(self.user2))
        self.assertFalse(bot.can_edit(self.user2))
        self.assertFalse(collaborator.can_edit)
        self.assertTrue(collaborator.can_read)


class BotAPITest(TestCase):
    """Bot API测试"""

    def setUp(self):
        self.client = APIClient()
        self.user1 = User.objects.create_user(
            username='testuser1',
            email='test1@example.com',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password='testpass123'
        )

    @allure.step("用户登录获取认证")
    def authenticate_user(self, user):
        """用户认证辅助方法"""
        self.client.force_authenticate(user=user)

    @allure.step("测试获取Bot列表")
    def test_get_bot_list(self):
        """测试获取Bot列表"""
        self.authenticate_user(self.user1)
        
        # 创建测试Bot
        Bot.objects.create(
            name="用户1的Bot",
            creator=self.user1
        )
        Bot.objects.create(
            name="公开Bot",
            creator=self.user2,
            access_type='public'
        )
        
        url = reverse('bot:bot-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)

    @allure.step("测试基本list功能")
    def test_basic_list(self):
        """测试基本的Bot列表功能"""
        self.authenticate_user(self.user1)
        
        # 清理可能存在的测试数据
        Bot.objects.filter(name__in=["基本测试Bot"]).delete()
        
        # 创建测试数据
        bot = Bot.objects.create(
            name="基本测试Bot",
            creator=self.user1
        )
        
        # 验证数据创建
        self.assertEqual(Bot.objects.filter(name="基本测试Bot").count(), 1)
        
        # 测试获取Bot列表
        url = reverse('bot:bot-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        print(f"API返回的Bot数量: {len(response.data['results'])}")
        print(f"API返回的Bot名称: {[bot['name'] for bot in response.data['results']]}")
        
        # 检查是否包含我们的测试Bot
        test_bot_names = [bot['name'] for bot in response.data['results'] if bot['name'] == "基本测试Bot"]
        self.assertEqual(len(test_bot_names), 1)
        self.assertEqual(test_bot_names[0], "基本测试Bot")

    @allure.step("测试分页功能")
    def test_pagination(self):
        """测试Bot分页功能"""
        self.authenticate_user(self.user1)
        
        # 创建多个Bot
        for i in range(15):
            Bot.objects.create(
                name=f"Bot {i}",
                creator=self.user1
            )
        
        url = reverse('bot:bot-list')
        response = self.client.get(url, {'page': 1, 'page_size': 10})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 10)
        self.assertEqual(response.data['count'], 15)
        self.assertIsNotNone(response.data['next'])
        self.assertIsNone(response.data['previous'])

    @allure.step("测试元数据过滤")
    def test_metadata_filtering(self):
        """测试通过元数据过滤Bot"""
        self.authenticate_user(self.user1)
        
        Bot.objects.create(
            name="公开Bot",
            creator=self.user1,
            access_type='public'
        )
        Bot.objects.create(
            name="私有Bot",
            creator=self.user1,
            access_type='collaborators'
        )
        
        url = reverse('bot:bot-list')
        response = self.client.get(url, {'access_type': 'public'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # 应该只返回公开的Bot
        for bot in response.data['results']:
            self.assertEqual(bot['access_type'], 'public')

    @patch('bot.views.bot.langgraph_client')
    @allure.step("测试创建Bot")
    def test_create_bot(self, mock_langgraph_client):
        """测试创建Bot（模拟LangGraph API）"""
        self.authenticate_user(self.user1)
        
        # 模拟LangGraph API响应
        mock_assistant = {
            'assistant_id': 'test_assistant_123',
            'name': '新Bot',
            'description': '测试描述'
        }
        mock_langgraph_client.assistants.create.return_value = mock_assistant
        
        url = reverse('bot:bot-list')
        data = {
            'name': '新Bot',
            'description': '测试描述',
            'access_type': 'collaborators'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], '新Bot')
        self.assertEqual(response.data['creator']['id'], self.user1.id)
        
        # 验证LangGraph API被调用
        mock_langgraph_client.assistants.create.assert_called_once()
        
        # 验证数据库中创建了Bot
        bot = Bot.objects.get(name='新Bot')
        self.assertEqual(bot.assistant_id, 'test_assistant_123')

    @patch('bot.views.bot.langgraph_client')
    @allure.step("测试更新Bot")
    def test_update_bot(self, mock_langgraph_client):
        """测试更新Bot"""
        self.authenticate_user(self.user1)
        
        bot = Bot.objects.create(
            name="原始Bot",
            creator=self.user1,
            assistant_id="test_assistant_123"
        )
        
        # 模拟LangGraph API响应
        mock_langgraph_client.assistants.update.return_value = {}
        
        url = reverse('bot:bot-detail', kwargs={'pk': bot.id})
        data = {
            'name': '更新后的Bot',
            'description': '更新后的描述'
        }
        
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], '更新后的Bot')
        
        # 验证LangGraph API被调用
        mock_langgraph_client.assistants.update.assert_called_once()

    @patch('bot.views.bot.langgraph_client')
    @allure.step("测试删除Bot")
    def test_delete_bot(self, mock_langgraph_client):
        """测试删除Bot"""
        self.authenticate_user(self.user1)
        
        bot = Bot.objects.create(
            name="待删除Bot",
            creator=self.user1,
            assistant_id="test_assistant_123"
        )
        
        # 模拟LangGraph API响应
        mock_langgraph_client.assistants.delete.return_value = {}
        
        url = reverse('bot:bot-detail', kwargs={'pk': bot.id})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # 验证LangGraph API被调用
        mock_langgraph_client.assistants.delete.assert_called_once_with(
            assistant_id="test_assistant_123"
        )
        
        # 验证Bot被删除
        self.assertFalse(Bot.objects.filter(id=bot.id).exists())

    @allure.step("测试非创建者删除Bot权限")
    def test_delete_bot_permission_denied(self):
        """测试非创建者不能删除Bot"""
        self.authenticate_user(self.user2)
        
        bot = Bot.objects.create(
            name="他人Bot",
            creator=self.user1
        )
        
        url = reverse('bot:bot-detail', kwargs={'pk': bot.id})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Bot.objects.filter(id=bot.id).exists())

    @allure.step("测试添加协作者")
    def test_add_collaborator(self):
        """测试添加协作者"""
        self.authenticate_user(self.user1)
        
        bot = Bot.objects.create(
            name="测试Bot",
            creator=self.user1
        )
        
        url = reverse('bot:bot-add-collaborator', kwargs={'pk': bot.id})
        data = {
            'username': self.user2.username,
            'role': 'admin'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['user']['username'], self.user2.username)
        self.assertEqual(response.data['role'], 'admin')
        
        # 验证协作者被添加
        self.assertTrue(
            BotCollaborator.objects.filter(
                bot=bot, 
                user=self.user2, 
                role='admin'
            ).exists()
        )

    @allure.step("测试管理协作者权限")
    def test_manage_collaborator(self):
        """测试管理协作者权限"""
        self.authenticate_user(self.user1)
        
        bot = Bot.objects.create(
            name="测试Bot",
            creator=self.user1
        )
        
        collaborator = BotCollaborator.objects.create(
            bot=bot,
            user=self.user2,
            role='readonly',
            added_by=self.user1
        )
        
        # 更新协作者权限
        url = reverse('bot:bot-manage-collaborator', kwargs={'pk': bot.id, 'user_id': self.user2.id})
        data = {'role': 'admin'}
        
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['role'], 'admin')
        
        # 验证权限被更新
        collaborator.refresh_from_db()
        self.assertEqual(collaborator.role, 'admin')

    @allure.step("测试移除协作者")
    def test_remove_collaborator(self):
        """测试移除协作者"""
        self.authenticate_user(self.user1)
        
        bot = Bot.objects.create(
            name="测试Bot",
            creator=self.user1
        )
        
        BotCollaborator.objects.create(
            bot=bot,
            user=self.user2,
            role='readonly',
            added_by=self.user1
        )
        
        url = reverse('bot:bot-manage-collaborator', kwargs={'pk': bot.id, 'user_id': self.user2.id})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # 验证协作者被移除
        self.assertFalse(
            BotCollaborator.objects.filter(
                bot=bot, 
                user=self.user2
            ).exists()
        )

    @allure.step("测试获取协作者列表")
    def test_get_collaborators(self):
        """测试获取协作者列表"""
        self.authenticate_user(self.user1)
        
        bot = Bot.objects.create(
            name="测试Bot",
            creator=self.user1
        )
        
        BotCollaborator.objects.create(
            bot=bot,
            user=self.user2,
            role='admin',
            added_by=self.user1
        )
        
        url = reverse('bot:bot-collaborators', kwargs={'pk': bot.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['user']['username'], self.user2.username)

    @allure.step("测试更新基本信息")
    def test_update_basic_info(self):
        """测试更新Bot基本信息"""
        self.authenticate_user(self.user1)
        
        bot = Bot.objects.create(
            name="原始Bot",
            creator=self.user1,
            assistant_id="test_assistant_123"
        )
        
        with patch('bot.views.bot.langgraph_client') as mock_client:
            mock_client.assistants.update.return_value = {}
            
            url = reverse('bot:bot-update-basic', kwargs={'pk': bot.id})
            data = {
                'name': '新名称',
                'description': '新描述',
                'access_type': 'public'
            }
            
            response = self.client.patch(url, data, format='json')
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data['name'], '新名称')
            self.assertEqual(response.data['access_type'], 'public')

    @patch('bot.views.bot.langgraph_client')
    @allure.step("测试从LangGraph同步")
    def test_sync_from_langgraph(self, mock_langgraph_client):
        """测试从LangGraph同步Assistants"""
        self.authenticate_user(self.user1)
        
        # 模拟LangGraph API响应
        mock_assistants = [
            {
                'assistant_id': 'assistant_1',
                'name': 'Assistant 1',
                'description': 'Description 1',
                'graph_id': GRAPH_ID
            },
            {
                'assistant_id': 'assistant_2',
                'name': 'Assistant 2',
                'description': 'Description 2',
                'graph_id': GRAPH_ID
            }
        ]
        mock_langgraph_client.assistants.search.return_value = mock_assistants
        
        url = reverse('bot:bot-sync-from-langgraph')
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['synced_count'], 2)
        
        # 验证Bot被创建
        self.assertEqual(Bot.objects.filter(creator=self.user1).count(), 2)
        self.assertTrue(Bot.objects.filter(assistant_id='assistant_1').exists())
        self.assertTrue(Bot.objects.filter(assistant_id='assistant_2').exists())

    @patch('bot.views.bot.langgraph_client')
    @allure.step("测试创建聊天线程")
    def test_create_thread(self, mock_langgraph_client):
        """测试创建聊天线程"""
        self.authenticate_user(self.user1)
        
        bot = Bot.objects.create(
            name="测试Bot",
            creator=self.user1,
            assistant_id="test_assistant_123"
        )
        
        # 模拟LangGraph API响应
        mock_thread = {'thread_id': 'thread_123'}
        mock_langgraph_client.threads.create.return_value = mock_thread
        
        url = reverse('bot:bot-create-thread', kwargs={'pk': bot.id})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['thread_id'], 'thread_123')
        self.assertEqual(response.data['message'], '聊天线程创建成功')
        
        # 验证调用参数
        mock_langgraph_client.threads.create.assert_called_once_with(
            metadata={
                "assistant_id": "test_assistant_123",
                "user_id": str(self.user1.id),
                "bot_id": str(bot.id)
            },
            graph_id=GRAPH_ID
        )

    @allure.step("测试创建聊天线程 - Bot不存在")
    def test_create_thread_permission_denied(self):
        """测试创建聊天线程 - Bot不存在或无权限访问"""
        self.authenticate_user(self.user2)
        
        bot = Bot.objects.create(
            name="私有Bot",
            creator=self.user1,
            assistant_id="test_assistant_123",
            access_type='collaborators'
        )
        
        url = reverse('bot:bot-create-thread', kwargs={'pk': bot.id})
        response = self.client.post(url)
        
        # 由于get_queryset过滤，用户2无法看到user1的私有Bot，所以会返回404
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @allure.step("测试创建聊天线程 - Bot未关联Assistant")
    def test_create_thread_no_assistant(self):
        """测试创建聊天线程 - Bot未关联Assistant"""
        self.authenticate_user(self.user1)
        
        bot = Bot.objects.create(
            name="测试Bot",
            creator=self.user1
        )
        
        url = reverse('bot:bot-create-thread', kwargs={'pk': bot.id})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'Bot未关联LangGraph Assistant')

    @patch('bot.views.bot.langgraph_client')
    @allure.step("测试聊天对话API")
    def test_chat_api(self, mock_langgraph_client):
        """测试聊天对话API"""
        self.authenticate_user(self.user1)
        
        bot = Bot.objects.create(
            name="测试Bot",
            creator=self.user1,
            assistant_id="test_assistant_123"
        )
        
        # 模拟流式响应
        def mock_stream():
            yield ("messages/partial", [{'content': '你好'}])
            yield ("messages/partial", [{'content': '你好，'}])
            yield ("messages/partial", [{'content': '你好，我是'}])
            yield ("messages/partial", [{'content': '你好，我是AI助手'}])
        
        mock_langgraph_client.runs.stream.return_value = mock_stream()
        mock_langgraph_client.threads.create.return_value = {'thread_id': 'thread_123'}
        
        url = reverse('bot:bot-chat', kwargs={'pk': bot.id})
        data = {'message': '你好'}
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'text/event-stream')
        
        # 验证调用参数
        mock_langgraph_client.threads.create.assert_called_once()
        
        # 读取流式响应内容来触发生成器的执行
        content = b''
        for chunk in response.streaming_content:
            content += chunk
        
        # 验证流式调用被触发
        mock_langgraph_client.runs.stream.assert_called_once()

    @allure.step("测试聊天对话API - 使用现有线程")
    def test_chat_with_existing_thread(self):
        """测试聊天对话API - 使用现有线程"""
        self.authenticate_user(self.user1)
        
        bot = Bot.objects.create(
            name="测试Bot",
            creator=self.user1,
            assistant_id="test_assistant_123"
        )
        
        with patch('bot.views.bot.langgraph_client') as mock_client:
            # 模拟流式响应
            def mock_stream():
                yield ("messages/partial", [{'content': '这是回复'}])
            
            mock_client.runs.stream.return_value = mock_stream()
            
            url = reverse('bot:bot-chat', kwargs={'pk': bot.id})
            data = {
                'message': '继续对话',
                'thread_id': 'existing_thread_123'
            }
            
            response = self.client.post(url, data, format='json')
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            
            # 读取流式响应内容来触发生成器的执行
            content = b''
            for chunk in response.streaming_content:
                content += chunk
            
            # 验证没有创建新线程
            mock_client.threads.create.assert_not_called()
            
            # 验证使用了现有线程ID
            mock_client.runs.stream.assert_called_once()
            call_args = mock_client.runs.stream.call_args
            self.assertEqual(call_args[1]['thread_id'], 'existing_thread_123')

    @allure.step("测试聊天对话API - 消息验证")
    def test_chat_message_validation(self):
        """测试聊天对话API - 消息验证"""
        self.authenticate_user(self.user1)
        
        bot = Bot.objects.create(
            name="测试Bot",
            creator=self.user1,
            assistant_id="test_assistant_123"
        )
        
        url = reverse('bot:bot-chat', kwargs={'pk': bot.id})
        
        # 测试空消息
        data = {'message': ''}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # 测试只有空白字符的消息
        data = {'message': '   '}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # 测试缺少message字段
        data = {}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
