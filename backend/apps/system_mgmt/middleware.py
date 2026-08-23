class OperationLogMiddleware:
    """操作日志 middleware：拦截写请求（POST/PUT/PATCH/DELETE）自动记录。

    Django 中间件层的 request.user 基于 session，纯 JWT Bearer 请求在此为
    AnonymousUser（DRF 只填充其 Request 包装器）。因此 request.user 未认证时
    再从 Authorization 头解析 JWT 取真实用户；两者都拿不到则不记录。
    记录失败（如字段超长、DB 抖动）静默吞掉，绝不影响业务响应。
    """

    WRITE_METHODS = ('POST', 'PUT', 'PATCH', 'DELETE')

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if request.method in self.WRITE_METHODS:
            try:
                user = self._resolve_user(request)
                if user is not None and user.is_authenticated:
                    from .models import OperationLog
                    OperationLog.objects.create(
                        user=user, action=request.method,
                        model_name='', object_id=None,
                        path=request.path[:256], detail=None,
                    )
            except Exception:
                pass
        return response

    @staticmethod
    def _resolve_user(request):
        user = getattr(request, 'user', None)
        if user is not None and user.is_authenticated:
            return user
        # JWT Bearer：中间件层 request.user 为匿名，需自行解析
        from rest_framework_simplejwt.authentication import JWTAuthentication
        result = JWTAuthentication().authenticate(request)
        return result[0] if result else None
