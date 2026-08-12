from django.http import HttpResponse
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from common.permissions import AdminWriteOthersReadOnly
from common.response import success_response, error_response
from common.views import BaseModelViewSet
from .importers import import_products, build_product_template, import_factories, build_factory_template
from .models import Category, Product, Factory, LogisticsProvider, Customer
from .serializers import CategorySerializer, CategoryTreeSerializer, ProductSerializer, FactorySerializer, LogisticsProviderSerializer, CustomerSerializer

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

    @action(detail=False, methods=['post'], url_path='import')
    def import_data(self, request):
        f = request.FILES.get('file')
        if not f:
            return error_response(1001, '未上传文件', status=400)
        result = import_products(f)
        return success_response(result)

    @action(detail=False, methods=['get'], url_path='import-template')
    def import_template(self, request):
        buf = build_product_template()
        resp = HttpResponse(buf, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        resp['Content-Disposition'] = 'attachment; filename=product_import_template.xlsx'
        return resp

class FactoryViewSet(BaseModelViewSet):
    queryset = Factory.objects.all()
    serializer_class = FactorySerializer
    permission_classes = [IsAuthenticated, AdminWriteOthersReadOnly]
    search_fields = ['name', 'alias', 'contact']
    ordering_fields = ['id', 'updated_at']

    @action(detail=False, methods=['post'], url_path='import')
    def import_data(self, request):
        f = request.FILES.get('file')
        if not f:
            return error_response(1001, '未上传文件', status=400)
        return success_response(import_factories(f))

    @action(detail=False, methods=['get'], url_path='import-template')
    def import_template(self, request):
        buf = build_factory_template()
        resp = HttpResponse(buf, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        resp['Content-Disposition'] = 'attachment; filename=factory_import_template.xlsx'
        return resp

class LogisticsProviderViewSet(BaseModelViewSet):
    queryset = LogisticsProvider.objects.all()
    serializer_class = LogisticsProviderSerializer
    permission_classes = [IsAuthenticated, AdminWriteOthersReadOnly]
    filterset_fields = ['type']
    search_fields = ['name', 'contact']
    ordering_fields = ['id', 'updated_at']

class CustomerViewSet(BaseModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = [IsAuthenticated, AdminWriteOthersReadOnly]
    filterset_fields = ['salesman']
    search_fields = ['name', 'contact_person', 'phone']
    ordering_fields = ['id', 'updated_at']
