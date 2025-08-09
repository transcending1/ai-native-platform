from django.urls import path, include
from rest_framework.routers import DefaultRouter

# 创建DRF路由器
router = DefaultRouter()

urlpatterns = [
    # Bot管理相关API
    path('', include(router.urls)),
]
