from rest_framework import serializers
from ..models.summary import UserSummary, PlatformSummary


class UserSummarySerializer(serializers.ModelSerializer):
    """用户统计数据序列化器"""
    
    username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = UserSummary
        fields = [
            'id',
            'username',
            'total_llm_models',
            'total_namespaces',
            'created_namespaces',
            'collaborated_namespaces',
            'total_documents',
            'normal_documents',
            'tool_documents',
            'created_bots',
            'collaborated_bots',
            'last_updated',
            'created_at'
        ]
        read_only_fields = [
            'id',
            'username',
            'total_llm_models',
            'total_namespaces',
            'created_namespaces',
            'collaborated_namespaces',
            'total_documents',
            'normal_documents',
            'tool_documents',
            'created_bots',
            'collaborated_bots',
            'last_updated',
            'created_at'
        ]


class PlatformSummarySerializer(serializers.ModelSerializer):
    """平台统计数据序列化器"""
    
    class Meta:
        model = PlatformSummary
        fields = [
            'id',
            'total_users',
            'active_users',
            'total_llm_models',
            'total_namespaces',
            'total_documents',
            'total_bots',
            'date',
            'created_at'
        ]
        read_only_fields = [
            'id',
            'total_users',
            'active_users',
            'total_llm_models',
            'total_namespaces',
            'total_documents',
            'total_bots',
            'date',
            'created_at'
        ]


class HomeDashboardSerializer(serializers.Serializer):
    """首页仪表板数据序列化器"""
    
    # 用户个人统计
    user_stats = UserSummarySerializer(read_only=True)
    
    # 平台统计
    platform_stats = PlatformSummarySerializer(read_only=True)
    
    # 增长统计（可选）
    growth_stats = serializers.DictField(read_only=True, required=False)
    
    class Meta:
        fields = ['user_stats', 'platform_stats', 'growth_stats']


class StatisticsRefreshSerializer(serializers.Serializer):
    """统计数据刷新响应序列化器"""
    
    message = serializers.CharField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    user_stats = UserSummarySerializer(read_only=True)
    
    class Meta:
        fields = ['message', 'updated_at', 'user_stats']
