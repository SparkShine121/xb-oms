from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from common.response import success_response, error_response
from .serializers import LoginSerializer, UserSerializer

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
