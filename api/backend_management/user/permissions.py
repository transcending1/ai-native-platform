from rest_framework import permissions


class IsAdminUser(permissions.BasePermission):
    """
    管理员权限类
    只有管理员角色的用户才能访问
    """
    
    def has_permission(self, request, view):
        """
        检查用户是否为管理员
        """
        return (
            request.user and 
            request.user.is_authenticated and 
            hasattr(request.user, 'is_admin') and 
            request.user.is_admin
        )


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    资源所有者或管理员权限类
    只有资源所有者或管理员才能访问
    """
    
    def has_permission(self, request, view):
        """
        检查基本权限：已认证用户
        """
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        """
        检查对象级权限：资源所有者或管理员
        """
        return (
            obj == request.user or  # 资源所有者
            (hasattr(request.user, 'is_admin') and request.user.is_admin)  # 管理员
        ) 