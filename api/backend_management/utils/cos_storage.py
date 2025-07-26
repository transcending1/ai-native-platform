from django.core.files.storage import Storage
from qcloud_cos import CosConfig
from qcloud_cos import CosS3Client
from django.conf import settings


class TencentCOSStorage(Storage):
    def __init__(self):
        self.config = CosConfig(
            Region=settings.COS_REGION,
            SecretId=settings.COS_SECRET_ID,
            SecretKey=settings.COS_SECRET_KEY
        )
        self.client = CosS3Client(self.config)
        self.bucket = settings.COS_BUCKET
        self.base_url = settings.COS_URL

    def _open(self, name, mode='rb'):
        # 获取文件内容
        response = self.client.get_object(
            Bucket=self.bucket,
            Key=name
        )
        return response['Body'].get_raw_stream()

    def _save(self, name, content):
        self.client.put_object(
            Bucket=self.bucket,
            Body=content,
            Key=name,
            StorageClass='STANDARD',
            EnableMD5=False
        )
        return name

    def url(self, name):
        return f"{self.base_url}/{name}"

    def exists(self, name):
        try:
            self.client.head_object(Bucket=self.bucket, Key=name)
            return True
        except:
            return False

    def delete(self, name):
        self.client.delete_object(Bucket=self.bucket, Key=name)
