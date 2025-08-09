from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from datetime import date

User = get_user_model()


class Command(BaseCommand):
    help = '创建管理员用户'

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, help='管理员用户名', default='admin')
        parser.add_argument('--email', type=str, help='管理员邮箱', default='admin@example.com')
        parser.add_argument('--password', type=str, help='管理员密码', default='admin123456')

    def handle(self, *args, **options):
        username = options['username']
        email = options['email']
        password = options['password']

        if User.objects.filter(username=username).exists():
            self.stdout.write(
                self.style.WARNING(f'用户 {username} 已存在')
            )
            return

        admin_user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            role='admin',
            gender='unknown',
            is_active=True
        )

        self.stdout.write(
            self.style.SUCCESS(f'管理员用户 {username} 创建成功！')
        )
        self.stdout.write(f'用户名: {username}')
        self.stdout.write(f'邮箱: {email}')
        self.stdout.write(f'密码: {password}')
        self.stdout.write(f'角色: 管理员')
        self.stdout.write('请在生产环境中修改默认密码！') 