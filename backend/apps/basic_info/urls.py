from rest_framework.routers import DefaultRouter
from .views import CategoryViewSet, ProductViewSet, FactoryViewSet, LogisticsProviderViewSet, CustomerViewSet
router = DefaultRouter()
router.register('categories', CategoryViewSet, basename='category')
router.register('products', ProductViewSet, basename='product')
router.register('factories', FactoryViewSet, basename='factory')
router.register('logistics', LogisticsProviderViewSet, basename='logistics')
router.register('customers', CustomerViewSet, basename='customer')
urlpatterns = router.urls
