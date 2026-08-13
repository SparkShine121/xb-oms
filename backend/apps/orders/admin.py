from django.contrib import admin
from .models import Order, OrderItem, ExchangeRate

admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(ExchangeRate)