"""开发环境设置。

说明：本机为 Windows 11 on ARM64，MySQL 无原生 ARM64 版本，
开发阶段使用 SQLite，部署时切换到 prod.py 的 MySQL 配置。
"""

import os

from .base import *  # noqa: F401,F403

DEBUG = True

ALLOWED_HOSTS = ["*"]

# 开发用 SQLite
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# SECRET_KEY：优先从 .env 读取，未配置时使用开发用默认值（仅限开发）
SECRET_KEY = os.environ.get(
    "SECRET_KEY", "django-insecure-dev-only-do-not-use-in-production"
)

# CORS / Vite 代理：前端开发服务器通过 Vite 代理访问 API（同源，无需 CORS）。
# 若需要前端跨域直连，再引入 django-cors-headers 并配置 CORS_ALLOWED_ORIGINS。
