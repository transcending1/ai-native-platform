import pytest
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from datetime import date

User = get_user_model()


@pytest.mark.django_db
class TestUserAuthentication(TestCase):
    """
    用户认证相关测试
    """

    def setUp(self):
        """
        测试前的准备工作
        """
        self.client = APIClient()
        self.test_username = 'testuser'
        self.test_password = 'testpass123'
        self.test_email = 'test@example.com'

        # 创建测试用户
        self.user = User.objects.create_user(
            username=self.test_username,
            password=self.test_password,
            email=self.test_email
        )

    def test_user_login_success(self):
        """
        测试用户登录成功
        """
        url = '/user/login/'
        data = {
            'username': self.test_username,
            'password': self.test_password,
            'remember_me': False
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()

        self.assertEqual(response_data['code'], 200)
        self.assertEqual(response_data['message'], '登录成功')
        self.assertIn('data', response_data)
        self.assertIn('access', response_data['data'])
        self.assertIn('refresh', response_data['data'])
        self.assertIn('user', response_data['data'])

    def test_user_login_with_remember_me(self):
        """
        测试用户登录带15天免登录选项
        """
        url = '/user/login/'
        data = {
            'username': self.test_username,
            'password': self.test_password,
            'remember_me': True
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()

        self.assertEqual(response_data['code'], 200)
        self.assertIn('access', response_data['data'])
        self.assertIn('refresh', response_data['data'])

    def test_user_login_wrong_password(self):
        """
        测试用户登录密码错误
        """
        url = '/user/login/'
        data = {
            'username': self.test_username,
            'password': 'wrongpassword',
            'remember_me': False
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response_data = response.json()

        self.assertEqual(response_data['code'], 400)
        self.assertEqual(response_data['message'], '登录失败')

    def test_user_login_nonexistent_user(self):
        """
        测试不存在的用户登录
        """
        url = '/user/login/'
        data = {
            'username': 'nonexistent',
            'password': 'password123',
            'remember_me': False
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response_data = response.json()

        self.assertEqual(response_data['code'], 400)
        self.assertEqual(response_data['message'], '登录失败')

    def test_user_login_missing_fields(self):
        """
        测试登录缺少必要字段
        """
        url = '/user/login/'
        data = {
            'username': self.test_username,
            # 缺少密码字段
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response_data = response.json()

        self.assertEqual(response_data['code'], 400)
        self.assertEqual(response_data['message'], '登录失败')

    def test_get_user_profile(self):
        """
        测试获取用户信息
        """
        # 先登录获取token
        login_url = '/user/login/'
        login_data = {
            'username': self.test_username,
            'password': self.test_password
        }

        login_response = self.client.post(login_url, login_data, format='json')
        access_token = login_response.json()['data']['access']

        # 使用token获取用户信息
        url = '/user/profile/'
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()

        self.assertEqual(response_data['code'], 200)
        self.assertEqual(response_data['message'], '获取用户信息成功')
        self.assertIn('data', response_data)
        self.assertEqual(response_data['data']['username'], self.test_username)
        self.assertEqual(response_data['data']['email'], self.test_email)

        # 验证返回的字段不包含 first_name 和 last_name
        self.assertNotIn('first_name', response_data['data'])
        self.assertNotIn('last_name', response_data['data'])

    def test_get_user_profile_without_auth(self):
        """
        测试未认证获取用户信息
        """
        url = '/user/profile/'

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_user_profile(self):
        """
        测试更新用户信息
        """
        # 先登录获取token
        login_url = '/user/login/'
        login_data = {
            'username': self.test_username,
            'password': self.test_password
        }

        login_response = self.client.post(login_url, login_data, format='json')
        access_token = login_response.json()['data']['access']

        # 使用token更新用户信息
        url = '/user/update_profile/'
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

        update_data = {
            'username': 'updateduser',
            'phone': '13800138000',
            'email': 'updated@example.com'
        }

        response = self.client.put(url, update_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()

        self.assertEqual(response_data['code'], 200)
        self.assertEqual(response_data['message'], '更新用户信息成功')
        self.assertEqual(response_data['data']['username'], 'updateduser')
        self.assertEqual(response_data['data']['phone'], '13800138000')
        self.assertEqual(response_data['data']['email'], 'updated@example.com')

        # 验证返回的字段不包含 first_name 和 last_name
        self.assertNotIn('first_name', response_data['data'])
        self.assertNotIn('last_name', response_data['data'])

    def test_update_user_profile_duplicate_username(self):
        """
        测试更新用户信息时用户名重复
        """
        # 创建另一个用户
        other_user = User.objects.create_user(
            username='otheruser',
            password='otherpass123',
            email='other@example.com'
        )

        # 先登录获取token
        login_url = '/user/login/'
        login_data = {
            'username': self.test_username,
            'password': self.test_password
        }

        login_response = self.client.post(login_url, login_data, format='json')
        access_token = login_response.json()['data']['access']

        # 尝试将用户名更新为已存在的用户名
        url = '/user/update_profile/'
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

        update_data = {
            'username': 'otheruser',  # 使用已存在的用户名
            'phone': '13800138000'
        }

        response = self.client.put(url, update_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response_data = response.json()

        self.assertEqual(response_data['code'], 400)
        self.assertEqual(response_data['message'], '更新失败')
        self.assertIn('username', response_data['errors'])

    def test_update_user_profile_same_username(self):
        """
        测试更新用户信息时使用相同用户名（应该成功）
        """
        # 先登录获取token
        login_url = '/user/login/'
        login_data = {
            'username': self.test_username,
            'password': self.test_password
        }

        login_response = self.client.post(login_url, login_data, format='json')
        access_token = login_response.json()['data']['access']

        # 使用相同的用户名更新其他信息
        url = '/user/update_profile/'
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

        update_data = {
            'username': self.test_username,  # 使用相同的用户名
            'phone': '13800138000'
        }

        response = self.client.put(url, update_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()

        self.assertEqual(response_data['code'], 200)
        self.assertEqual(response_data['message'], '更新用户信息成功')
        self.assertEqual(response_data['data']['username'], self.test_username)
        self.assertEqual(response_data['data']['phone'], '13800138000')

    def test_user_logout(self):
        """
        测试用户登出
        """
        # 先登录获取token
        login_url = '/user/login/'
        login_data = {
            'username': self.test_username,
            'password': self.test_password
        }

        login_response = self.client.post(login_url, login_data, format='json')
        tokens = login_response.json()['data']
        access_token = tokens['access']
        refresh_token = tokens['refresh']

        # 登出
        url = '/user/logout/'
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

        logout_data = {
            'refresh': refresh_token
        }

        response = self.client.post(url, logout_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()

        self.assertEqual(response_data['code'], 200)
        self.assertEqual(response_data['message'], '登出成功')

    def test_user_register(self):
        """
        测试用户注册
        """
        url = '/user/register/'
        data = {
            'username': 'newuser',
            'password': 'newpass123',
            'password_confirm': 'newpass123',
            'email': 'newuser@example.com',
            'phone': '13800138000'
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response_data = response.json()

        self.assertEqual(response_data['code'], 201)
        self.assertEqual(response_data['message'], '注册成功')
        self.assertIn('data', response_data)
        self.assertEqual(response_data['data']['username'], 'newuser')

        # 验证返回的字段不包含 first_name 和 last_name
        self.assertNotIn('first_name', response_data['data'])
        self.assertNotIn('last_name', response_data['data'])

        # 验证用户确实被创建
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_user_register_password_mismatch(self):
        """
        测试用户注册密码不匹配
        """
        url = '/user/register/'
        data = {
            'username': 'newuser',
            'password': 'newpass123',
            'password_confirm': 'differentpass',
            'email': 'newuser@example.com',
            'phone': '13800138000'
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response_data = response.json()

        self.assertEqual(response_data['code'], 400)
        self.assertEqual(response_data['message'], '注册失败')

    def test_token_refresh(self):
        """
        测试token刷新功能
        """
        # 首先登录获取token
        login_url = '/user/login/'
        login_data = {
            'username': self.test_username,
            'password': self.test_password,
            'remember_me': True
        }

        login_response = self.client.post(login_url, login_data, format='json')
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        
        login_data = login_response.json()
        refresh_token = login_data['data']['refresh']
        
        # 测试刷新token
        refresh_url = '/user/refresh/'
        refresh_data = {
            'refresh': refresh_token
        }

        refresh_response = self.client.post(refresh_url, refresh_data, format='json')
        self.assertEqual(refresh_response.status_code, status.HTTP_200_OK)
        
        refresh_response_data = refresh_response.json()
        self.assertIn('access', refresh_response_data)
        self.assertIn('refresh', refresh_response_data)
        
        # 验证新的access token可以正常使用
        new_access_token = refresh_response_data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {new_access_token}')
        
        profile_url = '/user/profile/'
        profile_response = self.client.get(profile_url)
        self.assertEqual(profile_response.status_code, status.HTTP_200_OK)

    def test_user_register_duplicate_username(self):
        """
        测试用户注册重复用户名
        """
        url = '/user/register/'
        data = {
            'username': self.test_username,  # 使用已存在的用户名
            'password': 'newpass123',
            'password_confirm': 'newpass123',
            'email': 'newuser@example.com'
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response_data = response.json()

        self.assertEqual(response_data['code'], 400)
        self.assertEqual(response_data['message'], '注册失败')


@pytest.mark.django_db
class TestUserManagement(TestCase):
    """
    用户管理功能测试（管理员专用）
    """

    def setUp(self):
        """
        测试前的准备工作
        """
        self.client = APIClient()
        
        # 创建管理员用户
        self.admin_user = User.objects.create_user(
            username='admin',
            password='adminpass123',
            email='admin@example.com',
            role='admin'
        )
        
        # 创建普通用户
        self.normal_user = User.objects.create_user(
            username='normaluser',
            password='normalpass123',
            email='normal@example.com',
            role='user',
            phone='13800138000',
            gender='male',
            birthday=date(1990, 1, 1),
            is_active=True
        )
        
        # 获取管理员token
        login_url = '/user/login/'
        login_data = {
            'username': 'admin',
            'password': 'adminpass123'
        }
        
        login_response = self.client.post(login_url, login_data, format='json')
        self.admin_token = login_response.json()['data']['access']
        
        # 获取普通用户token
        login_data = {
            'username': 'normaluser',
            'password': 'normalpass123'
        }
        
        login_response = self.client.post(login_url, login_data, format='json')
        self.normal_token = login_response.json()['data']['access']

    def test_admin_list_users(self):
        """
        测试管理员获取用户列表
        """
        url = '/user/admin/management/'
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.admin_token}')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        
        self.assertEqual(response_data['code'], 200)
        self.assertEqual(response_data['message'], '获取用户列表成功')
        self.assertIn('data', response_data)
        self.assertIn('results', response_data['data'])
        self.assertGreaterEqual(len(response_data['data']['results']), 2)

    def test_normal_user_cannot_access_user_management(self):
        """
        测试普通用户无法访问用户管理接口
        """
        url = '/user/admin/management/'
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.normal_token}')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_search_users_by_username(self):
        """
        测试管理员按用户名搜索用户
        """
        url = '/user/admin/management/?username=normal'
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.admin_token}')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        
        self.assertEqual(response_data['code'], 200)
        results = response_data['data']['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['username'], 'normaluser')

    def test_admin_search_users_by_email(self):
        """
        测试管理员按邮箱搜索用户
        """
        url = '/user/admin/management/?email=normal@example.com'
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.admin_token}')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        
        results = response_data['data']['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['email'], 'normal@example.com')

    def test_admin_search_users_by_role(self):
        """
        测试管理员按角色搜索用户
        """
        url = '/user/admin/management/?role=admin'
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.admin_token}')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        
        results = response_data['data']['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['role'], 'admin')

    def test_admin_search_users_by_gender(self):
        """
        测试管理员按性别搜索用户
        """
        url = '/user/admin/management/?gender=male'
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.admin_token}')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        
        results = response_data['data']['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['gender'], 'male')

    def test_admin_order_users_by_created_at(self):
        """
        测试管理员按创建时间排序用户
        """
        url = '/user/admin/management/?ordering=-created_at'
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.admin_token}')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        
        results = response_data['data']['results']
        self.assertGreaterEqual(len(results), 2)
        # 验证排序正确（最新创建的在前）
        self.assertGreaterEqual(results[0]['created_at'], results[1]['created_at'])

    def test_admin_get_user_detail(self):
        """
        测试管理员获取用户详情
        """
        url = f'/user/admin/management/{self.normal_user.id}/'
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.admin_token}')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        
        self.assertEqual(response_data['code'], 200)
        self.assertEqual(response_data['message'], '获取用户详情成功')
        user_data = response_data['data']
        self.assertEqual(user_data['username'], 'normaluser')
        self.assertEqual(user_data['email'], 'normal@example.com')
        self.assertEqual(user_data['role'], 'user')
        self.assertEqual(user_data['gender'], 'male')
        self.assertEqual(user_data['age'], 35)  # 根据1990年1月1日计算

    def test_admin_create_user(self):
        """
        测试管理员创建用户
        """
        url = '/user/admin/management/'
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.admin_token}')
        
        create_data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'newpass123',
            'phone': '13900139000',
            'role': 'user',
            'gender': 'female',
            'birthday': '1995-06-15',
            'is_active': True
        }
        
        response = self.client.post(url, create_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response_data = response.json()
        
        self.assertEqual(response_data['code'], 201)
        self.assertEqual(response_data['message'], '创建用户成功')
        user_data = response_data['data']
        self.assertEqual(user_data['username'], 'newuser')
        self.assertEqual(user_data['email'], 'newuser@example.com')
        self.assertEqual(user_data['role'], 'user')
        self.assertEqual(user_data['gender'], 'female')
        
        # 验证用户确实被创建
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_admin_update_user(self):
        """
        测试管理员更新用户信息
        """
        url = f'/user/admin/management/{self.normal_user.id}/'
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.admin_token}')
        
        update_data = {
            'username': 'updateduser',
            'email': 'updated@example.com',
            'phone': '13700137000',
            'role': 'admin',
            'gender': 'female',
            'birthday': '1992-12-25',
            'is_active': False
        }
        
        response = self.client.put(url, update_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        
        self.assertEqual(response_data['code'], 200)
        self.assertEqual(response_data['message'], '更新用户信息成功')
        user_data = response_data['data']
        self.assertEqual(user_data['username'], 'updateduser')
        self.assertEqual(user_data['email'], 'updated@example.com')
        self.assertEqual(user_data['role'], 'admin')
        self.assertEqual(user_data['gender'], 'female')
        self.assertEqual(user_data['is_active'], False)

    def test_admin_delete_user(self):
        """
        测试管理员删除用户
        """
        # 创建一个用于删除的用户
        delete_user = User.objects.create_user(
            username='deleteuser',
            password='deletepass123',
            email='delete@example.com'
        )
        
        url = f'/user/admin/management/{delete_user.id}/'
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.admin_token}')
        
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        
        self.assertEqual(response_data['code'], 200)
        self.assertEqual(response_data['message'], '删除用户成功')
        
        # 验证用户确实被删除
        self.assertFalse(User.objects.filter(id=delete_user.id).exists())

    def test_admin_toggle_user_status(self):
        """
        测试管理员切换用户有效状态
        """
        url = f'/user/admin/management/{self.normal_user.id}/toggle_status/'
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.admin_token}')
        
        # 检查初始状态
        self.assertTrue(self.normal_user.is_active)
        
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        
        self.assertEqual(response_data['code'], 200)
        self.assertIn('禁用', response_data['message'])
        self.assertEqual(response_data['data']['is_active'], False)
        
        # 再次切换
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        
        self.assertEqual(response_data['code'], 200)
        self.assertIn('启用', response_data['message'])
        self.assertEqual(response_data['data']['is_active'], True)

    def test_admin_reset_user_password(self):
        """
        测试管理员重置用户密码
        """
        url = f'/user/admin/management/{self.normal_user.id}/reset_password/'
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.admin_token}')
        
        reset_data = {
            'new_password': 'newpassword123'
        }
        
        response = self.client.post(url, reset_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        
        self.assertEqual(response_data['code'], 200)
        self.assertEqual(response_data['message'], '密码重置成功')
        
        # 验证密码确实被重置（通过尝试用新密码登录）
        login_url = '/user/login/'
        login_data = {
            'username': 'normaluser',
            'password': 'newpassword123'
        }
        
        login_response = self.client.post(login_url, login_data, format='json')
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)

    def test_normal_user_cannot_reset_password(self):
        """
        测试普通用户无法重置其他用户密码
        """
        url = f'/user/admin/management/{self.admin_user.id}/reset_password/'
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.normal_token}')
        
        reset_data = {
            'new_password': 'newpassword123'
        }
        
        response = self.client.post(url, reset_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_normal_user_cannot_create_user(self):
        """
        测试普通用户无法创建新用户
        """
        url = '/user/admin/management/'
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.normal_token}')
        
        create_data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'newpass123',
            'role': 'user'
        }
        
        response = self.client.post(url, create_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_normal_user_cannot_update_other_user(self):
        """
        测试普通用户无法更新其他用户信息
        """
        url = f'/user/admin/management/{self.admin_user.id}/'
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.normal_token}')
        
        update_data = {
            'username': 'hackedadmin',
            'role': 'user'
        }
        
        response = self.client.put(url, update_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_normal_user_cannot_delete_user(self):
        """
        测试普通用户无法删除用户
        """
        url = f'/user/admin/management/{self.admin_user.id}/'
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.normal_token}')
        
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_create_user_duplicate_username(self):
        """
        测试管理员创建重复用户名的用户
        """
        url = '/user/admin/management/'
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.admin_token}')
        
        create_data = {
            'username': 'normaluser',  # 使用已存在的用户名
            'email': 'duplicate@example.com',
            'password': 'newpass123',
            'role': 'user'
        }
        
        response = self.client.post(url, create_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response_data = response.json()
        
        self.assertEqual(response_data['code'], 400)
        self.assertEqual(response_data['message'], '创建用户失败')

    def test_admin_update_user_duplicate_username(self):
        """
        测试管理员更新用户为重复用户名
        """
        # 创建另一个用户
        other_user = User.objects.create_user(
            username='otheruser',
            password='otherpass123',
            email='other@example.com'
        )
        
        url = f'/user/admin/management/{other_user.id}/'
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.admin_token}')
        
        update_data = {
            'username': 'normaluser',  # 使用已存在的用户名
            'email': 'updated@example.com'
        }
        
        response = self.client.put(url, update_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response_data = response.json()
        
        self.assertEqual(response_data['code'], 400)
        self.assertEqual(response_data['message'], '更新用户信息失败')

    def test_user_model_age_calculation(self):
        """
        测试用户模型的年龄计算属性
        """
        # 验证年龄计算
        self.assertEqual(self.normal_user.age, 35)  # 1990年出生，当前年份2025年
        
        # 测试没有生日的用户
        user_without_birthday = User.objects.create_user(
            username='nobirthdayuser',
            password='pass123',
            email='nobirthday@example.com'
        )
        self.assertIsNone(user_without_birthday.age)

    def test_user_model_is_admin_property(self):
        """
        测试用户模型的is_admin属性
        """
        self.assertTrue(self.admin_user.is_admin)
        self.assertFalse(self.normal_user.is_admin)
