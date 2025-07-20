from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from .models import Namespace, Directory, Note
from .serializers import (
    NamespaceSerializer,
    DirectorySerializer,
    DirectoryTreeSerializer,
    NoteSerializer
)


class NamespaceViewSet(viewsets.ModelViewSet):
    queryset = Namespace.objects.all()
    serializer_class = NamespaceSerializer


class DirectoryViewSet(viewsets.ModelViewSet):
    queryset = Directory.objects.select_related('namespace', 'parent')
    serializer_class = DirectorySerializer

    def get_queryset(self):
        # 支持按命名空间过滤
        queryset = super().get_queryset()
        namespace_id = self.request.query_params.get('namespace')
        if namespace_id:
            queryset = queryset.filter(namespace_id=namespace_id)
        return queryset

    @action(detail=False, methods=['GET'], url_path='tree/(?P<namespace_id>[^/.]+)')
    def namespace_tree(self, request, namespace_id=None):
        """获取整个命名空间的目录树"""
        root_dirs = Directory.objects.filter(
            namespace_id=namespace_id,
            parent__isnull=True
        ).prefetch_related('children', 'notes')

        serializer = DirectoryTreeSerializer(root_dirs, many=True)
        return Response(serializer.data)

    @transaction.atomic
    @action(detail=True, methods=['POST'])
    def move(self, request, pk=None):
        """移动目录到新位置"""
        directory = self.get_object()
        new_parent_id = request.data.get('parent_id')

        # 验证新父目录
        new_parent = None
        if new_parent_id:
            try:
                new_parent = Directory.objects.get(id=new_parent_id)
                if new_parent.namespace != directory.namespace:
                    return Response(
                        {"error": "不能跨命名空间移动"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            except Directory.DoesNotExist:
                return Response(
                    {"error": "父目录不存在"},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # 防止循环引用 - 使用高效查询方法
        if new_parent:
            # 方法1：使用内存中的集合（适合层级不深的情况）
            if new_parent.id in directory.get_descendants():
                return Response(
                    {"error": "不能移动到子目录中"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # 方法2：使用数据库查询（适合深度层级）
            # if directory.id in [d.id for d in new_parent.get_descendant_queryset()]:
            #     return Response(...)

            # 防止移动到自身
            if new_parent.id == directory.id:
                return Response(
                    {"error": "不能移动到自身"},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # 执行移动
        directory.parent = new_parent
        directory.save(update_fields=['parent'])

        return Response(DirectorySerializer(directory).data)


class NoteViewSet(viewsets.ModelViewSet):
    queryset = Note.objects.select_related('directory')
    serializer_class = NoteSerializer

    def get_queryset(self):
        # 支持按目录过滤
        queryset = super().get_queryset()
        directory_id = self.request.query_params.get('directory')
        if directory_id:
            queryset = queryset.filter(directory_id=directory_id)
        return queryset

    @action(detail=True, methods=['POST'])
    def move(self, request, pk=None):
        """移动笔记到新目录"""
        note = self.get_object()
        new_directory_id = request.data.get('directory_id')

        try:
            new_directory = Directory.objects.get(id=new_directory_id)
            if new_directory.namespace != note.directory.namespace:
                return Response(
                    {"error": "不能跨命名空间移动笔记"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except Directory.DoesNotExist:
            return Response(
                {"error": "目标目录不存在"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 检查目标目录是否已有同名笔记
        if Note.objects.filter(
                directory=new_directory,
                title=note.title
        ).exclude(id=note.id).exists():
            return Response(
                {"error": "目标目录已存在同名笔记"},
                status=status.HTTP_400_BAD_REQUEST
            )

        note.directory = new_directory
        note.save()

        return Response(NoteSerializer(note).data)