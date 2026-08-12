import pytest
from django.core.management import call_command


@pytest.fixture(autouse=True)
def ensure_groups(db):
    """每个测试前确保 4 个角色 Group 存在（pytest-django 测试库为新建库，测试依赖 Group 存在）。"""
    call_command('create_groups')
