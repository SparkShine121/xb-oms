"""Django 公共设置（base）：所有环境共享。

dev.py / prod.py 通过 `from .base import *` 继承，并各自覆盖环境相关配置。
"""

import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

# 项目根目录（backend/）
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# 加载 backend/.env（若存在；键值见 .env.example）
load_dotenv(BASE_DIR / ".env")

# SECRET_KEY / DEBUG / ALLOWED_HOSTS 由 dev.py、prod.py 各自定义

# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # 第三方
    "rest_framework",
    "rest_framework_simplejwt.token_blacklist",
    "django_filters",
    # 业务应用
    "apps.accounts",
    "apps.basic_info",
    "apps.orders",
    "apps.tracking",
    "apps.factory_payment",
    "apps.logistics",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "xb_project.urls"

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

WSGI_APPLICATION = "xb_project.wsgi.application"
ASGI_APPLICATION = "xb_project.asgi.application"

# Database
# 不在此处定义，由 dev.py（SQLite）/ prod.py（MySQL）覆盖

# AUTH 预留：自定义用户模型，待 apps.accounts 实现后启用
# AUTH_USER_MODEL = "accounts.User"

# Password validation

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

LANGUAGE_CODE = "zh-hans"

TIME_ZONE = "Asia/Shanghai"

USE_I18N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)

STATIC_URL = "static/"

# Default primary key field type

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# JWT（djangorestframework-simplejwt）
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=8),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
}

# DRF（djangorestframework）
REST_FRAMEWORK = {
    # 默认认证：JWT（djangorestframework-simplejwt）
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    # 默认分页器：common.pagination.StandardResultsSetPagination（page_size=20）
    "DEFAULT_PAGINATION_CLASS": "common.pagination.StandardResultsSetPagination",
    # 过滤后端：django-filter 精确筛选（filterset_fields）+ 搜索（search_fields）+ 排序
    "DEFAULT_FILTER_BACKENDS": (
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ),
    # 统一异常处理器：common.exceptions.custom_exception_handler
    "EXCEPTION_HANDLER": "common.exceptions.custom_exception_handler",
}

# Media files（上传文件：跟单照片等）
MEDIA_ROOT = BASE_DIR / 'media'
MEDIA_URL = '/media/'
