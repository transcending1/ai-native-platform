from django.conf import settings
from django.db import models
import json


def knowledge_file_upload_path(instance, filename):
    """
    知识文档文件上传路径
    """
    return f"knowledge/{instance.namespace.id}/documents/{filename}"


class KnowledgeDocument(models.Model):
    """
    知识文档模型 - 支持文件夹和文档两种类型
    """
    # 文档类型选择
    TYPE_CHOICES = [
        ('folder', '文件夹'),
        ('document', '文档'),
        ('tool', '工具'),
        ('form', '表单'),
    ]

    # 文档状态选择
    STATUS_CHOICES = [
        ('draft', '草稿'),
        ('published', '已发布'),
        ('archived', '已归档'),
    ]

    title = models.CharField(
        max_length=255,
        verbose_name="标题",
        help_text="知识文档或文件夹的标题"
    )
    content = models.TextField(
        blank=True,
        null=True,
        verbose_name="内容",
        help_text="知识文档的内容，支持Markdown格式"
    )
    summary = models.TextField(
        blank=True,
        null=True,
        verbose_name="摘要",
        help_text="知识文档的摘要描述"
    )
    doc_type = models.CharField(
        max_length=10,
        choices=TYPE_CHOICES,
        default='document',
        verbose_name="文档类型",
        help_text="文件夹、文档、工具或表单"
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name="状态"
    )
    namespace = models.ForeignKey(
        'knowledge.Namespace',
        related_name='documents',
        on_delete=models.CASCADE,
        verbose_name="所属知识库"
    )
    parent = models.ForeignKey(
        'self',
        blank=True,
        null=True,
        related_name='children',
        on_delete=models.CASCADE,
        verbose_name="父级文档",
        help_text="用于构建层次结构"
    )
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='created_documents',
        on_delete=models.CASCADE,
        verbose_name="创建者"
    )
    last_editor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='edited_documents',
        on_delete=models.CASCADE,
        verbose_name="最后编辑者"
    )
    sort_order = models.IntegerField(
        default=0,
        verbose_name="排序序号",
        help_text="在同级目录中的排序序号，数字越小排序越靠前"
    )
    is_public = models.BooleanField(
        default=False,
        verbose_name="是否公开",
        help_text="是否对知识库内所有成员公开"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="是否有效"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="创建时间"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="更新时间"
    )
    type_specific_data = models.JSONField(
        blank=True,
        null=True,
        verbose_name="类型特定数据",
        help_text="存储不同知识类型的特定数据（工具配置、表单配置等）"
    )

    class Meta:
        verbose_name = "知识文档"
        verbose_name_plural = "知识文档"
        ordering = ['sort_order', 'title']
        indexes = [
            models.Index(fields=['namespace', 'parent']),
            models.Index(fields=['namespace', 'doc_type']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.namespace.name} - {self.title}"

    def save(self, *args, **kwargs):
        """
        保存时的处理逻辑
        """
        # 如果是文件夹类型，清空content和type_specific_data
        if self.doc_type == 'folder':
            self.content = None
            self.type_specific_data = None

        # 如果是工具或表单类型，初始化type_specific_data
        if self.doc_type in ['tool', 'form'] and not self.type_specific_data:
            self.type_specific_data = self._get_default_type_data()

        # 如果是新创建的对象且没有设置last_editor，则设置为creator
        if not self.pk and not self.last_editor_id and self.creator_id:
            self.last_editor = self.creator

        super().save(*args, **kwargs)

    @property
    def is_folder(self):
        """
        判断是否为文件夹
        """
        return self.doc_type == 'folder'

    @property
    def is_document(self):
        """
        判断是否为文档
        """
        return self.doc_type == 'document'

    @property
    def is_tool(self):
        """
        判断是否为工具知识
        """
        return self.doc_type == 'tool'

    @property
    def is_form(self):
        """
        判断是否为表单知识
        """
        return self.doc_type == 'form'

    @property
    def breadcrumbs(self):
        """
        获取面包屑导航
        """
        breadcrumbs = []
        current = self
        while current:
            breadcrumbs.insert(0, {
                'id': current.id,
                'title': current.title,
                'type': current.doc_type
            })
            current = current.parent
        return breadcrumbs

    @property
    def depth(self):
        """
        获取文档在目录树中的深度
        """
        depth = 0
        current = self.parent
        while current:
            depth += 1
            current = current.parent
        return depth

    def get_descendants(self):
        """
        获取所有子孙文档
        """
        descendants = []
        for child in self.children.filter(is_active=True):
            descendants.append(child)
            descendants.extend(child.get_descendants())
        return descendants

    def can_access(self, user):
        """
        检查用户是否可以访问此文档
        """
        # 检查知识库访问权限
        if not self.namespace.can_access(user):
            return False

        # 如果是公开文档，任何有知识库访问权限的用户都可以访问
        if self.is_public:
            return True

        # 如果是创建者，可以访问
        if self.creator == user:
            return True

        # 检查知识库的编辑权限（编辑者可以访问所有文档）
        return self.namespace.can_edit(user)

    def can_edit(self, user):
        """
        检查用户是否可以编辑此文档
        """
        # 如果是创建者，可以编辑
        if self.creator == user:
            return True

        # 检查知识库的编辑权限
        return self.namespace.can_edit(user)

    def _get_default_type_data(self):
        """
        获取不同类型的默认数据结构
        """
        if self.doc_type == 'tool':
            return {
                'name': '',
                'description': '',
                'input_schema': {
                    'type': 'object',
                    'properties': {},
                    'required': []
                },
                'few_shots': [],
                'tool_type': 'dynamic',
                'extra_params': {}
            }
        elif self.doc_type == 'form':
            return {
                'table_name': '',
                'table_description': '',
                'fields': []
            }
        return {}

    def get_tool_data(self):
        """
        获取工具知识的数据
        """
        if self.is_tool and self.type_specific_data:
            return self.type_specific_data
        return self._get_default_type_data() if self.is_tool else None

    def set_tool_data(self, data):
        """
        设置工具知识的数据
        """
        if self.is_tool:
            self.type_specific_data = data

    def get_form_data(self):
        """
        获取表单知识的数据
        """
        if self.is_form and self.type_specific_data:
            return self.type_specific_data
        return self._get_default_type_data() if self.is_form else None

    def set_form_data(self, data):
        """
        设置表单知识的数据
        """
        if self.is_form:
            self.type_specific_data = data

    def get_dynamic_table_name(self):
        """
        获取表单知识对应的动态表名
        """
        if self.is_form:
            # 生成唯一的表名：namespace_id + document_id
            return f"form_data_{self.namespace_id}_{self.id}"
        return None


class FormDataEntry(models.Model):
    """
    表单知识的数据条目模型 - 用于存储用户提交的表单数据
    """
    form_document = models.ForeignKey(
        KnowledgeDocument,
        related_name='form_entries',
        on_delete=models.CASCADE,
        verbose_name="关联的表单知识"
    )
    data = models.JSONField(
        verbose_name="表单数据",
        help_text="用户提交的表单数据"
    )
    submitter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='form_submissions',
        on_delete=models.CASCADE,
        verbose_name="提交者"
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
        verbose_name = "表单数据条目"
        verbose_name_plural = "表单数据条目"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['form_document', 'created_at']),
            models.Index(fields=['submitter', 'created_at']),
        ]

    def __str__(self):
        return f"{self.form_document.title} - {self.submitter.username} - {self.created_at}"


