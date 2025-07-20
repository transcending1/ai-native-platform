from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from django.http import Http404
from django.db.models import Q
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

from user.models.knowledge_base import KnowledgeBase, Document, KnowledgeBaseCollaborator
from user.models.book_manager import User
from user.serializers.knowledge_base import (
    KnowledgeBaseSerializer,
    KnowledgeBaseCreateSerializer,
    KnowledgeBaseUpdateSerializer,
    KnowledgeBaseListSerializer,
    KnowledgeBaseSettingsSerializer,
    DocumentSerializer,
    DocumentCreateSerializer,
    DocumentUpdateSerializer,
    KnowledgeBaseCollaboratorSerializer,
    KnowledgeBaseCollaboratorCreateSerializer
)


class KnowledgeBasePagination(PageNumberPagination):
    """知识库分页器"""
    page_size = 10
    page_size_query_param = 'size'
    max_page_size = 100


class KnowledgeBaseViewSet(viewsets.ModelViewSet):
    """知识库管理视图集"""
    queryset = KnowledgeBase.objects.all().order_by('-updated_time')
    pagination_class = KnowledgeBasePagination
    filterset_fields = ['name', 'owner', 'doc_width', 'enable_comments']
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    
    def get_queryset(self):
        """根据用户权限过滤知识库"""
        user = self.request.user
        if not user.is_authenticated:
            return KnowledgeBase.objects.none()
        
        # 获取用户的自定义User对象
        try:
            custom_user = User.objects.get(email=user.email)
        except User.DoesNotExist:
            return KnowledgeBase.objects.none()
        
        # 返回用户拥有的和作为协作者的知识库
        return KnowledgeBase.objects.filter(
            Q(owner=custom_user) | 
            Q(collaborators__user=custom_user, collaborators__is_active=True)
        ).distinct()
    
    def get_serializer_class(self):
        """根据不同的action返回不同的序列化器"""
        if self.action == 'create':
            return KnowledgeBaseCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return KnowledgeBaseUpdateSerializer
        elif self.action == 'list':
            return KnowledgeBaseListSerializer
        elif self.action == 'update_settings':
            return KnowledgeBaseSettingsSerializer
        return KnowledgeBaseSerializer
    
    def create(self, request, *args, **kwargs):
        """
        创建知识库
        参数：名称（name）、描述（desc，选填）、封面图片等
        功能：创建新的知识库
        """
        serializer = self.get_serializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            knowledge_base = serializer.save()
            return Response({
                'success': True,
                'message': '知识库创建成功',
                'data': {
                    'kbId': knowledge_base.id,
                    'name': knowledge_base.name,
                    'desc': knowledge_base.desc,
                    'cover_image': knowledge_base.cover_image,
                    'owner': knowledge_base.owner.name,
                    'created_time': knowledge_base.created_time
                }
            }, status=status.HTTP_201_CREATED)
        else:
            return Response({
                'success': False,
                'message': '知识库创建失败',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
    
    def list(self, request, *args, **kwargs):
        """
        查询知识库列表
        参数：分页参数（page、size）
        功能：返回知识库列表，包含 kbId、名称、更新时间、文档数量等信息
        """
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            paginated_response = self.get_paginated_response(serializer.data)
            return Response({
                'success': True,
                'message': '获取知识库列表成功',
                'data': {
                    'results': paginated_response.data['results'],
                    'count': paginated_response.data['count'],
                    'next': paginated_response.data['next'],
                    'previous': paginated_response.data['previous']
                }
            })
        
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'success': True,
            'message': '获取知识库列表成功',
            'data': serializer.data
        })
    
    def retrieve(self, request, *args, **kwargs):
        """获取单个知识库详情"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            'success': True,
            'message': '获取知识库详情成功',
            'data': serializer.data
        })
    
    def update(self, request, *args, **kwargs):
        """
        更新知识库信息
        参数：kbId（路径参数）、需更新字段（如名称name、描述desc、封面等）
        功能：修改知识库基本信息，返回更新成功标识
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        # 检查权限：只有拥有者和有编辑权限的协作者可以更新
        if not self._check_edit_permission(request.user, instance):
            return Response({
                'success': False,
                'message': '没有权限修改此知识库'
            }, status=status.HTTP_403_FORBIDDEN)
        
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        
        if serializer.is_valid():
            updated_instance = serializer.save()
            return Response({
                'success': True,
                'message': '知识库更新成功',
                'data': {
                    'kbId': updated_instance.id,
                    'name': updated_instance.name,
                    'desc': updated_instance.desc,
                    'cover_image': updated_instance.cover_image,
                    'updated_time': updated_instance.updated_time
                }
            })
        else:
            return Response({
                'success': False,
                'message': '知识库更新失败',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
    
    def partial_update(self, request, *args, **kwargs):
        """部分更新知识库信息"""
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        """
        删除知识库
        参数：kbId（路径参数）
        功能：删除指定知识库，返回删除结果
        """
        try:
            instance = self.get_object()
            
            # 检查权限：只有拥有者可以删除
            if not self._check_owner_permission(request.user, instance):
                return Response({
                    'success': False,
                    'message': '只有知识库拥有者可以删除知识库'
                }, status=status.HTTP_403_FORBIDDEN)
            
            kb_id = instance.id
            kb_name = instance.name
            
            # 检查是否有关联的文档
            document_count = instance.document_count
            
            # 执行删除操作
            instance.delete()
            
            return Response({
                'success': True,
                'message': f'知识库 "{kb_name}" 删除成功',
                'data': {
                    'kbId': kb_id,
                    'deleted_documents': document_count
                }
            }, status=status.HTTP_200_OK)
            
        except Http404:
            return Response({
                'success': False,
                'message': '知识库不存在'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'success': False,
                'message': f'删除知识库失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['post'])
    def upload_cover(self, request, pk=None):
        """
        上传知识库封面
        """
        knowledge_base = self.get_object()
        
        # 检查权限
        if not self._check_edit_permission(request.user, knowledge_base):
            return Response({
                'success': False,
                'message': '没有权限修改此知识库'
            }, status=status.HTTP_403_FORBIDDEN)
        
        cover_image = request.FILES.get('cover_image')
        if not cover_image:
            return Response({
                'success': False,
                'message': '请选择要上传的图片文件'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 使用腾讯云COS上传服务
        from user.utils.cos_storage import cos_upload_service
        
        try:
            # 删除旧的封面图片
            if knowledge_base.cover_image:
                # 从URL中提取文件路径
                old_path = knowledge_base.cover_image.split('/')[-4:]  # 提取路径部分
                if len(old_path) >= 4:
                    old_file_path = '/'.join(old_path)
                    cos_upload_service.delete_image(old_file_path)
            
            # 上传新的封面图片
            upload_result = cos_upload_service.upload_image(
                cover_image, 
                folder='knowledge-base-covers'
            )
            
            if upload_result['success']:
                knowledge_base.cover_image = upload_result['url']
                knowledge_base.save()
                
                return Response({
                    'success': True,
                    'message': upload_result['message'],
                    'data': {
                        'cover_image': upload_result['url']
                    }
                })
            else:
                return Response({
                    'success': False,
                    'message': upload_result['message']
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            return Response({
                'success': False,
                'message': f'封面上传失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['patch'])
    def update_settings(self, request, pk=None):
        """
        更新知识库设置
        """
        knowledge_base = self.get_object()
        
        # 检查权限
        if not self._check_edit_permission(request.user, knowledge_base):
            return Response({
                'success': False,
                'message': '没有权限修改此知识库'
            }, status=status.HTTP_403_FORBIDDEN)
        
        serializer = self.get_serializer(knowledge_base, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'success': True,
                'message': '设置更新成功',
                'data': serializer.data
            })
        else:
            return Response({
                'success': False,
                'message': '设置更新失败',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get', 'post'])
    def collaborators(self, request, pk=None):
        """
        管理知识库协作者
        GET: 获取协作者列表
        POST: 添加协作者
        """
        knowledge_base = self.get_object()
        
        if request.method == 'GET':
            collaborators = knowledge_base.collaborators.filter(is_active=True)
            serializer = KnowledgeBaseCollaboratorSerializer(collaborators, many=True)
            return Response({
                'success': True,
                'message': '获取协作者列表成功',
                'data': serializer.data
            })
        
        elif request.method == 'POST':
            # 检查权限：只有拥有者可以添加协作者
            if not self._check_owner_permission(request.user, knowledge_base):
                return Response({
                    'success': False,
                    'message': '只有知识库拥有者可以添加协作者'
                }, status=status.HTTP_403_FORBIDDEN)
            
            serializer = KnowledgeBaseCollaboratorCreateSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save(knowledge_base=knowledge_base)
                return Response({
                    'success': True,
                    'message': '协作者添加成功',
                    'data': serializer.data
                }, status=status.HTTP_201_CREATED)
            else:
                return Response({
                    'success': False,
                    'message': '添加协作者失败',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['patch', 'delete'], url_path='collaborators/(?P<collaborator_id>[^/.]+)')
    def manage_collaborator(self, request, pk=None, collaborator_id=None):
        """
        管理单个协作者
        PATCH: 更新协作者权限
        DELETE: 移除协作者
        """
        knowledge_base = self.get_object()
        
        # 检查权限：只有拥有者可以管理协作者
        if not self._check_owner_permission(request.user, knowledge_base):
            return Response({
                'success': False,
                'message': '只有知识库拥有者可以管理协作者'
            }, status=status.HTTP_403_FORBIDDEN)
        
        try:
            collaborator = knowledge_base.collaborators.get(id=collaborator_id)
        except KnowledgeBaseCollaborator.DoesNotExist:
            return Response({
                'success': False,
                'message': '协作者不存在'
            }, status=status.HTTP_404_NOT_FOUND)
        
        if request.method == 'PATCH':
            serializer = KnowledgeBaseCollaboratorSerializer(
                collaborator, data=request.data, partial=True
            )
            if serializer.is_valid():
                serializer.save()
                return Response({
                    'success': True,
                    'message': '协作者权限更新成功',
                    'data': serializer.data
                })
            else:
                return Response({
                    'success': False,
                    'message': '更新失败',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
        
        elif request.method == 'DELETE':
            collaborator_name = collaborator.user.name
            collaborator.delete()
            return Response({
                'success': True,
                'message': f'协作者 "{collaborator_name}" 已移除'
            })
    
    @action(detail=False, methods=['post'], url_path='accept-invite/(?P<invite_token>[^/.]+)')
    def accept_invite(self, request, invite_token=None):
        """
        接受协作邀请
        """
        try:
            collaborator = KnowledgeBaseCollaborator.objects.get(
                invite_token=invite_token,
                is_active=True,
                accepted_at__isnull=True
            )
        except KnowledgeBaseCollaborator.DoesNotExist:
            return Response({
                'success': False,
                'message': '邀请链接无效或已过期'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # 验证当前用户是否是被邀请的用户
        user = request.user
        try:
            custom_user = User.objects.get(email=user.email)
        except User.DoesNotExist:
            return Response({
                'success': False,
                'message': '用户不存在'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if collaborator.user != custom_user:
            return Response({
                'success': False,
                'message': '该邀请不是发给您的'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # 接受邀请
        from django.utils import timezone
        collaborator.accepted_at = timezone.now()
        collaborator.save()
        
        return Response({
            'success': True,
            'message': '成功加入知识库',
            'data': {
                'knowledge_base_name': collaborator.knowledge_base.name,
                'permission': collaborator.get_permission_display()
            }
        })
    
    def _check_owner_permission(self, user, knowledge_base):
        """检查是否是知识库拥有者"""
        try:
            custom_user = User.objects.get(email=user.email)
            return knowledge_base.owner == custom_user
        except User.DoesNotExist:
            return False
    
    def _check_edit_permission(self, user, knowledge_base):
        """检查是否有编辑权限（拥有者或有编辑权限的协作者）"""
        try:
            custom_user = User.objects.get(email=user.email)
            # 检查是否是拥有者
            if knowledge_base.owner == custom_user:
                return True
            # 检查是否是有编辑权限的协作者
            return knowledge_base.collaborators.filter(
                user=custom_user,
                permission='edit',
                is_active=True
            ).exists()
        except User.DoesNotExist:
            return False


class DocumentViewSet(viewsets.ModelViewSet):
    """文档管理视图集"""
    queryset = Document.objects.all().order_by('position', '-updated_time')
    filterset_fields = ['knowledge_base', 'title', 'file_type', 'is_published'] 
    
    def get_serializer_class(self):
        """根据不同的action返回不同的序列化器"""
        if self.action == 'create':
            return DocumentCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return DocumentUpdateSerializer
        return DocumentSerializer 