from rest_framework import serializers
from .models import Category, Product, Factory

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'parent', 'sort_order', 'created_at', 'updated_at']

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'product_no', 'model', 'name', 'category', 'spec',
                  'default_price', 'default_cost_price', 'remark', 'created_at', 'updated_at']

class CategoryTreeSerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()
    class Meta:
        model = Category
        fields = ['id', 'name', 'parent', 'sort_order', 'children']
    def get_children(self, obj):
        return CategoryTreeSerializer(obj.children.all(), many=True).data

class FactorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Factory
        fields = ['id', 'name', 'alias', 'contact', 'phone', 'settle_currency', 'remark', 'created_at', 'updated_at']
