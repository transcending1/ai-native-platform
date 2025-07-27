from django.urls import include, path
from rest_framework import routers

from user.views import user

# 普通用户相关路由
router = routers.DefaultRouter()
router.register(r'', user.UserViewSet)

# 管理员专用的用户管理路由
admin_router = routers.DefaultRouter()
admin_router.register(r'management', user.UserManagementViewSet)

# 合并路由
urlpatterns = [
    path('', include(router.urls)),
    path('admin/', include(admin_router.urls)),
]
