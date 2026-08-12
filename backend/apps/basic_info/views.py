from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from common.permissions import AdminWriteOthersReadOnly
from common.response import success_response
from common.views import BaseModelViewSet
from .models import Category, Product
from .serializers import CategorySerializer, CategoryTreeSerializer, ProductSerializer

class CategoryViewSet(BaseModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated, AdminWriteOthersReadOnly]
    filterset_fields = ['parent']
    search_fields = ['name']

    @action(detail=False, methods=['get'])
    def tree(self, request):
        roots = Category.objects.filter(parent__isnull=True)
        return success_response(CategoryTreeSerializer(roots, many=True).data)

class ProductViewSet(BaseModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated, AdminWriteOthersReadOnly]
    filterset_fields = ['category']
    search_fields = ['product_no', 'model', 'name']
    ordering_fields = ['id', 'updated_at']
