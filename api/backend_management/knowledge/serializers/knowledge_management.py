import base64
import re
import uuid

import html2text
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from rest_framework import serializers

from ..models import (
    KnowledgeDocument,
    FormDataEntry,
    ToolExecution
)

User = get_user_model()


class UserSimpleSerializer(serializers.ModelSerializer):
    """
    用户简单信息序列化器
    """

    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'avatar']
        read_only_fields = fields


class KnowledgeDocumentListSerializer(serializers.ModelSerializer):
    """
    知识文档列表序列化器 - 用于列表显示
    """
    creator = UserSimpleSerializer(read_only=True)
    last_editor = UserSimpleSerializer(read_only=True)
    children_count = serializers.SerializerMethodField()
    breadcrumbs = serializers.ReadOnlyField()
    depth = serializers.ReadOnlyField()

    class Meta:
        model = KnowledgeDocument
        fields = [
            'id', 'title', 'summary', 'doc_type', 'status',
            'sort_order', 'is_public', 'is_active',
            'created_at', 'updated_at', 'creator', 'last_editor',
            'children_count', 'breadcrumbs', 'depth', 'parent'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'creator', 'last_editor',
            'children_count', 'breadcrumbs', 'depth'
        ]

    def get_children_count(self, obj):
        """获取子文档数量"""
        return obj.children.filter(is_active=True).count()


