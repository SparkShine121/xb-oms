from rest_framework.views import APIView
from rest_framework import viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from common.response import success_response, error_response
from common.permissions import RolePermission
from .serializers import LoginSerializer, UserSerializer, UserManageSerializer

class LoginView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        s = LoginSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        user = authenticate(username=s.validated_data['username'], password=s.validated_data['password'])
        if not user:
            return error_response(1002, '用户名或密码错误', status=401)
        refresh = RefreshToken.for_user(user)
        return success_response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        })

class MeView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        return success_response(UserSerializer(request.user).data)

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        try:
            RefreshToken(request.data.get('refresh')).blacklist()
        except Exception:
            pass
        return success_response(None, '已登出')

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserManageSerializer
    permission_classes = [IsAuthenticated, RolePermission]
    allowed_roles = []  # 仅 admin（RolePermission 对 admin 直接放行）
