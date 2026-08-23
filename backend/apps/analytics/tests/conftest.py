import pytest
from django.core.management import call_command


@pytest.fixture(autouse=True)
def ensure_groups(db):
    """数据分析权限依赖角色组（admin/finance），测试前确保已创建。"""
    call_command('create_groups')
