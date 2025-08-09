from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
import base64
import uuid
import mimetypes

from bot.models.bot import Bot, BotCollaborator

User = get_user_model()


class Base64ImageField(serializers.ImageField):
    """
    Base64图片字段，用于处理前端发送的base64编码图片
    """
    def to_internal_value(self, data):
        # 如果是字符串且包含base64数据
        if isinstance(data, str) and data.startswith('data:image'):
            # 解析base64数据
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            
            # 验证图片格式
            if ext not in ['jpeg', 'jpg', 'png', 'gif', 'webp']:
                raise serializers.ValidationError("不支持的图片格式，仅支持：jpeg、jpg、png、gif、webp")
            
            # 解码base64数据
            try:
                img_data = base64.b64decode(imgstr)
            except Exception:
                raise serializers.ValidationError("无效的base64图片数据")
            
            # 生成文件名
            filename = f"{uuid.uuid4().hex}.{ext}"
            
            # 创建ContentFile对象
            data = ContentFile(img_data, name=filename)
        
        return super().to_internal_value(data)


class CollaboratorUserSerializer(serializers.ModelSerializer):
    """
    协作者用户信息序列化器
    """
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'avatar']
        read_only_fields = ['id', 'username', 'first_name', 'last_name', 'avatar']


class BotCollaboratorSerializer(serializers.ModelSerializer):
    """
    Bot协作者序列化器
    """
    user = CollaboratorUserSerializer(read_only=True)
    user_id = serializers.IntegerField(write_only=True)
    username = serializers.CharField(write_only=True, required=False)
    added_by = CollaboratorUserSerializer(read_only=True)
    can_edit = serializers.ReadOnlyField()  # 兼容旧接口
    can_read = serializers.ReadOnlyField()

    class Meta:
        model = BotCollaborator
        fields = ['id', 'user', 'user_id', 'username', 'role', 'can_edit', 'can_read', 'added_by', 'added_at']
        read_only_fields = ['id', 'user', 'added_by', 'added_at', 'can_edit', 'can_read']

    def validate(self, attrs):
        """
        验证用户信息
        """
        user_id = attrs.get('user_id')
        username = attrs.get('username')
        
        if not user_id and not username:
            raise serializers.ValidationError("必须提供user_id或username")
        
        # 如果提供了username，尝试找到对应的用户
        if username and not user_id:
            try:
                user = User.objects.get(username=username)
                attrs['user_id'] = user.id
            except User.DoesNotExist:
                raise serializers.ValidationError(f"用户名 '{username}' 不存在")
        
        # 验证用户存在
        if user_id:
            try:
                User.objects.get(id=user_id)
            except User.DoesNotExist:
                raise serializers.ValidationError("指定的用户不存在")
        
        return attrs

    def create(self, validated_data):
        """
        创建协作者
        """
        # 移除不需要的字段
        validated_data.pop('username', None)
        
        # 设置添加者
        validated_data['added_by'] = self.context['request'].user
        
        return super().create(validated_data)


class BotSerializer(serializers.ModelSerializer):
    """
    Bot序列化器
    """
    creator = CollaboratorUserSerializer(read_only=True)
    collaborators = BotCollaboratorSerializer(many=True, read_only=True)
    collaborator_count = serializers.ReadOnlyField()
    is_public = serializers.ReadOnlyField()
    can_access = serializers.SerializerMethodField()
    can_edit = serializers.SerializerMethodField()
    avatar = Base64ImageField(required=False)

    class Meta:
        model = Bot
        fields = [
            'id', 'name', 'description', 'avatar', 'access_type', 'creator', 
            'slug', 'is_active', 'assistant_id', 'graph_id', 'created_at', 'updated_at', 
            'collaborators', 'collaborator_count', 'is_public', 'can_access', 'can_edit'
        ]
        read_only_fields = ['id', 'creator', 'slug', 'assistant_id', 'created_at', 'updated_at']

    def get_can_access(self, obj):
        """
        获取当前用户是否可以访问
        """
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            return obj.can_access(request.user)
        return False

    def get_can_edit(self, obj):
        """
        获取当前用户是否可以编辑
        """
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            return obj.can_edit(request.user)
        return False

    def create(self, validated_data):
        """
        创建Bot时设置创建者
        """
        validated_data['creator'] = self.context['request'].user
        return super().create(validated_data)


