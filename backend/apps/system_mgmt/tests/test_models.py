import pytest
from django.contrib.auth.models import User, Group
from rest_framework.test import APIClient

from apps.system_mgmt.models import ApprovalRequest, OperationLog, BackupRecord


def _make_user(name, group_name):
    u = User.objects.create_user(name, password='pw123456')
    u.groups.add(Group.objects.get(name=group_name))
    return u


# ---- ApprovalRequest ----

def test_approval_request_crud(db):
    submitter = _make_user('sales1', 'salesman')
    reviewer = _make_user('adm', 'admin')
    ar = ApprovalRequest.objects.create(
        approval_type='settlement', target_id=1,
        target_model='FactoryPayment', submitted_by=submitter)
    assert ar.status == 'pending'
    assert ar.note == ''

    ar.status = 'approved'
    ar.reviewed_by = reviewer
    ar.save()
    ar.refresh_from_db()
    assert ar.status == 'approved'
    assert ar.reviewed_by_id == reviewer.id

    # related_name 校验
    assert list(submitter.approval_requests.all()) == [ar]
    assert list(reviewer.reviewed_requests.all()) == [ar]

    # 提交人删除 → SET_NULL 不级联
    submitter.delete()
    ar.refresh_from_db()
    assert ar.submitted_by is None

    ar.delete()
    assert ApprovalRequest.objects.count() == 0


def test_approval_request_type_choices(db):
    for t in ('settlement', 'payment', 'order_change', 'logistics'):
        ApprovalRequest.objects.create(approval_type=t, target_id=t.__hash__() % 1000 + 1,
                                       target_model='X')
    assert ApprovalRequest.objects.count() == 4


# ---- OperationLog ----

def test_operation_log_crud(db):
    u = _make_user('op1', 'tracker')
    log = OperationLog.objects.create(
        user=u, action='POST', model_name='', object_id=None,
        path='/api/orders/', detail=None)
    log.refresh_from_db()
    assert log.action == 'POST'
    assert log.created_at is not None
    assert list(u.operation_logs.all()) == [log]
    log.delete()
    assert OperationLog.objects.count() == 0


def test_operation_middleware_logs_write_requests(db):
    """POST/PUT/PATCH/DELETE 已认证请求自动记录操作日志；GET 不记录。"""
    from django.http import HttpResponse
    from django.test import RequestFactory
    from apps.system_mgmt.middleware import OperationLogMiddleware

    u = _make_user('mw_u', 'admin')
    mw = OperationLogMiddleware(lambda r: HttpResponse('ok'))
    rf = RequestFactory()

    req = rf.get('/api/basic-info/factories/')
    req.user = u
    mw(req)
    assert OperationLog.objects.count() == 0

    req = rf.post('/api/basic-info/factories/', {'name': '华鑫'})
    req.user = u
    mw(req)
    logs = OperationLog.objects.filter(path='/api/basic-info/factories/')
    assert logs.count() == 1
    assert logs.first().action == 'POST'
    assert logs.first().user_id == u.id


def test_operation_middleware_ignores_anonymous_and_errors(db):
    """未认证请求不记录；记录失败不影响响应。"""
    from unittest.mock import patch
    from django.http import HttpResponse
    from django.test import RequestFactory
    from apps.system_mgmt.middleware import OperationLogMiddleware

    rf = RequestFactory()
    mw = OperationLogMiddleware(lambda r: HttpResponse('ok'))

    req = rf.post('/api/auth/login/')  # 未认证（无 user 属性）
    mw(req)
    assert OperationLog.objects.count() == 0

    from django.contrib.auth.models import AnonymousUser
    req = rf.delete('/api/whatever/999/')
    req.user = AnonymousUser()
    mw(req)
    assert OperationLog.objects.count() == 0

    u = _make_user('mw_e', 'admin')
    req = rf.delete('/api/whatever/999/')
    req.user = u
    with patch('apps.system_mgmt.models.OperationLog.objects.create',
               side_effect=RuntimeError('boom')):
        resp = mw(req)  # 不抛异常
    assert resp.status_code == 200


def test_operation_middleware_registered():
    """middleware 已注册到 MIDDLEWARE 配置末尾。"""
    from django.conf import settings
    assert settings.MIDDLEWARE[-1] == 'apps.system_mgmt.middleware.OperationLogMiddleware'


# ---- BackupRecord ----

def test_backup_record_crud(db):
    br = BackupRecord.objects.create(file_path='backups/b1.db', file_size=1024,
                                     trigger='manual')
    br.refresh_from_db()
    assert br.file_size == 1024
    assert br.trigger == 'manual'
    assert br.created_at is not None

    br2 = BackupRecord.objects.create(file_path='backups/b2.db')  # trigger 默认 manual
    assert br2.trigger == 'manual'

    br.delete()
    assert BackupRecord.objects.count() == 1
    br2.delete()
    assert BackupRecord.objects.count() == 0
