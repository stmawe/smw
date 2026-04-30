"""Management command to seed shipping carriers and rates."""

from django.core.management.base import BaseCommand
from mydak.shipping import ShippingSeeder


class Command(BaseCommand):
    help = 'Seed default shipping carriers and rates'
    
    def handle(self, *args, **options):
        self.stdout.write('Seeding shipping carriers and rates...')
        
        try:
            ShippingSeeder.seed_carriers()
            self.stdout.write(self.style.SUCCESS('Carriers seeded'))
            
            ShippingSeeder.seed_rates()
            self.stdout.write(self.style.SUCCESS('Rates seeded'))
            
            self.stdout.write(self.style.SUCCESS('Shipping data initialized successfully!'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {str(e)}'))
