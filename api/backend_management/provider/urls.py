from django.urls import path, include
from rest_framework.routers import DefaultRouter
from provider.views.provider import (
    LLMModelViewSet, GlobalConfigCacheViewSet
)

# 创建路由器
router = DefaultRouter()

# 注册视图集
router.register(r'global-config-cache', GlobalConfigCacheViewSet, basename='global-config-cache')
router.register(r'llm-models', LLMModelViewSet, basename='llm-model')

app_name = 'provider'

urlpatterns = [
    path('', include(router.urls)),
]
