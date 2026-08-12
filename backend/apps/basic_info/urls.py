from rest_framework.routers import DefaultRouter
from .views import CategoryViewSet, ProductViewSet, FactoryViewSet
router = DefaultRouter()
router.register('categories', CategoryViewSet, basename='category')
router.register('products', ProductViewSet, basename='product')
router.register('factories', FactoryViewSet, basename='factory')
urlpatterns = router.urls
