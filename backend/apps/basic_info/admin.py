from django.contrib import admin
from .models import Category

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'parent', 'sort_order', 'created_at', 'updated_at']
    list_filter = ['parent']
    search_fields = ['name']
