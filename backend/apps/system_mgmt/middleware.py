class OperationLogMiddleware:
    """操作日志 middleware：拦截写请求（POST/PUT/PATCH/DELETE）自动记录。

    记录失败（如字段超长、DB 抖动）静默吞掉，绝不影响业务响应。
    """

    WRITE_METHODS = ('POST', 'PUT', 'PATCH', 'DELETE')

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if request.method in self.WRITE_METHODS \
                and hasattr(request, 'user') and request.user.is_authenticated:
            try:
                from .models import OperationLog
                OperationLog.objects.create(
                    user=request.user, action=request.method,
                    model_name='', object_id=None,
                    path=request.path[:256], detail=None,
                )
            except Exception:
                pass
        return response
