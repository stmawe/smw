"""
Migration: add ShopManager model to tenant schema.
Apply with: python manage.py migrate_schemas --tenant
"""

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mydak', '0012_shop_url_routing'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ShopManager',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('can_edit_listings', models.BooleanField(default=True, help_text='Can create and edit listings for this shop')),
                ('can_view_orders', models.BooleanField(default=True, help_text='Can view orders and transactions for this shop')),
                ('can_message_buyers', models.BooleanField(default=True, help_text='Can respond to buyer messages for this shop')),
                ('is_active', models.BooleanField(default=True)),
                ('assigned_by', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='shop_manager_assignments',
                    to=settings.AUTH_USER_MODEL,
                )),
                ('manager', models.ForeignKey(
                    db_index=True,
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='managed_shops',
                    to=settings.AUTH_USER_MODEL,
                )),
                ('shop', models.ForeignKey(
                    db_index=True,
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='managers',
                    to='mydak.shop',
                )),
            ],
            options={
                'ordering': ['-created_at'],
                'unique_together': {('shop', 'manager')},
            },
        ),
        migrations.AddIndex(
            model_name='shopmanager',
            index=models.Index(fields=['manager', 'is_active'], name='mydak_shopmanager_mgr_active_idx'),
        ),
        migrations.AddIndex(
            model_name='shopmanager',
            index=models.Index(fields=['shop', 'is_active'], name='mydak_shopmanager_shop_active_idx'),
        ),
    ]
