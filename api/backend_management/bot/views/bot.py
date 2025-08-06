from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q
from django.contrib.auth import get_user_model
from django.utils import timezone
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
import json

from bot.models.bot import Bot, BotCollaborator
from bot.serializers.bot import (
    BotSerializer,
    BotListSerializer,
    BotCollaboratorSerializer,
    AddCollaboratorSerializer,
    BotBasicUpdateSerializer
)
from core.extensions.ext_langgraph import langgraph_client, GRAPH_ID
from llm_api.settings.base import error_logger, info_logger, warning_logger

User = get_user_model()


@extend_schema_view(
    list=extend_schema(
        summary="获取Bot列表",
        description="获取当前用户可访问的Bot列表，支持元数据过滤、分页和排序",
        parameters=[
            OpenApiParameter(
                name='search',
                description='搜索关键词，支持按Bot名称搜索（通过元数据过滤）',
                required=False,
                type=OpenApiTypes.STR,
            ),
            OpenApiParameter(
                name='access_type',
                description='访问类型过滤：collaborators或public（通过元数据过滤）',
                required=False,
                type=OpenApiTypes.STR,
            ),
            OpenApiParameter(
                name='page',
                description='页码，从1开始',
                required=False,
                type=OpenApiTypes.INT,
            ),
            OpenApiParameter(
                name='page_size',
                description='每页数量，默认10',
                required=False,
                type=OpenApiTypes.INT,
            ),
        ],
        tags=['Bot管理']
    ),
    create=extend_schema(
        summary="创建Bot",
        description="创建一个新的Bot，同时在LangGraph中创建对应的Assistant",
        tags=['Bot管理']
    ),
    retrieve=extend_schema(
        summary="获取Bot详情",
        description="获取指定Bot的详细信息",
        tags=['Bot管理']
    ),
    update=extend_schema(
        summary="更新Bot",
        description="更新Bot的基本信息，同时同步到LangGraph",
        tags=['Bot管理']
    ),
    partial_update=extend_schema(
        summary="部分更新Bot",
        description="部分更新Bot的基本信息，同时同步到LangGraph",
        tags=['Bot管理']
    ),
    destroy=extend_schema(
        summary="删除Bot",
        description="删除指定的Bot，同时删除LangGraph中的Assistant（仅创建者可操作）",
        tags=['Bot管理']
    ),
)
class BotViewSet(viewsets.ModelViewSet):
    """
    Bot管理视图集
    """
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['access_type', 'is_active']
    pagination_class = PageNumberPagination

    def get_queryset(self):
        """
        获取当前用户可访问的Bot
        """
        user = self.request.user
        
        # 用户创建的Bot + 被邀请协作的Bot + 公开的Bot
        queryset = Bot.objects.filter(
            Q(creator=user) |  # 自己创建的
            Q(collaborators__user=user) |  # 被邀请协作的
            Q(access_type='public')  # 公开的
        ).distinct().filter(is_active=True)

        # 搜索功能
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(name__icontains=search)

        return queryset.order_by('-created_at')

    def list(self, request, *args, **kwargs):
        """
        重写list方法，支持从LangGraph获取Assistants列表
        """
        # 获取查询参数
        search = request.query_params.get('search', '')
        access_type = request.query_params.get('access_type', '')
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 10))
        
        # 计算offset
        offset = (page - 1) * page_size
        
        try:
            # 准备元数据过滤条件
            metadata_filter = {}
            
            # 如果指定了访问类型，添加到元数据过滤
            if access_type:
                metadata_filter['access_type'] = access_type
            
            # 如果指定了搜索关键词，添加到元数据过滤
            if search:
                metadata_filter['search_keyword'] = search
            
            # 添加用户ID过滤（只显示当前用户的Bot）
            metadata_filter['user_id'] = str(request.user.id)
            
            # 调用LangGraph API获取Assistants列表
            assistants = langgraph_client.assistants.search(
                metadata=metadata_filter,
                graph_id=GRAPH_ID,
                limit=page_size,
                offset=offset,
                sort_by="created_at",
                sort_order='desc'
            )
            
            # 将LangGraph的Assistants转换为Bot对象
            bot_list = []
            for assistant in assistants:
                # 检查本地数据库中是否已存在该Bot
                bot, created = Bot.objects.get_or_create(
                    assistant_id=assistant['assistant_id'],
                    defaults={
                        'name': assistant.get('name', f"Assistant_{assistant['assistant_id'][:8]}"),
                        'description': assistant.get('description', ''),
                        'creator': request.user,
                        'graph_id': assistant.get('graph_id', GRAPH_ID),
                        'access_type': assistant.get('metadata', {}).get('access_type', 'collaborators'),
                    }
                )
                
                # 如果Bot已存在，更新基本信息
                if not created:
                    bot.name = assistant.get('name', bot.name)
                    bot.description = assistant.get('description', bot.description)
                    bot.save()
                
                # 检查用户是否有权限访问此Bot
                if bot.can_access(request.user):
                    bot_list.append(bot)
            
            # 序列化Bot列表
            serializer = self.get_serializer(bot_list, many=True)
            
            # 构造分页响应
            total_count = len(bot_list)  # 这里简化处理，实际应该从LangGraph获取总数
            
            return Response({
                'count': total_count,
                'next': f"?page={page + 1}" if len(bot_list) == page_size else None,
                'previous': f"?page={page - 1}" if page > 1 else None,
                'results': serializer.data
            })
            
        except Exception as e:
            error_logger(f"LangGraph API调用失败，回退到本地数据库查询: {str(e)}")
            # 如果LangGraph API调用失败，回退到本地数据库查询
            queryset = self.get_queryset()
            
            # 应用搜索过滤
            if search:
                queryset = queryset.filter(name__icontains=search)
            
            if access_type:
                queryset = queryset.filter(access_type=access_type)
            
            # 分页
            paginator = self.paginator_class(queryset, page_size)
            page_obj = paginator.get_page(page)
            
            serializer = self.get_serializer(page_obj, many=True)
            
            return Response({
                'count': paginator.count,
                'next': page_obj.has_next() and f"?page={page + 1}" or None,
                'previous': page_obj.has_previous() and f"?page={page - 1}" or None,
                'results': serializer.data
            })

    def get_serializer_class(self):
        """
        根据操作选择序列化器
        """
        if self.action == 'list':
            return BotListSerializer
        elif self.action in ['update_basic', 'partial_update_basic']:
            return BotBasicUpdateSerializer
        return BotSerializer

    def perform_create(self, serializer):
        """
        创建Bot时同时在LangGraph中创建Assistant
        """
        try:
            # 先保存Bot实例以获取ID
            bot = serializer.save()
            
            # 准备LangGraph metadata
            metadata = {
                'user_id': str(self.request.user.id),
                'creator_username': self.request.user.username,
                'created_at': timezone.now().isoformat(),
                'updated_at': timezone.now().isoformat(),
                'bot_id': str(bot.id),
                'access_type': bot.access_type,
                'search_keyword': bot.name,  # 用于搜索功能
            }
            
            # 如果有头像，添加到metadata
            if bot.avatar:
                metadata['avatar'] = self.request.build_absolute_uri(bot.avatar.url)
            
            # 调用LangGraph API创建Assistant
            assistant = langgraph_client.assistants.create(
                graph_id=GRAPH_ID,
                name=bot.name,
                description=bot.description or "",
                metadata=metadata
            )
            
            # 更新Bot实例的assistant_id
            bot.assistant_id = assistant['assistant_id']
            bot.save()
            
            info_logger(f"用户 {self.request.user.username} 创建了Bot: {bot.name}，Assistant ID: {bot.assistant_id}")
            
        except Exception as e:
            error_logger(f"创建Bot时调用LangGraph API失败: {str(e)}")
            # 如果LangGraph API调用失败，删除已创建的Bot实例
            if 'bot' in locals():
                bot.delete()
            raise Exception(f"创建Bot失败，LangGraph API错误: {str(e)}")

    def perform_update(self, serializer):
        """
        更新Bot时同步到LangGraph
        """
        try:
            bot = serializer.save()
            
            # 如果有assistant_id，同步更新到LangGraph
            if bot.assistant_id:
                # 准备更新的metadata
                metadata = {
                    'user_id': str(bot.creator.id),
                    'creator_username': bot.creator.username,
                    'created_at': bot.created_at.isoformat(),
                    'updated_at': timezone.now().isoformat(),
                    'bot_id': str(bot.id),
                }
                
                # 如果有头像，添加到metadata
                if bot.avatar:
                    metadata['avatar'] = self.request.build_absolute_uri(bot.avatar.url)
                
                # 调用LangGraph API更新Assistant
                langgraph_client.assistants.update(
                    assistant_id=bot.assistant_id,
                    graph_id=GRAPH_ID,
                    name=bot.name,
                    description=bot.description or "",
                    metadata=metadata
                )
                
                info_logger(f"用户 {self.request.user.username} 更新了Bot: {bot.name}，Assistant ID: {bot.assistant_id}")
            
        except Exception as e:
            error_logger(f"更新Bot时同步LangGraph API失败: {str(e)}")
            warning_logger(f"Bot {bot.name} 数据库更新成功，但LangGraph同步失败")

    def perform_destroy(self, instance):
        """
        删除Bot时检查权限并删除LangGraph中的Assistant
        """
        if instance.creator != self.request.user:
            error_logger(f"用户 {self.request.user.username} 尝试删除非自己创建的Bot: {instance.name}")
            return Response(
                {'error': '只有创建者可以删除Bot'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            # 删除LangGraph中的Assistant
            if instance.assistant_id:
                langgraph_client.assistants.delete(
                    assistant_id=instance.assistant_id
                )
                info_logger(f"已删除LangGraph Assistant: {instance.assistant_id}")
                
        except Exception as e:
            error_logger(f"删除LangGraph Assistant失败: {str(e)}")
            warning_logger(f"继续删除数据库中的Bot: {instance.name}")
        
        info_logger(f"用户 {self.request.user.username} 删除了Bot: {instance.name}")
        instance.delete()

    @extend_schema(
        summary="添加协作者",
        description="为Bot添加协作者",
        request=AddCollaboratorSerializer,
        tags=['Bot管理']
    )
    @action(detail=True, methods=['post'])
    def add_collaborator(self, request, pk=None):
        """
        添加协作者
        """
        bot = self.get_object()
        
        # 检查权限：只有创建者和有编辑权限的协作者可以添加
        if not bot.can_edit(request.user):
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
                if BotCollaborator.objects.filter(bot=bot, user=user).exists():
                    return Response(
                        {'error': '该用户已经是协作者'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # 检查是否是创建者
                if bot.creator == user:
                    return Response(
                        {'error': '不能将创建者添加为协作者'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # 创建协作关系
                collaborator = BotCollaborator.objects.create(
                    bot=bot,
                    user=user,
                    role=role,
                    added_by=request.user
                )
                
                info_logger(f"用户 {request.user.username} 将 {username} 添加为Bot {bot.name} 的协作者")
                
                return Response(
                    BotCollaboratorSerializer(collaborator).data,
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
        request=BotCollaboratorSerializer,
        tags=['Bot管理']
    )
    @action(detail=True, methods=['patch', 'delete'], url_path='collaborators/(?P<user_id>[^/.]+)')
    def manage_collaborator(self, request, pk=None, user_id=None):
        """
        管理协作者（更新权限或移除）
        """
        bot = self.get_object()
        
        # 检查权限：只有创建者可以管理协作者
        if bot.creator != request.user:
            error_msg = '只有创建者可以移除协作者' if request.method == 'DELETE' else '只有创建者可以更新协作者权限'
            return Response(
                {'error': error_msg},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            collaborator = BotCollaborator.objects.get(
                bot=bot,
                user_id=user_id
            )
            
            if request.method == 'DELETE':
                # 移除协作者
                username = collaborator.user.username
                collaborator.delete()
                
                info_logger(f"用户 {request.user.username} 从Bot {bot.name} 中移除了协作者 {username}")
                
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
                    info_logger(f"用户 {request.user.username} 将Bot {bot.name} 中协作者 {collaborator.user.username} 的角色更新为 {role}")
                
                # 兼容旧的can_edit字段（仅当没有提供role时）
                elif 'can_edit' in request.data:
                    can_edit = request.data.get('can_edit')
                    # 确保正确的类型转换，处理字符串类型的布尔值
                    can_edit_bool = bool(can_edit) if can_edit not in [False, 'false', 'False', 0, '0'] else False
                    new_role = 'admin' if can_edit_bool else 'readonly'
                    collaborator.role = new_role
                    updated = True
                    info_logger(f"用户 {request.user.username} 更新了Bot {bot.name} 中协作者 {collaborator.user.username} 的权限，新角色：{new_role}")
                
                if updated:
                    collaborator.save()
                    # 重新从数据库获取以确保数据同步
                    collaborator.refresh_from_db()
                
                return Response(
                    BotCollaboratorSerializer(collaborator).data,
                    status=status.HTTP_200_OK
                )
            
        except BotCollaborator.DoesNotExist:
            return Response(
                {'error': '协作者不存在'},
                status=status.HTTP_404_NOT_FOUND
            )

    @extend_schema(
        summary="获取协作者列表",
        description="获取Bot的所有协作者",
        tags=['Bot管理']
    )
    @action(detail=True, methods=['get'])
    def collaborators(self, request, pk=None):
        """
        获取协作者列表
        """
        bot = self.get_object()
        
        # 检查访问权限
        if not bot.can_access(request.user):
            return Response(
                {'error': '没有权限查看协作者'},
                status=status.HTTP_403_FORBIDDEN
            )

        collaborators = bot.collaborators.all()
        serializer = BotCollaboratorSerializer(collaborators, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="更新基本信息",
        description="更新Bot的基本信息（名称、描述、头像、访问权限），同时同步到LangGraph",
        request=BotBasicUpdateSerializer,
        tags=['Bot管理']
    )
    @action(detail=True, methods=['patch'])
    def update_basic(self, request, pk=None):
        """
        更新Bot基本信息
        """
        bot = self.get_object()
        
        # 检查编辑权限
        if not bot.can_edit(request.user):
            return Response(
                {'error': '没有权限编辑Bot'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = BotBasicUpdateSerializer(
            bot,
            data=request.data,
            partial=True
        )
        
        if serializer.is_valid():
            # 保存更新
            updated_bot = serializer.save()
            
            # 同步到LangGraph
            try:
                if updated_bot.assistant_id:
                    # 准备更新的metadata
                    metadata = {
                        'user_id': str(updated_bot.creator.id),
                        'creator_username': updated_bot.creator.username,
                        'created_at': updated_bot.created_at.isoformat(),
                        'updated_at': timezone.now().isoformat(),
                        'bot_id': str(updated_bot.id),
                    }
                    
                    # 如果有头像，添加到metadata
                    if updated_bot.avatar:
                        metadata['avatar'] = request.build_absolute_uri(updated_bot.avatar.url)
                    
                    # 调用LangGraph API更新Assistant
                    langgraph_client.assistants.update(
                        assistant_id=updated_bot.assistant_id,
                        graph_id=GRAPH_ID,
                        name=updated_bot.name,
                        description=updated_bot.description or "",
                        metadata=metadata
                    )
                    
            except Exception as e:
                error_logger(f"更新Bot基本信息时同步LangGraph失败: {str(e)}")
                warning_logger(f"Bot {updated_bot.name} 数据库更新成功，但LangGraph同步失败")
            
            info_logger(f"用户 {request.user.username} 更新了Bot {updated_bot.name} 的基本信息")
            return Response(serializer.data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary="从LangGraph同步Bots",
        description="从LangGraph获取用户的Assistants并同步到本地数据库",
        tags=['Bot管理']
    )
    @action(detail=False, methods=['post'])
    def sync_from_langgraph(self, request):
        """
        从LangGraph同步用户的Assistants
        """
        try:
            # 获取用户在LangGraph中的Assistants
            assistants = langgraph_client.assistants.search(
                metadata={
                    "user_id": str(request.user.id)
                },
                graph_id=GRAPH_ID,
                limit=100,
                offset=0,
                sort_by="created_at",
                sort_order='desc'
            )
            
            synced_count = 0
            for assistant in assistants:
                assistant_id = assistant['assistant_id']
                
                # 检查本地是否已存在
                if not Bot.objects.filter(assistant_id=assistant_id).exists():
                    # 创建新的Bot记录
                    bot = Bot.objects.create(
                        name=assistant.get('name', f"Assistant_{assistant_id[:8]}"),
                        description=assistant.get('description', ''),
                        creator=request.user,
                        assistant_id=assistant_id,
                        graph_id=assistant.get('graph_id', GRAPH_ID),
                    )
                    synced_count += 1
                    info_logger(f"从LangGraph同步了Assistant: {assistant_id} -> Bot: {bot.name}")
            
            return Response({
                'message': f'成功同步 {synced_count} 个Assistants',
                'synced_count': synced_count
            })
            
        except Exception as e:
            error_logger(f"从LangGraph同步Assistants失败: {str(e)}")
            return Response(
                {'error': f'同步失败: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
