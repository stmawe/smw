# Admin Panel Deployment Guide

## Pre-Deployment Checklist

### 1. System Requirements
- [ ] Python 3.8+
- [ ] Django 3.2+
- [ ] PostgreSQL 12+ (recommended) or MySQL 5.7+
- [ ] Redis 6+ (for caching, optional but recommended)
- [ ] SSL certificate (for HTTPS)
- [ ] Domain name
- [ ] Sufficient storage (at least 10GB for uploads)
- [ ] Adequate memory (at least 2GB RAM)

### 2. Environment Configuration
- [ ] Create `.env` file with secure settings
  ```
  SECRET_KEY=your-secure-random-key
  DEBUG=False
  ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
  DATABASE_URL=postgresql://user:password@localhost:5432/smw
  REDIS_URL=redis://localhost:6379/0
  ADMIN_EMAIL=admin@yourdomain.com
  ```
- [ ] Generate secure SECRET_KEY
- [ ] Set DEBUG=False
- [ ] Configure ALLOWED_HOSTS
- [ ] Setup database credentials

### 3. Database Setup
- [ ] Create database and user
- [ ] Run migrations: `python manage.py migrate`
- [ ] Create tables with: `python manage.py migrate app`
- [ ] Verify migrations succeeded

### 4. Create Admin Users
- [ ] Create superuser: `python manage.py createsuperuser`
- [ ] Create admin users: `python manage.py seed_admins`
- [ ] Verify users can login
- [ ] Test different roles (Admin, Moderator, Support)
- [ ] Assign appropriate permissions

### 5. Configure Admin Settings
- [ ] Set site name and title
- [ ] Configure email (SMTP settings)
- [ ] Setup payment gateway (if applicable)
- [ ] Configure file storage
- [ ] Setup logging

### 6. SSL Certificate Setup
- [ ] Generate/obtain SSL certificate
  - Option A: Let's Encrypt: `./setup_ssl.sh`
  - Option B: Purchase from provider
  - Option C: Use Certbot: `certbot certonly --standalone -d yourdomain.com`
- [ ] Install certificate in web server
- [ ] Configure web server for HTTPS
- [ ] Set SECURE_SSL_REDIRECT=True in settings

### 7. Web Server Configuration
- [ ] Configure Nginx or Apache
  - [ ] Setup proxy to Django app
  - [ ] Enable GZIP compression
  - [ ] Configure static/media file serving
  - [ ] Setup caching headers
- [ ] Test server responds on port 80 and 443
- [ ] Verify redirects from HTTP to HTTPS

### 8. Static Files & Media
- [ ] Run `python manage.py collectstatic`
- [ ] Verify static files directory: `static/`
- [ ] Setup media file storage
- [ ] Configure file upload limits
- [ ] Setup virus scanning (optional)

### 9. Caching & Performance
- [ ] Setup Redis connection: `redis-server`
- [ ] Configure Django cache backend
  ```python
  CACHES = {
      'default': {
          'BACKEND': 'django_redis.cache.RedisCache',
          'LOCATION': 'redis://127.0.0.1:6379/1',
          'OPTIONS': {'CLIENT_CLASS': 'django_redis.client.DefaultClient'}
      }
  }
  ```
- [ ] Test cache functionality
- [ ] Monitor cache hit rates

### 10. Logging & Monitoring
- [ ] Configure logging to file/service
- [ ] Setup error monitoring (Sentry, etc.)
- [ ] Configure daily log rotation
- [ ] Setup uptime monitoring
- [ ] Enable request logging

### 11. Security Hardening
- [ ] Set CSRF_COOKIE_SECURE=True
- [ ] Set SESSION_COOKIE_SECURE=True
- [ ] Set X_FRAME_OPTIONS='DENY'
- [ ] Enable HSTS headers
- [ ] Configure CORS (if needed)
- [ ] Setup IP whitelist for admin (optional)
- [ ] Enable 2FA for admin users (optional)
- [ ] Change all default passwords

### 12. Backup Strategy
- [ ] Setup automated database backups
- [ ] Configure backup retention (30+ days)
- [ ] Setup file backups (media uploads)
- [ ] Test backup restoration procedure
- [ ] Document backup recovery process

### 13. Admin Panel Testing
- [ ] Test user login and logout
- [ ] Test role-based access (all 5 roles)
- [ ] Test permission checks
  - [ ] Superuser can access all
  - [ ] Admin cannot access tenant management
  - [ ] Moderator cannot access settings
  - [ ] Support/Viewer have read-only access
- [ ] Test CRUD operations
  - [ ] Create user
  - [ ] Edit shop
  - [ ] Approve listing
  - [ ] Process refund
  - [ ] Create category
- [ ] Test data export (CSV)
- [ ] Test data import with validation
- [ ] Test activity feed and audit logs
- [ ] Test error handling (test 403, 404, 500 pages)

### 14. Feature Testing
- [ ] Dashboard metrics display correctly
- [ ] Search functionality works
- [ ] Filters work on all list pages
- [ ] Pagination works
- [ ] Bulk operations function
- [ ] Notifications display
- [ ] Announcements show correctly
- [ ] Theme switching works

### 15. Performance Testing
- [ ] Test with production-like data volume
- [ ] Check dashboard load time (target: <2s)
- [ ] Check list pages with pagination (target: <1s)
- [ ] Monitor database query count (prevent N+1)
- [ ] Monitor memory usage
- [ ] Load test with multiple concurrent users
- [ ] Check response times under load

### 16. Load Balancing (if applicable)
- [ ] Setup multiple app servers
- [ ] Configure load balancer (Nginx, HAProxy)
- [ ] Setup session storage (Redis)
- [ ] Configure sticky sessions (if needed)
- [ ] Test failover scenarios

### 17. Monitoring & Alerting
- [ ] Setup monitoring dashboard
- [ ] Configure alerts for:
  - [ ] High error rate (>1%)
  - [ ] Slow response times (>5s)
  - [ ] Low disk space (<10% free)
  - [ ] High memory usage (>90%)
  - [ ] Database connection failures
- [ ] Setup log aggregation (ELK, Splunk, etc.)

### 18. Final Verification
- [ ] Test all admin features one more time
- [ ] Verify SSL certificate is valid
- [ ] Check that DEBUG=False in production
- [ ] Verify SECRET_KEY is secure
- [ ] Test backup restoration
- [ ] Document deployment configuration
- [ ] Create runbook for common issues

### 19. Deployment Documentation
- [ ] Document server configuration
- [ ] Create deployment checklist
- [ ] Document recovery procedures
- [ ] Create troubleshooting guide
- [ ] Document admin users and roles

### 20. Post-Deployment
- [ ] Monitor system closely for 24-48 hours
- [ ] Check error logs regularly
- [ ] Verify database backups are running
- [ ] Train admin users on new features
- [ ] Schedule security audit
- [ ] Plan for regular updates and patches

## Quick Start Commands

```bash
# Setup environment
cp .env.template .env
# Edit .env with your settings

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Create demo admin users
python manage.py seed_admins

# Collect static files
python manage.py collectstatic --no-input

# Run development server
python manage.py runserver

# Run production server (with Gunicorn)
gunicorn smw.wsgi:application --workers 4 --bind 0.0.0.0:8000
```

## Troubleshooting

### Issue: Admin login page shows but login fails
**Solution:**
1. Check database connection: `python manage.py dbshell`
2. Verify admin user exists: `User.objects.filter(is_staff=True)`
3. Check SECRET_KEY is same in all servers
4. Clear sessions: `python manage.py clearsessions`

### Issue: Permissions not working
**Solution:**
1. Verify middleware is installed in MIDDLEWARE
2. Check AdminPermission model is created: `python manage.py migrate app`
3. Test with Django shell: `from app.admin_permissions import AdminPermission`
4. Verify user has proper role assigned

### Issue: Static files not loading (404)
**Solution:**
1. Run: `python manage.py collectstatic --no-input`
2. Verify web server is serving `/static/` directory
3. Check STATIC_URL and STATIC_ROOT settings
4. For development, enable DEBUG=True

### Issue: Slow admin pages
**Solution:**
1. Check query count: Add `django-debug-toolbar`
2. Verify Redis cache is running
3. Check database indexes exist
4. Monitor slow query logs
5. Scale horizontally if needed

### Issue: Out of memory errors
**Solution:**
1. Reduce worker processes
2. Increase available RAM
3. Implement pagination more aggressively
4. Clear old audit logs: `AdminAuditLog.objects.filter(created_at__lt=old_date).delete()`
5. Optimize queries with `select_related()` and `prefetch_related()`

## Monitoring Dashboard

Monitor these metrics:
- **Request rate** (requests/sec)
- **Error rate** (errors/min)
- **Response time** (avg, p95, p99)
- **Database connections** (active/max)
- **Cache hit rate** (target: >80%)
- **Disk usage** (monitor growth)
- **Memory usage** (target: <70%)
- **CPU usage** (target: <80%)

## Support

For issues or questions:
1. Check logs: `/var/log/django/` or `/var/log/admin-panel/`
2. Run Django checks: `python manage.py check`
3. Test with shell: `python manage.py shell`
4. Contact development team with error details
