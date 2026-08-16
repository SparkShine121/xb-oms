from django.db import models
from django.contrib.auth.models import User
from apps.orders.models import Order

class TrackingLog(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='tracking_logs')
    node = models.CharField(max_length=16, choices=Order.TRACKING_STATUS_CHOICES)
    note = models.TextField(blank=True)
    operator = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='tracking_logs')
    is_reject = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

class TrackingPhoto(models.Model):
    tracking_log = models.ForeignKey(TrackingLog, on_delete=models.CASCADE, related_name='photos')
    image = models.ImageField(upload_to='tracking/%Y%m/')
    created_at = models.DateTimeField(auto_now_add=True)
