from django.db import models
from django.conf import settings
import uuid
import os


def cover_upload_path(instance, filename):
    """
    知识库封面上传路径生成函数
    """
    # 获取文件扩展名
    ext = filename.split('.')[-1]
    # 生成唯一文件名：namespace_covers/知识库ID/uuid.扩展名
    filename = f"{uuid.uuid4().hex}.{ext}"
    return f"namespace_covers/{instance.id}/{filename}"


class Namespace(models.Model):
    """
    知识库模型
    """
    # 访问权限选择
    ACCESS_CHOICES = [
        ('collaborators', '仅协作者可访问'),
        ('public', '所有用户可访问'),
    ]
    
    name = models.CharField(
        max_length=255, 
        verbose_name="知识库名称",
        help_text="知识库的名称"
    )
    description = models.TextField(
        blank=True, 
        null=True, 
        verbose_name="知识库简介",
        help_text="知识库的简介描述"
    )
    cover = models.ImageField(
        upload_to=cover_upload_path,
        blank=True,
        null=True,
        verbose_name="知识库封面",
        help_text="知识库封面图片，支持jpg、png、gif、webp格式，最大5MB"
    )
    access_type = models.CharField(
        max_length=20,
        choices=ACCESS_CHOICES,
        default='collaborators',
        verbose_name="访问权限",
        help_text="设置谁可以访问这个知识库"
    )
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='created_namespaces',
        on_delete=models.CASCADE,
        verbose_name="创建者"
    )
    slug = models.CharField(
        max_length=100,
        unique=True,
        blank=True,
        verbose_name="知识库路径",
        help_text="用于URL的唯一标识符，如果为空则自动生成"
    )
    is_active = models.BooleanField(
        default=True, 
        verbose_name="是否有效",
        help_text="是否启用该知识库"
    )
    created_at = models.DateTimeField(
        auto_now_add=True, 
        verbose_name="创建时间"
    )
    updated_at = models.DateTimeField(
        auto_now=True, 
        verbose_name="更新时间"
    )

    class Meta:
        verbose_name = "知识库"
        verbose_name_plural = "知识库"
        ordering = ['-created_at']

    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        """
        保存时自动生成slug
        """
        if not self.slug:
            # 使用UUID生成唯一slug
            self.slug = str(uuid.uuid4())[:8]
        super().save(*args, **kwargs)
    
    @property
    def is_public(self):
        """
        判断是否为公开知识库
        """
        return self.access_type == 'public'
    
    @property
    def collaborator_count(self):
        """
        获取协作者数量
        """
        return self.collaborators.count()
    
    def can_access(self, user):
        """
        检查用户是否可以访问此知识库
        """
        if not user.is_authenticated:
            return False
        
        # 创建者可以访问
        if self.creator == user:
            return True
        
        # 公开知识库所有用户都可以访问
        if self.is_public:
            return True
        
        # 检查是否为协作者
        return self.collaborators.filter(user=user).exists()
    
    def can_edit(self, user):
        """
        检查用户是否可以编辑此知识库
        """
        if not user.is_authenticated:
            return False
        
        # 创建者可以编辑
        if self.creator == user:
            return True
        
        # 检查是否为有管理权限的协作者
        return self.collaborators.filter(user=user, role='admin').exists()


class NamespaceCollaborator(models.Model):
    """
    知识库协作者模型
    """
    # 协作者角色选择
    ROLE_CHOICES = [
        ('admin', '管理权限'),  # 可以编辑知识库配置和内容
        ('readonly', '只读权限'),  # 只能查看，不能编辑
    ]
    
    namespace = models.ForeignKey(
        Namespace,
        related_name='collaborators',
        on_delete=models.CASCADE,
        verbose_name="知识库"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='collaborating_namespaces',
        on_delete=models.CASCADE,
        verbose_name="协作用户"
    )
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='readonly',
        verbose_name="角色权限",
        help_text="协作者在知识库中的权限级别"
    )
    added_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='added_collaborators',
        on_delete=models.CASCADE,
        verbose_name="添加者"
    )
    added_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="添加时间"
    )

    class Meta:
        verbose_name = "知识库协作者"
        verbose_name_plural = "知识库协作者"
        unique_together = ('namespace', 'user')
        ordering = ['-added_at']

    def __str__(self):
        return f"{self.namespace.name} - {self.user.username} ({self.get_role_display()})"
    
    @property
    def can_edit(self):
        """
        判断是否有编辑权限（兼容旧代码）
        """
        return self.role == 'admin'
    
    @property
    def can_read(self):
        """
        判断是否有读取权限
        """
        return True  # 所有协作者都有读取权限 