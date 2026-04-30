"""Management command to add development host entries."""

import os
import platform
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Add a development host entry to the system hosts file (Windows/Linux/Mac)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--domain',
            type=str,
            required=True,
            help='Domain name to add (e.g., testshop.localhost)'
        )
        parser.add_argument(
            '--ip',
            type=str,
            default='127.0.0.1',
            help='IP address to bind (default: 127.0.0.1)'
        )

    def handle(self, *args, **options):
        domain = options['domain']
        ip = options['ip']
        system = platform.system()

        if system == 'Windows':
            self._add_to_hosts_windows(ip, domain)
        elif system in ['Linux', 'Darwin']:
            self._add_to_hosts_unix(ip, domain)
        else:
            raise CommandError(f'Unsupported OS: {system}')

    def _add_to_hosts_windows(self, ip, domain):
        """Add entry to Windows hosts file."""
        hosts_path = r'C:\Windows\System32\drivers\etc\hosts'
        self._add_hosts_entry(hosts_path, ip, domain)

    def _add_to_hosts_unix(self, ip, domain):
        """Add entry to Unix/Linux/Mac hosts file."""
        hosts_path = '/etc/hosts'
        
        # Check permissions
        if not os.access(hosts_path, os.W_OK):
            self.stdout.write(
                self.style.ERROR(
                    f'ERROR: No write permissions for {hosts_path}\n'
                    f'Try: sudo python manage.py add_dev_host --domain={domain}'
                )
            )
            raise CommandError('Permission denied')
        
        self._add_hosts_entry(hosts_path, ip, domain)

    def _add_hosts_entry(self, hosts_path, ip, domain):
        """Add or verify hosts entry."""
        entry = f"{ip}  {domain}"

        try:
            # Read current hosts file
            with open(hosts_path, 'r') as f:
                content = f.read()
        except FileNotFoundError:
            raise CommandError(f'Hosts file not found: {hosts_path}')

        # Check if entry already exists
        for line in content.split('\n'):
            if line.strip() == entry:
                self.stdout.write(
                    self.style.WARNING(f'Entry already exists: {entry}')
                )
                return

        # Add entry
        try:
            with open(hosts_path, 'a') as f:
                f.write(f'\n{entry}\n')
            self.stdout.write(
                self.style.SUCCESS(f'Successfully added: {entry}')
            )
            self.stdout.write(
                self.style.WARNING(
                    f'You can now access: http://{domain}/'
                )
            )
        except IOError as e:
            raise CommandError(f'Failed to write to {hosts_path}: {e}')
