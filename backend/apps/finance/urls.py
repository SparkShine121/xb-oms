from rest_framework.routers import DefaultRouter

from .views import PaymentInViewSet

router = DefaultRouter()
router.register('payments-in', PaymentInViewSet, basename='payments-in')
urlpatterns = router.urls
