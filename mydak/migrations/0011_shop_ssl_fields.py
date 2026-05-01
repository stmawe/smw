# Generated migration for SSL certificate fields on Shop model

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mydak', '0010_sellerrule_offerrule'),
    ]

    operations = [
        migrations.AddField(
            model_name='shop',
            name='has_ssl',
            field=models.BooleanField(default=False, help_text='Whether SSL certificate is active'),
        ),
        migrations.AddField(
            model_name='shop',
            name='ssl_subdomain',
            field=models.CharField(blank=True, db_index=True, help_text='Subdomain with SSL certificate (e.g., shop-name.smw.pgwiz.cloud)', max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='shop',
            name='ssl_cert_path',
            field=models.CharField(blank=True, help_text='Path to SSL certificate on server', max_length=512, null=True),
        ),
        migrations.AddField(
            model_name='shop',
            name='ssl_expires_at',
            field=models.DateTimeField(blank=True, help_text='SSL certificate expiration date', null=True),
        ),
    ]
