from django.contrib.auth.models import AbstractUser
from django.db import models
from datetime import date
import uuid
import os


def avatar_upload_path(instance, filename):
    """
    用户头像上传路径生成函数
    """
    # 获取文件扩展名
    ext = filename.split('.')[-1]
    # 生成唯一文件名：avatars/用户ID/uuid.扩展名
    filename = f"{uuid.uuid4().hex}.{ext}"
    return f"avatars/{instance.id}/{filename}"


class CustomUser(AbstractUser):
    """
    自定义用户模型，扩展Django内置用户模型
    """
    # 角色选择
    ROLE_CHOICES = [
        ('user', '普通用户'),
        ('admin', '管理员'),
    ]
    
    # 性别选择
    GENDER_CHOICES = [
        ('male', '男性'),
        ('female', '女性'),
        ('unknown', '未知'),
    ]
    
    phone = models.CharField(max_length=20, blank=True, verbose_name="手机号")
    avatar = models.ImageField(
        upload_to=avatar_upload_path, 
        blank=True, 
        null=True, 
        verbose_name="头像",
        help_text="用户头像，支持jpg、png、gif、webp格式，最大5MB"
    )
    role = models.CharField(
        max_length=10, 
        choices=ROLE_CHOICES, 
        default='user', 
        verbose_name="角色"
    )
    gender = models.CharField(
        max_length=10, 
        choices=GENDER_CHOICES, 
        default='unknown', 
        verbose_name="性别"
    )
    birthday = models.DateField(blank=True, null=True, verbose_name="生日")
    is_active = models.BooleanField(default=True, verbose_name="是否有效")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        verbose_name = "用户"
        verbose_name_plural = "用户"

    def __str__(self):
        return self.username
    
    @property
    def age(self):
        """
        计算年龄的属性
        """
        if self.birthday:
            today = date.today()
            return today.year - self.birthday.year - ((today.month, today.day) < (self.birthday.month, self.birthday.day))
        return None
    
    @property
    def is_admin(self):
        """
        判断是否为管理员
        """
        return self.role == 'admin'
    
    def delete_old_avatar(self):
        """
        删除旧头像文件
        """
        if self.avatar:
            try:
                # 如果使用腾讯云存储，调用存储后端的删除方法
                self.avatar.storage.delete(self.avatar.name)
            except Exception:
                # 忽略删除错误，避免影响主流程
                pass 