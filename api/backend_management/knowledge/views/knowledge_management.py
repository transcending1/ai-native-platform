from rest_framework import viewsets, status, permissions, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import NotFound, PermissionDenied
from django.shortcuts import get_object_or_404
from django.db.models import Q, F
from django.db import transaction
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from ..models import (
    Namespace,
    KnowledgeDocument,
    FormDataEntry,
    ToolExecution
)
from ..serializers import (
    KnowledgeDocumentListSerializer,
    KnowledgeDocumentDetailSerializer,
    KnowledgeDocumentTreeSerializer,
    KnowledgeDocumentCreateSerializer,
    KnowledgeDocumentMoveSerializer,
    KnowledgeDocumentToolSerializer,
    KnowledgeDocumentFormSerializer,
    FormDataEntrySerializer,
    ToolExecutionSerializer
)
from llm_api.settings.base import info_logger, error_logger


class KnowledgeBaseViewSet(viewsets.GenericViewSet):
    """
    知识管理基础视图集 - 提供公共方法
    """
    permission_classes = [permissions.IsAuthenticated]

    def get_namespace(self):
        """获取知识库对象"""
        namespace_pk = self.kwargs.get('namespace_pk')
        namespace = get_object_or_404(Namespace, id=namespace_pk, is_active=True)
        
        # 检查访问权限
        if not namespace.can_access(self.request.user):
            raise PermissionDenied("您没有访问此知识库的权限")
        
        return namespace

    def check_edit_permission(self, namespace):
        """检查编辑权限"""
        if not namespace.can_edit(self.request.user):
            raise PermissionDenied("您没有编辑此知识库的权限")

    def get_serializer_context(self):
        """获取序列化器上下文"""
        context = super().get_serializer_context()
        if hasattr(self, 'kwargs') and 'namespace_pk' in self.kwargs:
            context['namespace_pk'] = self.kwargs['namespace_pk']
        return context


