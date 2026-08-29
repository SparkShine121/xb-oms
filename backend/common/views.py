from rest_framework import viewsets
from rest_framework.decorators import action
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
        ids = request.data.get('ids') or []
        if not isinstance(ids, list) or not ids:
            return error_response(1001, '未指定要删除的记录', status=400)
        qs = self.get_queryset().filter(pk__in=ids)
        deleted = 0
        for obj in qs:
            self.check_object_permissions(request, obj)
            obj.delete()
            deleted += 1
        return success_response({'deleted': deleted}, message='已删除')
