"""Shipping calculator and utilities."""

from decimal import Decimal
from mydak.models import ShippingCarrier, ShippingRate, ShippingOption


class ShippingCalculator:
    """Calculate shipping costs based on carrier and weight."""
    
    @staticmethod
    def get_shipping_options(listing, weight_kg=None):
        """Get available shipping options for a listing."""
        
        if weight_kg is None:
            weight_kg = Decimal('0.5')  # Default assumption
        
        active_carriers = ShippingCarrier.objects.filter(is_active=True)
        options = []
        
        for carrier in active_carriers:
            rate = ShippingRate.objects.filter(
                carrier=carrier,
                weight_min_kg__lte=weight_kg,
                weight_max_kg__gte=weight_kg
            ).first()
            
            if rate:
                options.append({
                    'carrier': carrier,
                    'rate': rate,
                    'estimated_cost': rate.price_kes,
                    'estimated_days': (carrier.estimated_days_min, carrier.estimated_days_max),
                })
            else:
                # If no exact match, use default rate (0-100kg)
                default_rate = ShippingRate.objects.filter(
                    carrier=carrier,
                    weight_min_kg=0,
                    weight_max_kg=100
                ).first()
                
                if default_rate:
                    options.append({
                        'carrier': carrier,
                        'rate': default_rate,
                        'estimated_cost': default_rate.price_kes,
                        'estimated_days': (carrier.estimated_days_min, carrier.estimated_days_max),
                    })
        
        return options
    
    @staticmethod
    def calculate_total_with_shipping(listing_price, shipping_cost):
        """Calculate total including shipping."""
        return listing_price + shipping_cost
    
    @staticmethod
    def get_carrier_by_id(carrier_id):
        """Get carrier by ID."""
        try:
            return ShippingCarrier.objects.get(id=carrier_id)
        except ShippingCarrier.DoesNotExist:
            return None


class ShippingSeeder:
    """Initialize default shipping carriers and rates."""
    
    @staticmethod
    def seed_carriers():
        """Create default carriers."""
        carriers = [
            ('local_pickup', 'Local Pickup', 0, 1),
            ('posta', 'Posta (National)', 3, 7),
            ('jiji', 'Jiji Courier', 1, 3),
        ]
        
        for code, name, min_days, max_days in carriers:
            ShippingCarrier.objects.get_or_create(
                name=code,
                defaults={
                    'display_name': name,
                    'estimated_days_min': min_days,
                    'estimated_days_max': max_days,
                    'is_active': True,
                }
            )
    
    @staticmethod
    def seed_rates():
        """Create default shipping rates."""
        ShippingSeeder.seed_carriers()
        
        rates_data = [
            # Local Pickup - free
            ('local_pickup', 0, 100, 0),
            
            # Posta - national
            ('posta', 0, 1, 200),      # 0-1kg: 200 KES
            ('posta', 1, 2, 350),      # 1-2kg: 350 KES
            ('posta', 2, 5, 500),      # 2-5kg: 500 KES
            ('posta', 5, 10, 750),     # 5-10kg: 750 KES
            ('posta', 10, 100, 1000),  # 10+kg: 1000 KES
            
            # Jiji Courier - express
            ('jiji', 0, 1, 500),       # 0-1kg: 500 KES
            ('jiji', 1, 2, 700),       # 1-2kg: 700 KES
            ('jiji', 2, 5, 1000),      # 2-5kg: 1000 KES
            ('jiji', 5, 10, 1500),     # 5-10kg: 1500 KES
            ('jiji', 10, 100, 2000),   # 10+kg: 2000 KES
        ]
        
        for carrier_code, min_kg, max_kg, price in rates_data:
            carrier = ShippingCarrier.objects.get(name=carrier_code)
            ShippingRate.objects.get_or_create(
                carrier=carrier,
                weight_min_kg=min_kg,
                weight_max_kg=max_kg,
                defaults={'price_kes': price}
            )
