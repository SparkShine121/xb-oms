from rest_framework.routers import DefaultRouter
from .views import FactoryPaymentViewSet, FactoryPaymentRecordViewSet

router = DefaultRouter()
router.register('payments', FactoryPaymentViewSet, basename='factory-payment')
router.register('records', FactoryPaymentRecordViewSet, basename='factory-payment-record')
urlpatterns = router.urls