class KnowledgeDocumentDetailSerializer(serializers.ModelSerializer):
    """
    知识文档详情序列化器 - 用于详情显示和编辑
    """
    creator = UserSimpleSerializer(read_only=True)
    last_editor = UserSimpleSerializer(read_only=True)
    children = serializers.SerializerMethodField()
    breadcrumbs = serializers.ReadOnlyField()
    depth = serializers.ReadOnlyField()

    class Meta:
        model = KnowledgeDocument
        fields = [
            'id', 'title', 'content', 'markdown_content', 'summary', 'doc_type', 'status',
            'parent', 'sort_order', 'is_public', 'is_active',
            'created_at', 'updated_at', 'creator', 'last_editor',
            'children', 'breadcrumbs', 'depth'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'creator', 'last_editor',
            'breadcrumbs', 'depth', 'markdown_content'
        ]

    def get_children(self, obj):
        """获取子文档列表"""
        if obj.is_folder:
            children = obj.children.filter(is_active=True).order_by('sort_order', 'title')
            return KnowledgeDocumentListSerializer(children, many=True, context=self.context).data
        return []

    def validate_parent(self, value):
        """验证父文档"""
        if value:
            # 检查父文档是否为文件夹类型
            if not value.is_folder:
                raise serializers.ValidationError("父级必须是文件夹类型")

            # 检查是否在同一个命名空间
            namespace_pk = self.context.get('namespace_pk')
            if value.namespace_id != namespace_pk:
                raise serializers.ValidationError("父级文档必须在同一个知识库中")

            # 防止循环引用（如果是更新操作）
            if self.instance and value == self.instance:
                raise serializers.ValidationError("不能将自己设为父级")

            # 防止将父级设为自己的子级
            if self.instance and value in self.instance.get_descendants():
                raise serializers.ValidationError("不能将子级设为父级")

        return value

    def create(self, validated_data):
        """创建文档"""
        # 设置创建者和命名空间
        validated_data['creator'] = self.context['request'].user
        validated_data['last_editor'] = self.context['request'].user
        validated_data['namespace_id'] = self.context['namespace_pk']

        # 先创建文档以获取ID
        document = super().create(validated_data)

        # 处理HTML内容中的base64图片（如果有的话）
        if document.content:
            processed_content = self._process_base64_images(
                document.content,
                document.namespace.id,
                document.id
            )

            # 如果内容有变化，更新文档
            if processed_content != document.content:
                document.content = processed_content

                # 转换为Markdown
                markdown_content = self._html_to_markdown(processed_content)
                document.markdown_content = markdown_content

                document.save()

                # 异步存储到向量数据库
                if document.markdown_content and document.is_document:
                    try:
                        import asyncio
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        loop.run_until_complete(self._store_to_vector_database(document))
                        loop.close()
                    except Exception as e:
                        from llm_api.settings.base import error_logger
                        error_logger(f"向量数据库存储异步处理失败: {str(e)}")

        return document

    def _process_base64_images(self, html_content, namespace_id, document_id):
        """处理HTML中的base64图片，转换为COS存储的URL"""
        if not html_content:
            return html_content

        # 查找所有base64图片
        base64_pattern = r'<img[^>]*src="data:image/([^;]+);base64,([^"]+)"[^>]*>'

        def replace_base64_image(match):
            image_format = match.group(1)
            base64_data = match.group(2)

            try:
                # 解码base64数据
                image_data = base64.b64decode(base64_data)

                # 生成文件名
                file_name = f"{uuid.uuid4().hex}.{image_format}"
                file_path = f"knowledge/{namespace_id}/{document_id}/{file_name}"

                # 创建文件对象
                file_obj = ContentFile(image_data, name=file_name)

                # 保存到COS
                file_url = default_storage.save(file_path, file_obj)
                full_url = default_storage.url(file_url)

                # 替换原始的img标签
                return match.group(0).replace(f"data:image/{image_format};base64,{base64_data}", full_url)

            except Exception as e:
                # 如果转换失败，保持原始内容
                return match.group(0)

        # 替换所有base64图片
        processed_content = re.sub(base64_pattern, replace_base64_image, html_content)
        return processed_content

    @staticmethod
    def _html_to_markdown(html_content):
        """将HTML转换为Markdown"""
        if not html_content:
            return ""

        # 配置html2text
        h = html2text.HTML2Text()
        h.ignore_links = False
        h.ignore_images = False
        h.body_width = 0  # 不限制行宽

        # 转换
        markdown_content = h.handle(html_content)
        return markdown_content.strip()

    @staticmethod
    async def _store_to_vector_database(document):
        """存储到向量数据库"""
        try:
            from core.indexing.index import index
            from langchain_core.documents import Document as LangchainDocument

            if not document.markdown_content:
                return

            # 创建文档对象
            doc = LangchainDocument(
                page_content=document.markdown_content,
                metadata={
                    "tenant": str(document.creator.id),
                    "owner": str(document.creator.id),
                    "namespace": str(document.namespace.id),
                    "source": f"document_{document.id}",
                    "document_id": str(document.id),
                    "title": document.title,
                    "H1": "",
                    "H2": "",
                    "H3": "",
                    "H4": "",
                    "H5": "",
                    "H6": "",
                }
            )

            # 存储到向量数据库
            await index(
                document_id=str(document.id),
                tenant=str(document.creator.id),
                namespace=str(document.namespace.id),
                doc=doc,
            )

        except Exception as e:
            from llm_api.settings.base import error_logger
            error_logger(f"存储到向量数据库失败: {str(e)}")

    def _extract_image_urls(self, html_content):
        """从HTML内容中提取图片URL"""
        if not html_content:
            return []
        
        # 匹配img标签中的src属性，只匹配COS存储的图片
        pattern = r'<img[^>]*src="([^"]*knowledge/[^"]*)"[^>]*>'
        matches = re.findall(pattern, html_content)
        return matches

    def _cleanup_removed_images(self, old_image_urls, new_image_urls):
        """清理不再使用的图片"""
        try:
            # 计算删除的图片
            removed_images = set(old_image_urls) - set(new_image_urls)
            
            # 删除不再使用的图片
            for image_url in removed_images:
                import asyncio
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(self._delete_cos_image(image_url))
                    loop.close()
                    from llm_api.settings.base import info_logger
                    info_logger(f"已删除不再使用的图片: {image_url}")
                except Exception as e:
                    from llm_api.settings.base import error_logger
                    error_logger(f"删除图片失败: {str(e)}")
                        
        except Exception as e:
            from llm_api.settings.base import error_logger
            error_logger(f"清理图片失败: {str(e)}")

    async def _delete_cos_image(self, image_url):
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
                    from llm_api.settings.base import info_logger
                    info_logger(f"已删除COS图片: {file_path}")
                    
        except Exception as e:
            from llm_api.settings.base import error_logger
            error_logger(f"删除COS图片失败: {str(e)}")

    def update(self, instance, validated_data):
        """更新文档"""
        # 设置最后编辑者
        validated_data['last_editor'] = self.context['request'].user

        # 获取更新前的图片列表（用于后续清理）
        old_image_urls = self._extract_image_urls(instance.content) if instance.content else []

        # 处理HTML内容中的base64图片
        if 'content' in validated_data and validated_data['content']:
            processed_content = self._process_base64_images(
                validated_data['content'],
                instance.namespace.id,
                instance.id
            )
            validated_data['content'] = processed_content

            # 转换为Markdown
            markdown_content = self._html_to_markdown(processed_content)
            validated_data['markdown_content'] = markdown_content

        # 更新文档
        document = super().update(instance, validated_data)

        # 处理图片引用变更
        if 'content' in validated_data:
            new_image_urls = self._extract_image_urls(document.content) if document.content else []
            self._cleanup_removed_images(old_image_urls, new_image_urls)

        # 异步存储到向量数据库
        if document.markdown_content and document.is_document:
            try:
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self._store_to_vector_database(document))
                loop.close()
            except Exception as e:
                from llm_api.settings.base import error_logger
                error_logger(f"向量数据库存储异步处理失败: {str(e)}")

        return document


class KnowledgeDocumentTreeSerializer(serializers.ModelSerializer):
    """
    知识文档树形结构序列化器 - 用于目录树显示
    """
    children = serializers.SerializerMethodField()

    class Meta:
        model = KnowledgeDocument
        fields = [
            'id', 'title', 'doc_type', 'sort_order', 'is_public',
            'created_at', 'updated_at', 'children'
        ]

    def get_children(self, obj):
        """递归获取子文档"""
        if obj.is_folder:
            children = obj.children.filter(is_active=True).order_by('sort_order', 'title')
            return KnowledgeDocumentTreeSerializer(children, many=True).data
        return []


class KnowledgeDocumentCreateSerializer(serializers.ModelSerializer):
    """
    知识文档创建序列化器 - 简化的创建接口
    """

    class Meta:
        model = KnowledgeDocument
        fields = [
            'title', 'content', 'summary', 'doc_type', 'status',
            'parent', 'sort_order', 'is_public'
        ]

    def validate_parent(self, value):
        """验证父文档"""
        if value and not value.is_folder:
            raise serializers.ValidationError("父级必须是文件夹类型")
        return value

    def create(self, validated_data):
        """创建文档"""
        # 设置基本信息
        validated_data['creator'] = self.context['request'].user
        validated_data['last_editor'] = self.context['request'].user
        validated_data['namespace_id'] = self.context['namespace_pk']

        # 创建文档
        document = super().create(validated_data)

        return document


class KnowledgeDocumentMoveSerializer(serializers.Serializer):
    """
    知识文档移动序列化器
    """
    target_parent_id = serializers.IntegerField(required=False, allow_null=True)
    sort_order = serializers.IntegerField(required=False)

    def validate_target_parent_id(self, value):
        """验证目标父文档"""
        if value:
            try:
                parent = KnowledgeDocument.objects.get(
                    id=value,
                    namespace_id=self.context['namespace_pk'],
                    doc_type='folder'
                )

                # 防止循环引用
                document = self.context['document']
                if parent == document or parent in document.get_descendants():
                    raise serializers.ValidationError("不能移动到自己或子文档下")

                return parent
            except KnowledgeDocument.DoesNotExist:
                raise serializers.ValidationError("目标文件夹不存在")
        return None


class ToolDataSerializer(serializers.Serializer):
    """
    工具知识数据序列化器
    """
    name = serializers.CharField(
        max_length=255,
        required=True,
        help_text="工具名称"
    )
    description = serializers.CharField(
        required=True,
        help_text="工具描述"
    )
    input_schema = serializers.JSONField(
        required=False,
        default=lambda: {
            'type': 'object',
            'properties': {},
            'required': []
        },
        help_text="输入参数结构"
    )
    few_shots = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=list,
        help_text="使用示例"
    )
    tool_type = serializers.ChoiceField(
        choices=[
            ('dynamic', '动态工具'),
            ('static', '静态工具'),
            ('api', 'API工具')
        ],
        default='dynamic',
        help_text="工具类型"
    )
    extra_params = serializers.JSONField(
        required=False,
        default=dict,
        help_text="额外参数"
    )

    def validate_input_schema(self, value):
        """验证输入参数结构"""
        # 如果没有提供值，使用默认值
        if value is None:
            value = {
                'type': 'object',
                'properties': {},
                'required': []
            }

        if not isinstance(value, dict):
            raise serializers.ValidationError("input_schema必须是JSON对象")

        required_keys = ['type', 'properties']
        for key in required_keys:
            if key not in value:
                raise serializers.ValidationError(f"input_schema缺少必需字段: {key}")

        if value['type'] != 'object':
            raise serializers.ValidationError("input_schema的type必须是'object'")

        if not isinstance(value['properties'], dict):
            raise serializers.ValidationError("properties必须是对象")

        return value

    def validate_extra_params(self, value):
        """验证额外参数"""
        if not isinstance(value, dict):
            raise serializers.ValidationError("extra_params必须是JSON对象")
        return value


