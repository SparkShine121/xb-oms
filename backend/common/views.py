from django.db import transaction
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied as DRFPermissionDenied
from common.response import success_response, error_response


class BaseModelViewSet(viewsets.ModelViewSet):
    """统一 CRUD 响应包装：所有响应均为 {code, message, data} 结构。

    list/create/retrieve/update/destroy 内部先调用父类逻辑（含分页、
    权限、过滤），再把结果包进 success_response。子类只需声明
    queryset/serializer_class/权限/过滤，无需重复包装。
    """

    def list(self, request, *args, **kwargs):
        resp = super().list(request, *args, **kwargs)
        return success_response(resp.data)

    def create(self, request, *args, **kwargs):
        resp = super().create(request, *args, **kwargs)
        return success_response(resp.data, status=resp.status_code)

    def retrieve(self, request, *args, **kwargs):
        resp = super().retrieve(request, *args, **kwargs)
        return success_response(resp.data)

    def update(self, request, *args, **kwargs):
        resp = super().update(request, *args, **kwargs)
        return success_response(resp.data)

    def destroy(self, request, *args, **kwargs):
        super().destroy(request, *args, **kwargs)
        return success_response(None, message='已删除')

    @action(detail=False, methods=['post'], url_path='bulk-delete')
    def bulk_delete(self, request, *args, **kwargs):
        """批量删除：权限规则与单条删除（destroy）完全一致。

        校验期间把 action 视为 destroy，走完整权限链（操作级
        check_permissions + 逐对象 has_object_permission），
        保证"批量永不比单条更宽松"（BUG-SIM-001）。
        部分失败不中断：响应报告 forbidden（无权限）与
        not_found（范围外/不存在）清单（BUG-SIM-025）。
        """
        ids = request.data.get('ids') or []
        if not isinstance(ids, list) or not ids:
            return error_response(1001, '未指定要删除的记录', status=400)
        original_action = self.action
        self.action = 'destroy'
        try:
            try:
                self.check_permissions(request)
            except DRFPermissionDenied:
                return error_response(1003, '没有删除权限', status=403)
            found = {obj.pk: obj for obj in self.get_queryset().filter(pk__in=ids)}
            forbidden, not_found, deleted = [], [], 0
            with transaction.atomic():
                for oid in ids:
                    obj = found.get(oid)
                    if obj is None and str(oid).lstrip('-').isdigit():
                        obj = found.get(int(oid))
                    if obj is None:
                        not_found.append(oid)
                        continue
                    try:
                        self.check_object_permissions(request, obj)
                    except DRFPermissionDenied:
                        forbidden.append(oid)
                        continue
                    obj.delete()
                    deleted += 1
        finally:
            self.action = original_action
        if deleted == 0 and forbidden and not not_found:
            return error_response(1003, '没有删除权限', status=403)
        return success_response(
            {'deleted': deleted, 'forbidden': forbidden, 'not_found': not_found},
            message='已删除')
