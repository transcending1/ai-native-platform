import os
import uuid
from datetime import datetime
from django.conf import settings
from django.core.files.storage import Storage
from django.core.files.base import ContentFile
from django.utils.deconstruct import deconstructible
import logging

logger = logging.getLogger(__name__)

try:
    from qcloud_cos import CosConfig
    from qcloud_cos import CosS3Client
    from qcloud_cos.cos_exception import CosServiceError, CosClientError
    COS_AVAILABLE = True
except ImportError:
    COS_AVAILABLE = False
    logger.warning("qcloud_cos not installed. COS storage will not work.")


@deconstructible
class TencentCOSStorage(Storage):
    """
    腾讯云COS存储后端
    """
    
    def __init__(self):
        self.config = getattr(settings, 'TENCENT_COS_SETTINGS', {})
        self.secret_id = self.config.get('SECRET_ID', '')
        self.secret_key = self.config.get('SECRET_KEY', '')
        self.region = self.config.get('REGION', 'ap-beijing')
        self.bucket = self.config.get('BUCKET', '')
        self.domain = self.config.get('DOMAIN', '')
        self.is_https = self.config.get('IS_HTTPS', True)
        
        if COS_AVAILABLE and self.secret_id and self.secret_key:
            config = CosConfig(
                Region=self.region, 
                SecretId=self.secret_id, 
                SecretKey=self.secret_key
            )
            self.client = CosS3Client(config)
        else:
            self.client = None
            logger.warning("COS client not initialized. Check your credentials.")
    
    def _save(self, name, content):
        """
        保存文件到腾讯云COS
        """
        if not self.client:
            raise Exception("COS client not available")
        
        # 生成唯一的文件名
        ext = os.path.splitext(name)[1]
        unique_name = f"{uuid.uuid4().hex}{ext}"
        
        # 构建存储路径（按日期分组）
        date_path = datetime.now().strftime('%Y/%m/%d')
        key = f"knowledge-base-covers/{date_path}/{unique_name}"
        
        try:
            # 读取文件内容
            if hasattr(content, 'read'):
                content_data = content.read()
            else:
                content_data = content
            
            # 上传到COS
            response = self.client.put_object(
                Bucket=self.bucket,
                Body=content_data,
                Key=key,
                ContentType=self._get_content_type(name)
            )
            
            logger.info(f"File uploaded to COS: {key}")
            return key
            
        except (CosServiceError, CosClientError) as e:
            logger.error(f"Failed to upload file to COS: {str(e)}")
            raise Exception(f"Upload failed: {str(e)}")
    
    def delete(self, name):
        """
        从腾讯云COS删除文件
        """
        if not self.client:
            return False
        
        try:
            self.client.delete_object(Bucket=self.bucket, Key=name)
            logger.info(f"File deleted from COS: {name}")
            return True
        except (CosServiceError, CosClientError) as e:
            logger.error(f"Failed to delete file from COS: {str(e)}")
            return False
    
    def exists(self, name):
        """
        检查文件是否存在于腾讯云COS
        """
        if not self.client:
            return False
        
        try:
            self.client.head_object(Bucket=self.bucket, Key=name)
            return True
        except (CosServiceError, CosClientError):
            return False
    
    def url(self, name):
        """
        获取文件的访问URL
        """
        if self.domain:
            # 使用自定义域名
            protocol = 'https' if self.is_https else 'http'
            return f"{protocol}://{self.domain}/{name}"
        else:
            # 使用默认域名
            protocol = 'https' if self.is_https else 'http'
            return f"{protocol}://{self.bucket}.cos.{self.region}.myqcloud.com/{name}"
    
    def size(self, name):
        """
        获取文件大小
        """
        if not self.client:
            return 0
        
        try:
            response = self.client.head_object(Bucket=self.bucket, Key=name)
            return int(response.get('Content-Length', 0))
        except (CosServiceError, CosClientError):
            return 0
    
    def _get_content_type(self, name):
        """
        根据文件扩展名获取Content-Type
        """
        ext = os.path.splitext(name)[1].lower()
        content_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.webp': 'image/webp',
        }
        return content_types.get(ext, 'application/octet-stream')


class COSUploadService:
    """
    腾讯云COS上传服务
    """
    
    def __init__(self):
        self.storage = TencentCOSStorage()
    
    def upload_image(self, image_file, folder='images'):
        """
        上传图片文件
        
        Args:
            image_file: 图片文件对象
            folder: 存储文件夹
            
        Returns:
            dict: 包含上传结果的字典
        """
        try:
            # 验证文件格式
            if not self._validate_image(image_file):
                return {
                    'success': False,
                    'message': '不支持的图片格式或文件过大',
                    'url': None
                }
            
            # 构建文件名
            ext = os.path.splitext(image_file.name)[1]
            unique_name = f"{uuid.uuid4().hex}{ext}"
            
            # 构建存储路径
            date_path = datetime.now().strftime('%Y/%m/%d')
            file_path = f"{folder}/{date_path}/{unique_name}"
            
            # 保存文件
            saved_path = self.storage._save(file_path, image_file)
            file_url = self.storage.url(saved_path)
            
            return {
                'success': True,
                'message': '上传成功',
                'url': file_url,
                'path': saved_path
            }
            
        except Exception as e:
            logger.error(f"Image upload failed: {str(e)}")
            return {
                'success': False,
                'message': f'上传失败: {str(e)}',
                'url': None
            }
    
    def delete_image(self, file_path):
        """
        删除图片文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            bool: 删除是否成功
        """
        try:
            return self.storage.delete(file_path)
        except Exception as e:
            logger.error(f"Image deletion failed: {str(e)}")
            return False
    
    def _validate_image(self, image_file):
        """
        验证图片文件
        
        Args:
            image_file: 图片文件对象
            
        Returns:
            bool: 是否有效
        """
        # 检查文件扩展名
        ext = os.path.splitext(image_file.name)[1].lower()
        allowed_exts = getattr(settings, 'ALLOWED_IMAGE_EXTENSIONS', ['.jpg', '.jpeg', '.png', '.gif', '.webp'])
        
        if ext not in allowed_exts:
            return False
        
        # 检查文件大小
        max_size = getattr(settings, 'MAX_IMAGE_SIZE', 5 * 1024 * 1024)  # 5MB
        if image_file.size > max_size:
            return False
        
        return True


# 创建全局实例
cos_upload_service = COSUploadService() 