from django.db import models
from django.utils import timezone
from django.core.validators import MinLengthValidator


class Namespace(models.Model):
    """
    命名空间（工作空间）表
    - 作为最顶层容器，隔离不同用户/团队的数据
    - 示例：用户A的私人空间、团队B的协作空间
    """
    name = models.CharField(
        max_length=100,
        unique=True,
        validators=[MinLengthValidator(3)],
        help_text="命名空间唯一标识（3-100字符）"
    )
    description = models.TextField(
        blank=True,
        null=True,
        help_text="空间描述信息"
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Directory(models.Model):
    """
    多级目录表（自关联实现树形结构）
    - 支持无限层级嵌套
    - 每个目录必须属于一个命名空间
    """
    name = models.CharField(
        max_length=255,
        validators=[MinLengthValidator(1)],
        help_text="目录名称（1-255字符）"
    )
    namespace = models.ForeignKey(
        Namespace,
        on_delete=models.CASCADE,
        related_name='directories',
        help_text="所属命名空间"
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        related_name='children',
        null=True,
        blank=True,
        help_text="父目录（空表示根目录）"
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # 同一层级下不允许重名
        unique_together = [['namespace', 'parent', 'name']]
        ordering = ['name']

    def __str__(self):
        return f"{self.namespace.name}/{self.get_full_path()}"

    def get_full_path(self):
        """ 获取目录完整路径 """
        parts = []
        current = self
        while current:
            parts.insert(0, current.name)
            current = current.parent
        return '/'.join(parts)

    def get_descendants(self, include_self=False):
        """
        获取所有后代目录（包括自身）
        :param include_self: 是否包含自身
        :return: 后代目录ID集合
        """
        descendants = set()
        to_process = [self]

        while to_process:
            current = to_process.pop()
            if include_self or current != self:
                descendants.add(current.id)
            # 添加所有直接子目录
            to_process.extend(current.children.all())

        return descendants

    def get_descendant_queryset(self):
        """获取后代目录的查询集"""
        from django.db.models import Q
        # 使用递归CTE在数据库层面高效查询
        return Directory.objects.raw(
            """
            WITH RECURSIVE descendants AS (SELECT id, parent_id
                                           FROM your_app_directory -- 替换your_app为实际应用名
                                           WHERE id = %s
                                           UNION ALL
                                           SELECT d.id, d.parent_id
                                           FROM your_app_directory d
                                                    INNER JOIN descendants dc ON dc.id = d.parent_id)
            SELECT id
            FROM descendants
            """,
            [self.id]
        )


class Note(models.Model):
    """
    笔记内容表
    - 存储在具体目录下
    - 支持富文本内容
    """
    title = models.CharField(
        max_length=255,
        validators=[MinLengthValidator(1)],
        help_text="笔记标题（1-255字符）"
    )
    content = models.TextField(
        blank=True,
        default='',
        help_text="富文本内容（支持HTML）"
    )
    directory = models.ForeignKey(
        Directory,
        on_delete=models.CASCADE,
        related_name='notes',
        help_text="所属目录"
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    category = models.CharField(
        max_length=50,
        choices=[
            ('md', 'Markdown'),
            ('database', 'Database'),
            ('tool', 'Tool')
        ],
        default='md',
        help_text="笔记类别（md, database, tool）"
    )

    class Meta:
        # 同一目录下不允许标题重复
        unique_together = [['directory', 'title']]
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.title} @ {self.directory}"
