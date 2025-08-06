from django.urls import path, include
from rest_framework.routers import DefaultRouter

from bot.views.bot import BotViewSet

# 创建DRF路由器
router = DefaultRouter()
router.register(r'bots', BotViewSet, basename='bot')

app_name = 'bot'

urlpatterns = [
    # Bot管理相关API
    path('', include(router.urls)),
]
