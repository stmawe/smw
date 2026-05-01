"""Management command to seed admin users with RBAC roles."""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from app.admin_permissions import AdminRole

User = get_user_model()


class Command(BaseCommand):
    help = 'Seed default admin users with RBAC roles and permissions'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Reset admin users before seeding'
        )
        parser.add_argument(
            '--include-demo',
            action='store_true',
            help='Include demo admin users for testing different roles'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('Seeding admin users with RBAC roles...'))

        # Create admin groups if they don't exist
        admin_groups = {
            'superuser': Group.objects.get_or_create(name='superuser')[0],
            'admin': Group.objects.get_or_create(name='admin')[0],
            'moderator': Group.objects.get_or_create(name='moderator')[0],
            'support': Group.objects.get_or_create(name='support')[0],
            'viewer': Group.objects.get_or_create(name='viewer')[0],
        }
        self.stdout.write(self.style.SUCCESS('Created/verified admin groups'))

        # Production admin users (always created)
        admin_users = [
            {
                'username': 'admins',
                'email': 'admin@smw.pgwiz.cloud',
                'password': 'haha6admin',
                'first_name': 'Site',
                'last_name': 'Administrator',
                'is_staff': True,
                'is_superuser': True,
                'role': AdminRole.SUPERUSER,
                'group': 'superuser',
            },
        ]

        # Demo admin users (only if --include-demo flag)
        if options.get('include_demo'):
            admin_users.extend([
                {
                    'username': 'admin_user',
                    'email': 'admin-user@smw.pgwiz.cloud',
                    'password': 'AdminPass123!',
                    'first_name': 'Full',
                    'last_name': 'Admin',
                    'is_staff': True,
                    'is_superuser': False,
                    'role': AdminRole.ADMIN,
                    'group': 'admin',
                },
                {
                    'username': 'moderator_user',
                    'email': 'moderator@smw.pgwiz.cloud',
                    'password': 'ModeratorPass123!',
                    'first_name': 'Content',
                    'last_name': 'Moderator',
                    'is_staff': True,
                    'is_superuser': False,
                    'role': AdminRole.MODERATOR,
                    'group': 'moderator',
                },
                {
                    'username': 'support_user',
                    'email': 'support@smw.pgwiz.cloud',
                    'password': 'SupportPass123!',
                    'first_name': 'Support',
                    'last_name': 'Agent',
                    'is_staff': True,
                    'is_superuser': False,
                    'role': AdminRole.SUPPORT,
                    'group': 'support',
                },
                {
                    'username': 'viewer_user',
                    'email': 'viewer@smw.pgwiz.cloud',
                    'password': 'ViewerPass123!',
                    'first_name': 'Read',
                    'last_name': 'Only',
                    'is_staff': True,
                    'is_superuser': False,
                    'role': AdminRole.VIEWER,
                    'group': 'viewer',
                },
            ])

        # Seed admin users
        created_count = 0
        updated_count = 0

        for admin_data in admin_users:
            username = admin_data['username']
            email = admin_data['email']
            password = admin_data['password']
            role = admin_data.get('role')
            group_name = admin_data.get('group')

            try:
                user = User.objects.get(username=username)
                self.stdout.write(f"Admin user '{username}' already exists")
                
                # Update password and email if different
                if user.email != email:
                    user.email = email
                    user.save()
                    self.stdout.write(f"  Updated email: {email}")
                
                updated_count += 1
                
            except User.DoesNotExist:
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    first_name=admin_data.get('first_name', ''),
                    last_name=admin_data.get('last_name', ''),
                )
                user.is_staff = admin_data.get('is_staff', True)
                user.is_superuser = admin_data.get('is_superuser', False)
                
                # Set admin role (for future database field)
                if hasattr(user, 'admin_role'):
                    user.admin_role = role
                
                user.save()
                
                self.stdout.write(self.style.SUCCESS(f"✓ Created admin user: {username}"))
                self.stdout.write(f"  Email: {email}")
                self.stdout.write(f"  Role: {role.value if role else 'N/A'}")
                self.stdout.write(f"  Staff: {user.is_staff}")
                self.stdout.write(f"  Superuser: {user.is_superuser}")
                
                # Add to appropriate group
                if group_name and group_name in admin_groups:
                    user.groups.add(admin_groups[group_name])
                    self.stdout.write(f"  Added to group: {group_name}")
                
                created_count += 1

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(f'Admin users seeded: {created_count} created, {updated_count} updated'))
        self.stdout.write('')
        self.stdout.write('Login credentials (Production):')
        self.stdout.write('  Username: admins')
        self.stdout.write('  Password: haha6admin')
        self.stdout.write('  Role: Superuser (all permissions)')
        
        if options.get('include_demo'):
            self.stdout.write('')
            self.stdout.write('Demo Admin Users (for testing):')
            self.stdout.write('  admin_user / AdminPass123! (Admin - full control)')
            self.stdout.write('  moderator_user / ModeratorPass123! (Moderator - content only)')
            self.stdout.write('  support_user / SupportPass123! (Support - limited access)')
            self.stdout.write('  viewer_user / ViewerPass123! (Viewer - read-only)')
        
        self.stdout.write('')
        self.stdout.write('Access admin dashboard at: /admin/ or admin.smw.pgwiz.cloud')

