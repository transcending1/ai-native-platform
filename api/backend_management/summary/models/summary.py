from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class UserSummary(models.Model):
    """用户首页统计数据模型"""
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        verbose_name="用户",
        help_text="关联的用户"
    )
    
    # 统计数据字段
    total_llm_models = models.IntegerField(
        default=0,
        verbose_name="接入大模型数量",
        help_text="平台接入的大模型总数量"
    )
    
    total_namespaces = models.IntegerField(
        default=0,
        verbose_name="知识库数量",
        help_text="当前用户可访问的知识库数量"
    )
    
    created_namespaces = models.IntegerField(
        default=0,
        verbose_name="创建的知识库数量",
        help_text="当前用户创建的知识库数量"
    )
    
    collaborated_namespaces = models.IntegerField(
        default=0,
        verbose_name="协作知识库数量",
        help_text="当前用户被邀请协作的知识库数量"
    )
    
    total_documents = models.IntegerField(
        default=0,
        verbose_name="文档总数",
        help_text="当前用户创建的文档总数"
    )
    
    normal_documents = models.IntegerField(
        default=0,
        verbose_name="普通文档数量",
        help_text="当前用户创建的普通文档数量"
    )
    
    tool_documents = models.IntegerField(
        default=0,
        verbose_name="工具文档数量",
        help_text="当前用户创建的工具文档数量"
    )
    
    created_bots = models.IntegerField(
        default=0,
        verbose_name="创建的机器人数量",
        help_text="当前用户创建的机器人数量"
    )
    
    collaborated_bots = models.IntegerField(
        default=0,
        verbose_name="协作机器人数量",
        help_text="当前用户被邀请协作的机器人数量"
    )
    
    # 时间字段
    last_updated = models.DateTimeField(
        auto_now=True,
        verbose_name="最后更新时间"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="创建时间"
    )
    
    class Meta:
        db_table = 'summary_user_summary'
        verbose_name = "用户统计"
        verbose_name_plural = "用户统计"
        indexes = [
            models.Index(fields=['user'], name='summary_user_idx'),
            models.Index(fields=['last_updated'], name='summary_updated_idx'),
        ]
    
    def __str__(self):
        return f"{self.user.username}的统计数据"
    
    def refresh_statistics(self):
        """刷新统计数据"""
        from provider.models.provider import LLMModel
        from knowledge.models.namespace import Namespace
        from knowledge.models.knowledge_management import KnowledgeDocument
        from bot.models.bot import Bot
        
        # 更新大模型数量（平台级别）
        self.total_llm_models = LLMModel.objects.filter(is_active=True).count()
        
        # 更新知识库相关统计
        user_namespaces = Namespace.objects.filter(creator=self.user)
        self.created_namespaces = user_namespaces.count()
        
        # 用户协作的知识库（通过协作者关系）
        collaborated_namespaces = Namespace.objects.filter(
            collaborators__user=self.user
        ).exclude(creator=self.user)
        self.collaborated_namespaces = collaborated_namespaces.count()
        
        # 总知识库数量
        self.total_namespaces = self.created_namespaces + self.collaborated_namespaces
        
        # 更新文档相关统计
        user_documents = KnowledgeDocument.objects.filter(creator=self.user)
        self.total_documents = user_documents.count()
        
        # 按文档类型统计
        self.normal_documents = user_documents.filter(doc_type='document').count()
        self.tool_documents = user_documents.filter(doc_type='tool').count()
        
        # 更新机器人相关统计
        self.created_bots = Bot.objects.filter(creator=self.user).count()
        
        # 协作的机器人（如果有协作机制的话）
        self.collaborated_bots = 0  # 暂时设为0，后续如果Bot有协作机制再更新
        
        self.save()
        return self


class PlatformSummary(models.Model):
    """平台全局统计数据模型"""
    
    total_users = models.IntegerField(
        default=0,
        verbose_name="总用户数",
        help_text="平台注册用户总数"
    )
    
    active_users = models.IntegerField(
        default=0,
        verbose_name="活跃用户数",
        help_text="近30天活跃用户数"
    )
    
    total_llm_models = models.IntegerField(
        default=0,
        verbose_name="大模型总数",
        help_text="平台接入的大模型总数"
    )
    
    total_namespaces = models.IntegerField(
        default=0,
        verbose_name="知识库总数",
        help_text="平台知识库总数"
    )
    
    total_documents = models.IntegerField(
        default=0,
        verbose_name="文档总数",
        help_text="平台文档总数"
    )
    
    total_bots = models.IntegerField(
        default=0,
        verbose_name="机器人总数",
        help_text="平台机器人总数"
    )
    
    # 时间字段
    date = models.DateField(
        verbose_name="统计日期",
        help_text="统计数据对应的日期"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="创建时间"
    )
    
    class Meta:
        db_table = 'summary_platform_summary'
        verbose_name = "平台统计"
        verbose_name_plural = "平台统计"
        unique_together = ['date']
        indexes = [
            models.Index(fields=['date'], name='summary_date_idx'),
            models.Index(fields=['created_at'], name='summary_created_idx'),
        ]
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.date}的平台统计"
    
    @classmethod
    def generate_daily_summary(cls, target_date=None):
        """生成指定日期的平台统计数据"""
        from django.utils import timezone
        from django.contrib.auth import get_user_model
        from provider.models.provider import LLMModel
        from knowledge.models.namespace import Namespace
        from knowledge.models.knowledge_management import KnowledgeDocument
        from bot.models.bot import Bot
        
        if target_date is None:
            target_date = timezone.now().date()
        
        User = get_user_model()
        
        # 获取或创建当日统计记录
        summary, created = cls.objects.get_or_create(
            date=target_date,
            defaults={
                'total_users': User.objects.count(),
                'active_users': User.objects.filter(
                    last_login__gte=target_date - timezone.timedelta(days=30)
                ).count(),
                'total_llm_models': LLMModel.objects.filter(is_active=True).count(),
                'total_namespaces': Namespace.objects.count(),
                'total_documents': KnowledgeDocument.objects.count(),
                'total_bots': Bot.objects.count(),
            }
        )
        
        # 如果不是新创建的记录，更新数据
        if not created:
            summary.total_users = User.objects.count()
            summary.active_users = User.objects.filter(
                last_login__gte=target_date - timezone.timedelta(days=30)
            ).count()
            summary.total_llm_models = LLMModel.objects.filter(is_active=True).count()
            summary.total_namespaces = Namespace.objects.count()
            summary.total_documents = KnowledgeDocument.objects.count()
            summary.total_bots = Bot.objects.count()
            summary.save()
        
        return summary
