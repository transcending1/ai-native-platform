import json
import os
import django
import pytest
from django.core.cache import cache
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

# 设置Django环境
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "llm_api.settings.dev_settings")
django.setup()

from user.models.user import CustomUser


class GlobalConfigCacheViewSetTest(TestCase):
    """
    全局配置缓存视图集测试
    """
    
    def setUp(self):
        """测试前准备"""
        self.client = APIClient()
        
        # 创建管理员用户
        self.admin_user = CustomUser.objects.create_user(
            username='admin',
            password='admin123',
            email='admin@test.com',
            is_staff=True,
            is_superuser=True,
            role='admin'  # 设置为管理员角色
        )
        
        # 清除缓存
        cache.clear()
    
    def test_get_configs_empty(self):
        """测试获取空配置"""
        self.client.force_authenticate(user=self.admin_user)
        
        response = self.client.get('/provider/global-config-cache/get_configs/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['code'], 200)
        self.assertEqual(response.data['data']['llm_config'], {})
        self.assertEqual(response.data['data']['embedding_config'], {})
    
    def test_update_llm_config(self):
        """测试更新LLM配置"""
        self.client.force_authenticate(user=self.admin_user)
        
        llm_config = {
            'model': 'gpt-3.5-turbo',
            'model_provider': 'openai',
            'base_url': 'https://api.openai.com/v1',
            'api_key': 'test-api-key',
            'temperature': 0.7,
            'max_tokens': 2048
        }
        
        response = self.client.post('/provider/global-config-cache/update_llm_config/', llm_config)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['code'], 200)
        
        # 验证缓存中的数据
        cached_config = cache.get('global_model')
        self.assertIsNotNone(cached_config)
        
        config_data = json.loads(cached_config)
        self.assertEqual(config_data['global_model'], 'gpt-3.5-turbo')
        self.assertEqual(config_data['global_model_provider'], 'openai')
        self.assertEqual(float(config_data['global_temperature']), 0.7)
        self.assertEqual(int(config_data['global_max_tokens']), 2048)
    
    def test_update_embedding_config(self):
        """测试更新Embedding配置"""
        self.client.force_authenticate(user=self.admin_user)
        
        embedding_config = {
            'model': 'text-embedding-ada-002',
            'model_provider': 'openai',
            'base_url': 'https://api.openai.com/v1',
            'token': 'test-token'
        }
        
        response = self.client.post('/provider/global-config-cache/update_embedding_config/', embedding_config)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['code'], 200)
        
        # 验证缓存中的数据
        cached_config = cache.get('global_embedding')
        self.assertIsNotNone(cached_config)
        
        config_data = json.loads(cached_config)
        self.assertEqual(config_data['global_embedding_model'], 'text-embedding-ada-002')
        self.assertEqual(config_data['global_embedding_model_provider'], 'openai')
    
    def test_get_configs_with_data(self):
        """测试获取有数据的配置"""
        self.client.force_authenticate(user=self.admin_user)
        
        # 先设置一些配置
        llm_config = {
            'global_model': 'gpt-3.5-turbo',
            'global_model_provider': 'openai',
            'global_temperature': 0.7,
            'global_max_tokens': 2048,
            'global_base_url': 'https://api.openai.com/v1',
            'global_api_key': 'test-api-key'
        }
        
        embedding_config = {
            'global_embedding_model': 'text-embedding-ada-002',
            'global_embedding_model_provider': 'openai',
            'global_embedding_base_url': 'https://api.openai.com/v1',
            'global_embedding_token': 'test-token'
        }
        
        cache.set('global_model', json.dumps(llm_config), timeout=None)
        cache.set('global_embedding', json.dumps(embedding_config), timeout=None)
        
        response = self.client.get('/provider/global-config-cache/get_configs/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['code'], 200)
        
        data = response.data['data']
        self.assertEqual(data['llm_config']['global_model'], 'gpt-3.5-turbo')
        self.assertEqual(data['embedding_config']['global_embedding_model'], 'text-embedding-ada-002')
    
    def test_update_llm_config_missing_required_fields(self):
        """测试更新LLM配置缺少必需字段"""
        self.client.force_authenticate(user=self.admin_user)
        
        llm_config = {
            'base_url': 'https://api.openai.com/v1',
            'api_key': 'test-api-key'
        }
        
        response = self.client.post('/provider/global-config-cache/update_llm_config/', llm_config)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['code'], 400)
    
    def test_update_embedding_config_missing_required_fields(self):
        """测试更新Embedding配置缺少必需字段"""
        self.client.force_authenticate(user=self.admin_user)
        
        embedding_config = {
            'base_url': 'https://api.openai.com/v1',
            'token': 'test-token'
        }
        
        response = self.client.post('/provider/global-config-cache/update_embedding_config/', embedding_config)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['code'], 400)
    
    def test_unauthorized_access(self):
        """测试未授权访问"""
        # 不进行身份验证
        response = self.client.get('/provider/global-config-cache/get_configs/')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_non_admin_access(self):
        """测试非管理员访问"""
        # 创建普通用户
        normal_user = CustomUser.objects.create_user(
            username='normal',
            password='normal123',
            email='normal@test.com'
        )
        
        self.client.force_authenticate(user=normal_user)
        
        response = self.client.get('/provider/global-config-cache/get_configs/')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def tearDown(self):
        """测试后清理"""
        cache.clear()
        CustomUser.objects.all().delete() 