from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views.summary import UserSummaryViewSet, PlatformSummaryViewSet

# 创建DRF路由器
router = DefaultRouter()

# 注册视图集
router.register(r'user-stats', UserSummaryViewSet, basename='user-summary')
router.register(r'platform-stats', PlatformSummaryViewSet, basename='platform-summary')

urlpatterns = [
    # 统计管理相关API
    path('', include(router.urls)),
]
