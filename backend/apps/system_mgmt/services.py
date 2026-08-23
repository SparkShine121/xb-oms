"""备份服务：SQLite 在线备份 + 滚动清理。

审批通过（trigger='approval'）与手动备份（trigger='manual'）共用。
生产环境为 MySQL 时跳过（返回 None），备份策略另行部署。
"""

import os
import sqlite3
from pathlib import Path

from django.conf import settings
from django.db import connection
from django.utils import timezone


def _backup_dir() -> Path:
    d = Path(getattr(settings, 'BACKUP_DIR', Path(settings.BASE_DIR) / 'backups'))
    d.mkdir(parents=True, exist_ok=True)
    return d


def perform_backup(trigger):
    """执行一次 SQLite .backup → 落盘 + BackupRecord，返回记录；非 SQLite 返回 None。"""
    if not connection.settings_dict['ENGINE'].endswith('sqlite3'):
        return None

    from .models import BackupRecord

    connection.ensure_connection()
    name = f"backup_{timezone.localtime().strftime('%Y%m%d_%H%M%S_%f')}_{trigger}.db"
    dest_path = _backup_dir() / name
    dest = sqlite3.connect(str(dest_path))
    try:
        connection.connection.backup(dest)
    finally:
        dest.close()

    br = BackupRecord.objects.create(
        file_path=str(dest_path),
        file_size=dest_path.stat().st_size,
        trigger=trigger,
    )
    cleanup_old_backups()
    return br


def cleanup_old_backups():
    """滚动保留最近 BACKUP_MAX_COUNT 份，超出部分删最旧（记录 + 文件）。"""
    max_count = int(getattr(settings, 'BACKUP_MAX_COUNT', 1000))
    from .models import BackupRecord

    # id 单调递增，按 -id 即最新在前；切片取超出上限的最旧部分
    stale = BackupRecord.objects.order_by('-id')[max_count:]
    for br in stale:
        try:
            os.remove(br.file_path)
        except OSError:
            pass  # 文件已不存在/被移动：仍需清掉孤儿记录
        br.delete()
