from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.http import StreamingHttpResponse, Http404
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
import json
import uuid

from bot.models.bot import Bot, BotCollaborator
from bot.serializers.bot import (
    BotSerializer,
    BotListSerializer,
    BotCollaboratorSerializer,
    AddCollaboratorSerializer,
    BotBasicUpdateSerializer,
    ChatMessageSerializer,
    ChatResponseSerializer,
    ThreadSerializer
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
        获取Bot列表
        """
        return super().list(request, *args, **kwargs)

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

    def destroy(self, request, *args, **kwargs):
        """
        删除Bot时检查权限并删除LangGraph中的Assistant
        """
        # 直接通过pk获取Bot，不使用过滤的queryset
        try:
            instance = Bot.objects.get(pk=kwargs['pk'], is_active=True)
        except Bot.DoesNotExist:
            return Response(
                {'error': 'Bot不存在'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # 检查权限
        if instance.creator != request.user:
            error_logger(f"用户 {request.user.username} 尝试删除非自己创建的Bot: {instance.name}")
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
        
        info_logger(f"用户 {request.user.username} 删除了Bot: {instance.name}")
        instance.delete()
        
        return Response(status=status.HTTP_204_NO_CONTENT)

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

    @extend_schema(
        summary="更新Bot配置",
        description="更新Bot的详细配置，包括模型配置、记忆配置、RAG配置等",
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'prompt': {'type': 'string', 'description': 'Bot的人设与回复逻辑'},
                    'model_config': {
                        'type': 'object',
                        'properties': {
                            'last_model': {'type': 'string', 'description': '问答模型名称'},
                            'last_model_provider': {'type': 'string', 'description': '问答模型提供商'},
                            'last_temperature': {'type': 'number', 'description': '问答模型温度'},
                            'last_max_tokens': {'type': 'integer', 'description': '问答模型最大Token数'},
                            'knowledge_rerank_model': {'type': 'string', 'description': '知识精排模型名称'},
                            'knowledge_rerank_model_provider': {'type': 'string', 'description': '知识精排模型提供商'},
                            'knowledge_rerank_temperature': {'type': 'number', 'description': '知识精排模型温度'},
                            'knowledge_rerank_max_tokens': {'type': 'integer', 'description': '知识精排模型最大Token数'},
                        }
                    },
                    'memory_config': {
                        'type': 'object',
                        'properties': {
                            'max_tokens': {'type': 'integer', 'description': '多轮对话记忆中最大的token数量'}
                        }
                    },
                    'rag_config': {
                        'type': 'object',
                        'properties': {
                            'is_rag': {'type': 'boolean', 'description': '是否开启普通知识的RAG模式'},
                            'retrieve_top_n': {'type': 'integer', 'description': '召回文档数量'},
                            'retrieve_threshold': {'type': 'number', 'description': '召回文档阈值'},
                            'is_rerank': {'type': 'boolean', 'description': '是否开启重排模式'},
                            'rerank_top_n': {'type': 'integer', 'description': '重排数量'},
                            'rerank_threshold': {'type': 'number', 'description': '重排文档阈值'},
                            'is_llm_rerank': {'type': 'boolean', 'description': '是否进行大模型重排操作'},
                            'namespace_list': {'type': 'array', 'items': {'type': 'string'}, 'description': '知识库ID列表'},
                        }
                    },
                    'tool_config': {
                        'type': 'object',
                        'properties': {
                            'is_rag': {'type': 'boolean', 'description': '是否开启工具知识的RAG模式'},
                            'retrieve_top_n': {'type': 'integer', 'description': '召回工具数量'},
                            'retrieve_threshold': {'type': 'number', 'description': '召回工具阈值'},
                            'is_rerank': {'type': 'boolean', 'description': '是否开启重排模式'},
                            'rerank_top_n': {'type': 'integer', 'description': '重排数量'},
                            'rerank_threshold': {'type': 'number', 'description': '重排文档阈值'},
                            'is_llm_rerank': {'type': 'boolean', 'description': '是否进行大模型重排操作'},
                            'max_iterations': {'type': 'integer', 'description': 'Agent的最大迭代次数'},
                            'namespace_list': {'type': 'array', 'items': {'type': 'string'}, 'description': '工具知识库ID列表'},
                        }
                    }
                }
            }
        },
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'message': {'type': 'string'},
                    'config': {'type': 'object', 'description': '更新后的配置'}
                }
            },
            400: {'description': '请求参数错误'},
            403: {'description': '无权限操作'},
            404: {'description': 'Bot不存在'},
            500: {'description': '服务器错误'}
        },
        tags=['Bot管理']
    )
    @action(detail=True, methods=['post'])
    def update_config(self, request, pk=None):
        """
        更新Bot配置
        """
        try:
            bot = self.get_object()
            
            # 检查权限
            if not bot.can_edit(request.user):
                return Response(
                    {'error': '您没有权限编辑此Bot'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            if not bot.assistant_id:
                return Response(
                    {'error': 'Bot未关联LangGraph Assistant'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # 构建LangGraph配置
            config_data = request.data
            langgraph_config = self._build_langgraph_config(config_data, request.user)
            
            # 更新LangGraph Assistant配置
            updated_assistant = langgraph_client.assistants.update(
                assistant_id=bot.assistant_id,
                config=langgraph_config,
            )
            
            info_logger(f"用户 {request.user.username} 更新了Bot配置: {bot.name}")
            
            return Response({
                'message': 'Bot配置更新成功',
                'config': updated_assistant.get('config', {})
            })
            
        except Exception as e:
            error_logger(f"更新Bot配置失败: {str(e)}")
            return Response(
                {'error': f'配置更新失败: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @extend_schema(
        summary="获取Bot配置",
        description="获取Bot的详细配置信息",
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'config': {'type': 'object', 'description': 'Bot配置信息'}
                }
            },
            403: {'description': '无权限操作'},
            404: {'description': 'Bot不存在'},
            500: {'description': '服务器错误'}
        },
        tags=['Bot管理']
    )
    @action(detail=True, methods=['get'])
    def get_config(self, request, pk=None):
        """
        获取Bot配置
        """
        try:
            bot = self.get_object()
            
            # 检查权限
            if not bot.can_access(request.user):
                return Response(
                    {'error': '您没有权限访问此Bot'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            if not bot.assistant_id:
                return Response({
                    'config': self._get_default_config(request.user)
                })
            
            # 从LangGraph获取配置
            assistant = langgraph_client.assistants.get(
                assistant_id=bot.assistant_id
            )
            
            return Response({
                'config': assistant.get('config', {})
            })
            
        except Exception as e:
            error_logger(f"获取Bot配置失败: {str(e)}")
            return Response(
                {'error': f'获取配置失败: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _build_langgraph_config(self, config_data, user):
        """
        构建LangGraph配置
        """
        import os
        from django.utils import timezone
        
        # 基础配置
        base_config = {
            "configurable": {
                "sys_config": {
                    "owner": str(user.id),
                },
                "chat_bot_config": {
                    "prompt": config_data.get('prompt', '你是一个有用的AI助手'),
                },
                "memory_config": {
                    "max_tokens": config_data.get('memory_config', {}).get('max_tokens', 2560),
                },
                "rag_config": {
                    "is_rag": config_data.get('rag_config', {}).get('is_rag', True),
                    "retrieve_top_n": config_data.get('rag_config', {}).get('retrieve_top_n', 5),
                    "retrieve_threshold": config_data.get('rag_config', {}).get('retrieve_threshold', 0.2),
                    "is_rerank": config_data.get('rag_config', {}).get('is_rerank', True),
                    "rerank_top_n": config_data.get('rag_config', {}).get('rerank_top_n', 3),
                    "rerank_threshold": config_data.get('rag_config', {}).get('rerank_threshold', 0.4),
                    "is_llm_rerank": config_data.get('rag_config', {}).get('is_llm_rerank', True),
                    "namespace_list": config_data.get('rag_config', {}).get('namespace_list', []),
                    "is_structured_output": False
                },
                "tool_config": {
                    "is_rag": config_data.get('tool_config', {}).get('is_rag', True),
                    "retrieve_top_n": config_data.get('tool_config', {}).get('retrieve_top_n', 5),
                    "retrieve_threshold": config_data.get('tool_config', {}).get('retrieve_threshold', 0.2),
                    "is_rerank": config_data.get('tool_config', {}).get('is_rerank', True),
                    "rerank_top_n": config_data.get('tool_config', {}).get('rerank_top_n', 3),
                    "rerank_threshold": config_data.get('tool_config', {}).get('rerank_threshold', 0.4),
                    "is_llm_rerank": config_data.get('tool_config', {}).get('is_llm_rerank', True),
                    "max_iterations": config_data.get('tool_config', {}).get('max_iterations', 3),
                    "namespace_list": config_data.get('tool_config', {}).get('namespace_list', []),
                }
            }
        }
        
        # 模型配置
        model_config = config_data.get('model_config', {})
        
        # 问答模型配置
        if 'last_model' in model_config:
            base_config["configurable"]["last_model"] = model_config['last_model']
        if 'last_model_provider' in model_config:
            base_config["configurable"]["last_model_provider"] = model_config['last_model_provider']
        if 'last_temperature' in model_config:
            base_config["configurable"]["last_temperature"] = model_config['last_temperature']
        if 'last_max_tokens' in model_config:
            base_config["configurable"]["last_max_tokens"] = model_config['last_max_tokens']
        
        # 设置默认API配置
        base_config["configurable"]["last_base_url"] = os.getenv('CHAT_MODEL_DEFAULT_BASE_URL', '')
        base_config["configurable"]["last_api_key"] = os.getenv('CHAT_MODEL_DEFAULT_API_KEY', '')
        base_config["configurable"]["last_extra_body"] = {
            "chat_template_kwargs": {
                "enable_thinking": False
            }
        }
        
        # 知识精排模型配置
        if 'knowledge_rerank_model' in model_config:
            base_config["configurable"]["knowledge_rerank_model"] = model_config['knowledge_rerank_model']
        if 'knowledge_rerank_model_provider' in model_config:
            base_config["configurable"]["knowledge_rerank_model_provider"] = model_config['knowledge_rerank_model_provider']
        if 'knowledge_rerank_temperature' in model_config:
            base_config["configurable"]["knowledge_rerank_temperature"] = model_config['knowledge_rerank_temperature']
        if 'knowledge_rerank_max_tokens' in model_config:
            base_config["configurable"]["knowledge_rerank_max_tokens"] = model_config['knowledge_rerank_max_tokens']
        
        # 设置知识精排默认API配置
        base_config["configurable"]["knowledge_rerank_base_url"] = os.getenv('CHAT_MODEL_DEFAULT_BASE_URL', '')
        base_config["configurable"]["knowledge_rerank_api_key"] = os.getenv('CHAT_MODEL_DEFAULT_API_KEY', '')
        base_config["configurable"]["knowledge_rerank_extra_body"] = {
            "chat_template_kwargs": {
                "enable_thinking": False
            }
        }
        
        return base_config

    def _get_default_config(self, user):
        """
        获取默认配置
        """
        import os
        
        return {
            "configurable": {
                "sys_config": {
                    "owner": str(user.id),
                },
                "chat_bot_config": {
                    "prompt": "你是一个有用的AI助手",
                },
                "memory_config": {
                    "max_tokens": 2560,
                },
                "rag_config": {
                    "is_rag": True,
                    "retrieve_top_n": 5,
                    "retrieve_threshold": 0.2,
                    "is_rerank": True,
                    "rerank_top_n": 3,
                    "rerank_threshold": 0.4,
                    "is_llm_rerank": False,
                    "namespace_list": [],
                    "is_structured_output": False
                },
                "tool_config": {
                    "is_rag": True,
                    "retrieve_top_n": 5,
                    "retrieve_threshold": 0.2,
                    "is_rerank": True,
                    "rerank_top_n": 3,
                    "rerank_threshold": 0.4,
                    "is_llm_rerank": False,
                    "max_iterations": 3,
                    "namespace_list": [],
                },
                "last_temperature": 0,
                "last_max_tokens": 5120,
                "last_base_url": os.getenv('CHAT_MODEL_DEFAULT_BASE_URL', ''),
                "last_api_key": os.getenv('CHAT_MODEL_DEFAULT_API_KEY', ''),
                "last_extra_body": {
                    "chat_template_kwargs": {
                        "enable_thinking": False
                    }
                },
                "knowledge_rerank_temperature": 0,
                "knowledge_rerank_max_tokens": 5120,
                "knowledge_rerank_base_url": os.getenv('CHAT_MODEL_DEFAULT_BASE_URL', ''),
                "knowledge_rerank_api_key": os.getenv('CHAT_MODEL_DEFAULT_API_KEY', ''),
                "knowledge_rerank_extra_body": {
                    "chat_template_kwargs": {
                        "enable_thinking": False
                    }
                }
            }
        }

    @extend_schema(
        summary="获取可用模型列表",
        description="获取所有可用的LLM模型列表，用于配置选择",
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'models': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'id': {'type': 'string'},
                                'model_id': {'type': 'string'},
                                'provider': {'type': 'string'},
                                'is_active': {'type': 'boolean'}
                            }
                        }
                    }
                }
            },
            500: {'description': '服务器错误'}
        },
        tags=['Bot管理']
    )
    @action(detail=False, methods=['get'])
    def available_models(self, request):
        """
        获取可用模型列表
        """
        try:
            from provider.models.provider import LLMModel
            
            models = LLMModel.objects.filter(is_active=True).values(
                'id', 'model_id', 'provider', 'is_active'
            )
            
            return Response({
                'models': list(models)
            })
            
        except Exception as e:
            error_logger(f"获取模型列表失败: {str(e)}")
            return Response(
                {'error': f'获取模型列表失败: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @extend_schema(
        summary="获取可用知识库列表",
        description="获取当前用户可访问的知识库列表，用于配置选择",
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'namespaces': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'id': {'type': 'integer'},
                                'name': {'type': 'string'},
                                'description': {'type': 'string'},
                                'can_access': {'type': 'boolean'}
                            }
                        }
                    }
                }
            },
            500: {'description': '服务器错误'}
        },
        tags=['Bot管理']
    )
    @action(detail=False, methods=['get'])
    def available_namespaces(self, request):
        """
        获取可用知识库列表
        """
        try:
            from knowledge.models.namespace import Namespace
            from django.db.models import Q
            
            user = request.user
            
            # 获取用户可访问的知识库
            namespaces = Namespace.objects.filter(
                Q(creator=user) |  # 自己创建的
                Q(collaborators__user=user) |  # 被邀请协作的
                Q(access_type='public')  # 公开的
            ).distinct().filter(is_active=True).values(
                'id', 'name', 'description'
            )
            
            # 添加权限信息
            namespace_list = []
            for ns in namespaces:
                namespace_obj = Namespace.objects.get(id=ns['id'])
                namespace_list.append({
                    'id': ns['id'],
                    'name': ns['name'],
                    'description': ns['description'],
                    'can_access': namespace_obj.can_access(user)
                })
            
            return Response({
                'namespaces': namespace_list
            })
            
        except Exception as e:
            error_logger(f"获取知识库列表失败: {str(e)}")
            return Response(
                {'error': f'获取知识库列表失败: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @extend_schema(
        summary="创建聊天线程",
        description="为Bot创建一个新的聊天线程",
        responses={
            201: {
                'type': 'object',
                'properties': {
                    'thread_id': {'type': 'string', 'description': '线程ID'},
                    'message': {'type': 'string', 'description': '创建结果消息'}
                }
            },
            403: {'description': '无权限操作'},
            404: {'description': 'Bot不存在'},
            500: {'description': '服务器错误'}
        },
        tags=['Bot管理']
    )
    @action(detail=True, methods=['post'])
    def create_thread(self, request, pk=None):
        """
        创建聊天线程
        """
        try:
            bot = self.get_object()
            
            # 检查权限
            if not bot.can_access(request.user):
                return Response(
                    {'error': '您没有权限访问此Bot'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            if not bot.assistant_id:
                return Response(
                    {'error': 'Bot未关联LangGraph Assistant'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # 创建线程
            thread = langgraph_client.threads.create(
                metadata={
                    "assistant_id": bot.assistant_id,
                    "user_id": str(request.user.id),
                    "bot_id": str(bot.id)
                },
                graph_id=GRAPH_ID
            )
            
            info_logger(f"用户 {request.user.username} 为Bot {bot.name} 创建了聊天线程: {thread['thread_id']}")
            
            return Response({
                'thread_id': thread['thread_id'],
                'message': '聊天线程创建成功'
            }, status=status.HTTP_201_CREATED)
            
        except Http404:
            return Response(
                {'error': 'Bot不存在'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            error_logger(f"创建聊天线程失败: {str(e)}")
            return Response(
                {'error': f'创建聊天线程失败: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @extend_schema(
        summary="发送聊天消息",
        description="向Bot发送消息并获取流式回复",
        request=ChatMessageSerializer,
        responses={
            200: {
                'type': 'string',
                'format': 'binary',
                'description': 'Server-Sent Events流式数据'
            },
            400: {'description': '请求参数错误'},
            403: {'description': '无权限操作'},
            404: {'description': 'Bot不存在'},
            500: {'description': '服务器错误'}
        },
        tags=['Bot管理']
    )
    @action(detail=True, methods=['post'])
    def chat(self, request, pk=None):
        """
        与Bot进行聊天对话，支持流式输出
        """
        try:
            bot = self.get_object()
            
            # 检查权限
            if not bot.can_access(request.user):
                return Response(
                    {'error': '您没有权限访问此Bot'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            if not bot.assistant_id:
                return Response(
                    {'error': 'Bot未关联LangGraph Assistant'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # 验证请求数据
            serializer = ChatMessageSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            message = serializer.validated_data['message']
            thread_id = serializer.validated_data.get('thread_id')
            
            # 如果没有提供thread_id，创建新线程
            if not thread_id:
                thread = langgraph_client.threads.create(
                    metadata={
                        "assistant_id": bot.assistant_id,
                        "user_id": str(request.user.id),
                        "bot_id": str(bot.id)
                    },
                    graph_id=GRAPH_ID
                )
                thread_id = thread['thread_id']
                info_logger(f"为用户 {request.user.username} 创建新线程: {thread_id}")
            
            def generate_response():
                """
                生成流式响应
                """
                try:
                    info_logger(f"开始生成流式响应，thread_id: {thread_id}, assistant_id: {bot.assistant_id}")
                    
                    # 发送消息并获取流式响应
                    stream_count = 0
                    for stream_mode, chunk in langgraph_client.runs.stream(
                        thread_id=thread_id,
                        assistant_id=bot.assistant_id,
                        input={"question": message},
                        stream_mode=["messages"]
                    ):
                        stream_count += 1
                        info_logger(f"收到流式数据 #{stream_count}: mode={stream_mode}, chunk={chunk}")
                        
                        if stream_mode == "messages/partial":
                            if chunk and len(chunk) > 0:
                                content = chunk[0].get('content', '')
                                info_logger(f"提取内容: {content}")
                                if content:
                                    # 构造SSE格式的响应
                                    data = {
                                        "thread_id": thread_id,
                                        "message": content,
                                        "is_partial": True,
                                        "is_completed": False
                                    }
                                    yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
                    
                    info_logger(f"流式响应结束，总共收到 {stream_count} 个数据块")
                    
                    # 发送完成标志
                    final_data = {
                        "thread_id": thread_id,
                        "message": "",
                        "is_partial": False,
                        "is_completed": True
                    }
                    yield f"data: {json.dumps(final_data, ensure_ascii=False)}\n\n"
                    
                except Exception as e:
                    error_logger(f"聊天流式响应生成失败: {str(e)}")
                    import traceback
                    error_logger(f"错误详情: {traceback.format_exc()}")
                    error_data = {
                        "thread_id": thread_id,
                        "error": f"聊天失败: {str(e)}",
                        "is_partial": False,
                        "is_completed": True
                    }
                    yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"
            
            info_logger(f"用户 {request.user.username} 向Bot {bot.name} 发送消息: {message[:50]}...")
            
            # 返回流式响应
            response = StreamingHttpResponse(
                generate_response(),
                content_type='text/event-stream'
            )
            response['Cache-Control'] = 'no-cache'
            response['X-Accel-Buffering'] = 'no'  # 禁用nginx缓冲
            response['Access-Control-Allow-Origin'] = '*'
            response['Access-Control-Allow-Headers'] = 'Cache-Control'
            
            return response
            
        except Exception as e:
            error_logger(f"聊天请求处理失败: {str(e)}")
            return Response(
                {'error': f'聊天请求处理失败: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
