import logging

from django.db import IntegrityError
from rest_framework.views import exception_handler
from rest_framework.response import Response

logger = logging.getLogger(__name__)

ERROR_CODES = {
    400: 1001, 401: 1002, 403: 1003, 404: 1004, 500: 5000,
}

def _flatten_message(data):
    """400 字段级错误 dict（{'name': ['已存在同名客户']}）拍平为可读字符串，
    前端 toast 可直接显示（BUG-SIM-007 followup / UX 问题清单#6）。"""
    parts = []
    for v in data.values():
        if isinstance(v, (list, tuple)):
            parts.extend(str(i) for i in v)
        else:
            parts.append(str(v))
    return '；'.join(parts)

def custom_exception_handler(exc, context):
    if isinstance(exc, IntegrityError):
        # 仅唯一性冲突映射为 400；FK/非空/Check 等其余完整性错误保持 500 语义并留日志
        cause = str(getattr(exc, '__cause__', None) or exc)
        if 'UNIQUE constraint failed' in cause or 'Duplicate entry' in cause or '1062' in cause:
            return Response({'code': 1001, 'message': '保存失败：数据重复或唯一性冲突', 'data': None}, status=400)
        logger.exception('数据库完整性错误（非唯一性冲突）：%s', exc)
        return Response({'code': 5000, 'message': '服务器内部错误', 'data': None}, status=500)
    response = exception_handler(exc, context)
    if response is not None:
        code = ERROR_CODES.get(response.status_code, 5000)
        if isinstance(response.data, dict) and 'detail' in response.data:
            message = response.data['detail']
        elif isinstance(response.data, dict):
            message = _flatten_message(response.data)
        else:
            message = str(response.data)
        response.data = {'code': code, 'message': message, 'data': None}
    return response
