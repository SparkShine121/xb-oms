from rest_framework import serializers
from .models import TrackingLog, TrackingPhoto

class TrackingPhotoSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    class Meta:
        model = TrackingPhoto
        fields = ['id', 'image', 'image_url', 'created_at']
    def get_image_url(self, obj):
        request = self.context.get('request')
        if request and obj.image:
            return request.build_absolute_uri(obj.image.url)
        return obj.image.url if obj.image else ''

class TrackingLogSerializer(serializers.ModelSerializer):
    photos = TrackingPhotoSerializer(many=True, read_only=True)
    operator_name = serializers.CharField(source='operator.username', read_only=True, default='')
    order_no = serializers.CharField(source='order.order_no', read_only=True, default='')
    class Meta:
        model = TrackingLog
        fields = ['id', 'order', 'order_no', 'node', 'note', 'operator', 'operator_name', 'is_reject', 'photos', 'created_at']
        read_only_fields = ['order', 'operator', 'is_reject', 'created_at']
