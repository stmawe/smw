"""Management command to fix admin user permissions."""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Fix admin user permissions - ensure admin user is a superuser with all permissions'

    def handle(self, *args, **options):
        """Update admin user to have full superuser permissions."""
        try:
            user = User.objects.get(username='admins')
            
            self.stdout.write(f'Found admin user: {user}')
            self.stdout.write(f'  Current is_superuser: {user.is_superuser}')
            self.stdout.write(f'  Current is_staff: {user.is_staff}')
            
            # Update to superuser if not already
            updated = False
            if not user.is_superuser:
                user.is_superuser = True
                updated = True
                self.stdout.write('  Setting is_superuser=True')
            
            if not user.is_staff:
                user.is_staff = True
                updated = True
                self.stdout.write('  Setting is_staff=True')
            
            if updated:
                user.save()
                self.stdout.write(self.style.SUCCESS('✓ Admin user permissions updated'))
                self.stdout.write(f'  is_superuser: {user.is_superuser}')
                self.stdout.write(f'  is_staff: {user.is_staff}')
            else:
                self.stdout.write(self.style.SUCCESS('✓ Admin user already has full permissions'))
        
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR('✗ Admin user "admins" not found'))
            self.stdout.write('  Please run: python manage.py seed_admins')
