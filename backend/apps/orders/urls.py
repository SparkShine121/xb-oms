from rest_framework.routers import DefaultRouter
from .views import OrderViewSet, ExchangeRateViewSet

router = DefaultRouter()
router.register('orders', OrderViewSet, basename='order')
router.register('exchange-rates', ExchangeRateViewSet, basename='exchangerate')
urlpatterns = router.urls