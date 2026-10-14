class OperationLogMiddleware:
    """操作日志 middleware：拦截写请求（POST/PUT/PATCH/DELETE）自动记录。

    Django 中间件层的 request.user 基于 session，纯 JWT Bearer 请求在此为
    AnonymousUser（DRF 只填充其 Request 包装器）。因此 request.user 未认证时
    再从 Authorization 头解析 JWT 取真实用户；两者都拿不到则不记录。
    记录失败（如字段超长、DB 抖动）静默吞掉，绝不影响业务响应。
    """

    WRITE_METHODS = ('POST', 'PUT', 'PATCH', 'DELETE')

    @staticmethod
    def _mask(data):
        """递归脱敏：顶层与嵌套 dict/list 中的敏感键统一 ***（BUG-SIM-026 followup）。"""
        if isinstance(data, dict):
            return {
                k: ('***' if k.lower() in OperationLogMiddleware.SENSITIVE_KEYS else OperationLogMiddleware._mask(v))
                for k, v in data.items()
            }
        if isinstance(data, list):
            return [OperationLogMiddleware._mask(v) for v in data]
        return data

    def __init__(self, get_response):
        self.get_response = get_response

    # BUG-SIM-026 Q1:a：请求体中的敏感键统一脱敏
    SENSITIVE_KEYS = {'password', 'old_password', 'new_password', 'refresh', 'access', 'token'}

    def __call__(self, request):
        response = self.get_response(request)
        if request.method in self.WRITE_METHODS:
            try:
                user = self._resolve_user(request)
                if user is not None and user.is_authenticated:
                    from .models import OperationLog
                    model_name, object_id, detail = self._describe(request, response)
                    OperationLog.objects.create(
                        user=user, action=request.method,
                        model_name=model_name, object_id=object_id,
                        path=request.path[:256], detail=detail,
                    )
            except Exception:
                pass
        return response

    @staticmethod
    def _describe(request, response):
        """BUG-SIM-026 Q1:a：从路由解析 model/object_id，构造脱敏请求体摘要。

        model_name：resolve 命中的 ViewSet queryset 的模型名（无 queryset 视图留空）
        object_id：detail 路由 kwargs 中的 pk（纯数字）
        detail：{status, body}——body 为 JSON 请求体摘要（敏感键 ***、非 JSON 记
        content_type、超 2000 字符截断）
        """
        import json
        from django.urls import resolve as url_resolve
        model_name, object_id = '', None
        try:
            match = url_resolve(request.path)
            # DRF ViewSetMixin.as_view 挂 cls；Django View.as_view 挂 view_class
            view_cls = getattr(match.func, 'cls', None) or getattr(match.func, 'view_class', None)
            qs = getattr(view_cls, 'queryset', None)
            if qs is not None:
                model_name = qs.model._meta.object_name
            pk = match.kwargs.get('pk')
            if pk is not None and str(pk).isdigit():
                object_id = int(pk)
        except Exception:
            pass

        body = None
        try:
            raw = request.body
            if raw:
                try:
                    parsed = json.loads(raw)
                    if isinstance(parsed, dict):
                        masked = OperationLogMiddleware._mask(parsed)
                        body = json.dumps(masked, ensure_ascii=False, default=str)[:2000]
                except json.JSONDecodeError:
                    body = f'<{request.content_type or "unknown"}>'
        except Exception:
            body = f'<unreadable:{request.content_type or "unknown"}>'  # 流已被视图消费（如 multipart 上传）

        detail = {'status': response.status_code}
        if body:
            detail['body'] = body
        # POST 列路由：URL 无 pk，新建对象 ID 从统一响应 envelope 的 data.id 取
        if request.method == 'POST' and object_id is None:
            try:
                data = getattr(response, 'data', None)
                inner = data.get('data') if isinstance(data, dict) else None
                if isinstance(inner, dict) and str(inner.get('id', '')).isdigit():
                    object_id = int(inner['id'])
            except Exception:
                pass
        return model_name, object_id, detail

    @staticmethod
    def _resolve_user(request):
        user = getattr(request, 'user', None)
        if user is not None and user.is_authenticated:
            return user
        # JWT Bearer：中间件层 request.user 为匿名，需自行解析
        from rest_framework_simplejwt.authentication import JWTAuthentication
        result = JWTAuthentication().authenticate(request)
        return result[0] if result else None