class KnowledgeDocumentViewSet(KnowledgeBaseViewSet):
    """
    知识文档视图集
    """
    
    def get_queryset(self):
        """获取文档查询集"""
        namespace = self.get_namespace()
        return KnowledgeDocument.objects.filter(
            namespace=namespace,
            is_active=True
        ).select_related('creator', 'last_editor', 'parent')

    def get_serializer_class(self):
        """根据操作和文档类型选择序列化器"""
        if self.action == 'list':
            return KnowledgeDocumentListSerializer
        elif self.action == 'tree':
            return KnowledgeDocumentTreeSerializer
        elif self.action == 'create':
            # 根据请求数据中的doc_type选择创建序列化器
            doc_type = getattr(self.request, 'data', {}).get('doc_type', 'document')
            if doc_type == 'tool':
                return KnowledgeDocumentToolSerializer
            elif doc_type == 'form':
                return KnowledgeDocumentFormSerializer
            else:
                return KnowledgeDocumentCreateSerializer
        elif self.action == 'move':
            return KnowledgeDocumentMoveSerializer
        elif self.action in ['retrieve', 'update', 'partial_update']:
            # 根据实例的类型选择序列化器
            instance = getattr(self, 'get_object', lambda: None)()
            if instance:
                if instance.is_tool:
                    return KnowledgeDocumentToolSerializer
                elif instance.is_form:
                    return KnowledgeDocumentFormSerializer
            return KnowledgeDocumentDetailSerializer
        else:
            return KnowledgeDocumentDetailSerializer

    def get_serializer_context(self):
        """获取序列化器上下文"""
        context = super().get_serializer_context()
        if self.action == 'move' and hasattr(self, 'get_object'):
            try:
                context['document'] = self.get_object()
            except:
                pass
        return context

    @swagger_auto_schema(
        operation_summary="获取知识文档列表",
        operation_description="获取指定知识库的文档列表，支持分页和搜索",
        manual_parameters=[
            openapi.Parameter('parent_id', openapi.IN_QUERY, description="父文档ID", type=openapi.TYPE_INTEGER),
            openapi.Parameter('search', openapi.IN_QUERY, description="搜索关键词", type=openapi.TYPE_STRING),
            openapi.Parameter('doc_type', openapi.IN_QUERY, description="文档类型", type=openapi.TYPE_STRING),
        ],
        responses={200: KnowledgeDocumentListSerializer(many=True)}
    )
    def list(self, request, namespace_pk=None):
        """获取文档列表"""
        try:
            queryset = self.get_queryset()
            
            # 过滤父文档
            parent_id = request.query_params.get('parent_id')
            if parent_id:
                if parent_id == '0':  # 根目录
                    queryset = queryset.filter(parent__isnull=True)
                else:
                    queryset = queryset.filter(parent_id=parent_id)
            
            # 搜索
            search = request.query_params.get('search')
            if search:
                queryset = queryset.filter(
                    Q(title__icontains=search) |
                    Q(content__icontains=search) |
                    Q(summary__icontains=search)
                )
            
            # 文档类型过滤
            doc_type = request.query_params.get('doc_type')
            if doc_type:
                queryset = queryset.filter(doc_type=doc_type)
            
            # 排序
            queryset = queryset.order_by('sort_order', 'title')
            
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)
        except Exception as e:
            error_logger(f"获取文档列表失败: {str(e)}")
            return Response(
                {"error": "获取文档列表失败"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
        operation_summary="获取文档详情",
        operation_description="获取指定文档的详细信息",
        responses={200: KnowledgeDocumentDetailSerializer}
    )
    def retrieve(self, request, namespace_pk=None, pk=None):
        """获取文档详情"""
        try:
            namespace = self.get_namespace()
            document = get_object_or_404(
                KnowledgeDocument,
                id=pk,
                namespace=namespace,
                is_active=True
            )
            
            # 检查访问权限
            if not document.can_access(request.user):
                raise PermissionDenied("您没有访问此文档的权限")
            
            serializer = self.get_serializer(document)
            return Response(serializer.data)
        except PermissionDenied:
            raise
        except Exception as e:
            error_logger(f"获取文档详情失败: {str(e)}")
            return Response(
                {"error": "获取文档详情失败"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
        operation_summary="创建知识文档",
        operation_description="在指定知识库中创建新的文档或文件夹",
        request_body=KnowledgeDocumentCreateSerializer,
        responses={201: KnowledgeDocumentDetailSerializer}
    )
    def create(self, request, namespace_pk=None):
        """创建文档"""
        try:
            namespace = self.get_namespace()
            self.check_edit_permission(namespace)
            
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            document = serializer.save()
            
            # 返回详细信息
            detail_serializer = KnowledgeDocumentDetailSerializer(
                document, 
                context=self.get_serializer_context()
            )
            
            info_logger(f"用户 {request.user.username} 在知识库 {namespace_pk} 创建文档: {document.title}")
            return Response(detail_serializer.data, status=status.HTTP_201_CREATED)
        except PermissionDenied:
            raise
        except serializers.ValidationError as e:
            # 序列化器验证错误，返回400状态码
            error_logger(f"创建文档验证失败: {str(e)}")
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            error_logger(f"创建文档失败: {str(e)}")
            return Response(
                {"error": "创建文档失败"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
        operation_summary="更新知识文档",
        operation_description="更新指定文档的信息",
        request_body=KnowledgeDocumentDetailSerializer,
        responses={200: KnowledgeDocumentDetailSerializer}
    )
    def update(self, request, namespace_pk=None, pk=None):
        """更新文档"""
        try:
            namespace = self.get_namespace()
            document = get_object_or_404(
                KnowledgeDocument,
                id=pk,
                namespace=namespace,
                is_active=True
            )
            
            # 检查编辑权限
            if not document.can_edit(request.user):
                raise PermissionDenied("您没有编辑此文档的权限")
            
            serializer = self.get_serializer(document, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            
            info_logger(f"用户 {request.user.username} 更新文档: {document.title}")
            return Response(serializer.data)
        except PermissionDenied:
            raise
        except Exception as e:
            error_logger(f"更新文档失败: {str(e)}")
            return Response(
                {"error": "更新文档失败"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
        operation_summary="删除知识文档",
        operation_description="删除指定的文档或文件夹",
        responses={204: "删除成功"}
    )
    def destroy(self, request, namespace_pk=None, pk=None):
        """删除文档"""
        try:
            namespace = self.get_namespace()
            document = get_object_or_404(
                KnowledgeDocument,
                id=pk,
                namespace=namespace,
                is_active=True
            )
            
            # 检查编辑权限
            if not document.can_edit(request.user):
                raise PermissionDenied("您没有删除此文档的权限")
            
            with transaction.atomic():
                # 软删除文档及其所有子文档
                def soft_delete_recursive(doc):
                    doc.is_active = False
                    doc.save()
                    for child in doc.children.filter(is_active=True):
                        soft_delete_recursive(child)
                
                soft_delete_recursive(document)
            
            info_logger(f"用户 {request.user.username} 删除文档: {document.title}")
            return Response(status=status.HTTP_204_NO_CONTENT)
        except PermissionDenied:
            raise
        except Exception as e:
            error_logger(f"删除文档失败: {str(e)}")
            return Response(
                {"error": "删除文档失败"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
        operation_summary="获取文档树",
        operation_description="获取知识库的文档树形结构",
        responses={200: KnowledgeDocumentTreeSerializer(many=True)}
    )
    @action(detail=False, methods=['get'])
    def tree(self, request, namespace_pk=None):
        """获取文档树"""
        try:
            namespace = self.get_namespace()
            
            # 获取根级文档
            root_documents = KnowledgeDocument.objects.filter(
                namespace=namespace,
                parent__isnull=True,
                is_active=True
            ).order_by('sort_order', 'title')
            
            serializer = self.get_serializer(root_documents, many=True)
            return Response(serializer.data)
        except Exception as e:
            error_logger(f"获取文档树失败: {str(e)}")
            return Response(
                {"error": "获取文档树失败"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
        operation_summary="移动文档",
        operation_description="移动文档到指定位置",
        request_body=KnowledgeDocumentMoveSerializer,
        responses={200: "移动成功"}
    )
    @action(detail=True, methods=['post'])
    def move(self, request, namespace_pk=None, pk=None):
        """移动文档"""
        try:
            namespace = self.get_namespace()
            document = get_object_or_404(
                KnowledgeDocument,
                id=pk,
                namespace=namespace,
                is_active=True
            )
            
            # 检查编辑权限
            if not document.can_edit(request.user):
                raise PermissionDenied("您没有移动此文档的权限")
            
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            # 执行移动
            target_parent = serializer.validated_data.get('target_parent_id')
            sort_order = serializer.validated_data.get('sort_order', 0)
            
            document.parent = target_parent
            document.sort_order = sort_order
            document.save()
            
            info_logger(f"用户 {request.user.username} 移动文档: {document.title}")
            return Response({"message": "移动成功"})
        except PermissionDenied:
            raise
        except Exception as e:
            error_logger(f"移动文档失败: {str(e)}")
            return Response(
                {"error": "移动文档失败"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
        operation_summary="执行工具",
        operation_description="执行指定的工具知识",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'input_data': openapi.Schema(type=openapi.TYPE_OBJECT, description='输入参数')
            },
            required=['input_data']
        ),
        responses={200: ToolExecutionSerializer}
    )
    @action(detail=True, methods=['post'])
    def execute_tool(self, request, namespace_pk=None, pk=None):
        """执行工具"""
        try:
            namespace = self.get_namespace()
            document = get_object_or_404(
                KnowledgeDocument,
                id=pk,
                namespace=namespace,
                is_active=True,
                doc_type='tool'
            )

            # 检查访问权限
            if not document.can_access(request.user):
                raise PermissionDenied("您没有访问此工具的权限")

            # 创建执行记录
            serializer = ToolExecutionSerializer(
                data=request.data,
                context={
                    'request': request,
                    'tool_document_id': document.id
                }
            )
            serializer.is_valid(raise_exception=True)
            execution = serializer.save()

            # TODO: 这里可以添加实际的工具执行逻辑
            # 目前只是创建执行记录，实际执行逻辑需要根据具体需求实现

            info_logger(f"用户 {request.user.username} 执行工具: {document.title}")
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except PermissionDenied:
            raise
        except Exception as e:
            error_logger(f"执行工具失败: {str(e)}")
            return Response(
                {"error": "执行工具失败"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
        operation_summary="获取工具执行历史",
        operation_description="获取指定工具的执行历史记录",
        responses={200: ToolExecutionSerializer(many=True)}
    )
    @action(detail=True, methods=['get'])
    def tool_executions(self, request, namespace_pk=None, pk=None):
        """获取工具执行历史"""
        try:
            namespace = self.get_namespace()
            document = get_object_or_404(
                KnowledgeDocument,
                id=pk,
                namespace=namespace,
                is_active=True,
                doc_type='tool'
            )

            # 检查访问权限
            if not document.can_access(request.user):
                raise PermissionDenied("您没有访问此工具的权限")

            executions = document.tool_executions.all()
            serializer = ToolExecutionSerializer(executions, many=True)
            return Response(serializer.data)

        except PermissionDenied:
            raise
        except Exception as e:
            error_logger(f"获取工具执行历史失败: {str(e)}")
            return Response(
                {"error": "获取工具执行历史失败"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
        operation_summary="提交表单数据",
        operation_description="向指定表单知识提交数据",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'data': openapi.Schema(type=openapi.TYPE_OBJECT, description='表单数据')
            },
            required=['data']
        ),
        responses={201: FormDataEntrySerializer}
    )
    @action(detail=True, methods=['post'])
    def submit_form_data(self, request, namespace_pk=None, pk=None):
        """提交表单数据"""
        try:
            namespace = self.get_namespace()
            document = get_object_or_404(
                KnowledgeDocument,
                id=pk,
                namespace=namespace,
                is_active=True,
                doc_type='form'
            )

            # 检查访问权限
            if not document.can_access(request.user):
                raise PermissionDenied("您没有访问此表单的权限")

            # 创建表单数据条目
            serializer = FormDataEntrySerializer(
                data=request.data,
                context={
                    'request': request,
                    'form_document_id': document.id
                }
            )
            serializer.is_valid(raise_exception=True)
            entry = serializer.save()

            info_logger(f"用户 {request.user.username} 提交表单数据: {document.title}")
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except PermissionDenied:
            raise
        except Exception as e:
            error_logger(f"提交表单数据失败: {str(e)}")
            return Response(
                {"error": "提交表单数据失败"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
        operation_summary="获取表单数据",
        operation_description="获取指定表单的所有数据条目",
        responses={200: FormDataEntrySerializer(many=True)}
    )
    @action(detail=True, methods=['get'])
    def form_data(self, request, namespace_pk=None, pk=None):
        """获取表单数据"""
        try:
            namespace = self.get_namespace()
            document = get_object_or_404(
                KnowledgeDocument,
                id=pk,
                namespace=namespace,
                is_active=True,
                doc_type='form'
            )

            # 检查访问权限
            if not document.can_access(request.user):
                raise PermissionDenied("您没有访问此表单的权限")

            entries = document.form_entries.all()
            serializer = FormDataEntrySerializer(entries, many=True)
            return Response(serializer.data)

        except PermissionDenied:
            raise
        except Exception as e:
            error_logger(f"获取表单数据失败: {str(e)}")
            return Response(
                {"error": "获取表单数据失败"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            ) 