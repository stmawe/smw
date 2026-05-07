"""
Shared Cloudflare DNS helper.

Used by:
- accounts/views._register_user_subdomain() — on user registration
- app/entity_admin_views.py — on entity activation/approval

All calls are non-fatal: errors are logged but never raised.
"""

import logging

logger = logging.getLogger(__name__)


def create_subdomain_dns_record(subdomain: str) -> None:
    """
    Create a Cloudflare DNS A record for {subdomain}.{BASE_DOMAIN}.

    - Proxied through Cloudflare (orange cloud) so wildcard SSL applies.
    - Skips silently if CLOUDFLARE_API_TOKEN, CLOUDFLARE_ZONE_ID, or SERVER_IP
      are not configured.
    - Skips if the A record already exists.
    - Never raises — logs errors and returns.

    Args:
        subdomain: The subdomain segment only (e.g. "uon", "juju254").
                   Full record name becomes {subdomain}.{BASE_DOMAIN}.
    """
    from django.conf import settings
    import requests as http_requests

    cf_token  = getattr(settings, 'CLOUDFLARE_API_TOKEN', '') or getattr(settings, 'CF_API_TOKEN', '') or ''
    cf_zone   = getattr(settings, 'CLOUDFLARE_ZONE_ID', '') or ''
    server_ip = getattr(settings, 'SERVER_IP', '') or ''
    base_domain = getattr(settings, 'BASE_DOMAIN', 'smw.pgwiz.cloud')

    if not (cf_token and cf_zone and server_ip):
        logger.warning(
            'Cloudflare DNS skipped for "%s" — '
            'CLOUDFLARE_API_TOKEN, CLOUDFLARE_ZONE_ID or SERVER_IP not configured',
            subdomain,
        )
        return

    record_name = f'{subdomain}.{base_domain}'
    headers = {
        'Authorization': f'Bearer {cf_token}',
        'Content-Type': 'application/json',
    }

    try:
        # Check if record already exists
        list_resp = http_requests.get(
            f'https://api.cloudflare.com/client/v4/zones/{cf_zone}/dns_records'
            f'?type=A&name={record_name}',
            headers=headers,
            timeout=10,
        )
        existing = list_resp.json().get('result', [])

        if existing:
            logger.warning(
                'Cloudflare DNS A record already exists for "%s" — skipping',
                record_name,
            )
            return

        create_resp = http_requests.post(
            f'https://api.cloudflare.com/client/v4/zones/{cf_zone}/dns_records',
            headers=headers,
            json={
                'type': 'A',
                'name': record_name,
                'content': server_ip,
                'ttl': 1,        # 1 = auto TTL
                'proxied': True,  # orange-cloud → wildcard SSL applies
            },
            timeout=10,
        )
        result = create_resp.json()
        if result.get('success'):
            logger.info('Cloudflare DNS A record created: %s → %s', record_name, server_ip)
        else:
            logger.error(
                'Cloudflare DNS creation failed for "%s": %s',
                record_name,
                result.get('errors'),
            )

    except Exception as exc:
        logger.error('Cloudflare DNS registration failed for "%s": %s', record_name, exc)
