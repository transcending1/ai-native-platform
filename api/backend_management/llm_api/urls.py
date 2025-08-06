"""
URL configuration for llm_api project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import JsonResponse
from django.urls import path, include
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView
)
from rest_framework_simplejwt.views import (
    TokenRefreshView,
    TokenVerifyView
)

urlpatterns = [

                  # 心跳检查
                  path("ping/", lambda request: JsonResponse({'message': 'pong'}), name="ping"),

                  # 后台管理
                  path("admin/", admin.site.urls, name="admin"),

                  # JWT Token相关端点
                  path('user/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
                  path('user/verify/', TokenVerifyView.as_view(), name='token_verify'),

                  # 业务模块
                  path('user/', include('user.urls'), name='user'),
                  path('knowledge/', include('knowledge.urls'), name='knowledge'),
                  path('provider/', include('provider.urls'), name='provider'),
                  path('bot/', include('bot.urls'), name='bot'),

                  # static
                  path('static/', include('django.contrib.staticfiles.urls')),
                  # 生成 Schema 文件（YAML/JSON）
                  path('schema/', SpectacularAPIView.as_view(), name='schema'),

                  # Swagger UI 文档（交互式）
                  path('swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),

                  # Redoc 文档（静态排版）
                  path('redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

              ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
