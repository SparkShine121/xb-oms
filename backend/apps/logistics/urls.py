from rest_framework.routers import DefaultRouter

from .views import LogisticsViewSet

router = DefaultRouter()
router.register('shipments', LogisticsViewSet, basename='logistics')
urlpatterns = router.urls
