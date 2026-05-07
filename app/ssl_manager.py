"""
SSL Certificate Management for Serv00 hosting.

On Serv00, SSL is handled two ways:
1. Cloudflare proxy (*.smw.pgwiz.cloud subdomains) — automatic, no action needed
2. devil ssl www add — for custom domains that bypass Cloudflare

Command: devil ssl www add IP_ADDRESS le le DOMAIN_NAME
"""

import subprocess
import os
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

SERVER_IP = '128.204.223.70'


class SSLCertificateManager:
    """Manages SSL certificates for custom domains on Serv00 via devil command."""

    def generate_certificate_for_domain(self, domain):
        """
        Issue a Let's Encrypt certificate for a custom domain using devil.

        Prerequisites:
        - Domain A record must point to SERVER_IP
        - Domain must be reachable (Let's Encrypt checks DNS)

        Args:
            domain: Full domain name (e.g. shop.juju.co.ke)

        Returns:
            dict with success bool and message
        """
        try:
            cmd = ['devil', 'ssl', 'www', 'add', SERVER_IP, 'le', 'le', domain]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

            if result.returncode == 0:
                logger.info('SSL cert issued for %s via devil', domain)
                return {'success': True, 'message': f'SSL certificate issued for {domain}'}
            else:
                error = result.stderr or result.stdout
                logger.error('devil ssl failed for %s: %s', domain, error)
                return {'success': False, 'error': error}

        except Exception as e:
            logger.error('SSL generation error for %s: %s', domain, e)
            return {'success': False, 'error': str(e)}

    def list_certificates(self):
        """List all SSL certificates on the server."""
        try:
            result = subprocess.run(
                ['devil', 'ssl', 'www', 'list'],
                capture_output=True, text=True, timeout=30
            )
            return result.stdout
        except Exception as e:
            return str(e)

    def get_certificate_info(self, domain):
        """Get certificate info for a domain."""
        try:
            result = subprocess.run(
                ['devil', 'ssl', 'www', 'get', SERVER_IP, domain],
                capture_output=True, text=True, timeout=30
            )
            return {'exists': result.returncode == 0, 'info': result.stdout}
        except Exception as e:
            return {'exists': False, 'error': str(e)}


def get_ssl_manager():
    return SSLCertificateManager()
