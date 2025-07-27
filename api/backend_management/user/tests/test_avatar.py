import io

from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from user.models.user import CustomUser


class AvatarUploadTestCase(TestCase):
    """
    用户头像上传功能测试
    """

    def setUp(self):
        """
        测试初始化
        """
        self.client = APIClient()

        # 创建测试用户
        self.user = CustomUser.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        # 用户登录
        login_response = self.client.post('/user/login/', {
            'username': 'testuser',
            'password': 'testpass123'
        })

        self.assertEqual(login_response.status_code, status.HTTP_200_OK)

        # 获取访问令牌
        access_token = login_response.data['data']['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

    def create_test_image(self, format='JPEG', size=(200, 200), color=(255, 0, 0)):
        """
        创建测试图片
        """
        image = Image.new('RGB', size, color)
        image_io = io.BytesIO()
        image.save(image_io, format=format)
        image_io.seek(0)

        filename = f'test_avatar.{format.lower()}'
        if format == 'JPEG':
            filename = 'test_avatar.jpg'

        return SimpleUploadedFile(
            filename,
            image_io.getvalue(),
            content_type=f'image/{format.lower()}'
        )

    def test_upload_avatar_success(self):
        """
        测试成功上传头像
        """
        # 创建测试图片
        avatar_file = self.create_test_image()

        # 上传头像
        response = self.client.post('/user/upload_avatar/', {
            'avatar': avatar_file
        }, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['code'], 200)
        self.assertEqual(response.data['message'], '头像上传成功')
        self.assertIn('avatar_url', response.data['data'])

        # 验证用户头像已保存
        self.user.refresh_from_db()
        self.assertIsNotNone(self.user.avatar)

    def test_upload_avatar_png_format(self):
        """
        测试上传PNG格式头像
        """
        # 创建PNG测试图片
        avatar_file = self.create_test_image(format='PNG')

        # 上传头像
        response = self.client.post('/user/upload_avatar/', {
            'avatar': avatar_file
        }, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['code'], 200)

    def test_upload_avatar_file_too_large(self):
        """
        测试上传过大文件
        """
        # 创建大文件（超过5MB限制）
        large_image = Image.new('RGB', (3000, 3000), (255, 0, 0))
        image_io = io.BytesIO()
        large_image.save(image_io, format='JPEG', quality=100)
        image_io.seek(0)

        # 模拟超大文件
        large_file_content = b'0' * (6 * 1024 * 1024)  # 6MB
        large_file = SimpleUploadedFile(
            'large_avatar.jpg',
            large_file_content,
            content_type='image/jpeg'
        )

        response = self.client.post('/user/upload_avatar/', {
            'avatar': large_file
        }, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['code'], 400)

    def test_upload_avatar_invalid_format(self):
        """
        测试上传不支持的文件格式
        """
        # 创建文本文件模拟无效格式
        invalid_file = SimpleUploadedFile(
            'test.txt',
            b'This is not an image file',
            content_type='text/plain'
        )

        response = self.client.post('/user/upload_avatar/', {
            'avatar': invalid_file
        }, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['code'], 400)

    def test_upload_avatar_no_file(self):
        """
        测试不提供文件
        """
        response = self.client.post('/user/upload_avatar/', {}, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['code'], 400)

    def test_upload_avatar_unauthorized(self):
        """
        测试未认证用户上传头像
        """
        # 清除认证信息
        self.client.credentials()

        avatar_file = self.create_test_image()

        response = self.client.post('/user/upload_avatar/', {
            'avatar': avatar_file
        }, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_delete_avatar_success(self):
        """
        测试成功删除头像
        """
        # 先上传头像
        avatar_file = self.create_test_image()
        upload_response = self.client.post('/user/upload_avatar/', {
            'avatar': avatar_file
        }, format='multipart')

        self.assertEqual(upload_response.status_code, status.HTTP_200_OK)

        # 删除头像
        delete_response = self.client.delete('/user/delete_avatar/')

        self.assertEqual(delete_response.status_code, status.HTTP_200_OK)
        self.assertEqual(delete_response.data['code'], 200)
        self.assertEqual(delete_response.data['message'], '头像删除成功')

        # 验证头像已删除
        self.user.refresh_from_db()
        self.assertFalse(self.user.avatar)

    def test_delete_avatar_no_avatar(self):
        """
        测试删除不存在的头像
        """
        response = self.client.delete('/user/delete_avatar/')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['code'], 400)
        self.assertEqual(response.data['message'], '用户暂无头像')

    def test_delete_avatar_unauthorized(self):
        """
        测试未认证用户删除头像
        """
        # 清除认证信息
        self.client.credentials()

        response = self.client.delete('/user/delete_avatar/')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_upload_replace_existing_avatar(self):
        """
        测试替换现有头像
        """
        # 第一次上传
        avatar_file_1 = self.create_test_image(color=(255, 0, 0))
        response_1 = self.client.post('/user/upload_avatar/', {
            'avatar': avatar_file_1
        }, format='multipart')

        self.assertEqual(response_1.status_code, status.HTTP_200_OK)
        first_avatar_url = response_1.data['data']['avatar_url']

        # 第二次上传（替换）
        avatar_file_2 = self.create_test_image(color=(0, 255, 0))
        response_2 = self.client.post('/user/upload_avatar/', {
            'avatar': avatar_file_2
        }, format='multipart')

        self.assertEqual(response_2.status_code, status.HTTP_200_OK)
        second_avatar_url = response_2.data['data']['avatar_url']

        # 验证URL不同（说明替换成功）
        self.assertNotEqual(first_avatar_url, second_avatar_url)

        # 验证用户当前头像是新的
        self.user.refresh_from_db()
        self.assertIsNotNone(self.user.avatar)

    def test_get_user_profile_with_avatar(self):
        """
        测试获取包含头像的用户信息
        """
        # 上传头像
        avatar_file = self.create_test_image()
        upload_response = self.client.post('/user/upload_avatar/', {
            'avatar': avatar_file
        }, format='multipart')

        self.assertEqual(upload_response.status_code, status.HTTP_200_OK)

        # 获取用户信息
        profile_response = self.client.get('/user/profile/')

        self.assertEqual(profile_response.status_code, status.HTTP_200_OK)
        self.assertEqual(profile_response.data['code'], 200)

        # 验证响应包含头像URL
        user_data = profile_response.data['data']
        self.assertIsNotNone(user_data['avatar'])
        self.assertIn('avatars/', user_data['avatar'])
