from rest_framework import serializers
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from django.conf import settings
from django.core.files.uploadedfile import InMemoryUploadedFile
import os
from user.models.user import CustomUser


class UserLoginSerializer(serializers.Serializer):
    """
    用户登录序列化器
    """
    username = serializers.CharField(max_length=150, required=True, help_text="用户名")
    password = serializers.CharField(max_length=128, required=True, help_text="密码", write_only=True)
    remember_me = serializers.BooleanField(default=False, required=False, help_text="15天免登录")

    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')
        
        if username and password:
            user = authenticate(username=username, password=password)
            if user:
                if user.is_active:
                    attrs['user'] = user
                else:
                    raise serializers.ValidationError("用户账号已被禁用")
            else:
                raise serializers.ValidationError("用户名或密码错误")
        else:
            raise serializers.ValidationError("必须提供用户名和密码")
        
        return attrs

    def get_tokens(self, user, remember_me=False):
        """
        获取JWT token
        """
        refresh = RefreshToken.for_user(user)
        
        # 根据是否选择15天免登录来设置不同的过期时间
        if remember_me:
            # 选择了15天免登录：refresh token使用15天，access token使用1小时
            from datetime import timedelta
            # refresh token已经在settings中配置为15天，不需要修改
            # access token设置为1小时
            refresh.access_token.set_exp(lifetime=timedelta(hours=24*7))
        else:
            # 没有选择免登录：refresh token使用1天，access token使用1小时
            from datetime import timedelta
            # 设置refresh token过期时间为1天
            refresh.set_exp(lifetime=timedelta(days=7))
            # access token设置为1小时
            refresh.access_token.set_exp(lifetime=timedelta(hours=24*7))
            
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': UserInfoSerializer(user).data
        }


