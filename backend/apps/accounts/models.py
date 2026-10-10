from django.conf import settings
from django.db import models
# 模型将在后续任务中实现


class PasswordFlag(models.Model):
    """BUG-SIM-020 Q4:a：密码强度标记（hash 不可逆，设置时判定并持久化）。

    aa1234 等过渡态 → is_weak=True，用户管理列表提示 admin 通知本人改密升级。
    """
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='password_flag')
    is_weak = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)
