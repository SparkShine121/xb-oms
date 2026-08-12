import pytest
from django.core.management import call_command


@pytest.fixture(autouse=True)
def ensure_groups(db):
    """每个测试前确保 4 个角色 Group 存在（测试数据库为会话级新建，admin_user 等 fixture 依赖它们）。"""
    call_command('create_groups')