class UserInfoSerializer(serializers.ModelSerializer):
    """
    用户信息序列化器
    """
    age = serializers.ReadOnlyField(help_text="年龄（根据生日计算）")
    
    class Meta:
        model = CustomUser
        fields = [
            'id', 'username', 'email', 'phone', 'avatar', 'role', 
            'gender', 'birthday', 'age', 'is_active', 'date_joined', 'last_login'
        ]
        read_only_fields = ['id', 'role', 'date_joined', 'last_login', 'age']


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    用户注册序列化器（为后续扩展准备）
    """
    password = serializers.CharField(write_only=True, min_length=8, help_text="密码最少8位")
    password_confirm = serializers.CharField(write_only=True, help_text="确认密码")

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password', 'password_confirm', 'phone']

    def validate(self, attrs):
        password = attrs.get('password')
        password_confirm = attrs.get('password_confirm')
        
        if password != password_confirm:
            raise serializers.ValidationError("两次密码输入不一致")
        
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        user = CustomUser.objects.create_user(password=password, **validated_data)
        return user


# ===== 响应序列化器，用于规范Swagger文档 =====

class LoginTokenDataSerializer(serializers.Serializer):
    """
    登录成功后返回的token数据序列化器
    """
    access = serializers.CharField(help_text="访问令牌")
    refresh = serializers.CharField(help_text="刷新令牌")
    user = UserInfoSerializer(help_text="用户信息")


class LoginResponseSerializer(serializers.Serializer):
    """
    登录接口响应序列化器
    """
    code = serializers.IntegerField(help_text="响应状态码")
    message = serializers.CharField(help_text="响应消息")
    data = LoginTokenDataSerializer(help_text="登录数据")


class UserProfileResponseSerializer(serializers.Serializer):
    """
    用户信息接口响应序列化器
    """
    code = serializers.IntegerField(help_text="响应状态码")
    message = serializers.CharField(help_text="响应消息")
    data = UserInfoSerializer(help_text="用户数据")


class UserRegistrationResponseSerializer(serializers.Serializer):
    """
    用户注册接口响应序列化器
    """
    code = serializers.IntegerField(help_text="响应状态码")
    message = serializers.CharField(help_text="响应消息")
    data = UserInfoSerializer(help_text="用户数据")


class LogoutRequestSerializer(serializers.Serializer):
    """
    登出接口请求序列化器
    """
    refresh = serializers.CharField(help_text="刷新令牌")


class BaseResponseSerializer(serializers.Serializer):
    """
    基础响应序列化器
    """
    code = serializers.IntegerField(help_text="响应状态码")
    message = serializers.CharField(help_text="响应消息")


class ErrorResponseSerializer(serializers.Serializer):
    """
    错误响应序列化器
    """
    code = serializers.IntegerField(help_text="错误状态码")
    message = serializers.CharField(help_text="错误消息")
    errors = serializers.DictField(required=False, help_text="详细错误信息")
    error = serializers.CharField(required=False, help_text="错误详情")


class UserUpdateProfileSerializer(serializers.ModelSerializer):
    """
    用户更新个人信息序列化器
    """
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'phone', 'gender', 'birthday']
        extra_kwargs = {
            'username': {'help_text': '用户名'},
            'email': {'help_text': '邮箱'},
            'phone': {'help_text': '手机号'},
            'gender': {'help_text': '性别'},
            'birthday': {'help_text': '生日'},
        }

    def validate_username(self, value):
        """
        验证用户名是否重复
        """
        # 获取当前用户实例
        instance = self.instance
        if instance and instance.username == value:
            # 如果用户名没有改变，则允许
            return value
        
        # 检查是否有其他用户使用了这个用户名
        if CustomUser.objects.filter(username=value).exists():
            raise serializers.ValidationError("该用户名已被使用，请选择其他用户名")
        
        return value


class AvatarUploadSerializer(serializers.Serializer):
    """
    用户头像上传序列化器
    """
    avatar = serializers.ImageField(
        required=True,
        help_text="用户头像文件，支持jpg、png、gif、webp格式，最大5MB"
    )

    def validate_avatar(self, value):
        """
        验证头像文件
        """
        if not isinstance(value, InMemoryUploadedFile):
            raise serializers.ValidationError("请上传有效的图片文件")
        
        # 检查文件大小
        if value.size > settings.MAX_IMAGE_SIZE:
            raise serializers.ValidationError(f"文件大小不能超过{settings.MAX_IMAGE_SIZE // (1024*1024)}MB")
        
        # 检查文件扩展名
        file_extension = os.path.splitext(value.name)[1].lower()
        if file_extension not in settings.ALLOWED_IMAGE_EXTENSIONS:
            allowed_formats = ', '.join(settings.ALLOWED_IMAGE_EXTENSIONS)
            raise serializers.ValidationError(f"不支持的文件格式，请上传以下格式的文件：{allowed_formats}")
        
        return value

    def save(self, user):
        """
        保存头像并更新用户信息
        """
        avatar_file = self.validated_data['avatar']
        
        # 如果用户已有头像，删除旧头像
        if user.avatar:
            user.delete_old_avatar()
        
        # 保存新头像
        user.avatar = avatar_file
        user.save()
        
        return user


# ===== 新增响应序列化器 =====

class AvatarUploadResponseSerializer(serializers.Serializer):
    """
    头像上传接口响应序列化器
    """
    code = serializers.IntegerField(help_text="响应状态码")
    message = serializers.CharField(help_text="响应消息")
    data = serializers.DictField(help_text="头像数据", child=serializers.CharField())


class AvatarDeleteResponseSerializer(serializers.Serializer):
    """
    头像删除接口响应序列化器
    """
    code = serializers.IntegerField(help_text="响应状态码")
    message = serializers.CharField(help_text="响应消息")


# ===== 用户管理相关序列化器（管理员专用） =====

class UserManagementSerializer(serializers.ModelSerializer):
    """
    用户管理序列化器（管理员专用）
    """
    age = serializers.ReadOnlyField(help_text="年龄（根据生日计算）")
    
    class Meta:
        model = CustomUser
        fields = [
            'id', 'username', 'email', 'phone', 'avatar', 'role', 
            'gender', 'birthday', 'age', 'is_active', 'last_login', 
            'date_joined', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'last_login', 'date_joined', 'created_at', 'updated_at', 'age']


class UserCreateSerializer(serializers.ModelSerializer):
    """
    创建用户序列化器（管理员专用）
    """
    password = serializers.CharField(write_only=True, min_length=8, help_text="密码最少8位")
    
    class Meta:
        model = CustomUser
        fields = [
            'username', 'email', 'phone', 'password', 'role', 
            'gender', 'birthday', 'is_active'
        ]
    
    def create(self, validated_data):
        password = validated_data.pop('password')
        user = CustomUser.objects.create_user(password=password, **validated_data)
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """
    更新用户信息序列化器（管理员专用）
    """
    class Meta:
        model = CustomUser
        fields = [
            'username', 'email', 'phone', 'role', 'gender', 
            'birthday', 'is_active'
        ]
    
    def validate_username(self, value):
        """
        验证用户名是否重复
        """
        instance = self.instance
        if instance and instance.username == value:
            return value
        
        if CustomUser.objects.filter(username=value).exists():
            raise serializers.ValidationError("该用户名已被使用，请选择其他用户名")
        
        return value


class PasswordResetSerializer(serializers.Serializer):
    """
    密码重置序列化器（管理员专用）
    """
    new_password = serializers.CharField(
        write_only=True, 
        min_length=8, 
        help_text="新密码，最少8位"
    )
    
    def save(self, user):
        """
        重置用户密码
        """
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


class UserSearchSerializer(serializers.Serializer):
    """
    用户搜索序列化器
    """
    username = serializers.CharField(required=False, help_text="用户名")
    phone = serializers.CharField(required=False, help_text="手机号")
    email = serializers.CharField(required=False, help_text="邮箱")
    gender = serializers.ChoiceField(
        choices=CustomUser.GENDER_CHOICES, 
        required=False, 
        help_text="性别"
    )
    role = serializers.ChoiceField(
        choices=CustomUser.ROLE_CHOICES, 
        required=False, 
        help_text="角色"
    )
    is_active = serializers.BooleanField(required=False, help_text="是否有效")
    ordering = serializers.CharField(
        required=False, 
        help_text="排序字段，支持：created_at, -created_at, last_login, -last_login"
    )


# ===== 响应序列化器 =====

class UserManagementListResponseSerializer(serializers.Serializer):
    """
    用户管理列表响应序列化器
    """
    code = serializers.IntegerField(help_text="响应状态码")
    message = serializers.CharField(help_text="响应消息")
    data = serializers.DictField(help_text="用户列表数据")


class UserManagementDetailResponseSerializer(serializers.Serializer):
    """
    用户管理详情响应序列化器
    """
    code = serializers.IntegerField(help_text="响应状态码")
    message = serializers.CharField(help_text="响应消息")
    data = UserManagementSerializer(help_text="用户详情数据")


class PasswordResetResponseSerializer(serializers.Serializer):
    """
    密码重置响应序列化器
    """
    code = serializers.IntegerField(help_text="响应状态码")
    message = serializers.CharField(help_text="响应消息")


class UserAvatarManagementSerializer(serializers.Serializer):
    """
    用户头像管理序列化器（管理员专用）
    """
    avatar = serializers.ImageField(
        required=True,
        help_text="用户头像文件，支持jpg、png、gif、webp格式，最大5MB"
    )

    def validate_avatar(self, value):
        """
        验证头像文件
        """
        if not isinstance(value, InMemoryUploadedFile):
            raise serializers.ValidationError("请上传有效的图片文件")
        
        # 检查文件大小（使用Django设置）
        max_size = getattr(settings, 'MAX_IMAGE_SIZE', 5 * 1024 * 1024)  # 默认5MB
        if value.size > max_size:
            raise serializers.ValidationError(f"文件大小不能超过{max_size // (1024*1024)}MB")
        
        # 检查文件扩展名
        allowed_extensions = getattr(settings, 'ALLOWED_IMAGE_EXTENSIONS', ['.jpg', '.jpeg', '.png', '.gif', '.webp'])
        file_extension = os.path.splitext(value.name)[1].lower()
        if file_extension not in allowed_extensions:
            allowed_formats = ', '.join(allowed_extensions)
            raise serializers.ValidationError(f"不支持的文件格式，请上传以下格式的文件：{allowed_formats}")
        
        return value

    def save(self, user):
        """
        保存头像并更新用户信息
        """
        avatar_file = self.validated_data['avatar']
        
        # 如果用户已有头像，删除旧头像
        if user.avatar:
            user.delete_old_avatar()
        
        # 保存新头像
        user.avatar = avatar_file
        user.save()
        
        return user 