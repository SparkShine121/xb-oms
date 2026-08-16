from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import TrackingViewSet

router = DefaultRouter()
router.register('orders', TrackingViewSet, basename='tracking')
urlpatterns = router.urls + [
    path('my/', TrackingViewSet.as_view({'get': 'my'}), name='tracking-my'),
]
