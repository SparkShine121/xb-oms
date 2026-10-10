from django.core.cache import cache
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from common.response import success_response, error_response
from common.permissions import RolePermission
from common.views import BaseModelViewSet
from .serializers import LoginSerializer, UserSerializer, UserManageSerializer, validate_password_policy

LOGIN_FAIL_LIMIT = 5     # 5 次失败
LOGIN_WINDOW = 300       # 计数窗口 5 分钟
LOGIN_LOCKOUT = 600      # 锁定 10 分钟


def _client_ip(request):
    # followup：优先 REMOTE_ADDR（直连下 XFF 可伪造）；生产经反代时由反代覆盖
    # X-Forwarded-For 且后端以 REMOTE_ADDR 见到反代——如需信任 XFF 须配可信代理白名单
    xff = request.META.get('HTTP_X_FORWARDED_FOR', '')
    remote = request.META.get('REMOTE_ADDR', '')
    # 仅当直连地址是本机回环/内网反代特征时才采信 XFF 首段（简单启发，生产建议配 ipware）
    if xff and remote in ('127.0.0.1', '::1'):
        return xff.split(',')[0].strip()
    return remote


class LoginView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        # BUG-SIM-018 Q1:a：按 IP 缓存计数限流（不锁用户名——防恶意锁死真实用户）
        ip = _client_ip(request)
        if cache.get(f'login_lock:{ip}'):
            return error_response(1029, '尝试过于频繁，请稍后再试', status=429)
        s = LoginSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        user = authenticate(username=s.validated_data['username'], password=s.validated_data['password'])
        if not user:
            fails = cache.get(f'login_fail:{ip}', 0) + 1
            if fails >= LOGIN_FAIL_LIMIT:
                cache.set(f'login_lock:{ip}', True, LOGIN_LOCKOUT)
                cache.delete(f'login_fail:{ip}')
            else:
                cache.set(f'login_fail:{ip}', fails, LOGIN_WINDOW)
            return error_response(1002, '用户名或密码错误', status=401)
        cache.delete(f'login_fail:{ip}')  # 成功清零
        refresh = RefreshToken.for_user(user)
        return success_response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        })

class MeView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        return success_response(UserSerializer(request.user).data)


class ChangePasswordView(APIView):
    """个人改密（连带补充）：验旧密码 + 新密码走强度规则，让 aa1234 过渡态可自行升级。"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        old_pwd = request.data.get('old_password', '')
        new_pwd = request.data.get('new_password', '')
        if not request.user.check_password(old_pwd):
            return error_response(1002, '旧密码不正确', status=401)
        try:
            validate_password_policy(new_pwd)
        except ValueError as e:
            return error_response(1001, str(e), status=400)
        request.user.set_password(new_pwd)
        request.user.save(update_fields=['password'])
        from .serializers import mark_password_flag
        mark_password_flag(request.user, new_pwd)
        return success_response(None, '密码已修改')

class LogoutView(APIView):
    # followup：refresh token 本身就是拉黑操作的凭证，无需 access 鉴权——
    # 否则 access 过期场景（最需要登出时）blacklist 必然 401，N7 修复在过期路径失效
    permission_classes = [AllowAny]
    def post(self, request):
        try:
            RefreshToken(request.data.get('refresh')).blacklist()
        except Exception:
            pass
        return success_response(None, '已登出')

class UserViewSet(BaseModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserManageSerializer
    permission_classes = [IsAuthenticated, RolePermission]  # RolePermission 默认 allowed_roles=[]，非 admin 全拒
