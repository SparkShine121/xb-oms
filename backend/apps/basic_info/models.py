from django.db import models
from django.contrib.auth.models import User

class Category(models.Model):
    name = models.CharField(max_length=64)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='children')
    sort_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['sort_order', 'id']

    def __str__(self):
        return self.name

class Product(models.Model):
    product_no = models.CharField(max_length=64, unique=True)
    model = models.CharField(max_length=64, blank=True)
    name = models.CharField(max_length=128)
    category = models.ForeignKey(Category, null=True, blank=True, on_delete=models.SET_NULL, related_name='products')
    spec = models.TextField(blank=True)
    default_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)      # USD
    default_cost_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)  # CNY
    remark = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.product_no} {self.name}'

class Factory(models.Model):
    name = models.CharField(max_length=128, unique=True)
    alias = models.CharField(max_length=128, blank=True)
    contact = models.CharField(max_length=64, blank=True)
    phone = models.CharField(max_length=32, blank=True)
    settle_currency = models.CharField(max_length=8, default='CNY')
    remark = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class LogisticsProvider(models.Model):
    TYPE_CHOICES = [('domestic', '国内'), ('international', '国际')]
    name = models.CharField(max_length=128)
    type = models.CharField(max_length=16, choices=TYPE_CHOICES)
    contact = models.CharField(max_length=64, blank=True)
    phone = models.CharField(max_length=32, blank=True)
    remark = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.name}({self.type})'

class Customer(models.Model):
    name = models.CharField(max_length=128)
    contact_person = models.CharField(max_length=64, blank=True)
    phone = models.CharField(max_length=32, blank=True)
    email = models.CharField(max_length=128, blank=True)
    salesman = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='customers')
    remark = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
