"""
Management command to seed demo data for admin panel testing.
Creates demo admins (all roles), demo users, demo shops with listings.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from mydak.models import Shop, Listing, Category, Transaction
from app.models import Theme, AdminAuditLog, AdminActivityFeed

User = get_user_model()


class Command(BaseCommand):
    help = 'Seed demo data for admin panel testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--users',
            type=int,
            default=10,
            help='Number of demo users to create'
        )
        parser.add_argument(
            '--shops',
            type=int,
            default=5,
            help='Number of demo shops to create'
        )
        parser.add_argument(
            '--listings',
            type=int,
            default=20,
            help='Number of demo listings to create'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing demo data first'
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write("Clearing existing demo data...")
            User.objects.filter(username__startswith='demo_').delete()
            AdminAuditLog.objects.all().delete()
            AdminActivityFeed.objects.all().delete()
            self.stdout.write("✓ Demo data cleared")

        self.stdout.write("Creating demo admins...")
        self.create_demo_admins()

        self.stdout.write(f"Creating {options['users']} demo users...")
        self.create_demo_users(options['users'])

        self.stdout.write(f"Creating {options['shops']} demo shops...")
        self.create_demo_shops(options['shops'])

        self.stdout.write(f"Creating {options['listings']} demo listings...")
        self.create_demo_listings(options['listings'])

        self.stdout.write(f"Creating demo transactions...")
        self.create_demo_transactions()

        self.stdout.write(self.style.SUCCESS('✓ Demo data seeded successfully!'))

    def create_demo_admins(self):
        """Create admin users with different roles."""
        admin_roles = [
            ('superuser', 'superuser@demo.local', True, True),
            ('admin', 'admin@demo.local', True, False),
            ('moderator', 'moderator@demo.local', True, False),
            ('support', 'support@demo.local', True, False),
            ('viewer', 'viewer@demo.local', True, False),
        ]

        for role, email, is_staff, is_superuser in admin_roles:
            username = f'demo_{role}'
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': email,
                    'first_name': role.capitalize(),
                    'last_name': 'Admin',
                    'is_staff': is_staff,
                    'is_superuser': is_superuser,
                    'role': 'superadmin' if role == 'superuser' else role,
                }
            )
            if created:
                user.set_password('demo123456')
                user.save()
                self.stdout.write(f"  ✓ Created {username}")

    def create_demo_users(self, count):
        """Create demo buyer/seller users."""
        for i in range(count):
            username = f'demo_user_{i}'
            email = f'demo_user_{i}@demo.local'

            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': email,
                    'first_name': f'Demo',
                    'last_name': f'User {i}',
                    'role': 'seller' if i % 2 == 0 else 'buyer',
                }
            )
            if created:
                user.set_password('demo123456')
                user.save()

        self.stdout.write(f"  ✓ Created {count} demo users")

    def create_demo_shops(self, count):
        """Create demo shops."""
        sellers = User.objects.filter(role='seller')[:count]

        for i, seller in enumerate(sellers):
            shop, created = Shop.objects.get_or_create(
                name=f'Demo Shop {i}',
                owner=seller,
                defaults={
                    'domain': f'demo-shop-{i}',
                    'description': f'Demo shop for testing #{i}',
                    'is_active': i % 2 == 0,  # Half active, half inactive
                    'theme_id': 'campus_light',
                }
            )
            if created:
                self.stdout.write(f"  ✓ Created {shop.name}")

    def create_demo_listings(self, count):
        """Create demo listings."""
        shops = Shop.objects.all()
        categories = Category.objects.all()

        if not categories:
            categories = [Category.objects.create(name='Demo', icon='package')]

        for i in range(count):
            shop = shops[i % len(shops)] if shops else None
            category = categories[i % len(categories)]

            if shop:
                listing, created = Listing.objects.get_or_create(
                    title=f'Demo Product {i}',
                    shop=shop,
                    category=category,
                    defaults={
                        'description': f'This is a demo listing for testing purposes #{i}',
                        'status': ['pending', 'active', 'rejected'][i % 3],
                        'is_featured': i % 5 == 0,
                        'price': 100 + i * 10,
                    }
                )
                if created:
                    if i % 20 == 0:
                        self.stdout.write(f"  ✓ Created {count} demo listings")

    def create_demo_transactions(self):
        """Create demo transactions."""
        shops = Shop.objects.all()
        listings = Listing.objects.filter(status='active')
        buyers = User.objects.filter(role='buyer')

        created_count = 0
        for i, listing in enumerate(listings[:10]):
            buyer = buyers[i % len(buyers)] if buyers else None
            if buyer and listing.shop:
                transaction, created = Transaction.objects.get_or_create(
                    listing=listing,
                    defaults={
                        'buyer': buyer,
                        'seller': listing.shop.owner,
                        'shop': listing.shop,
                        'amount': listing.price if hasattr(listing, 'price') else 100,
                        'status': 'completed',
                        'created_at': timezone.now() - timedelta(days=i),
                    }
                )
                if created:
                    created_count += 1

        self.stdout.write(f"  ✓ Created {created_count} demo transactions")
