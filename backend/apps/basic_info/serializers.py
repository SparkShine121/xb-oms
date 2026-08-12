from rest_framework import serializers
from .models import Category

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'parent', 'sort_order', 'created_at', 'updated_at']

class CategoryTreeSerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()
    class Meta:
        model = Category
        fields = ['id', 'name', 'parent', 'sort_order', 'children']
    def get_children(self, obj):
        return CategoryTreeSerializer(obj.children.all(), many=True).data
