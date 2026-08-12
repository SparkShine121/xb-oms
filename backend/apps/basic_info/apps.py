from django.apps import AppConfig


class BasicInfoConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.basic_info"
    verbose_name = "基础信息"
