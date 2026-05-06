"""
Migration: shop URL routing tier system

Changes:
  1. Add Shop.is_root_shop (BooleanField, default=False)
  2. Add Shop.slug_approved (BooleanField, default=False)
  3. Remove unique constraint on Shop.domain
  4. Add unique_together [['owner', 'domain']] on Shop
  5. Create ShopSlugRequest model
"""

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mydak', '0011_shop_ssl_fields'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # 1. Add is_root_shop
        migrations.AddField(
            model_name='shop',
            name='is_root_shop',
            field=models.BooleanField(
                default=False,
                db_index=True,
                help_text='If True, this shop serves at the root of the owner subdomain (e.g. juju254.smw.pgwiz.cloud/)',
            ),
        ),

        # 2. Add slug_approved
        migrations.AddField(
            model_name='shop',
            name='slug_approved',
            field=models.BooleanField(
                default=False,
                help_text='If True, a custom slug was admin-approved for this shop',
            ),
        ),

        # 3. Remove old global unique constraint on Shop.domain
        migrations.AlterField(
            model_name='shop',
            name='domain',
            field=models.CharField(
                blank=True,
                db_index=True,
                help_text='Shop slug used as URL path segment (e.g. juju-electronics). Unique per owner.',
                max_length=255,
                null=True,
            ),
        ),

        # 4. Add per-owner unique_together on (owner, domain)
        migrations.AlterUniqueTogether(
            name='shop',
            unique_together={('owner', 'domain')},
        ),

        # 5. Create ShopSlugRequest
        migrations.CreateModel(
            name='ShopSlugRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('request_type', models.CharField(
                    choices=[('root_promotion', 'Root Promotion'), ('custom_slug', 'Custom Slug')],
                    db_index=True,
                    max_length=20,
                )),
                ('requested_slug', models.CharField(
                    blank=True,
                    help_text='Desired custom slug (required for custom_slug requests only)',
                    max_length=48,
                    null=True,
                )),
                ('status', models.CharField(
                    choices=[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')],
                    db_index=True,
                    default='pending',
                    max_length=20,
                )),
                ('payment_reference', models.CharField(
                    blank=True,
                    help_text='M-Pesa payment reference (if payment was required)',
                    max_length=255,
                    null=True,
                )),
                ('reviewer_notes', models.TextField(
                    blank=True,
                    help_text='Admin notes — required when rejecting',
                )),
                ('shop', models.ForeignKey(
                    db_index=True,
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='slug_requests',
                    to='mydak.shop',
                )),
                ('admin_reviewer', models.ForeignKey(
                    blank=True,
                    help_text='Admin who approved or rejected this request',
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='reviewed_slug_requests',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'ordering': ['created_at'],
                'indexes': [
                    models.Index(fields=['shop', 'status'], name='mydak_shopslug_shop_status_idx'),
                    models.Index(fields=['request_type', 'status'], name='mydak_shopslug_type_status_idx'),
                ],
                'unique_together': {('shop', 'request_type', 'status')},
            },
        ),
    ]
