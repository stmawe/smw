"""
SSL Certificate Management for Multi-Tenant Shops
Automatically generates and manages SSL certificates for new domains
"""

import subprocess
import os
from pathlib import Path
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class SSLCertificateManager:
    """Manages SSL certificate generation for shop subdomains"""
    
    def __init__(self):
        self.cf_api_token = os.environ.get('CF_API_TOKEN') or settings.CF_API_TOKEN
        self.domain_base = getattr(settings, 'PRIMARY_DOMAIN', 'smw.pgwiz.cloud')
        self.cert_base_path = getattr(settings, 'LETSENCRYPT_PATH', '/etc/letsencrypt/live')
    
    def generate_certificate_for_shop(self, shop_name):
        """
        Generate SSL certificate for a shop subdomain.
        
        Args:
            shop_name: Shop name (will become shop-name.smw.pgwiz.cloud)
        
        Returns:
            dict with keys:
            - success: bool
            - message: str
            - cert_path: str (if successful)
            - error: str (if failed)
        """
        if not self.cf_api_token:
            return {
                'success': False,
                'message': 'SSL disabled: CF_API_TOKEN not configured',
                'error': 'Missing Cloudflare API token'
            }
        
        try:
            # Generate subdomain from shop name
            from app.shop_urls import generate_shop_slug
            shop_slug = generate_shop_slug(shop_name)
            subdomain = f"{shop_slug}.{self.domain_base}"
            
            logger.info(f"Generating SSL certificate for shop: {subdomain}")
            
            # Create credentials file temporarily
            cert_result = self._issue_certificate(subdomain)
            
            if cert_result['success']:
                logger.info(f"SSL certificate issued for {subdomain}")
                return {
                    'success': True,
                    'message': f'SSL certificate issued for {subdomain}',
                    'subdomain': subdomain,
                    'cert_path': cert_result['cert_path']
                }
            else:
                logger.error(f"Failed to issue certificate for {subdomain}: {cert_result['error']}")
                return cert_result
                
        except Exception as e:
            logger.error(f"Error generating certificate for shop {shop_name}: {str(e)}")
            return {
                'success': False,
                'message': f'Error generating certificate: {str(e)}',
                'error': str(e)
            }
    
    def _issue_certificate(self, subdomain):
        """
        Issue certificate for subdomain using Certbot.
        
        Args:
            subdomain: Full subdomain (e.g., shop-name.smw.pgwiz.cloud)
        
        Returns:
            dict with success bool and cert_path or error
        """
        # Create temporary credentials file
        creds_path = Path.home() / '.secrets' / f'cf_{subdomain}.ini'
        
        try:
            # Create secrets directory
            Path.home().joinpath('.secrets').mkdir(exist_ok=True)
            
            # Write credentials file
            with open(creds_path, 'w') as f:
                f.write(f'dns_cloudflare_api_token = {self.cf_api_token}\n')
            
            # Set permissions to 600 (rw-------)
            os.chmod(creds_path, 0o600)
            
            # Issue certificate
            cmd = [
                'certbot', 'certonly',
                '--non-interactive',
                '--agree-tos',
                '--register-unsafely-without-email',
                '--dns-cloudflare',
                f'--dns-cloudflare-credentials', str(creds_path),
                '-d', subdomain
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                cert_path = os.path.join(self.cert_base_path, subdomain)
                return {
                    'success': True,
                    'cert_path': cert_path,
                    'message': f'Certificate issued for {subdomain}'
                }
            else:
                error = result.stderr or result.stdout
                return {
                    'success': False,
                    'error': error,
                    'message': f'Certbot failed: {error}'
                }
        
        finally:
            # Clean up credentials file
            if creds_path.exists():
                try:
                    os.remove(creds_path)
                except:
                    pass
    
    def renew_certificate(self, subdomain):
        """Renew certificate for a subdomain."""
        try:
            cmd = ['certbot', 'renew', '--force-renewal', '-d', subdomain]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                return {'success': True, 'message': f'Certificate renewed for {subdomain}'}
            else:
                return {'success': False, 'error': result.stderr or result.stdout}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_certificate_info(self, subdomain):
        """Get certificate expiration and details."""
        try:
            cert_path = os.path.join(self.cert_base_path, subdomain, 'cert.pem')
            
            if not os.path.exists(cert_path):
                return {
                    'exists': False,
                    'error': f'Certificate not found for {subdomain}'
                }
            
            # Get expiration date
            cmd = [
                'openssl', 'x509',
                '-in', cert_path,
                '-noout', '-dates'
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            return {
                'exists': True,
                'subdomain': subdomain,
                'cert_info': result.stdout
            }
        except Exception as e:
            return {'exists': False, 'error': str(e)}


# Global instance
_ssl_manager = None


def get_ssl_manager():
    """Get or create SSL manager instance."""
    global _ssl_manager
    if _ssl_manager is None:
        _ssl_manager = SSLCertificateManager()
    return _ssl_manager
