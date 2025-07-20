from django.db import models
from django.utils import timezone
import uuid
from user.models.book_manager import User


class KnowledgeBase(models.Model):
    """知识库模型"""
    # 基础信息
    name = models.CharField(max_length=255, verbose_name="知识库名称", help_text="知识库的名称")
    desc = models.TextField(blank=True, null=True, verbose_name="描述", help_text="知识库的描述信息")
    
    # 用户绑定
    owner = models.ForeignKey(
        User, 
        related_name='owned_knowledge_bases', 
        on_delete=models.CASCADE,
        verbose_name="拥有者",
        help_text="知识库的创建者",
        null=True,  # 临时允许为空，方便数据迁移
        blank=True
    )
    
    # 封面图片
    cover_image = models.URLField(
        blank=True, 
        null=True, 
        verbose_name="封面图片", 
        help_text="知识库封面图片URL（存储在腾讯云）"
    )
    
    # 文档设置
    DOC_WIDTH_CHOICES = [
        ('standard', '标准页宽'),
        ('wide', '超宽显示'),
    ]
    doc_width = models.CharField(
        max_length=20, 
        choices=DOC_WIDTH_CHOICES, 
        default='standard',
        verbose_name="文档展示宽度",
        help_text="文档展示宽度设置"
    )
    
    # 高级选项
    enable_comments = models.BooleanField(
        default=True, 
        verbose_name="开启评论功能",
        help_text="是否允许用户评论"
    )
    auto_publish = models.BooleanField(
        default=False, 
        verbose_name="开启自动发布",
        help_text="文档保存时自动发布到阅读页"
    )
    
    DOC_CREATE_POSITION_CHOICES = [
        ('top', '顶部'),
        ('bottom', '底部'),
    ]
    doc_create_position = models.CharField(
        max_length=20, 
        choices=DOC_CREATE_POSITION_CHOICES, 
        default='top',
        verbose_name="文档新建位置",
        help_text="新建文档在层级中的位置"
    )
    
    # 时间字段
    created_time = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_time = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    
    class Meta:
        db_table = 'knowledge_base'
        verbose_name = '知识库'
        verbose_name_plural = '知识库'
        ordering = ['-updated_time']
    
    def __str__(self):
        return self.name
    
    @property
    def document_count(self):
        """获取文档数量"""
        return self.documents.count()
    
    @property
    def collaborator_count(self):
        """获取协作者数量"""
        return self.collaborators.count()


class KnowledgeBaseCollaborator(models.Model):
    """知识库协作者模型"""
    PERMISSION_CHOICES = [
        ('read', '可阅读'),
        ('edit', '可编辑'),
    ]
    
    knowledge_base = models.ForeignKey(
        KnowledgeBase, 
        related_name='collaborators', 
        on_delete=models.CASCADE,
        verbose_name="知识库"
    )
    user = models.ForeignKey(
        User, 
        related_name='collaborated_knowledge_bases', 
        on_delete=models.CASCADE,
        verbose_name="协作者"
    )
    permission = models.CharField(
        max_length=10, 
        choices=PERMISSION_CHOICES, 
        default='read',
        verbose_name="权限",
        help_text="协作者的权限级别"
    )
    
    # 邀请相关
    invite_token = models.UUIDField(
        default=uuid.uuid4, 
        unique=True, 
        verbose_name="邀请令牌",
        help_text="用于生成邀请链接的唯一令牌"
    )
    invite_url = models.URLField(
        blank=True, 
        null=True, 
        verbose_name="邀请链接",
        help_text="协作者邀请链接"
    )
    invited_at = models.DateTimeField(auto_now_add=True, verbose_name="邀请时间")
    accepted_at = models.DateTimeField(blank=True, null=True, verbose_name="接受邀请时间")
    is_active = models.BooleanField(default=True, verbose_name="是否激活")
    
    created_time = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_time = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    
    class Meta:
        db_table = 'knowledge_base_collaborator'
        verbose_name = '知识库协作者'
        verbose_name_plural = '知识库协作者'
        unique_together = ('knowledge_base', 'user')
        ordering = ['-created_time']
    
    def __str__(self):
        return f"{self.knowledge_base.name} - {self.user.name} ({self.get_permission_display()})"
    
    def save(self, *args, **kwargs):
        """保存时生成邀请链接"""
        if not self.invite_url:
            # 这里应该根据实际的前端路由来生成邀请链接
            self.invite_url = f"/invite/knowledge-base/{self.invite_token}"
        super().save(*args, **kwargs)


class Document(models.Model):
    """文档模型"""
    knowledge_base = models.ForeignKey(
        KnowledgeBase, 
        related_name='documents', 
        on_delete=models.CASCADE,
        verbose_name="所属知识库"
    )
    title = models.CharField(max_length=255, verbose_name="文档标题")
    content = models.TextField(verbose_name="文档内容")
    file_size = models.BigIntegerField(default=0, verbose_name="文件大小")
    file_type = models.CharField(max_length=50, blank=True, verbose_name="文件类型")
    
    # 文档状态
    is_published = models.BooleanField(default=False, verbose_name="是否已发布")
    published_at = models.DateTimeField(blank=True, null=True, verbose_name="发布时间")
    
    # 层级位置
    position = models.IntegerField(default=0, verbose_name="位置排序")
    
    created_time = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_time = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    
    class Meta:
        db_table = 'document'
        verbose_name = '文档'
        verbose_name_plural = '文档'
        ordering = ['position', '-updated_time']
    
    def __str__(self):
        return f"{self.knowledge_base.name} - {self.title}"
    
    def save(self, *args, **kwargs):
        """保存时处理自动发布逻辑"""
        if self.knowledge_base.auto_publish and not self.is_published:
            self.is_published = True
            self.published_at = timezone.now()
        super().save(*args, **kwargs) 