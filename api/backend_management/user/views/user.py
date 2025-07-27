from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import extend_schema, OpenApiExample
from django.db.models import Q
from django.contrib.auth import get_user_model

from llm_api.settings.base import info_logger, error_logger, warning_logger
from user.models.user import CustomUser
from user.permissions import IsAdminUser, IsOwnerOrAdmin
from user.serializers.user import (
    UserLoginSerializer,
    UserInfoSerializer,
    UserRegistrationSerializer,
    LoginResponseSerializer,
    UserProfileResponseSerializer,
    UserRegistrationResponseSerializer,
    LogoutRequestSerializer,
    BaseResponseSerializer,
    ErrorResponseSerializer,
    UserUpdateProfileSerializer,
    AvatarUploadSerializer,
    AvatarUploadResponseSerializer,
    AvatarDeleteResponseSerializer,
    # 新增用户管理相关序列化器
    UserManagementSerializer,
    UserCreateSerializer,
    UserUpdateSerializer,
    PasswordResetSerializer,
    UserSearchSerializer,
    UserManagementListResponseSerializer,
    UserManagementDetailResponseSerializer,
    PasswordResetResponseSerializer,
    UserAvatarManagementSerializer
)


class UserViewSet(viewsets.ModelViewSet):
    """
    用户相关视图集
    """
    queryset = CustomUser.objects.all().order_by('-date_joined')
    serializer_class = UserInfoSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        """
        设置不同action的权限
        """
        if self.action in ['login', 'register']:
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    @extend_schema(
        operation_id="user_login",
        summary="用户登录",
        description="通过用户名和密码进行登录，支持15天免登录选项",
        request=UserLoginSerializer,
        responses={
            200: LoginResponseSerializer,
            400: ErrorResponseSerializer,
            500: ErrorResponseSerializer,
        },
        examples=[
            OpenApiExample(
                "登录请求示例",
                value={
                    "username": "testuser",
                    "password": "testpass123",
                    "remember_me": True
                },
                request_only=True,
            ),
            OpenApiExample(
                "登录成功响应",
                value={
                    "code": 200,
                    "message": "登录成功",
                    "data": {
                        "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                        "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                        "user": {
                            "id": 1,
                            "username": "testuser",
                            "email": "test@example.com",
                            "phone": "",
                            "avatar": None,
                            "date_joined": "2024-01-01T00:00:00Z",
                            "last_login": "2024-01-01T00:00:00Z"
                        }
                    }
                },
                response_only=True,
                status_codes=["200"],
            ),
            OpenApiExample(
                "登录失败响应",
                value={
                    "code": 400,
                    "message": "登录失败",
                    "errors": {
                        "non_field_errors": ["用户名或密码错误"]
                    }
                },
                response_only=True,
                status_codes=["400"],
            ),
        ],
        tags=["用户认证"]
    )
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def login(self, request):
        """
        用户登录
        """
        try:
            serializer = UserLoginSerializer(data=request.data)
            if serializer.is_valid():
                user = serializer.validated_data['user']
                remember_me = serializer.validated_data.get('remember_me', False)

                # 生成JWT token
                tokens = serializer.get_tokens(user, remember_me)

                # 记录登录成功日志
                info_logger(f"用户 {user.username} 登录成功，IP: {request.META.get('REMOTE_ADDR')}")

                return Response({
                    'code': 200,
                    'message': '登录成功',
                    'data': tokens
                }, status=status.HTTP_200_OK)
            else:
                # 记录登录失败日志
                username = request.data.get('username', 'unknown')
                warning_logger(f"用户 {username} 登录失败，错误: {serializer.errors}")

                return Response({
                    'code': 400,
                    'message': '登录失败',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            error_logger(f"登录过程中发生错误: {str(e)}")
            return Response({
                'code': 500,
                'message': '服务器内部错误',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @extend_schema(
        operation_id="user_logout",
        summary="用户登出",
        description="用户登出，将refresh token加入黑名单",
        request=LogoutRequestSerializer,
        responses={
            200: BaseResponseSerializer,
            500: ErrorResponseSerializer,
        },
        examples=[
            OpenApiExample(
                "登出请求示例",
                value={
                    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
                },
                request_only=True,
            ),
            OpenApiExample(
                "登出成功响应",
                value={
                    "code": 200,
                    "message": "登出成功"
                },
                response_only=True,
                status_codes=["200"],
            ),
        ],
        tags=["用户认证"]
    )
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def logout(self, request):
        """
        用户登出
        """
        try:
            refresh_token = request.data.get("refresh")
            if refresh_token:
                try:
                    token = RefreshToken(refresh_token)
                    # 将token加入黑名单
                    token.blacklist()
                    info_logger(f"Token已成功加入黑名单")
                except Exception as token_error:
                    # 如果blacklist失败，记录警告但不影响登出流程
                    warning_logger(f"Token blacklist处理失败: {str(token_error)}")

            info_logger(f"用户 {request.user.username} 登出成功")

            return Response({
                'code': 200,
                'message': '登出成功'
            }, status=status.HTTP_200_OK)

        except Exception as e:
            error_logger(f"登出过程中发生错误: {str(e)}")
            return Response({
                'code': 500,
                'message': '服务器内部错误',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @extend_schema(
        operation_id="user_get_profile",
        summary="获取当前用户信息",
        description="获取当前登录用户的详细信息",
        responses={
            200: UserProfileResponseSerializer,
            401: ErrorResponseSerializer,
            500: ErrorResponseSerializer,
        },
        examples=[
            OpenApiExample(
                "获取用户信息成功响应",
                value={
                    "code": 200,
                    "message": "获取用户信息成功",
                    "data": {
                        "id": 1,
                        "username": "testuser",
                        "email": "test@example.com",
                        "phone": "13800138000",
                        "avatar": None,
                        "date_joined": "2024-01-01T00:00:00Z",
                        "last_login": "2024-01-01T00:00:00Z"
                    }
                },
                response_only=True,
                status_codes=["200"],
            ),
        ],
        tags=["用户信息"]
    )
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def profile(self, request):
        """
        获取当前用户信息
        """
        try:
            serializer = UserInfoSerializer(request.user)
            return Response({
                'code': 200,
                'message': '获取用户信息成功',
                'data': serializer.data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            error_logger(f"获取用户信息时发生错误: {str(e)}")
            return Response({
                'code': 500,
                'message': '服务器内部错误',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @extend_schema(
        operation_id="user_update_profile",
        summary="更新当前用户信息",
        description="更新当前登录用户的个人信息，支持更新用户名（会检查重名）",
        request=UserUpdateProfileSerializer,
        responses={
            200: UserProfileResponseSerializer,
            400: ErrorResponseSerializer,
            401: ErrorResponseSerializer,
            500: ErrorResponseSerializer,
        },
        examples=[
            OpenApiExample(
                "更新用户信息请求示例",
                value={
                    "username": "newusername",
                    "phone": "13800138000",
                    "email": "updated@example.com"
                },
                request_only=True,
            ),
            OpenApiExample(
                "更新用户信息成功响应",
                value={
                    "code": 200,
                    "message": "更新用户信息成功",
                    "data": {
                        "id": 1,
                        "username": "newusername",
                        "email": "updated@example.com",
                        "phone": "13800138000",
                        "avatar": None,
                        "date_joined": "2024-01-01T00:00:00Z",
                        "last_login": "2024-01-01T00:00:00Z"
                    }
                },
                response_only=True,
                status_codes=["200"],
            ),
            OpenApiExample(
                "用户名重复错误响应",
                value={
                    "code": 400,
                    "message": "更新失败",
                    "errors": {
                        "username": ["该用户名已被使用，请选择其他用户名"]
                    }
                },
                response_only=True,
                status_codes=["400"],
            ),
        ],
        tags=["用户信息"]
    )
    @action(detail=False, methods=['put'], permission_classes=[IsAuthenticated])
    def update_profile(self, request):
        """
        更新当前用户信息
        """
        try:
            serializer = UserUpdateProfileSerializer(request.user, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                info_logger(f"用户 {request.user.username} 更新个人信息成功")

                # 返回更新后的完整用户信息
                response_serializer = UserInfoSerializer(request.user)
                return Response({
                    'code': 200,
                    'message': '更新用户信息成功',
                    'data': response_serializer.data
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'code': 400,
                    'message': '更新失败',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            error_logger(f"更新用户信息时发生错误: {str(e)}")
            return Response({
                'code': 500,
                'message': '服务器内部错误',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @extend_schema(
        operation_id="user_register",
        summary="用户注册",
        description="新用户注册（为后续扩展准备）",
        request=UserRegistrationSerializer,
        responses={
            201: UserRegistrationResponseSerializer,
            400: ErrorResponseSerializer,
            500: ErrorResponseSerializer,
        },
        examples=[
            OpenApiExample(
                "用户注册请求示例",
                value={
                    "username": "newuser",
                    "email": "newuser@example.com",
                    "password": "newpass123",
                    "password_confirm": "newpass123",
                    "phone": "13800138000"
                },
                request_only=True,
            ),
            OpenApiExample(
                "用户注册成功响应",
                value={
                    "code": 201,
                    "message": "注册成功",
                    "data": {
                        "id": 2,
                        "username": "newuser",
                        "email": "newuser@example.com",
                        "phone": "13800138000",
                        "avatar": None,
                        "date_joined": "2024-01-01T00:00:00Z",
                        "last_login": None
                    }
                },
                response_only=True,
                status_codes=["201"],
            ),
            OpenApiExample(
                "用户注册失败响应",
                value={
                    "code": 400,
                    "message": "注册失败",
                    "errors": {
                        "username": ["具有该用户名的用户已存在。"]
                    }
                },
                response_only=True,
                status_codes=["400"],
            ),
        ],
        tags=["用户认证"]
    )
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def register(self, request):
        """
        用户注册（为后续扩展准备）
        """
        try:
            serializer = UserRegistrationSerializer(data=request.data)
            if serializer.is_valid():
                user = serializer.save()
                info_logger(f"新用户 {user.username} 注册成功")

                return Response({
                    'code': 201,
                    'message': '注册成功',
                    'data': UserInfoSerializer(user).data
                }, status=status.HTTP_201_CREATED)
            else:
                return Response({
                    'code': 400,
                    'message': '注册失败',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            error_logger(f"注册过程中发生错误: {str(e)}")
            return Response({
                'code': 500,
                'message': '服务器内部错误',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @extend_schema(
        operation_id="user_upload_avatar",
        summary="上传用户头像",
        description="上传或更新当前用户的头像，支持jpg、png、gif、webp格式，最大5MB",
        request={
            'multipart/form-data': {
                'type': 'object',
                'properties': {
                    'avatar': {
                        'type': 'string',
                        'format': 'binary',
                        'description': '用户头像文件'
                    }
                }
            }
        },
        responses={
            200: AvatarUploadResponseSerializer,
            400: ErrorResponseSerializer,
            401: ErrorResponseSerializer,
            500: ErrorResponseSerializer,
        },
        examples=[
            OpenApiExample(
                "头像上传成功响应",
                value={
                    "code": 200,
                    "message": "头像上传成功",
                    "data": {
                        "avatar_url": "https://test-bucket.cos.ap-beijing.myqcloud.com/avatars/1/abc123.jpg"
                    }
                },
                response_only=True,
                status_codes=["200"],
            ),
            OpenApiExample(
                "头像上传失败响应",
                value={
                    "code": 400,
                    "message": "头像上传失败",
                    "errors": {
                        "avatar": ["文件大小不能超过5MB"]
                    }
                },
                response_only=True,
                status_codes=["400"],
            ),
        ],
        tags=["用户头像"]
    )
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def upload_avatar(self, request):
        """
        上传用户头像
        """
        try:
            serializer = AvatarUploadSerializer(data=request.data)
            if serializer.is_valid():
                # 保存头像
                user = serializer.save(request.user)

                # 获取头像URL
                avatar_url = user.avatar.url if user.avatar else None

                info_logger(f"用户 {user.username} 上传头像成功，头像URL: {avatar_url}")

                return Response({
                    'code': 200,
                    'message': '头像上传成功',
                    'data': {
                        'avatar_url': avatar_url
                    }
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'code': 400,
                    'message': '头像上传失败',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            error_logger(f"头像上传过程中发生错误: {str(e)}")
            return Response({
                'code': 500,
                'message': '服务器内部错误',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @extend_schema(
        operation_id="user_delete_avatar",
        summary="删除用户头像",
        description="删除当前用户的头像",
        responses={
            200: AvatarDeleteResponseSerializer,
            401: ErrorResponseSerializer,
            500: ErrorResponseSerializer,
        },
        examples=[
            OpenApiExample(
                "头像删除成功响应",
                value={
                    "code": 200,
                    "message": "头像删除成功"
                },
                response_only=True,
                status_codes=["200"],
            ),
        ],
        tags=["用户头像"]
    )
    @action(detail=False, methods=['delete'], permission_classes=[IsAuthenticated])
    def delete_avatar(self, request):
        """
        删除用户头像
        """
        try:
            user = request.user

            if user.avatar:
                # 删除云存储中的文件
                user.delete_old_avatar()
                # 清空数据库中的头像字段
                user.avatar = None
                user.save()

                info_logger(f"用户 {user.username} 删除头像成功")

                return Response({
                    'code': 200,
                    'message': '头像删除成功'
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'code': 400,
                    'message': '用户暂无头像'
                }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            error_logger(f"头像删除过程中发生错误: {str(e)}")
            return Response({
                'code': 500,
                'message': '服务器内部错误',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserManagementViewSet(viewsets.ModelViewSet):
    """
    用户管理视图集（管理员专用）
    提供完整的用户CRUD操作，仅管理员可访问
    """
    queryset = CustomUser.objects.all().order_by('-date_joined')
    serializer_class = UserManagementSerializer
    permission_classes = [IsAdminUser]
    
    def get_serializer_class(self):
        """
        根据不同的action返回对应的序列化器
        """
        if self.action == 'create':
            return UserCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        elif self.action == 'search_users':
            return UserSearchSerializer
        return UserManagementSerializer
    
    def get_queryset(self):
        """
        获取查询集，支持搜索和排序
        """
        queryset = CustomUser.objects.all()
        
        # 获取搜索参数
        username = self.request.query_params.get('username', None)
        phone = self.request.query_params.get('phone', None)
        email = self.request.query_params.get('email', None)
        gender = self.request.query_params.get('gender', None)
        role = self.request.query_params.get('role', None)
        is_active = self.request.query_params.get('is_active', None)
        user_id = self.request.query_params.get('id', None)
        ordering = self.request.query_params.get('ordering', '-date_joined')
        
        # 构建搜索条件
        if username:
            queryset = queryset.filter(username__icontains=username)
        if phone:
            queryset = queryset.filter(phone__icontains=phone)
        if email:
            queryset = queryset.filter(email__icontains=email)
        if gender:
            queryset = queryset.filter(gender=gender)
        if role:
            queryset = queryset.filter(role=role)
        if is_active is not None:
            is_active_bool = is_active.lower() in ['true', '1', 'yes']
            queryset = queryset.filter(is_active=is_active_bool)
        if user_id:
            queryset = queryset.filter(id=user_id)
        
        # 排序
        valid_orderings = ['created_at', '-created_at', 'last_login', '-last_login', 'date_joined', '-date_joined']
        if ordering in valid_orderings:
            queryset = queryset.order_by(ordering)
        else:
            queryset = queryset.order_by('-date_joined')
        
        return queryset

    @extend_schema(
        operation_id="admin_list_users",
        summary="获取用户列表",
        description="管理员获取所有用户列表，支持搜索和排序",
        parameters=[
            {
                'name': 'username',
                'in': 'query',
                'description': '用户名（模糊搜索）',
                'required': False,
                'schema': {'type': 'string'}
            },
            {
                'name': 'phone',
                'in': 'query',
                'description': '手机号（模糊搜索）',
                'required': False,
                'schema': {'type': 'string'}
            },
            {
                'name': 'email',
                'in': 'query',
                'description': '邮箱（模糊搜索）',
                'required': False,
                'schema': {'type': 'string'}
            },
            {
                'name': 'gender',
                'in': 'query',
                'description': '性别',
                'required': False,
                'schema': {'type': 'string', 'enum': ['male', 'female', 'unknown']}
            },
            {
                'name': 'role',
                'in': 'query',
                'description': '角色',
                'required': False,
                'schema': {'type': 'string', 'enum': ['user', 'admin']}
            },
            {
                'name': 'is_active',
                'in': 'query',
                'description': '是否有效',
                'required': False,
                'schema': {'type': 'boolean'}
            },
            {
                'name': 'id',
                'in': 'query',
                'description': '用户ID',
                'required': False,
                'schema': {'type': 'integer'}
            },
            {
                'name': 'ordering',
                'in': 'query',
                'description': '排序字段',
                'required': False,
                'schema': {'type': 'string', 'enum': ['created_at', '-created_at', 'last_login', '-last_login']}
            }
        ],
        responses={
            200: UserManagementListResponseSerializer,
            403: ErrorResponseSerializer,
            500: ErrorResponseSerializer,
        },
        tags=["用户管理（管理员）"]
    )
    def list(self, request, *args, **kwargs):
        """
        获取用户列表
        """
        try:
            response = super().list(request, *args, **kwargs)
            return Response({
                'code': 200,
                'message': '获取用户列表成功',
                'data': response.data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            error_logger(f"获取用户列表时发生错误: {str(e)}")
            return Response({
                'code': 500,
                'message': '服务器内部错误',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @extend_schema(
        operation_id="admin_get_user",
        summary="获取用户详情",
        description="管理员获取指定用户的详细信息",
        responses={
            200: UserManagementDetailResponseSerializer,
            404: ErrorResponseSerializer,
            403: ErrorResponseSerializer,
            500: ErrorResponseSerializer,
        },
        tags=["用户管理（管理员）"]
    )
    def retrieve(self, request, *args, **kwargs):
        """
        获取用户详情
        """
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            return Response({
                'code': 200,
                'message': '获取用户详情成功',
                'data': serializer.data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            error_logger(f"获取用户详情时发生错误: {str(e)}")
            return Response({
                'code': 500,
                'message': '服务器内部错误',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @extend_schema(
        operation_id="admin_create_user",
        summary="创建用户",
        description="管理员创建新用户",
        request=UserCreateSerializer,
        responses={
            201: UserManagementDetailResponseSerializer,
            400: ErrorResponseSerializer,
            403: ErrorResponseSerializer,
            500: ErrorResponseSerializer,
        },
        tags=["用户管理（管理员）"]
    )
    def create(self, request, *args, **kwargs):
        """
        创建用户
        """
        try:
            serializer = self.get_serializer(data=request.data)
            if serializer.is_valid():
                user = serializer.save()
                info_logger(f"管理员 {request.user.username} 创建了新用户 {user.username}")
                
                response_serializer = UserManagementSerializer(user)
                return Response({
                    'code': 201,
                    'message': '创建用户成功',
                    'data': response_serializer.data
                }, status=status.HTTP_201_CREATED)
            else:
                return Response({
                    'code': 400,
                    'message': '创建用户失败',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            error_logger(f"创建用户时发生错误: {str(e)}")
            return Response({
                'code': 500,
                'message': '服务器内部错误',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @extend_schema(
        operation_id="admin_update_user",
        summary="更新用户信息",
        description="管理员更新指定用户的信息",
        request=UserUpdateSerializer,
        responses={
            200: UserManagementDetailResponseSerializer,
            400: ErrorResponseSerializer,
            404: ErrorResponseSerializer,
            403: ErrorResponseSerializer,
            500: ErrorResponseSerializer,
        },
        tags=["用户管理（管理员）"]
    )
    def update(self, request, *args, **kwargs):
        """
        更新用户信息
        """
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data)
            if serializer.is_valid():
                user = serializer.save()
                info_logger(f"管理员 {request.user.username} 更新了用户 {user.username} 的信息")
                
                response_serializer = UserManagementSerializer(user)
                return Response({
                    'code': 200,
                    'message': '更新用户信息成功',
                    'data': response_serializer.data
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'code': 400,
                    'message': '更新用户信息失败',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            error_logger(f"更新用户信息时发生错误: {str(e)}")
            return Response({
                'code': 500,
                'message': '服务器内部错误',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @extend_schema(
        operation_id="admin_delete_user",
        summary="删除用户",
        description="管理员删除指定用户",
        responses={
            200: BaseResponseSerializer,
            404: ErrorResponseSerializer,
            403: ErrorResponseSerializer,
            500: ErrorResponseSerializer,
        },
        tags=["用户管理（管理员）"]
    )
    def destroy(self, request, *args, **kwargs):
        """
        删除用户
        """
        try:
            instance = self.get_object()
            username = instance.username
            instance.delete()
            info_logger(f"管理员 {request.user.username} 删除了用户 {username}")
            
            return Response({
                'code': 200,
                'message': '删除用户成功'
            }, status=status.HTTP_200_OK)
        except Exception as e:
            error_logger(f"删除用户时发生错误: {str(e)}")
            return Response({
                'code': 500,
                'message': '服务器内部错误',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @extend_schema(
        operation_id="admin_toggle_user_status",
        summary="切换用户有效状态",
        description="管理员切换指定用户的有效状态（启用/禁用）",
        responses={
            200: UserManagementDetailResponseSerializer,
            404: ErrorResponseSerializer,
            403: ErrorResponseSerializer,
            500: ErrorResponseSerializer,
        },
        tags=["用户管理（管理员）"]
    )
    @action(detail=True, methods=['post'])
    def toggle_status(self, request, pk=None):
        """
        切换用户有效状态
        """
        try:
            user = self.get_object()
            user.is_active = not user.is_active
            user.save()
            
            status_text = "启用" if user.is_active else "禁用"
            info_logger(f"管理员 {request.user.username} {status_text}了用户 {user.username}")
            
            serializer = UserManagementSerializer(user)
            return Response({
                'code': 200,
                'message': f'用户状态切换成功，当前状态：{status_text}',
                'data': serializer.data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            error_logger(f"切换用户状态时发生错误: {str(e)}")
            return Response({
                'code': 500,
                'message': '服务器内部错误',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @extend_schema(
        operation_id="admin_reset_user_password",
        summary="重置用户密码",
        description="管理员重置指定用户的密码",
        request=PasswordResetSerializer,
        responses={
            200: PasswordResetResponseSerializer,
            400: ErrorResponseSerializer,
            404: ErrorResponseSerializer,
            403: ErrorResponseSerializer,
            500: ErrorResponseSerializer,
        },
        tags=["用户管理（管理员）"]
    )
    @action(detail=True, methods=['post'])
    def reset_password(self, request, pk=None):
        """
        重置用户密码
        """
        try:
            user = self.get_object()
            serializer = PasswordResetSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save(user)
                info_logger(f"管理员 {request.user.username} 重置了用户 {user.username} 的密码")
                
                return Response({
                    'code': 200,
                    'message': '密码重置成功'
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'code': 400,
                    'message': '密码重置失败',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            error_logger(f"重置密码时发生错误: {str(e)}")
            return Response({
                'code': 500,
                'message': '服务器内部错误',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @extend_schema(
        operation_id="admin_upload_user_avatar",
        summary="上传用户头像",
        description="管理员为指定用户上传头像",
        request={
            'multipart/form-data': {
                'type': 'object',
                'properties': {
                    'avatar': {
                        'type': 'string',
                        'format': 'binary',
                        'description': '用户头像文件'
                    }
                }
            }
        },
        responses={
            200: AvatarUploadResponseSerializer,
            400: ErrorResponseSerializer,
            404: ErrorResponseSerializer,
            403: ErrorResponseSerializer,
            500: ErrorResponseSerializer,
        },
        tags=["用户管理（管理员）"]
    )
    @action(detail=True, methods=['post'])
    def upload_avatar(self, request, pk=None):
        """
        为用户上传头像
        """
        try:
            user = self.get_object()
            serializer = UserAvatarManagementSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save(user)
                avatar_url = user.avatar.url if user.avatar else None
                
                info_logger(f"管理员 {request.user.username} 为用户 {user.username} 上传了头像")
                
                return Response({
                    'code': 200,
                    'message': '头像上传成功',
                    'data': {
                        'avatar_url': avatar_url
                    }
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'code': 400,
                    'message': '头像上传失败',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            error_logger(f"上传头像时发生错误: {str(e)}")
            return Response({
                'code': 500,
                'message': '服务器内部错误',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @extend_schema(
        operation_id="admin_delete_user_avatar",
        summary="删除用户头像",
        description="管理员删除指定用户的头像",
        responses={
            200: AvatarDeleteResponseSerializer,
            404: ErrorResponseSerializer,
            403: ErrorResponseSerializer,
            500: ErrorResponseSerializer,
        },
        tags=["用户管理（管理员）"]
    )
    @action(detail=True, methods=['delete'])
    def delete_avatar(self, request, pk=None):
        """
        删除用户头像
        """
        try:
            user = self.get_object()
            
            if user.avatar:
                user.delete_old_avatar()
                user.avatar = None
                user.save()
                
                info_logger(f"管理员 {request.user.username} 删除了用户 {user.username} 的头像")
                
                return Response({
                    'code': 200,
                    'message': '头像删除成功'
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'code': 400,
                    'message': '用户暂无头像'
                }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            error_logger(f"删除头像时发生错误: {str(e)}")
            return Response({
                'code': 500,
                'message': '服务器内部错误',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
