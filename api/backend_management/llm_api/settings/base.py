import logging
import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-insecure-_bfh4@oxyvbq%q@h)p&(n+$54wth6nd11n**gdy480b86w0_(&"

ALLOWED_HOSTS = ['*']

# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    'rest_framework',  # DRF
    'drf_yasg',  # swagger
    'corsheaders',  # 跨域
    'rest_framework_simplejwt',  # JWT
    'rest_framework_simplejwt.token_blacklist',  # JWT token黑名单
    'django_apscheduler',  # 定时任务
    'django_redis',  # redis
    'django_filters',  # django-filter
    'drf_spectacular',  # 注册应用
    'drf_spectacular_sidecar',  # 如果安装了 sidecar
    'user',
    'storages',
    'knowledge',
    'provider',
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    'corsheaders.middleware.CorsMiddleware',
]

ROOT_URLCONF = "llm_api.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "llm_api.wsgi.application"

# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)  
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = "static/"

# 自定义用户模型
AUTH_USER_MODEL = 'user.CustomUser'

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10,
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'EXCEPTION_HANDLER': 'errors.global_exception_handler',
    'DEFAULT_FILTER_BACKENDS': ['django_filters.rest_framework.DjangoFilterBackend']
}

# JWT配置
from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),  # 访问token有效期1小时
    'REFRESH_TOKEN_LIFETIME': timedelta(days=15),    # 刷新token有效期15天（满足15天免登录需求）
    'ROTATE_REFRESH_TOKENS': True,                   # 刷新token时是否生成新的refresh token
    'BLACKLIST_AFTER_ROTATION': True,               # 是否将旧的refresh token列入黑名单
    'UPDATE_LAST_LOGIN': True,                       # 是否更新最后登录时间
    
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUDIENCE': None,
    'ISSUER': None,
    'JWK_URL': None,
    'LEEWAY': 0,

    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'USER_AUTHENTICATION_RULE': 'rest_framework_simplejwt.authentication.default_user_authentication_rule',

    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    'TOKEN_USER_CLASS': 'rest_framework_simplejwt.models.TokenUser',

    'JTI_CLAIM': 'jti',

    'SLIDING_TOKEN_REFRESH_EXP_CLAIM': 'refresh_exp',
    'SLIDING_TOKEN_LIFETIME': timedelta(minutes=60),
    'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(days=15),
}

# Spectacular 配置
SPECTACULAR_SETTINGS = {
    'TITLE': 'AI Native Platform API',
    'DESCRIPTION': 'AI Native Platform',
    'VERSION': '0.0.1',
    'SERVE_INCLUDE_SCHEMA': False,
    'SWAGGER_UI_DIST': 'SIDECAR',  # Sidecar 模式（静态文件内嵌）
    'SWAGGER_UI_FAVICON_HREF': 'SIDECAR',
    'REDOC_DIST': 'SIDECAR',
    # 其他配置见下文
}

CORS_ORIGIN_ALLOW_ALL = True

CORS_ALLOW_METHODS = [
    'GET',
    'POST',
    'PUT',
    'PATCH',
    'DELETE',
    'OPTIONS'
]

CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with'
]

CORS_ALLOW_CREDENTIALS = True

SWAGGER_SETTINGS = {
    "DEFAULT_INFO": "llm_api.urls.openapi_info",
}

SCHEDULER_AUTOSTART = True

# 日志配置
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
        "default": {
            "format": '%(asctime)s %(name)s  %(pathname)s:%(lineno)d %(module)s:%(funcName)s '
                      '%(levelname)s- %(message)s',
            "datefmt": "%Y-%m-%d %H:%M:%S"
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'default'
        },
        'error': {
            'level': 'ERROR',
            'class': 'logging.StreamHandler',
            # 'filename': os.path.join(BASE_DIR, 'logs/error.log'),
            'formatter': 'default'
        },
        'warning': {
            'level': 'WARNING',
            'class': 'logging.StreamHandler',
            # 'filename': os.path.join(BASE_DIR, 'logs/warning.log'),
            'formatter': 'default'
        },
        'info': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            # 'filename': os.path.join(BASE_DIR, 'logs/info.log'),
            'formatter': 'default'
        },
    },
    'loggers': {
        # 应用中自定义日志记录器
        'error': {
            'level': 'ERROR',
            'handlers': ['console', 'error'],
            'propagate': True,
        },
        'warning': {
            'level': 'WARNING',
            'handlers': ['console', 'warning'],
            'propagate': True,
        },
        'info': {
            'level': 'INFO',
            'handlers': ['console', 'info'],
            'propagate': True,
        },
    },
}

SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'

STATIC_ROOT = os.path.join(BASE_DIR, 'static')

MEDIA_URL = '/media/'  # 默认存储在项目根目录下的media文件夹
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')  # 默认存储在项目根目录下的media文件夹

# 腾讯云COS配置 - 修正配置键名与cos_storage.py一致
COS_SECRET_ID = os.getenv('TENCENT_COS_SECRET_ID', 'test_secret_id')
COS_SECRET_KEY = os.getenv('TENCENT_COS_SECRET_KEY', 'test_secret_key') 
COS_REGION = os.getenv('TENCENT_COS_REGION', 'ap-beijing')
COS_BUCKET = os.getenv('TENCENT_COS_BUCKET', 'test-bucket')
COS_URL = os.getenv('TENCENT_COS_DOMAIN', 'https://test-bucket.cos.ap-beijing.myqcloud.com')

STORAGES = {
    'staticfiles': {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"
    },
    "default": {
        # 使用腾讯云存储
        "BACKEND": "utils.cos_storage.TencentCOSStorage",
    }
}

error_logger = logging.getLogger('error').error
warning_logger = logging.getLogger('warning').warning
info_logger = logging.getLogger('info').info

# 文件上传设置
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB

# 允许的图片格式
ALLOWED_IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB
