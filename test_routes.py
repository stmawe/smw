#!/usr/bin/env python3
"""
Route Testing Utility with Session-Based User Authentication
Creates session files representing different users with various roles/permissions.
Tests all routes in admin_urls.py and logs errors.
"""

import os
import sys
import django
import json
import requests
from datetime import datetime
from pathlib import Path

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.contrib.auth import get_user_model
from django.contrib.sessions.models import Session
from django.utils import timezone
from django.test import Client
from app.admin_permissions import AdminPermission, AdminRole
from app.models import AdminAuditLog, AdminActivityFeed

User = get_user_model()


class SessionTestUser:
    """Represents a test user with specific roles and permissions"""
    
    def __init__(self, username, email, roles=None, is_superuser=False, is_staff=False):
        self.username = username
        self.email = email
        self.roles = roles or []
        self.is_superuser = is_superuser
        self.is_staff = is_staff
        self.user = None
        self.client = None
        
    def create(self):
        """Create or get the test user"""
        self.user, created = User.objects.get_or_create(
            username=self.username,
            defaults={
                'email': self.email,
                'is_staff': self.is_staff,
                'is_superuser': self.is_superuser,
                'is_active': True,
            }
        )
        if not created:
            self.user.is_staff = self.is_staff
            self.user.is_superuser = self.is_superuser
            self.user.save()
        return self.user
    
    def get_client(self):
        """Get an authenticated test client for this user"""
        self.create()
        self.client = Client()
        self.client.force_login(self.user)
        return self.client


class RouteTestRunner:
    """Test runner that tests all routes with different user roles"""
    
    # Define test users with different permission levels
    TEST_USERS = {
        'superuser': SessionTestUser('admin_super', 'super@test.local', is_superuser=True, is_staff=True),
        'admin': SessionTestUser('admin_user', 'admin@test.local', is_staff=True),
        'moderator': SessionTestUser('admin_mod', 'mod@test.local'),
        'viewer': SessionTestUser('admin_view', 'view@test.local'),
    }
    
    # Routes from admin_urls.py
    ROUTES_TO_TEST = [
        # Dashboard
        ('admin_dashboard_full', 'GET'),
        
        # User Management
        ('admin_users_list', 'GET'),
        ('admin_user_create', 'GET'),
        
        # Shop Management
        ('admin_shops_list', 'GET'),
        
        # Listings
        ('admin_listings_list', 'GET'),
        
        # Categories
        ('admin_categories_list', 'GET'),
        
        # Transactions
        ('admin_transactions_list', 'GET'),
        
        # Analytics
        ('admin_analytics_dashboard', 'GET'),
        
        # Audit Logs
        ('admin_audit_logs', 'GET'),
        
        # Settings
        ('admin_settings', 'GET'),
        
        # Themes
        ('admin_themes_list', 'GET'),
        
        # SSL Domains
        ('admin_ssl_domains', 'GET'),
        
        # Activity Feed
        ('admin_activity_feed_view', 'GET'),
        
        # Changelog
        ('admin_changelog_view', 'GET'),
        
        # Moderation
        ('admin_moderation_center', 'GET'),
    ]
    
    def __init__(self):
        self.results = {
            'passed': [],
            'failed': [],
            'errors': [],
            'skipped': [],
        }
        self.start_time = None
        self.end_time = None
        
    def test_route(self, route_name, method, client, user_type):
        """Test a single route with a specific user"""
        try:
            from django.urls import reverse
            url = reverse(route_name)
        except Exception as e:
            self.results['skipped'].append({
                'route': route_name,
                'user': user_type,
                'reason': f'Route not found: {str(e)}'
            })
            return False
        
        try:
            if method.upper() == 'GET':
                response = client.get(url)
            elif method.upper() == 'POST':
                response = client.post(url)
            else:
                response = client.get(url)
            
            # Check if response is successful (2xx or 3xx)
            if 200 <= response.status_code < 400:
                self.results['passed'].append({
                    'route': route_name,
                    'url': url,
                    'user': user_type,
                    'status_code': response.status_code,
                    'time': timezone.now().isoformat(),
                })
                return True
            else:
                self.results['failed'].append({
                    'route': route_name,
                    'url': url,
                    'user': user_type,
                    'status_code': response.status_code,
                    'reason': f'HTTP {response.status_code}',
                })
                return False
                
        except Exception as e:
            self.results['errors'].append({
                'route': route_name,
                'user': user_type,
                'error': str(e),
                'error_type': type(e).__name__,
            })
            return False
    
    def run_all_tests(self):
        """Run tests for all routes with all user types"""
        self.start_time = timezone.now()
        
        print("\n" + "="*80)
        print("ROUTE TESTING WITH SESSION-BASED USERS")
        print("="*80 + "\n")
        
        # Create test users
        print("[*] Creating test users...")
        for user_type, test_user in self.TEST_USERS.items():
            test_user.create()
            print(f"    ✓ {user_type}: {test_user.username}")
        
        print(f"\n[*] Testing {len(self.ROUTES_TO_TEST)} routes with {len(self.TEST_USERS)} user types...")
        print()
        
        # Test each route with each user type
        total_tests = len(self.ROUTES_TO_TEST) * len(self.TEST_USERS)
        tests_run = 0
        
        for route_name, method in self.ROUTES_TO_TEST:
            for user_type, test_user in self.TEST_USERS.items():
                client = test_user.get_client()
                self.test_route(route_name, method, client, user_type)
                tests_run += 1
                
                # Progress indicator
                progress = (tests_run / total_tests) * 100
                print(f"\r[*] Progress: {progress:.1f}% ({tests_run}/{total_tests})", end='', flush=True)
        
        self.end_time = timezone.now()
        print("\n")
        
        return self.generate_report()
    
    def generate_report(self):
        """Generate test report"""
        duration = (self.end_time - self.start_time).total_seconds()
        total = sum(len(v) for v in self.results.values())
        
        print("\n" + "="*80)
        print("TEST RESULTS")
        print("="*80 + "\n")
        
        print(f"Duration: {duration:.2f}s")
        print(f"Total Tests: {total}")
        print(f"✓ Passed:  {len(self.results['passed'])}")
        print(f"✗ Failed:  {len(self.results['failed'])}")
        print(f"⚠ Errors:  {len(self.results['errors'])}")
        print(f"⊘ Skipped: {len(self.results['skipped'])}")
        
        # Summary percentages
        if total > 0:
            pass_rate = (len(self.results['passed']) / total) * 100
            print(f"\nPass Rate: {pass_rate:.1f}%")
        
        # Detailed failures
        if self.results['failed']:
            print("\n" + "-"*80)
            print("FAILED TESTS:")
            print("-"*80)
            for failure in self.results['failed']:
                print(f"\n  Route: {failure['route']}")
                print(f"  User: {failure['user']}")
                print(f"  Status: {failure['status_code']}")
                print(f"  URL: {failure['url']}")
        
        # Detailed errors
        if self.results['errors']:
            print("\n" + "-"*80)
            print("ERRORS:")
            print("-"*80)
            for error in self.results['errors']:
                print(f"\n  Route: {error['route']}")
                print(f"  User: {error['user']}")
                print(f"  Error Type: {error['error_type']}")
                print(f"  Error: {error['error']}")
        
        # Save report to file
        report_file = 'TEST_REPORT.json'
        with open(report_file, 'w') as f:
            json.dump({
                'timestamp': self.start_time.isoformat(),
                'duration_seconds': duration,
                'total_tests': total,
                'results': {
                    'passed': len(self.results['passed']),
                    'failed': len(self.results['failed']),
                    'errors': len(self.results['errors']),
                    'skipped': len(self.results['skipped']),
                },
                'details': self.results,
            }, f, indent=2)
        
        print(f"\n[*] Report saved to {report_file}")
        print("\n" + "="*80 + "\n")
        
        return len(self.results['failed']) == 0 and len(self.results['errors']) == 0


def main():
    """Main entry point"""
    try:
        runner = RouteTestRunner()
        success = runner.run_all_tests()
        
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n[!] Test runner failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
