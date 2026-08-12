from django.contrib.auth.models import User
from rest_framework import serializers

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

class UserSerializer(serializers.ModelSerializer):
    roles = serializers.SerializerMethodField()
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'roles']
    def get_roles(self, obj):
        return list(obj.groups.values_list('name', flat=True))
