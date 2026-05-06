"""
Migration: add Entity model to public schema.

Apply with:
    python manage.py migrate_schemas --shared
    (NEVER bare python manage.py migrate)
"""

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0005_add_mpesa_transaction'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Entity',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('entity_type', models.CharField(
                    help_text='Free-form type label, e.g. "University", "Location", "NGO"',
                    max_length=100,
                )),
                ('subdomain', models.SlugField(
                    help_text='Subdomain slug — becomes {subdomain}.smw.pgwiz.cloud',
                    max_length=63,
                    unique=True,
                )),
                ('status', models.CharField(
                    choices=[
                        ('pending', 'Pending'),
                        ('active', 'Active'),
                        ('suspended', 'Suspended'),
                    ],
                    db_index=True,
                    default='pending',
                    max_length=20,
                )),
                ('is_active', models.BooleanField(
                    default=False,
                    help_text='Derived from status in save() — do not set directly',
                )),
                ('city', models.CharField(blank=True, max_length=100)),
                ('country', models.CharField(blank=True, max_length=100)),
                ('website', models.URLField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('admin_user', models.ForeignKey(
                    blank=True,
                    help_text='Designated admin for this entity',
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='administered_entities',
                    to=settings.AUTH_USER_MODEL,
                )),
                ('created_by', models.ForeignKey(
                    blank=True,
                    help_text='NULL for self-registrations; set to admin user for admin-created entities',
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='created_entities',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'verbose_name_plural': 'entities',
                'ordering': ['name'],
            },
        ),
        migrations.AddIndex(
            model_name='entity',
            index=models.Index(fields=['status'], name='app_entity_status_idx'),
        ),
        migrations.AddIndex(
            model_name='entity',
            index=models.Index(fields=['is_active', 'name'], name='app_entity_active_name_idx'),
        ),
    ]
