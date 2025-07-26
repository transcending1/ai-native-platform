try:
    from .base import *
except ImportError:
    pass

DEBUG = True

# 使用SQLite作为本地测试数据库
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# 使用本地缓存
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

# 关闭腾讯云存储，使用本地文件存储
DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage' 