class FormFieldSerializer(serializers.Serializer):
    """
    表单字段序列化器
    """
    name = serializers.CharField(
        max_length=100,
        required=True,
        help_text="字段名称"
    )
    field_type = serializers.ChoiceField(
        choices=[
            ('String', '字符串'),
            ('Integer', '整数'),
            ('Time', '时间'),
            ('Number', '数字'),
            ('Boolean', '布尔值')
        ],
        required=True,
        help_text="字段类型"
    )
    description = serializers.CharField(
        max_length=500,
        required=False,
        allow_blank=True,
        help_text="字段描述"
    )
    is_required = serializers.BooleanField(
        default=False,
        help_text="是否必填"
    )
    default_value = serializers.CharField(
        max_length=255,
        required=False,
        allow_blank=True,
        allow_null=True,
        help_text="默认值"
    )

    def validate_name(self, value):
        """验证字段名称"""
        if not value.isidentifier():
            raise serializers.ValidationError("字段名称必须是有效的标识符")
        return value


class FormDataSerializer(serializers.Serializer):
    """
    表单知识数据序列化器
    """
    table_name = serializers.CharField(
        max_length=100,
        required=True,
        help_text="表名"
    )
    table_description = serializers.CharField(
        max_length=500,
        required=False,
        allow_blank=True,
        help_text="表描述"
    )
    fields = FormFieldSerializer(
        many=True,
        required=True,
        help_text="表字段列表"
    )

    def validate_table_name(self, value):
        """验证表名"""
        if not value.isidentifier():
            raise serializers.ValidationError("表名必须是有效的标识符")
        return value

    def validate_fields(self, value):
        """验证字段列表"""
        if not value:
            raise serializers.ValidationError("至少需要一个字段")

        # 检查字段名重复
        field_names = [field['name'] for field in value]
        if len(field_names) != len(set(field_names)):
            raise serializers.ValidationError("字段名不能重复")

        return value


class KnowledgeDocumentToolSerializer(KnowledgeDocumentDetailSerializer):
    """
    工具知识序列化器
    """
    tool_data = ToolDataSerializer(required=False)
    type_specific_data = ToolDataSerializer(required=False, write_only=True)

    class Meta(KnowledgeDocumentDetailSerializer.Meta):
        fields = KnowledgeDocumentDetailSerializer.Meta.fields + ['tool_data', 'type_specific_data']

    def to_internal_value(self, data):
        """自定义数据转换，支持type_specific_data字段和只更新工具数据的场景"""
        # 如果有type_specific_data但没有tool_data，则使用type_specific_data作为tool_data
        if 'type_specific_data' in data and 'tool_data' not in data:
            data = data.copy()  # 避免修改原始数据
            data['tool_data'] = data['type_specific_data']

        # 如果只提供了tool_data（工具数据更新场景），填充当前实例的基础字段
        if self.instance and len(data) == 1 and 'tool_data' in data:
            # 只更新工具数据的场景，保持其他字段不变
            enhanced_data = {
                'title': self.instance.title,
                'content': self.instance.content,
                'summary': self.instance.summary,
                'doc_type': self.instance.doc_type,
                'status': self.instance.status,
                'parent': self.instance.parent.id if self.instance.parent else None,
                'sort_order': self.instance.sort_order,
                'is_public': self.instance.is_public,
                'is_active': self.instance.is_active,
                'tool_data': data['tool_data']
            }
            data = enhanced_data

        return super().to_internal_value(data)

    def to_representation(self, instance):
        """自定义序列化输出"""
        data = super().to_representation(instance)
        if instance.is_tool:
            data['tool_data'] = instance.get_tool_data()
        return data

    def create(self, validated_data):
        """创建工具知识"""
        # 移除type_specific_data（如果存在），因为我们已经在to_internal_value中处理了
        validated_data.pop('type_specific_data', None)
        tool_data = validated_data.pop('tool_data', None)
        validated_data['doc_type'] = 'tool'

        # 创建文档
        instance = super().create(validated_data)

        # 设置工具数据
        if tool_data:
            instance.set_tool_data(tool_data)
            instance.save()

        return instance

    def update(self, instance, validated_data):
        """更新工具知识"""
        # 移除type_specific_data（如果存在），因为我们已经在to_internal_value中处理了
        validated_data.pop('type_specific_data', None)
        tool_data = validated_data.pop('tool_data', None)

        # 更新基础字段
        instance = super().update(instance, validated_data)

        # 更新工具数据
        if tool_data and instance.is_tool:
            instance.set_tool_data(tool_data)
            instance.save()

        return instance


