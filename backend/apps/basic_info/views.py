from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from common.permissions import AdminWriteOthersReadOnly
from common.response import success_response
from .models import Category
from .serializers import CategorySerializer, CategoryTreeSerializer

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated, AdminWriteOthersReadOnly]
    filterset_fields = ['parent']
    search_fields = ['name']

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page if page is not None else queryset, many=True)
        if page is not None:
            return success_response(self.get_paginated_response(serializer.data).data)
        return success_response(serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return success_response(serializer.data, '创建成功', status=201)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        return success_response(self.get_serializer(instance).data)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return success_response(serializer.data, '更新成功')

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return success_response(None, '删除成功')

    @action(detail=False, methods=['get'])
    def tree(self, request):
        roots = Category.objects.filter(parent__isnull=True)
        return success_response(CategoryTreeSerializer(roots, many=True).data)
