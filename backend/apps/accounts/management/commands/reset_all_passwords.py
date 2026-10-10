"""BUG-SIM-020 用户指令：一次性把所有用户密码重置为统一过渡密码（默认 aa1234）。

用法：.venv/bin/python manage.py reset_all_passwords --password aa1234
- 直 set_password 不走强度校验（aa1234 为过渡态，规则只对之后的建号/改密生效）
- 每用户维护 PasswordFlag 标记（is_weak=True），用户管理列表提示 admin
- 幂等：重复运行结果一致
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

from apps.accounts.serializers import mark_password_flag


class Command(BaseCommand):
    help = '把所有用户密码重置为统一过渡密码（一次性脚本）'

    def add_arguments(self, parser):
        parser.add_argument('--password', default='aa1234')

    def handle(self, *args, **options):
        pwd = options['password']
        count = 0
        for u in User.objects.all():
            u.set_password(pwd)
            u.save(update_fields=['password'])
            mark_password_flag(u, pwd)
            count += 1
        self.stdout.write(self.style.SUCCESS(f'已重置 {count} 个用户密码为过渡密码，全部标记为弱密码（待用户自行改密升级）'))
