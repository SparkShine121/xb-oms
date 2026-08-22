import pytest
from django.core.management import call_command

@pytest.fixture(autouse=True)
def ensure_groups(db):
    call_command('create_groups')
