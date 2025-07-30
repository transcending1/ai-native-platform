from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from knowledge.models.namespace import Namespace, NamespaceCollaborator
from knowledge.serializers.namespace import (
    NamespaceSerializer,
    NamespaceListSerializer,
    NamespaceCollaboratorSerializer,
    AddCollaboratorSerializer,
    NamespaceBasicUpdateSerializer
)
from llm_api.settings.base import error_logger, info_logger, warning_logger

User = get_user_model()


@extend_schema_view(
    list=extend_schema(
        summary="获取知识库列表",
        description="获取当前用户可访问的知识库列表，包括自己创建的和被邀请协作的知识库",
        parameters=[
            OpenApiParameter(
                name='search',
                description='搜索关键词，支持按知识库名称搜索',
                required=False,
                type=OpenApiTypes.STR,
            ),
            OpenApiParameter(
                name='access_type',
                description='访问类型过滤：collaborators或public',
                required=False,
                type=OpenApiTypes.STR,
            ),
        ],
        tags=['知识库管理']
    ),
    create=extend_schema(
        summary="创建知识库",
        description="创建一个新的知识库",
        tags=['知识库管理']
    ),
    retrieve=extend_schema(
        summary="获取知识库详情",
        description="获取指定知识库的详细信息",
        tags=['知识库管理']
    ),
    update=extend_schema(
        summary="更新知识库",
        description="更新知识库的基本信息",
        tags=['知识库管理']
    ),
    partial_update=extend_schema(
        summary="部分更新知识库",
        description="部分更新知识库的基本信息",
        tags=['知识库管理']
    ),
    destroy=extend_schema(
        summary="删除知识库",
        description="删除指定的知识库（仅创建者可操作）",
        tags=['知识库管理']
    ),
)
class NamespaceViewSet(viewsets.ModelViewSet):
    """
    知识库管理视图集
    """
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['access_type', 'is_active']

    def get_queryset(self):
        """
        获取当前用户可访问的知识库
        """
        user = self.request.user
        
        # 用户创建的知识库 + 被邀请协作的知识库 + 公开的知识库
        queryset = Namespace.objects.filter(
            Q(creator=user) |  # 自己创建的
            Q(collaborators__user=user) |  # 被邀请协作的
            Q(access_type='public')  # 公开的
        ).distinct().filter(is_active=True)

        # 搜索功能
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(name__icontains=search)

        return queryset.order_by('-created_at')

    def get_serializer_class(self):
        """
        根据操作选择序列化器
        """
        if self.action == 'list':
            return NamespaceListSerializer
        elif self.action in ['update_basic', 'partial_update_basic']:
            return NamespaceBasicUpdateSerializer
        return NamespaceSerializer

    def perform_create(self, serializer):
        """
        创建知识库时记录日志
        """
        namespace = serializer.save()
        info_logger(f"用户 {self.request.user.username} 创建了知识库: {namespace.name}")

    def perform_update(self, serializer):
        """
        更新知识库时记录日志
        """
        namespace = serializer.save()
        info_logger(f"用户 {self.request.user.username} 更新了知识库: {namespace.name}")

    def perform_destroy(self, instance):
        """
        删除知识库时检查权限并记录日志
        """
        if instance.creator != self.request.user:
            error_logger(f"用户 {self.request.user.username} 尝试删除非自己创建的知识库: {instance.name}")
            return Response(
                {'error': '只有创建者可以删除知识库'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        info_logger(f"用户 {self.request.user.username} 删除了知识库: {instance.name}")
        instance.delete()

    @extend_schema(
        summary="添加协作者",
        description="为知识库添加协作者",
        request=AddCollaboratorSerializer,
        tags=['知识库管理']
    )
    @action(detail=True, methods=['post'])
    def add_collaborator(self, request, pk=None):
        """
        添加协作者
        """
        namespace = self.get_object()
        
        # 检查权限：只有创建者和有编辑权限的协作者可以添加
        if not namespace.can_edit(request.user):
            return Response(
                {'error': '没有权限添加协作者'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = AddCollaboratorSerializer(data=request.data)
        if serializer.is_valid():
            username = serializer.validated_data['username']
            role = serializer.validated_data['role']
            
            try:
                user = User.objects.get(username=username)
                
                # 检查是否已经是协作者
                if NamespaceCollaborator.objects.filter(namespace=namespace, user=user).exists():
                    return Response(
                        {'error': '该用户已经是协作者'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # 检查是否是创建者
                if namespace.creator == user:
                    return Response(
                        {'error': '不能将创建者添加为协作者'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # 创建协作关系
                collaborator = NamespaceCollaborator.objects.create(
                    namespace=namespace,
                    user=user,
                    role=role,
                    added_by=request.user
                )
                
                info_logger(f"用户 {request.user.username} 将 {username} 添加为知识库 {namespace.name} 的协作者")
                
                return Response(
                    NamespaceCollaboratorSerializer(collaborator).data,
                    status=status.HTTP_201_CREATED
                )
                
            except User.DoesNotExist:
                return Response(
                    {'error': '用户不存在'},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary="管理协作者",
        description="更新或移除协作者（PATCH=更新权限，DELETE=移除协作者）",
        request=NamespaceCollaboratorSerializer,
        tags=['知识库管理']
    )
    @action(detail=True, methods=['patch', 'delete'], url_path='collaborators/(?P<user_id>[^/.]+)')
    def manage_collaborator(self, request, pk=None, user_id=None):
        """
        管理协作者（更新权限或移除）
        """
        namespace = self.get_object()
        
        # 检查权限：只有创建者可以管理协作者
        if namespace.creator != request.user:
            error_msg = '只有创建者可以移除协作者' if request.method == 'DELETE' else '只有创建者可以更新协作者权限'
            return Response(
                {'error': error_msg},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            collaborator = NamespaceCollaborator.objects.get(
                namespace=namespace,
                user_id=user_id
            )
            
            if request.method == 'DELETE':
                # 移除协作者
                username = collaborator.user.username
                collaborator.delete()
                
                info_logger(f"用户 {request.user.username} 从知识库 {namespace.name} 中移除了协作者 {username}")
                
                return Response(status=status.HTTP_204_NO_CONTENT)
            
            elif request.method == 'PATCH':
                # 更新协作者权限
                updated = False
                
                # 支持role字段更新
                role = request.data.get('role')
                if role is not None:
                    if role not in ['admin', 'readonly']:
                        return Response(
                            {'error': '无效的角色类型，只支持：admin、readonly'},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                    collaborator.role = role
                    updated = True
                    info_logger(f"用户 {request.user.username} 将知识库 {namespace.name} 中协作者 {collaborator.user.username} 的角色更新为 {role}")
                
                # 兼容旧的can_edit字段（仅当没有提供role时）
                elif 'can_edit' in request.data:
                    can_edit = request.data.get('can_edit')
                    # 确保正确的类型转换，处理字符串类型的布尔值
                    can_edit_bool = bool(can_edit) if can_edit not in [False, 'false', 'False', 0, '0'] else False
                    new_role = 'admin' if can_edit_bool else 'readonly'
                    collaborator.role = new_role
                    updated = True
                    info_logger(f"用户 {request.user.username} 更新了知识库 {namespace.name} 中协作者 {collaborator.user.username} 的权限，新角色：{new_role}")
                
                if updated:
                    collaborator.save()
                    # 重新从数据库获取以确保数据同步
                    collaborator.refresh_from_db()
                
                return Response(
                    NamespaceCollaboratorSerializer(collaborator).data,
                    status=status.HTTP_200_OK
                )
            
        except NamespaceCollaborator.DoesNotExist:
            return Response(
                {'error': '协作者不存在'},
                status=status.HTTP_404_NOT_FOUND
            )

    @extend_schema(
        summary="获取协作者列表",
        description="获取知识库的所有协作者",
        tags=['知识库管理']
    )
    @action(detail=True, methods=['get'])
    def collaborators(self, request, pk=None):
        """
        获取协作者列表
        """
        namespace = self.get_object()
        
        # 检查访问权限
        if not namespace.can_access(request.user):
            return Response(
                {'error': '没有权限查看协作者'},
                status=status.HTTP_403_FORBIDDEN
            )

        collaborators = namespace.collaborators.all()
        serializer = NamespaceCollaboratorSerializer(collaborators, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="更新基本信息",
        description="更新知识库的基本信息（名称、描述、封面、访问权限）",
        request=NamespaceBasicUpdateSerializer,
        tags=['知识库管理']
    )
    @action(detail=True, methods=['patch'])
    def update_basic(self, request, pk=None):
        """
        更新知识库基本信息
        """
        namespace = self.get_object()
        
        # 检查编辑权限
        if not namespace.can_edit(request.user):
            return Response(
                {'error': '没有权限编辑知识库'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = NamespaceBasicUpdateSerializer(
            namespace,
            data=request.data,
            partial=True
        )
        
        if serializer.is_valid():
            serializer.save()
            info_logger(f"用户 {request.user.username} 更新了知识库 {namespace.name} 的基本信息")
            return Response(serializer.data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST) 