class ToolExecution(models.Model):
    """
    工具执行记录模型 - 用于记录工具的执行历史
    """
    # 执行状态选择
    STATUS_CHOICES = [
        ('pending', '等待中'),
        ('running', '执行中'),
        ('success', '成功'),
        ('failed', '失败'),
        ('cancelled', '已取消'),
    ]

    tool_document = models.ForeignKey(
        KnowledgeDocument,
        related_name='tool_executions',
        on_delete=models.CASCADE,
        verbose_name="关联的工具知识"
    )
    executor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='tool_executions',
        on_delete=models.CASCADE,
        verbose_name="执行者"
    )
    input_data = models.JSONField(
        verbose_name="输入数据",
        help_text="工具执行时的输入参数"
    )
    output_data = models.JSONField(
        blank=True,
        null=True,
        verbose_name="输出数据",
        help_text="工具执行的结果"
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name="执行状态"
    )
    error_message = models.TextField(
        blank=True,
        null=True,
        verbose_name="错误信息",
        help_text="执行失败时的错误信息"
    )
    execution_time = models.DurationField(
        blank=True,
        null=True,
        verbose_name="执行时长",
        help_text="工具实际执行时长"
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
        verbose_name = "工具执行记录"
        verbose_name_plural = "工具执行记录"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['tool_document', 'status']),
            models.Index(fields=['executor', 'created_at']),
            models.Index(fields=['status', 'created_at']),
        ]

    def __str__(self):
        return f"{self.tool_document.title} - {self.executor.username} - {self.status}"
