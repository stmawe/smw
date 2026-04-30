"""Management command to seed admin users."""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

User = get_user_model()


class Command(BaseCommand):
    help = 'Seed default admin users and permissions'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Reset admin users before seeding'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('Seeding admin users and permissions...'))

        # Create site_admin group if it doesn't exist
        site_admin_group, created = Group.objects.get_or_create(name='site_admin')
        if created:
            self.stdout.write(self.style.SUCCESS('Created site_admin group'))
            
            # Add admin permissions to site_admin group
            admin_perms = Permission.objects.filter(
                codename__in=['add_user', 'change_user', 'delete_user', 'view_user']
            )
            site_admin_group.permissions.set(admin_perms)

        # Admin users to seed
        admin_users = [
            {
                'username': 'admins',
                'email': 'admin@smw.pgwiz.cloud',
                'password': 'haha6admin',
                'first_name': 'Site',
                'last_name': 'Administrator',
                'is_staff': True,
                'is_superuser': True,
            },
        ]

        for admin_data in admin_users:
            username = admin_data['username']
            email = admin_data['email']
            password = admin_data['password']

            try:
                user = User.objects.get(username=username)
                self.stdout.write(f"Admin user '{username}' already exists")
                
                # Update password and email if different
                if user.email != email:
                    user.email = email
                    user.save()
                    self.stdout.write(f"  Updated email: {email}")
                
            except User.DoesNotExist:
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    first_name=admin_data.get('first_name', ''),
                    last_name=admin_data.get('last_name', ''),
                )
                user.is_staff = admin_data.get('is_staff', True)
                user.is_superuser = admin_data.get('is_superuser', True)
                user.save()
                
                self.stdout.write(self.style.SUCCESS(f"Created admin user: {username}"))
                self.stdout.write(f"  Email: {email}")
                self.stdout.write(f"  Password: {password}")
                self.stdout.write(f"  Staff: {user.is_staff}")
                self.stdout.write(f"  Superuser: {user.is_superuser}")
                
                # Add to site_admin group
                user.groups.add(site_admin_group)

        self.stdout.write(self.style.SUCCESS('Admin users seeded successfully!'))
        self.stdout.write('')
        self.stdout.write('Login credentials:')
        self.stdout.write('  Username: admins')
        self.stdout.write('  Password: haha6admin')
        self.stdout.write('')
        self.stdout.write('Access admin dashboard at: /dashboard/deployment/dashboard/')
