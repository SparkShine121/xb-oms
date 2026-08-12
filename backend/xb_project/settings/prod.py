"""生产环境设置。

数据库连接信息（MySQL）从环境变量读取：
DB_NAME / DB_USER / DB_PASSWORD / DB_HOST / DB_PORT，键名见 backend/.env.example。
生产环境需安装 MySQL 驱动（mysqlclient），本机 ARM64 开发期不验证。
"""

import os

from .base import *  # noqa: F401,F403

DEBUG = False

# 部署时按实际域名/IP 配置
ALLOWED_HOSTS = []

# SECRET_KEY 必须由环境变量提供（缺失即启动失败，避免误用弱密钥）
SECRET_KEY = os.environ["SECRET_KEY"]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": os.environ.get("DB_NAME", "xb_dev"),
        "USER": os.environ.get("DB_USER", "xb"),
        "PASSWORD": os.environ.get("DB_PASSWORD", ""),
        "HOST": os.environ.get("DB_HOST", "127.0.0.1"),
        "PORT": os.environ.get("DB_PORT", "3306"),
        "CONN_MAX_AGE": 60,
        "OPTIONS": {
            "charset": "utf8mb4",
        },
    }
}
