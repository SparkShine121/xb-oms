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

def validate_password_policy(pwd):
    """BUG-SIM-020 Q3:a：≥8 位且同时含字母与数字。建用户/改密/个人改密共用。"""
    import re
    if not pwd or len(pwd) < 8:
        raise ValueError('密码长度不得少于 8 位')
    if not (re.search(r'[A-Za-z]', pwd) and re.search(r'\d', pwd)):
        raise ValueError('密码必须同时包含字母和数字')
    return pwd


def mark_password_flag(user, plain_password):
    """设置密码后调用：判定强度并持久化标记（Q4:a）。弱 = 不满足策略的过渡态。"""
    from .models import PasswordFlag
    try:
        validate_password_policy(plain_password)
        is_weak = False
    except ValueError:
        is_weak = True
    PasswordFlag.objects.update_or_create(user=user, defaults={'is_weak': is_weak})


class UserManageSerializer(serializers.ModelSerializer):
    groups = serializers.SlugRelatedField(queryset=Group.objects.all(), slug_field='name', many=True, required=False)
    password = serializers.CharField(write_only=True, required=True)
    is_weak_password = serializers.SerializerMethodField()

    def get_is_weak_password(self, obj):
        from .models import PasswordFlag
        return PasswordFlag.objects.filter(user=obj, is_weak=True).exists()

    def validate_groups(self, value):
        # 角色单选：每个用户最多一个角色组
        if len(value) > 1:
            raise serializers.ValidationError('每个用户只能分配一个角色')
        return value

    def validate_password(self, value):
        # BUG-SIM-020：建用户/改密全路径走强度规则
        from rest_framework.exceptions import ValidationError
        try:
            validate_password_policy(value)
        except ValueError as e:
            raise ValidationError(str(e))
        return value

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'groups', 'is_weak_password', 'is_active']

    def update(self, instance, validated):
        # BUG-SIM-028 Q2:a：停用即时生效——blacklist 该用户全部 refresh token
        deactivating = validated.get('is_active') is False and instance.is_active
        instance = super().update(instance, validated)
        if deactivating:
            from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
            for ot in OutstandingToken.objects.filter(user=instance):
                BlacklistedToken.objects.get_or_create(token=ot)
        return instance
    def create(self, validated):
        groups = validated.pop('groups', [])
        pwd = validated.get('password')
        user = User.objects.create_user(**validated)
        user.groups.set(groups)
        mark_password_flag(user, pwd)
        return user
    def update(self, instance, validated):
        groups = validated.pop('groups', None)
        password = validated.pop('password', None)
        for k, v in validated.items():
            setattr(instance, k, v)
        if password:
            instance.set_password(password)
            mark_password_flag(instance, password)
        if groups is not None:
            instance.groups.set(groups)
        instance.save()
        return instance
