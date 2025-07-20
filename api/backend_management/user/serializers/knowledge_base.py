from rest_framework import serializers
from django.contrib.auth import get_user_model
from user.models.knowledge_base import KnowledgeBase, Document, KnowledgeBaseCollaborator
from user.models.book_manager import User
from django.db import models


class DocumentSerializer(serializers.ModelSerializer):
    """文档序列化器"""
    class Meta:
        model = Document
        fields = '__all__'


class KnowledgeBaseCollaboratorSerializer(serializers.ModelSerializer):
    """知识库协作者序列化器"""
    user_name = serializers.CharField(source='user.name', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    permission_display = serializers.CharField(source='get_permission_display', read_only=True)
    
    class Meta:
        model = KnowledgeBaseCollaborator
        fields = [
            'id', 'user', 'user_name', 'user_email', 'permission', 'permission_display',
            'invite_token', 'invite_url', 'invited_at', 'accepted_at', 'is_active',
            'created_time', 'updated_time'
        ]
        read_only_fields = ['invite_token', 'invite_url', 'invited_at', 'accepted_at']


class KnowledgeBaseCollaboratorCreateSerializer(serializers.ModelSerializer):
    """协作者创建序列化器"""
    user_email = serializers.EmailField(write_only=True)
    
    class Meta:
        model = KnowledgeBaseCollaborator
        fields = ['user_email', 'permission']
    
    def validate_user_email(self, value):
        """验证用户邮箱是否存在"""
        try:
            user = User.objects.get(email=value)
            return value
        except User.DoesNotExist:
            raise serializers.ValidationError("该邮箱对应的用户不存在")
    
    def create(self, validated_data):
        """创建协作者"""
        user_email = validated_data.pop('user_email')
        user = User.objects.get(email=user_email)
        knowledge_base = validated_data.get('knowledge_base')
        
        # 检查是否已经是协作者
        if KnowledgeBaseCollaborator.objects.filter(
            knowledge_base=knowledge_base, 
            user=user
        ).exists():
            raise serializers.ValidationError("该用户已经是协作者")
        
        # 检查是否是知识库拥有者
        if knowledge_base.owner == user:
            raise serializers.ValidationError("不能将知识库拥有者添加为协作者")
        
        validated_data['user'] = user
        return super().create(validated_data)


class KnowledgeBaseSerializer(serializers.ModelSerializer):
    """知识库完整序列化器"""
    document_count = serializers.ReadOnlyField()
    collaborator_count = serializers.ReadOnlyField()
    owner_name = serializers.CharField(source='owner.name', read_only=True)
    owner_email = serializers.CharField(source='owner.email', read_only=True)
    doc_width_display = serializers.CharField(source='get_doc_width_display', read_only=True)
    doc_create_position_display = serializers.CharField(source='get_doc_create_position_display', read_only=True)
    collaborators = KnowledgeBaseCollaboratorSerializer(many=True, read_only=True)
    
    class Meta:
        model = KnowledgeBase
        fields = [
            'id', 'name', 'desc', 'owner', 'owner_name', 'owner_email',
            'cover_image', 'doc_width', 'doc_width_display', 'enable_comments',
            'auto_publish', 'doc_create_position', 'doc_create_position_display',
            'created_time', 'updated_time', 'document_count', 'collaborator_count',
            'collaborators'
        ]
        read_only_fields = ['owner', 'created_time', 'updated_time']


class KnowledgeBaseCreateSerializer(serializers.ModelSerializer):
    """知识库创建序列化器"""
    class Meta:
        model = KnowledgeBase
        fields = [
            'name', 'desc', 'cover_image', 'doc_width', 'enable_comments',
            'auto_publish', 'doc_create_position'
        ]
        
    def validate_name(self, value):
        """验证知识库名称不能为空"""
        if not value.strip():
            raise serializers.ValidationError("知识库名称不能为空")
        return value.strip()
    
    def create(self, validated_data):
        """创建知识库时自动设置拥有者"""
        user = self.context['request'].user
        if hasattr(user, 'pk'):
            # 如果是Django的User模型，需要获取对应的自定义User
            try:
                custom_user = User.objects.get(email=user.email)
                validated_data['owner'] = custom_user
            except User.DoesNotExist:
                raise serializers.ValidationError("用户不存在，请先创建用户信息")
        else:
            validated_data['owner'] = user
        return super().create(validated_data)


class KnowledgeBaseUpdateSerializer(serializers.ModelSerializer):
    """知识库更新序列化器"""
    class Meta:
        model = KnowledgeBase
        fields = [
            'name', 'desc', 'cover_image', 'doc_width', 'enable_comments',
            'auto_publish', 'doc_create_position'
        ]
        
    def validate_name(self, value):
        """验证知识库名称不能为空"""
        if value is not None and not value.strip():
            raise serializers.ValidationError("知识库名称不能为空")
        return value.strip() if value else value


class KnowledgeBaseListSerializer(serializers.ModelSerializer):
    """知识库列表序列化器"""
    kbId = serializers.IntegerField(source='id', read_only=True)
    document_count = serializers.ReadOnlyField()
    collaborator_count = serializers.ReadOnlyField()
    owner_name = serializers.CharField(source='owner.name', read_only=True)
    doc_width_display = serializers.CharField(source='get_doc_width_display', read_only=True)
    
    class Meta:
        model = KnowledgeBase
        fields = [
            'kbId', 'name', 'cover_image', 'owner_name', 'doc_width_display',
            'enable_comments', 'auto_publish', 'updated_time', 'document_count',
            'collaborator_count'
        ]


class KnowledgeBaseSettingsSerializer(serializers.ModelSerializer):
    """知识库设置序列化器"""
    class Meta:
        model = KnowledgeBase
        fields = [
            'doc_width', 'enable_comments', 'auto_publish', 'doc_create_position'
        ]


class DocumentCreateSerializer(serializers.ModelSerializer):
    """文档创建序列化器"""
    class Meta:
        model = Document
        fields = ['title', 'content', 'file_type', 'knowledge_base']
    
    def create(self, validated_data):
        """创建文档时根据知识库设置确定位置"""
        knowledge_base = validated_data['knowledge_base']
        
        if knowledge_base.doc_create_position == 'top':
            # 获取当前最大位置值，新文档放在顶部（位置为0，其他文档位置+1）
            Document.objects.filter(knowledge_base=knowledge_base).update(
                position=models.F('position') + 1
            )
            validated_data['position'] = 0
        else:
            # 放在底部，获取当前最大位置值+1
            max_position = Document.objects.filter(
                knowledge_base=knowledge_base
            ).aggregate(
                max_pos=models.Max('position')
            )['max_pos'] or 0
            validated_data['position'] = max_position + 1
        
        return super().create(validated_data)


class DocumentUpdateSerializer(serializers.ModelSerializer):
    """文档更新序列化器"""
    class Meta:
        model = Document
        fields = ['title', 'content', 'file_type', 'is_published', 'position'] 