class BotListSerializer(serializers.ModelSerializer):
    """
    Bot列表序列化器（简化版）
    """
    creator = CollaboratorUserSerializer(read_only=True)
    collaborator_count = serializers.ReadOnlyField()
    is_public = serializers.ReadOnlyField()
    can_access = serializers.SerializerMethodField()
    can_edit = serializers.SerializerMethodField()

    class Meta:
        model = Bot
        fields = [
            'id', 'name', 'description', 'avatar', 'access_type', 'creator',
            'slug', 'is_active', 'assistant_id', 'created_at', 'updated_at', 
            'collaborator_count', 'is_public', 'can_access', 'can_edit'
        ]
        read_only_fields = fields

    def get_can_access(self, obj):
        """
        获取当前用户是否可以访问
        """
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            return obj.can_access(request.user)
        return False

    def get_can_edit(self, obj):
        """
        获取当前用户是否可以编辑
        """
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            return obj.can_edit(request.user)
        return False


class AddCollaboratorSerializer(serializers.Serializer):
    """
    添加协作者序列化器
    """
    username = serializers.CharField(help_text="要添加的用户名")
    role = serializers.ChoiceField(
        choices=BotCollaborator.ROLE_CHOICES,
        required=False,
        help_text="协作者角色：admin（管理权限）或readonly（只读权限）"
    )
    # 保持兼容性
    can_edit = serializers.BooleanField(
        required=False,
        write_only=True,
        help_text="兼容字段：True表示管理权限，False表示只读权限"
    )

    def validate_username(self, value):
        """
        验证用户名
        """
        try:
            User.objects.get(username=value)
            return value
        except User.DoesNotExist:
            raise serializers.ValidationError(f"用户名 '{value}' 不存在")
    
    def validate(self, attrs):
        """
        处理can_edit字段的兼容性和默认值设置
        """
        # 如果提供了can_edit字段，将其转换为role（仅当没有直接提供role时）
        if 'can_edit' in attrs and 'role' not in attrs:
            attrs['role'] = 'admin' if attrs['can_edit'] else 'readonly'
        elif 'role' not in attrs and 'can_edit' not in attrs:
            # 如果既没有提供role也没有提供can_edit，设置默认值
            attrs['role'] = 'readonly'
        
        # 清理can_edit字段，因为它只是兼容性字段
        if 'can_edit' in attrs:
            del attrs['can_edit']
        
        return attrs


class BotBasicUpdateSerializer(serializers.ModelSerializer):
    """
    Bot基本信息更新序列化器
    """
    avatar = Base64ImageField(required=False)

    class Meta:
        model = Bot
        fields = ['name', 'description', 'avatar', 'access_type']


class ChatMessageSerializer(serializers.Serializer):
    """
    聊天消息序列化器
    """
    message = serializers.CharField(
        max_length=10000,
        help_text="用户输入的消息内容"
    )
    thread_id = serializers.CharField(
        required=False,
        help_text="会话线程ID，如果不提供将创建新线程"
    )

    def validate_message(self, value):
        """
        验证消息内容
        """
        if not value.strip():
            raise serializers.ValidationError("消息内容不能为空")
        return value.strip()


class ChatResponseSerializer(serializers.Serializer):
    """
    聊天响应序列化器
    """
    thread_id = serializers.CharField(help_text="会话线程ID")
    message = serializers.CharField(help_text="回复消息内容")
    is_partial = serializers.BooleanField(help_text="是否为流式输出的部分内容")
    is_completed = serializers.BooleanField(help_text="是否为完整的回复")


class ThreadSerializer(serializers.Serializer):
    """
    线程序列化器
    """
    thread_id = serializers.CharField(help_text="线程ID")
    created_at = serializers.DateTimeField(help_text="创建时间")
    metadata = serializers.DictField(help_text="线程元数据")
