from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework.routers import DefaultRouter
from .views import LoginView, MeView, LogoutView, UserViewSet
from django.urls import path

urlpatterns = [
    path('login/', LoginView.as_view()),
    path('refresh/', TokenRefreshView.as_view()),
    path('logout/', LogoutView.as_view()),
    path('me/', MeView.as_view()),
]

router = DefaultRouter()
router.register('users', UserViewSet, basename='user')
urlpatterns += router.urls
