"""
Async SSL Certificate Tasks
Uses Django Q or threading for background SSL certificate generation
"""

import threading
import logging
from django.conf import settings
from app.ssl_manager import get_ssl_manager

logger = logging.getLogger(__name__)


def generate_ssl_async(shop_name, shop_id=None):
    """
    Generate SSL certificate asynchronously (non-blocking).
    
    Args:
        shop_name: Shop name for subdomain generation
        shop_id: Optional shop ID for updating records
    """
    def _generate():
        try:
            ssl_manager = get_ssl_manager()
            result = ssl_manager.generate_certificate_for_shop(shop_name)
            
            if result['success'] and shop_id:
                # Update shop with certificate info
                from mydak.models import Shop
                try:
                    shop = Shop.objects.get(id=shop_id)
                    shop.ssl_subdomain = result['subdomain']
                    shop.ssl_cert_path = result['cert_path']
                    shop.has_ssl = True
                    shop.save()
                    logger.info(f"Shop {shop_id} SSL certificate updated")
                except Shop.DoesNotExist:
                    logger.warning(f"Shop {shop_id} not found for SSL update")
            
            # Log result
            log_entry = {
                'shop_name': shop_name,
                'shop_id': shop_id,
                'success': result['success'],
                'message': result.get('message', ''),
                'error': result.get('error', '')
            }
            logger.info(f"SSL generation completed: {log_entry}")
            
        except Exception as e:
            logger.error(f"Error in SSL generation for {shop_name}: {str(e)}")
    
    # Use threading for non-blocking execution
    thread = threading.Thread(target=_generate, daemon=True)
    thread.start()
    
    return thread


def generate_ssl_sync(shop_name, shop_id=None):
    """
    Generate SSL certificate synchronously (blocking).
    Use only in admin commands or background jobs.
    
    Args:
        shop_name: Shop name for subdomain generation
        shop_id: Optional shop ID for updating records
    
    Returns:
        dict with result
    """
    try:
        ssl_manager = get_ssl_manager()
        result = ssl_manager.generate_certificate_for_shop(shop_name)
        
        if result['success'] and shop_id:
            from mydak.models import Shop
            try:
                shop = Shop.objects.get(id=shop_id)
                shop.ssl_subdomain = result.get('subdomain')
                shop.ssl_cert_path = result.get('cert_path')
                shop.has_ssl = True
                shop.save()
            except Shop.DoesNotExist:
                pass
        
        return result
    
    except Exception as e:
        logger.error(f"SSL generation error for {shop_name}: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }
