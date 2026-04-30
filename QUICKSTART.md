# 🚀 UniMarket Quick Start Guide

## 5-Minute Setup (Development)

### 1. Prerequisites
```bash
# Check Python version
python --version  # Must be 3.11+

# Clone the project
cd E:\Backup\pgwiz\smw
```

### 2. Environment Setup
```bash
# Copy environment template
copy .env.example .env

# Update .env for local development:
# ENVIRONMENT=development
# DEBUG=True
# DATABASE=SQLite (default, no setup needed)
# REDIS is optional for development
```

### 3. Install & Run
```bash
# Create virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run migrations (SQLite creates db.sqlite3)
python manage.py migrate

# Create admin user
python manage.py createsuperuser

# Start development server
python manage.py runserver
```

### 4. Access the Platform
```
Frontend:  http://localhost:8000
Admin:     http://localhost:8000/admin/
Accounts:  http://localhost:8000/accounts/
Shops:     http://localhost:8000/shops/
Dashboard: http://localhost:8000/dashboard/
```

### 5. Test Accounts
```
Admin:     (created via createsuperuser)
Buyer:     Create via /accounts/signup/ with role='buyer'
Seller:    Create via /accounts/signup/ with role='seller'
University Admin: Create via /accounts/signup/ with role='university_admin'
```

---

## 📱 Platform Tour

### For Buyers
1. Go to `/shops/search/` to browse listings
2. Filter by category, price, condition
3. Click listing to view details
4. Message seller via conversation system
5. Complete purchase with M-Pesa

### For Sellers
1. Create shop at `/shops/create/`
2. Post listings at `/shops/create/`
3. View analytics at `/dashboard/seller/analytics/`
4. Manage messages at `/dashboard/seller/messages/`
5. Switch shop theme at `/dashboard/seller/settings/`

### For University Admins
1. Dashboard: `/dashboard/university/dashboard/`
2. Manage shops: `/dashboard/university/shops/`
3. Moderate listings: `/dashboard/university/listings/`
4. View analytics: `/dashboard/university/analytics/`

---

## 🧪 Running Tests

```bash
# Run all tests
python manage.py test

# Run specific test file
python manage.py test tests_integration

# Run with verbose output
python manage.py test -v 2

# Run with coverage
pip install coverage
coverage run --source='.' manage.py test
coverage report
coverage html  # Generate HTML report
```

---

## 📊 Key Features

### ✨ Marketplace
- [x] Browse & search listings
- [x] Filter by category, price, condition
- [x] View seller profile
- [x] Mark items as sold/sold-out
- [x] Image upload support

### 💬 Messaging
- [x] Real-time WebSocket chat
- [x] Read receipts
- [x] Typing indicators
- [x] Conversation threading
- [x] Message history

### 💳 Payments
- [x] M-Pesa STK push integration
- [x] Transaction tracking
- [x] Payment confirmation
- [x] Receipt management
- [x] Fee scheduling

### 🎨 Themes
- [x] Light & Dark built-in themes
- [x] Custom theme creation
- [x] Per-shop theme customization
- [x] CSS variable system
- [x] Theme preview

### 👥 Admin Dashboards
- [x] University admin console
- [x] Seller analytics dashboard
- [x] Shop management
- [x] Listing moderation
- [x] Revenue tracking

### 🤖 AI Features
- [x] Trending listings
- [x] Personalized recommendations
- [x] Smart search ranking
- [x] Fraud detection
- [x] Suspicious activity alerts

---

## 🔧 Common Tasks

### Add a New Category
```bash
python manage.py shell
>>> from mydak.models import Category
>>> Category.objects.create(name='Books', icon='book')
```

### Create Test Listings
```bash
python manage.py shell
>>> from app.models import User
>>> from mydak.models import Shop, Listing, Category
>>> seller = User.objects.create_user(email='seller@test.com', password='test123', role='seller')
>>> shop = Shop.objects.create(name='Test Shop', owner=seller, is_active=True)
>>> cat = Category.objects.get_or_create(name='Electronics')[0]
>>> Listing.objects.create(
...     title='Laptop', 
...     price=50000, 
...     seller=seller, 
...     shop=shop, 
...     category=cat, 
...     status='active'
... )
```

### Run with WebSocket Support
```bash
# Install Daphne (already in requirements.txt)
pip install daphne

# Start with WebSocket support
daphne -b 0.0.0.0 -p 8000 config.asgi:application

# Messaging will work in real-time
```

### Enable Email Verification
```python
# In .env:
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=your_app_password
```

---

## 📂 File Organization

```
Key Files to Know:

Settings:
- config/settings/base.py       ← Main config (read this first)
- config/asgi.py                ← WebSocket routing
- config/wsgi.py                ← WSGI entry point

Models:
- app/models.py                 ← Core models (User, Client, Category)
- mydak/models.py               ← Marketplace models

Views:
- mydak/listing_views.py        ← Listing CRUD + search
- mydak/seller_views.py         ← Seller dashboard
- app/university_admin_views.py ← Admin console

Forms:
- mydak/listing_forms.py        ← Listing forms
- mydak/payment_forms.py        ← Payment forms

Real-time:
- mydak/consumers.py            ← WebSocket consumer
- config/asgi.py                ← Channel routing

Payments:
- mydak/mpesa.py                ← M-Pesa integration
- mydak/payment_views.py        ← Payment flow

AI/Search:
- mydak/ai_features.py          ← Recommendations, ranking, fraud detection

Testing:
- tests_integration.py          ← Test suite
```

---

## 🐛 Troubleshooting

### Port 8000 Already in Use
```bash
# Find process using port 8000
netstat -ano | findstr :8000

# Kill process by PID
taskkill /PID <PID> /F

# Or use different port
python manage.py runserver 8001
```

### Database Locked (SQLite)
```bash
# Delete and recreate database
rm db.sqlite3
python manage.py migrate
python manage.py createsuperuser
```

### Migrations Failed
```bash
# Show migration history
python manage.py showmigrations

# Rollback specific app
python manage.py migrate mydak 0001

# Reapply migrations
python manage.py migrate
```

### Static Files Not Loading
```bash
# Collect static files
python manage.py collectstatic --noinput --clear

# For development, ensure DEBUG=True
```

### Themes Not Loading
```bash
# Create built-in themes
python manage.py shell
>>> from apps.themes.builtin_themes import create_built_in_themes
>>> create_built_in_themes()
```

---

## 📝 Next Steps

1. **Explore the Code**
   - Read `config/settings/base.py` to understand configuration
   - Browse `mydak/models.py` to see data models
   - Check `mydak/listing_views.py` for view patterns

2. **Customize for Your University**
   - Update `.env` with your university name/domain
   - Create university tenant via admin
   - Customize themes in `/themes/`
   - Add categories for your marketplace

3. **Deploy to Production**
   - Follow deployment guide in `IMPLEMENTATION_COMPLETE.md`
   - Set up PostgreSQL + Redis
   - Configure M-Pesa credentials
   - Use Gunicorn + Daphne for production

4. **Add Your Features**
   - Review `IMPLEMENTATION_COMPLETE.md` for architecture
   - Follow existing patterns for new models/views
   - Add tests for new features
   - Use permission classes for access control

---

## 📞 Quick Links

- **Documentation:** `IMPLEMENTATION_COMPLETE.md`
- **Progress Tracking:** `PROGRESS.md`
- **Audit Report:** `AUDIT.md`
- **Admin Panel:** `/admin/`
- **Settings:** `config/settings/base.py`
- **Models:** `app/models.py`, `mydak/models.py`

---

## ✅ Verification Checklist

```
[✓] Python 3.11+ installed
[✓] Dependencies installed (pip install -r requirements.txt)
[✓] Environment configured (.env created)
[✓] Migrations applied (python manage.py migrate)
[✓] Admin user created (python manage.py createsuperuser)
[✓] Server running (python manage.py runserver)
[✓] Can access http://localhost:8000
[✓] Can login to admin (/admin/)
[✓] Can access marketplace (/shops/search/)
[✓] Tests pass (python manage.py test)
```

---

**Status:** ✅ Production-Ready  
**Build Date:** 2026-04-30  
**Version:** 1.0

Enjoy building with UniMarket! 🎉
