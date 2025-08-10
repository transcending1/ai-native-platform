from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from datetime import timedelta
from drf_spectacular.utils import extend_schema, extend_schema_view

from ..models.summary import UserSummary, PlatformSummary
from ..serializers.summary import (
    UserSummarySerializer,
    PlatformSummarySerializer,
    HomeDashboardSerializer,
    StatisticsRefreshSerializer
)
from llm_api.settings.base import info_logger, error_logger


@extend_schema_view(
    list=extend_schema(
        summary="获取当前用户统计数据",
        description="获取当前登录用户的个人统计数据，包括创建的知识库、文档、机器人等统计信息",
        tags=["首页统计"]
    ),
    dashboard=extend_schema(
        summary="获取首页仪表板数据",
        description="获取首页仪表板所需的所有统计数据，包括用户个人统计和平台统计",
        tags=["首页统计"]
    ),
    refresh=extend_schema(
        summary="刷新用户统计数据",
        description="手动刷新当前用户的统计数据，重新计算各项指标",
        tags=["首页统计"]
    )
)
class UserSummaryViewSet(viewsets.ReadOnlyModelViewSet):
    """用户统计数据视图集"""
    
    serializer_class = UserSummarySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """只返回当前用户的统计数据"""
        return UserSummary.objects.filter(user=self.request.user)
    
    def get_or_create_user_summary(self):
        """获取或创建用户统计记录"""
        try:
            user_summary, created = UserSummary.objects.get_or_create(
                user=self.request.user
            )
            if created:
                info_logger(f"为用户 {self.request.user.username} 创建了新的统计记录")
                user_summary.refresh_statistics()
            return user_summary
        except Exception as e:
            error_logger(f"获取用户统计数据失败: {str(e)}")
            raise
    
    def list(self, request, *args, **kwargs):
        """获取当前用户统计数据"""
        try:
            user_summary = self.get_or_create_user_summary()
            serializer = self.get_serializer(user_summary)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            error_logger(f"获取用户统计数据失败: {str(e)}")
            return Response(
                {"error": "获取统计数据失败", "detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """获取首页仪表板数据"""
        try:
            # 获取用户统计数据
            user_summary = self.get_or_create_user_summary()
            
            # 获取最新的平台统计数据
            platform_summary = PlatformSummary.objects.first()
            if not platform_summary:
                # 如果没有平台统计数据，生成今日的
                platform_summary = PlatformSummary.generate_daily_summary()
            
            # 计算增长统计（可选功能）
            growth_stats = self.calculate_growth_stats(user_summary)
            
            # 构建仪表板数据
            dashboard_data = {
                'user_stats': UserSummarySerializer(user_summary).data,
                'platform_stats': PlatformSummarySerializer(platform_summary).data,
                'growth_stats': growth_stats
            }
            
            serializer = HomeDashboardSerializer(dashboard_data)
            info_logger(f"用户 {request.user.username} 获取了首页仪表板数据")
            
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except Exception as e:
            error_logger(f"获取仪表板数据失败: {str(e)}")
            return Response(
                {"error": "获取仪表板数据失败", "detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def refresh(self, request):
        """刷新用户统计数据"""
        try:
            user_summary = self.get_or_create_user_summary()
            user_summary.refresh_statistics()
            
            response_data = {
                'message': '统计数据已刷新',
                'updated_at': user_summary.last_updated,
                'user_stats': UserSummarySerializer(user_summary).data
            }
            
            serializer = StatisticsRefreshSerializer(response_data)
            info_logger(f"用户 {request.user.username} 刷新了统计数据")
            
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except Exception as e:
            error_logger(f"刷新统计数据失败: {str(e)}")
            return Response(
                {"error": "刷新统计数据失败", "detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def calculate_growth_stats(self, user_summary):
        """计算增长统计数据"""
        try:
            # 获取7天前的平台统计作为对比基准
            seven_days_ago = timezone.now().date() - timedelta(days=7)
            previous_platform_stats = PlatformSummary.objects.filter(
                date__lte=seven_days_ago
            ).first()
            
            if not previous_platform_stats:
                return {
                    'user_growth': 0,
                    'namespace_growth': 0,
                    'document_growth': 0,
                    'bot_growth': 0
                }
            
            # 计算增长率
            current_platform_stats = PlatformSummary.objects.first()
            if not current_platform_stats:
                return {
                    'user_growth': 0,
                    'namespace_growth': 0,
                    'document_growth': 0,
                    'bot_growth': 0
                }
            
            def calculate_growth_rate(current, previous):
                if previous == 0:
                    return 100 if current > 0 else 0
                return round(((current - previous) / previous) * 100, 1)
            
            return {
                'user_growth': calculate_growth_rate(
                    current_platform_stats.total_users,
                    previous_platform_stats.total_users
                ),
                'namespace_growth': calculate_growth_rate(
                    current_platform_stats.total_namespaces,
                    previous_platform_stats.total_namespaces
                ),
                'document_growth': calculate_growth_rate(
                    current_platform_stats.total_documents,
                    previous_platform_stats.total_documents
                ),
                'bot_growth': calculate_growth_rate(
                    current_platform_stats.total_bots,
                    previous_platform_stats.total_bots
                )
            }
            
        except Exception as e:
            error_logger(f"计算增长统计失败: {str(e)}")
            return {
                'user_growth': 0,
                'namespace_growth': 0,
                'document_growth': 0,
                'bot_growth': 0
            }


@extend_schema_view(
    list=extend_schema(
        summary="获取平台统计数据列表",
        description="获取平台历史统计数据，支持分页和日期筛选",
        tags=["平台统计"]
    ),
    latest=extend_schema(
        summary="获取最新平台统计数据",
        description="获取最新的平台统计数据",
        tags=["平台统计"]
    ),
    generate_today=extend_schema(
        summary="生成今日平台统计",
        description="手动生成或更新今日的平台统计数据",
        tags=["平台统计"]
    )
)
class PlatformSummaryViewSet(viewsets.ReadOnlyModelViewSet):
    """平台统计数据视图集"""
    
    serializer_class = PlatformSummarySerializer
    permission_classes = [IsAuthenticated]
    queryset = PlatformSummary.objects.all()
    
    @action(detail=False, methods=['get'])
    def latest(self, request):
        """获取最新平台统计数据"""
        try:
            latest_summary = PlatformSummary.objects.first()
            if not latest_summary:
                # 如果没有数据，生成今日统计
                latest_summary = PlatformSummary.generate_daily_summary()
            
            serializer = self.get_serializer(latest_summary)
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except Exception as e:
            error_logger(f"获取最新平台统计失败: {str(e)}")
            return Response(
                {"error": "获取平台统计失败", "detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def generate_today(self, request):
        """生成今日平台统计"""
        try:
            today_summary = PlatformSummary.generate_daily_summary()
            serializer = self.get_serializer(today_summary)
            
            info_logger(f"管理员 {request.user.username} 生成了今日平台统计")
            return Response(
                {
                    "message": "今日平台统计已生成",
                    "data": serializer.data
                },
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            error_logger(f"生成今日平台统计失败: {str(e)}")
            return Response(
                {"error": "生成平台统计失败", "detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
