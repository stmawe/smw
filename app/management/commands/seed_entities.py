"""
Management command: seed_entities

Imports university_data.json into the Entity table.
Idempotent — safe to run multiple times.

Usage:
    python manage.py seed_entities

Output:
    Created: N, Skipped: N, Failed: N
"""

import json
import os

from django.core.management.base import BaseCommand
from django.utils.text import slugify


class Command(BaseCommand):
    help = 'Seed Entity table from app/university_data.json (idempotent)'

    def handle(self, *args, **options):
        from app.models import Entity

        json_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            'university_data.json',
        )

        if not os.path.exists(json_path):
            self.stderr.write(self.style.ERROR(f'File not found: {json_path}'))
            return

        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError) as exc:
            self.stderr.write(self.style.ERROR(f'Could not read {json_path}: {exc}'))
            return

        universities = data.get('universities', [])
        created = skipped = failed = 0

        for entry in universities:
            try:
                name = (entry.get('name') or '').strip()
                if not name:
                    self.stderr.write(self.style.WARNING('Skipping entry with no name'))
                    skipped += 1
                    continue

                # Skip if name already exists
                if Entity.objects.filter(name=name).exists():
                    self.stdout.write(f'  SKIP  {name} (already exists)')
                    skipped += 1
                    continue

                # Derive subdomain from name
                base_subdomain = slugify(name)[:63]
                subdomain = base_subdomain
                suffix = 2
                while Entity.objects.filter(subdomain=subdomain).exists():
                    subdomain = f'{base_subdomain[:60]}-{suffix}'
                    suffix += 1

                # Extract optional location fields
                location = entry.get('location') or {}
                city    = location.get('city', '') if isinstance(location, dict) else ''
                country = location.get('country', '') if isinstance(location, dict) else ''
                website = entry.get('website', '') or ''

                Entity.objects.create(
                    name=name,
                    entity_type='University',
                    subdomain=subdomain,
                    status='active',    # seed data is immediately active
                    city=city,
                    country=country,
                    website=website,
                    created_by=None,    # seeded, not admin-created
                )
                self.stdout.write(self.style.SUCCESS(f'  CREATE {name} → {subdomain}.smw.pgwiz.cloud'))
                created += 1

            except Exception as exc:
                self.stderr.write(self.style.WARNING(f'  FAIL  {entry.get("name", "?")} — {exc}'))
                failed += 1

        self.stdout.write('')
        self.stdout.write(
            self.style.SUCCESS(f'Done. Created: {created}, Skipped: {skipped}, Failed: {failed}')
        )
