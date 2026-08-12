from django.contrib.auth.models import User, Group
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

class UserManageSerializer(serializers.ModelSerializer):
    groups = serializers.SlugRelatedField(queryset=Group.objects.all(), slug_field='name', many=True, required=False)
    password = serializers.CharField(write_only=True, required=True)
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'groups']
    def create(self, validated):
        groups = validated.pop('groups', [])
        user = User.objects.create_user(**validated)
        user.groups.set(groups)
        return user
    def update(self, instance, validated):
        groups = validated.pop('groups', None)
        password = validated.pop('password', None)
        for k, v in validated.items():
            setattr(instance, k, v)
        if password:
            instance.set_password(password)
        if groups is not None:
            instance.groups.set(groups)
        instance.save()
        return instance