class KnowledgeDocumentFormSerializer(KnowledgeDocumentDetailSerializer):
    """
    表单知识序列化器
    """
    form_data = FormDataSerializer(required=False)
    type_specific_data = FormDataSerializer(required=False, write_only=True)

    class Meta(KnowledgeDocumentDetailSerializer.Meta):
        fields = KnowledgeDocumentDetailSerializer.Meta.fields + ['form_data', 'type_specific_data']

    def to_internal_value(self, data):
        """自定义数据转换，支持type_specific_data字段和只更新表单数据的场景"""
        # 如果有type_specific_data但没有form_data，则使用type_specific_data作为form_data
        if 'type_specific_data' in data and 'form_data' not in data:
            data = data.copy()  # 避免修改原始数据
            data['form_data'] = data['type_specific_data']

        # 如果只提供了form_data（表单数据更新场景），填充当前实例的基础字段
        if self.instance and len(data) == 1 and 'form_data' in data:
            # 只更新表单数据的场景，保持其他字段不变
            enhanced_data = {
                'title': self.instance.title,
                'content': self.instance.content,
                'summary': self.instance.summary,
                'doc_type': self.instance.doc_type,
                'status': self.instance.status,
                'parent': self.instance.parent.id if self.instance.parent else None,
                'sort_order': self.instance.sort_order,
                'is_public': self.instance.is_public,
                'is_active': self.instance.is_active,
                'form_data': data['form_data']
            }
            data = enhanced_data

        return super().to_internal_value(data)

    def to_representation(self, instance):
        """自定义序列化输出"""
        data = super().to_representation(instance)
        if instance.is_form:
            data['form_data'] = instance.get_form_data()
        return data

    def create(self, validated_data):
        """创建表单知识"""
        # 移除type_specific_data（如果存在），因为我们已经在to_internal_value中处理了
        validated_data.pop('type_specific_data', None)
        form_data = validated_data.pop('form_data', None)
        validated_data['doc_type'] = 'form'

        # 创建文档
        instance = super().create(validated_data)

        # 设置表单数据
        if form_data:
            instance.set_form_data(form_data)
            instance.save()

        return instance

    def update(self, instance, validated_data):
        """更新表单知识"""
        # 移除type_specific_data（如果存在），因为我们已经在to_internal_value中处理了
        validated_data.pop('type_specific_data', None)
        form_data = validated_data.pop('form_data', None)

        # 更新基础字段
        instance = super().update(instance, validated_data)

        # 更新表单数据
        if form_data and instance.is_form:
            instance.set_form_data(form_data)
            instance.save()

        return instance


class FormDataEntrySerializer(serializers.ModelSerializer):
    """
    表单数据条目序列化器
    """
    submitter = UserSimpleSerializer(read_only=True)

    class Meta:
        model = FormDataEntry
        fields = [
            'id', 'data', 'submitter', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'submitter', 'created_at', 'updated_at']

    def create(self, validated_data):
        """创建表单数据条目"""
        validated_data['submitter'] = self.context['request'].user
        validated_data['form_document_id'] = self.context['form_document_id']
        return super().create(validated_data)


class ToolExecutionSerializer(serializers.ModelSerializer):
    """
    工具执行记录序列化器
    """
    executor = UserSimpleSerializer(read_only=True)

    class Meta:
        model = ToolExecution
        fields = [
            'id', 'input_data', 'output_data', 'status', 'error_message',
            'execution_time', 'executor', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'output_data', 'status', 'error_message', 'execution_time',
            'executor', 'created_at', 'updated_at'
        ]

    def create(self, validated_data):
        """创建工具执行记录"""
        validated_data['executor'] = self.context['request'].user
        validated_data['tool_document_id'] = self.context['tool_document_id']
        return super().create(validated_data)
