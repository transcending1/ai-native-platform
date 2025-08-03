import allure
import pytest
import base64
import json
from io import BytesIO
from PIL import Image
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch, AsyncMock, MagicMock

from ..models import Namespace, KnowledgeDocument

User = get_user_model()


class RichTextManagementTestCase(TestCase):
    """富文本知识管理测试用例"""
    
    def setUp(self):
        """设置测试数据"""
        self.client = APIClient()
        
        # 创建测试用户
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        # 创建测试知识库
        self.namespace = Namespace.objects.create(
            name='测试知识库',
            description='测试用知识库',
            creator=self.user,
            slug='test-namespace'
        )
    
    def create_test_image(self):
        """创建测试图片"""
        # 创建一个简单的测试图片
        img = Image.new('RGB', (100, 100), color='red')
        img_buffer = BytesIO()
        img.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        return img_buffer.getvalue()
    
    def get_base64_image(self):
        """获取base64编码的图片"""
        image_data = self.create_test_image()
        return base64.b64encode(image_data).decode('utf-8')
    
    @allure.feature("图片上传")
    @allure.story("上传图片到COS")
    def test_upload_image(self):
        """测试图片上传功能"""
        with allure.step("准备上传图片"):
            image_data = self.create_test_image()
            uploaded_file = SimpleUploadedFile(
                "test_image.png",
                image_data,
                content_type="image/png"
            )
        
        with allure.step("发送图片上传请求"):
            url = f'/knowledge/namespaces/{self.namespace.id}/documents/upload_image/'
            response = self.client.post(url, {'upload': uploaded_file}, format='multipart')
        
        with allure.step("验证上传结果"):
            assert response.status_code == status.HTTP_200_OK
            assert 'url' in response.data
            assert response.data['url'].startswith('http')
    
    @allure.feature("图片上传")
    @allure.story("上传不支持的文件类型")
    def test_upload_unsupported_file_type(self):
        """测试上传不支持的文件类型"""
        with allure.step("准备上传非图片文件"):
            uploaded_file = SimpleUploadedFile(
                "test_file.txt",
                b"test content",
                content_type="text/plain"
            )
        
        with allure.step("发送上传请求"):
            url = f'/knowledge/namespaces/{self.namespace.id}/documents/upload_image/'
            response = self.client.post(url, {'upload': uploaded_file}, format='multipart')
        
        with allure.step("验证拒绝上传"):
            assert response.status_code == status.HTTP_400_BAD_REQUEST
            assert "不支持的图片格式" in response.data['error']
    
    @allure.feature("文档管理")
    @allure.story("创建包含base64图片的文档")
    @patch('knowledge.serializers.knowledge_management.default_storage.save')
    @patch('knowledge.serializers.knowledge_management.default_storage.url')
    @patch('core.indexing.index.index')
    def test_create_document_with_base64_images(self, mock_index, mock_url, mock_save):
        """测试创建包含base64图片的文档"""
        # Mock存储和向量数据库方法
        mock_save.return_value = 'knowledge/1/1/test.png'
        mock_url.return_value = 'https://example.com/knowledge/1/1/test.png'
        mock_index.return_value = ([], [])
        
        with allure.step("准备包含base64图片的HTML内容"):
            base64_image = self.get_base64_image()
            html_content = f'''
            <p>这是一个测试文档</p>
            <p><img src="data:image/png;base64,{base64_image}" alt="测试图片"></p>
            <p>图片后的内容</p>
            '''
        
        with allure.step("创建文档"):
            url = f'/knowledge/namespaces/{self.namespace.id}/documents/'
            data = {
                'title': '测试文档',
                'content': html_content,
                'summary': '包含图片的测试文档',
                'doc_type': 'document'
            }
            response = self.client.post(url, data, format='json')
        
        with allure.step("验证文档创建成功"):
            assert response.status_code == status.HTTP_201_CREATED
            document_id = response.data['id']
        
        with allure.step("验证文档内容"):
            # 获取文档详情
            detail_url = f'/knowledge/namespaces/{self.namespace.id}/documents/{document_id}/'
            detail_response = self.client.get(detail_url)
            
            assert detail_response.status_code == status.HTTP_200_OK
            # 验证HTML中的base64已被替换为URL
            assert 'data:image/png;base64' not in detail_response.data['content']
            assert 'https://example.com' in detail_response.data['content']
    
    @allure.feature("文档管理")
    @allure.story("更新包含base64图片的文档")
    @patch('knowledge.serializers.knowledge_management.default_storage.save')
    @patch('knowledge.serializers.knowledge_management.default_storage.url')
    @patch('core.indexing.index.index')
    def test_update_document_with_base64_images(self, mock_index, mock_url, mock_save):
        """测试更新包含base64图片的文档"""
        # Mock存储和向量数据库方法
        mock_save.return_value = 'knowledge/1/1/test.png'
        mock_url.return_value = 'https://example.com/knowledge/1/1/test.png'
        mock_index.return_value = ([], [])
        
        with allure.step("创建初始文档"):
            document = KnowledgeDocument.objects.create(
                title='测试文档',
                content='<p>原始内容</p>',
                namespace=self.namespace,
                creator=self.user,
                last_editor=self.user,
                doc_type='document'
            )
        
        with allure.step("准备包含base64图片的更新内容"):
            base64_image = self.get_base64_image()
            updated_html_content = f'''
            <p>更新后的内容</p>
            <p><img src="data:image/png;base64,{base64_image}" alt="新图片"></p>
            <h1>一级标题</h1>
            <p>更多内容</p>
            '''
        
        with allure.step("更新文档"):
            url = f'/knowledge/namespaces/{self.namespace.id}/documents/{document.id}/'
            data = {
                'title': '更新后的测试文档',
                'content': updated_html_content,
                'summary': '更新后包含图片的测试文档'
            }
            response = self.client.put(url, data, format='json')
        
        with allure.step("验证文档更新成功"):
            assert response.status_code == status.HTTP_200_OK
            
            # 刷新文档对象
            document.refresh_from_db()
            
            # 验证HTML中的base64已被替换
            assert 'data:image/png;base64' not in document.content
            assert 'https://example.com' in document.content
            
            # 验证生成了Markdown内容
            assert document.markdown_content is not None
            assert '更新后的内容' in document.markdown_content
            assert '# 一级标题' in document.markdown_content
            
            # 验证调用了向量数据库存储
            mock_index.assert_called_once()
    
    @allure.feature("HTML转Markdown")
    @allure.story("HTML转换为Markdown格式")
    def test_html_to_markdown_conversion(self):
        """测试HTML到Markdown的转换"""
        from knowledge.serializers.knowledge_management import KnowledgeDocumentDetailSerializer
        
        with allure.step("准备HTML内容"):
            html_content = '''
            <h1>一级标题</h1>
            <h2>二级标题</h2>
            <p>这是一个<strong>粗体</strong>和<em>斜体</em>的段落。</p>
            <ul>
                <li>列表项1</li>
                <li>列表项2</li>
            </ul>
            <blockquote>这是引用内容</blockquote>
            '''
        
        with allure.step("转换为Markdown"):
            serializer = KnowledgeDocumentDetailSerializer()
            markdown_content = serializer._html_to_markdown(html_content)
        
        with allure.step("验证转换结果"):
            assert '# 一级标题' in markdown_content
            assert '## 二级标题' in markdown_content
            assert '**粗体**' in markdown_content
            assert '_斜体_' in markdown_content
            assert '* 列表项1' in markdown_content
            assert '> 这是引用内容' in markdown_content
    
    @allure.feature("文档管理")
    @allure.story("验证字段可见性")
    def test_markdown_content_field_visibility(self):
        """测试markdown_content字段的可见性"""
        with allure.step("创建文档"):
            document = KnowledgeDocument.objects.create(
                title='测试文档',
                content='<p>测试内容</p>',
                markdown_content='# 测试内容',
                namespace=self.namespace,
                creator=self.user,
                last_editor=self.user,
                doc_type='document'
            )
        
        with allure.step("获取文档详情"):
            url = f'/knowledge/namespaces/{self.namespace.id}/documents/{document.id}/'
            response = self.client.get(url)
        
        with allure.step("验证响应包含markdown_content字段"):
            assert response.status_code == status.HTTP_200_OK
            assert 'markdown_content' in response.data
            assert response.data['markdown_content'] == '# 测试内容'
        
        with allure.step("验证markdown_content是只读字段"):
            # 尝试直接更新markdown_content
            data = {
                'title': '更新标题',
                'markdown_content': '# 手动设置的Markdown'
            }
            update_response = self.client.patch(url, data, format='json')
            
            # 刷新文档
            document.refresh_from_db()
            
            # markdown_content不应该被手动设置的值覆盖
            assert document.markdown_content != '# 手动设置的Markdown'
    
    @allure.feature("图片管理")
    @allure.story("图片清理管理")
    @patch('knowledge.serializers.knowledge_management.default_storage')
    def test_image_cleanup_management(self, mock_storage):
        """测试图片清理管理"""
        with allure.step("模拟存储"):
            mock_storage.exists.return_value = True
            mock_storage.delete.return_value = True
        
        with allure.step("创建包含图片的文档"):
            html_content = '''
            <p>测试内容</p>
            <p><img src="https://example.com/knowledge/1/images/test1.png" alt="图片1"></p>
            '''
            
            document = KnowledgeDocument.objects.create(
                title='测试文档',
                content=html_content,
                namespace=self.namespace,
                creator=self.user,
                last_editor=self.user,
                doc_type='document'
            )
        
        with allure.step("更新文档内容，移除图片"):
            url = f'/knowledge/namespaces/{self.namespace.id}/documents/{document.id}/'
            data = {
                'title': '更新后的文档',
                'content': '<p>没有图片的内容</p>',
            }
            response = self.client.patch(url, data, format='json')
        
        with allure.step("验证更新成功"):
            assert response.status_code == status.HTTP_200_OK
            # 验证存储删除操作被调用
            mock_storage.delete.assert_called()
    
    @allure.feature("文档删除")
    @allure.story("删除文档时清理向量数据库和图片")
    @patch('core.indexing.index.delete')
    @patch('knowledge.views.knowledge_management.default_storage')
    def test_document_deletion_cleanup(self, mock_storage, mock_vector_delete):
        """测试文档删除时的资源清理"""
        with allure.step("模拟依赖"):
            mock_vector_delete.return_value = None
            mock_storage.exists.return_value = True
            mock_storage.delete.return_value = True
        
        with allure.step("创建包含图片和Markdown的文档"):
            html_content = '''
            <p>测试内容</p>
            <p><img src="https://example.com/knowledge/1/1/test.png" alt="测试图片"></p>
            '''
            
            document = KnowledgeDocument.objects.create(
                title='测试文档',
                content=html_content,
                markdown_content='# 测试Markdown内容',
                namespace=self.namespace,
                creator=self.user,
                last_editor=self.user,
                doc_type='document'
            )
        
        with allure.step("删除文档"):
            url = f'/knowledge/namespaces/{self.namespace.id}/documents/{document.id}/'
            response = self.client.delete(url)
        
        with allure.step("验证删除成功"):
            assert response.status_code == status.HTTP_204_NO_CONTENT
            
            # 验证文档被软删除
            document.refresh_from_db()
            assert document.is_active == False
    
    @allure.feature("图片管理")
    @allure.story("图片URL提取")
    def test_extract_image_urls(self):
        """测试图片URL提取功能"""
        from knowledge.serializers.knowledge_management import KnowledgeDocumentDetailSerializer
        
        with allure.step("准备包含多种图片的HTML"):
            html_content = '''
            <p>普通内容</p>
            <p><img src="https://example.com/knowledge/1/2/image1.png" alt="COS图片1"></p>
            <p><img src="https://external.com/image.jpg" alt="外部图片"></p>
            <p><img src="https://example.com/knowledge/1/3/image2.jpg" alt="COS图片2"></p>
            <p><img src="data:image/png;base64,iVBORw0..." alt="Base64图片"></p>
            '''
        
        with allure.step("提取图片URL"):
            serializer = KnowledgeDocumentDetailSerializer()
            image_urls = serializer._extract_image_urls(html_content)
        
        with allure.step("验证只提取COS图片"):
            assert len(image_urls) == 2
            assert "https://example.com/knowledge/1/2/image1.png" in image_urls
            assert "https://example.com/knowledge/1/3/image2.jpg" in image_urls
            assert "https://external.com/image.jpg" not in image_urls
    
    @allure.feature("图片管理")
    @allure.story("图片清理逻辑")
    def test_image_cleanup_logic(self):
        """测试图片清理逻辑"""
        from knowledge.serializers.knowledge_management import KnowledgeDocumentDetailSerializer
        
        with allure.step("测试图片清理"):
            serializer = KnowledgeDocumentDetailSerializer()
            old_urls = ["https://example.com/knowledge/1/2/old.png", "https://example.com/knowledge/1/2/keep.png"]
            new_urls = ["https://example.com/knowledge/1/2/keep.png", "https://example.com/knowledge/1/2/new.png"]
            
            # 计算应该删除的图片
            removed_images = set(old_urls) - set(new_urls)
        
        with allure.step("验证清理逻辑"):
            assert len(removed_images) == 1
            assert "https://example.com/knowledge/1/2/old.png" in removed_images
            assert "https://example.com/knowledge/1/2/keep.png" not in removed_images