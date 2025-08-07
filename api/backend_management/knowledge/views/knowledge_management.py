import json
import re
import uuid

from django.core.cache import cache
from django.core.files.storage import default_storage
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets, status, permissions, serializers
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response

from core.indexing.index import delete as delete_from_vector_db
from core.models.extractor.tool_generator import tool_generator_llm, tool_generator_examples_to_messages
from core.models.utils import from_examples_to_messages
from core.tool.dynamic_tool import create_dynamic_tool
from llm_api.settings.base import info_logger, error_logger
from ..models import (
    Namespace,
    KnowledgeDocument
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
from ..utils.vector_db_helper import ToolVectorDBWrapper


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
            try:
                instance = self.get_object()
                if instance:
                    if instance.is_tool:
                        return KnowledgeDocumentToolSerializer
                    elif instance.is_form:
                        return KnowledgeDocumentFormSerializer
            except:
                # 如果获取实例失败，使用默认序列化器
                pass
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
        except ValidationError as e:
            error_logger(f"更新文档验证失败: {str(e)}")
            return Response(
                {"error": "数据验证失败", "details": e.detail},
                status=status.HTTP_400_BAD_REQUEST
            )
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
                # 收集要删除的文档列表（用于向量数据库清理）
                documents_to_delete = []

                # 软删除文档及其所有子文档
                def soft_delete_recursive(doc):
                    documents_to_delete.append(doc)
                    doc.is_active = False
                    doc.save()
                    for child in doc.children.filter(is_active=True):
                        soft_delete_recursive(child)

                soft_delete_recursive(document)

                # 异步删除向量数据库内容和清理图片
                self._cleanup_documents_resources(documents_to_delete),

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

    def _cleanup_documents_resources(self, documents):
        """清理文档相关资源（向量数据库和图片）"""
        try:

            for doc in documents:
                # 删除普通文档的向量数据库内容
                if doc.is_document and doc.markdown_content:
                    try:
                        delete_from_vector_db(
                            document_id=str(doc.id),
                            tenant=str(doc.creator.id),
                            namespace=str(doc.namespace.id),
                            knowledge_type="common"
                        )
                        info_logger(f"已从向量数据库删除普通文档: {doc.id}")
                    except Exception as e:
                        error_logger(f"删除普通文档向量数据库内容失败: {str(e)}")

                # 删除工具文档的向量数据库内容
                elif doc.is_tool:
                    try:
                        delete_from_vector_db(
                            document_id=str(doc.id),
                            tenant=str(doc.creator.id),
                            namespace=str(doc.namespace.id),
                            knowledge_type="tool"
                        )
                        info_logger(f"已从向量数据库删除工具文档: {doc.id}")
                    except Exception as e:
                        error_logger(f"删除工具文档向量数据库内容失败: {str(e)}")

                # 清理文档相关图片
                if doc.content:
                    self._cleanup_document_images(doc)

        except Exception as e:
            error_logger(f"清理文档资源失败: {str(e)}")

    def _cleanup_document_images(self, document):
        """清理文档相关图片"""
        try:
            # 提取文档中的图片URL
            image_urls = self._extract_image_urls(document.content)

            for image_url in image_urls:
                # 直接删除图片（文档删除时不再需要引用计数）
                self._delete_cos_image(image_url)
                info_logger(f"已删除文档图片: {image_url}")

        except Exception as e:
            error_logger(f"清理文档图片失败: {str(e)}")

    @staticmethod
    def _extract_image_urls(html_content):
        """从HTML内容中提取图片URL"""
        if not html_content:
            return []

        # 匹配img标签中的src属性，只匹配COS存储的图片
        pattern = r'<img[^>]*src="([^"]*knowledge/[^"]*)"[^>]*>'
        matches = re.findall(pattern, html_content)
        return matches

    @staticmethod
    def _delete_cos_image(image_url):
        """删除COS中的图片"""
        try:
            # 从URL中提取文件路径
            if 'knowledge/' in image_url:
                # 提取路径部分
                path_start = image_url.find('knowledge/')
                file_path = image_url[path_start:]

                # 删除COS文件
                if default_storage.exists(file_path):
                    default_storage.delete(file_path)
                    info_logger(f"已删除COS图片: {file_path}")

        except Exception as e:
            error_logger(f"删除COS图片失败: {str(e)}")

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
        operation_description="执行指定的工具知识，支持JSON、Jinja2模板、HTML模板三种返回格式",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'input_data': openapi.Schema(type=openapi.TYPE_OBJECT, description='输入参数'),
                'output_type': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    enum=['json', 'jinja2', 'html'],
                    description='返回类型：json(原始数据)、jinja2(模板渲染文本)、html(HTML渲染)',
                    default='json'
                )
            },
            required=['input_data']
        ),
        responses={200: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'type': openapi.Schema(type=openapi.TYPE_STRING, description='返回数据类型'),
                'content': openapi.Schema(type=openapi.TYPE_STRING, description='返回内容'),
                'raw_data': openapi.Schema(type=openapi.TYPE_OBJECT, description='原始数据'),
                'execution_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='执行记录ID')
            }
        )}
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

            input_data = request.data.get('input_data', {})
            output_type = request.data.get('output_type', 'json')

            # 获取工具数据
            tool_data = document.get_tool_data()
            if not tool_data:
                return Response(
                    {"error": "工具配置数据不完整"},
                    status=status.HTTP_400_BAD_REQUEST
                )

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

            try:
                # 创建动态工具并执行
                is_jinja2 = output_type == 'jinja2'
                is_html = output_type == 'html'

                tool = create_dynamic_tool(
                    name=tool_data.get('name', ''),
                    description=tool_data.get('description', ''),
                    input_schema=tool_data.get('input_schema', {}),
                    function_code=tool_data.get('extra_params', {}).get('code', ''),
                    output_schema=tool_data.get('output_schema'),
                    jinja2_template=tool_data.get('output_schema_jinja2_template', ''),
                    is_jinja2_template=is_jinja2,
                    html_template=tool_data.get('html_template', ''),
                    is_html_template=is_html
                )

                # 执行工具
                result = tool._run(**input_data)

                # 根据返回类型格式化结果
                if output_type == 'html' and isinstance(result, dict) and result.get('type') == 'html':
                    response_data = {
                        'type': 'html',
                        'content': result.get('content', ''),
                        'raw_data': result.get('raw_data', {}),
                        'execution_id': execution.id
                    }
                elif output_type == 'jinja2' and isinstance(result, str):
                    response_data = {
                        'type': 'jinja2',
                        'content': result,
                        'raw_data': None,
                        'execution_id': execution.id
                    }
                else:
                    # JSON格式或其他格式
                    response_data = {
                        'type': 'json',
                        'content': json.dumps(result, ensure_ascii=False) if not isinstance(result, str) else result,
                        'raw_data': result if not isinstance(result, str) else None,
                        'execution_id': execution.id
                    }

                info_logger(f"用户 {request.user.username} 执行工具: {document.title}, 输出类型: {output_type}")
                return Response(response_data, status=status.HTTP_200_OK)

            except Exception as exec_error:
                error_logger(f"工具执行失败: {str(exec_error)}")
                return Response(
                    {
                        "error": f"工具执行失败: {str(exec_error)}",
                        "execution_id": execution.id
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

        except PermissionDenied:
            raise
        except Exception as e:
            error_logger(f"执行工具失败: {str(e)}")
            return Response(
                {"error": "执行工具失败"},
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

    @swagger_auto_schema(
        operation_summary="上传图片",
        operation_description="为CKEditor上传图片到COS存储",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['upload'],
            properties={
                'upload': openapi.Schema(
                    type=openapi.TYPE_FILE,
                    description='要上传的图片文件'
                )
            }
        ),
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'url': openapi.Schema(type=openapi.TYPE_STRING, description='图片URL')
                }
            )
        }
    )
    @action(detail=False, methods=['post'])
    def upload_image(self, request, namespace_pk=None):
        """上传图片"""
        try:
            namespace = self.get_namespace()

            if 'upload' not in request.FILES:
                return Response(
                    {"error": "没有上传文件"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            uploaded_file = request.FILES['upload']

            # 验证文件类型
            allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
            if uploaded_file.content_type not in allowed_types:
                return Response(
                    {"error": "不支持的图片格式"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # 验证文件大小（5MB）
            if uploaded_file.size > 5 * 1024 * 1024:
                return Response(
                    {"error": "文件大小不能超过5MB"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # 生成文件名
            file_extension = uploaded_file.name.split('.')[-1]
            file_name = f"{uuid.uuid4().hex}.{file_extension}"
            file_path = f"knowledge/{namespace_pk}/images/{file_name}"

            # 保存文件到COS
            file_url = default_storage.save(file_path, uploaded_file)
            full_url = default_storage.url(file_url)

            info_logger(f"用户 {request.user.username} 上传图片: {file_path}")
            return Response({"url": full_url})

        except Exception as e:
            error_logger(f"上传图片失败: {str(e)}")
            return Response(
                {"error": "上传图片失败"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
        operation_summary="AI智能生成工具",
        operation_description="根据用户描述通过AI智能生成工具知识。注意：AI生成过程可能需要1-3分钟，请耐心等待。",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'description': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='工具功能描述，用于AI生成工具（最多30000字符）',
                    example='请帮我生成一个请假的工具，输入请假天数和开始日期即可'
                ),
                'title': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='工具标题（可选）',
                    example='请假工具'
                ),
                'parent_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='父文档ID（可选）')
            },
            required=['description']
        ),
        responses={
            201: KnowledgeDocumentToolSerializer,
            408: openapi.Response(description="请求超时，AI生成时间过长"),
            500: openapi.Response(description="AI生成失败，请稍后重试")
        }
    )
    @action(detail=False, methods=['post'])
    def generate_tool_by_ai(self, request, namespace_pk=None):
        """AI智能生成工具"""
        try:
            namespace = self.get_namespace()
            description = request.data.get('description', '').strip()

            if not description:
                return Response(
                    {"error": "请提供工具功能描述"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # 验证描述长度
            if len(description) > 30000:
                return Response(
                    {"error": "工具功能描述不能超过30000个字符"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # 从Redis获取LLM配置
            try:
                config_json = json.loads(cache.get('code_model'))
                if not config_json:
                    return Response(
                        {"error": "AI服务配置未找到，请联系管理员"},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
            except (TypeError, json.JSONDecodeError):
                return Response(
                    {"error": "AI服务配置格式错误，请联系管理员"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            # 调用AI生成工具
            try:
                info_logger(f"用户 {request.user.username} 开始AI生成工具，描述: {description}")

                messages = from_examples_to_messages(
                    user_question=description,
                    examples=tool_generator_examples_to_messages
                )

                try:
                    ai_result = tool_generator_llm.invoke(
                        messages,
                        config={
                            "configurable": config_json
                        }
                    )
                except TimeoutError:
                    raise TimeoutError("AI生成超时，请稍后重试")

                info_logger(f"AI生成工具成功，用户: {request.user.username}, 工具名: {ai_result.tool_name}")

                # 构建工具数据
                tool_data = {
                    'name': ai_result.tool_name,
                    'description': ai_result.description,
                    'input_schema': ai_result.input_schema.dict(),
                    'output_schema': ai_result.output_schema.dict(),
                    'output_schema_jinja2_template': ai_result.output_schema_jinja2_template,
                    'html_template': ai_result.html_template,
                    'few_shots': ai_result.few_shots,
                    'tool_type': 'dynamic',
                    'extra_params': {
                        'code': ai_result.function_code
                    }
                }

                # 创建工具知识文档
                document_data = {
                    'title': request.data.get('title', ai_result.tool_name),
                    'content': f"AI生成的工具：{ai_result.description}",
                    'summary': ai_result.description,
                    'doc_type': 'tool',
                    'namespace': namespace.id,
                    'creator': request.user.id,
                    'last_editor': request.user.id,
                    'tool_data': tool_data
                }

                # 设置父文档
                parent_id = request.data.get('parent_id')
                if parent_id:
                    try:
                        parent = KnowledgeDocument.objects.get(
                            id=parent_id,
                            namespace=namespace,
                            is_active=True
                        )
                        document_data['parent'] = parent.id
                    except KnowledgeDocument.DoesNotExist:
                        return Response(
                            {"error": "指定的父文档不存在"},
                            status=status.HTTP_400_BAD_REQUEST
                        )

                # 创建文档
                serializer = KnowledgeDocumentToolSerializer(
                    data=document_data,
                    context=self.get_serializer_context()
                )
                serializer.is_valid(raise_exception=True)
                document = serializer.save()

                # 异步添加到向量数据库
                try:
                    ToolVectorDBWrapper.add_tool_to_vector_db(document, tool_data, request.user)
                    info_logger(f"工具已添加到向量数据库: {document.title}")
                except Exception as vector_error:
                    error_logger(f"添加工具到向量数据库失败: {str(vector_error)}")
                    # 不影响主流程，只记录错误

                info_logger(f"用户 {request.user.username} 通过AI生成工具: {document.title}")
                return Response(serializer.data, status=status.HTTP_201_CREATED)

            except TimeoutError as timeout_error:
                error_logger(f"AI生成工具超时: {str(timeout_error)}")
                return Response(
                    {"error": "AI生成超时，请稍后重试。如果问题持续存在，请检查网络连接或联系管理员。"},
                    status=status.HTTP_408_REQUEST_TIMEOUT
                )
            except Exception as ai_error:
                error_logger(f"AI生成工具失败: {str(ai_error)}")
                return Response(
                    {"error": f"AI生成工具失败: {str(ai_error)}。请检查描述是否清晰，或稍后重试。"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        except Exception as e:
            error_logger(f"生成工具失败: {str(e)}")
            return Response(
                {"error": "生成工具失败"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
