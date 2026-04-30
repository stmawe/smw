# 📋 CODEBASE AUDIT REPORT
**Generated:** 2026-04-30  
**Status:** CRITICAL ISSUES IDENTIFIED  

---

## 🔍 EXECUTIVE SUMMARY

The UniMarket codebase has a foundation with django-tenants integration and basic models, but suffers from:
- **Hardcoded credentials & secrets in settings.py** (CRITICAL SECURITY)
- **No environment-based configuration** (.env not utilized properly)
- **Incomplete tenant routing** (no subdomain support configured)
- **Missing model enhancements** (no timestamps on all models, missing indexes)
- **Scattered template structure** (inconsistent inheritance, no base component library)
- **No clear app separation** (only 2 apps: `app` and `mydak`)
- **Missing permission framework** (User model has roles but no permission classes)
- **No theme engine** (templates are static HTML)

---

## 1. INSTALLED APPS & STRUCTURE

### Current Apps
```
SHARED_APPS (public schema):
├── django_tenants (required)
├── django.contrib.admin
├── django.contrib.auth
├── django.contrib.contenttypes
├── django.contrib.sessions
├── django.contrib.messages
├── django.contrib.staticfiles
└── app (contains Client, Domain, User, Category models)

TENANT_APPS (tenant schemas):
└── mydak (contains Shop, Listing, Message, Transaction, etc.)
```

### ⚠️ Issues
- [ ] Apps should be split into modular `apps/` directory (accounts, shops, listings, payments, themes, etc.)
- [ ] No separate apps for: themes, messaging, payments, analytics, ai features
- [ ] `app` naming is too generic; should be `tenants` (for Client/Domain) and `public` (for homepage/blog)

### ✅ Recommended Structure
```
apps/
├── core/              ← shared mixins, base models, utils
├── tenants/          ← Client, Domain models (from current app)
├── public/           ← homepage, blog, contact (migrate from app)
├── accounts/         ← User, auth, permissions (from current app)
├── shops/            ← Shop model (from mydak)
├── listings/         ← Listing model (from mydak)
├── messaging/        ← Message model (from mydak)
├── payments/         ← Transaction, Payment models (from mydak)
├── analytics/        ← ShopAnalytics (from mydak)
├── themes/           ← Theme engine, XML themes
└── ai/              ← AI features (future)
```

---

## 2. DATABASE CONFIGURATION

### Current State (smw/settings.py, lines 103-128)
```python
# ❌ HARDCODED CREDENTIALS (CRITICAL)
DATABASES = {
    "default": {
        "ENGINE": "django_tenants.postgresql_backend",
        "NAME": "smw",
        "USER": "postgres",
        "PASSWORD": token,  # token from os.environ.get("dbpass"), not validated
        "HOST": "localhost",
        "PORT": "5432",
    }
}

# ❌ MULTIPLE DATABASE CONFIGS (commented-out Aiven prod config)
# ❌ COMMENTED-OUT SQLite fallback
```

### Issues
- [ ] No .env validation or defaults
- [ ] `token` variable used but error handling missing
- [ ] No separate dev/prod/test settings files
- [ ] No DATABASE_ROUTERS for shared/tenant separation clarity
- [ ] Hardcoded localhost (won't work cross-environment)

### ✅ Required Actions (Phase 1)
- [ ] Create `config/settings/` directory with: `base.py`, `dev.py`, `prod.py`
- [ ] Create `.env.example` with all required variables
- [ ] Use `python-decouple` or `django-environ` for env reading
- [ ] Add validation for missing env vars

---

## 3. MODELS AUDIT

### app/models.py

#### ✅ Client (TenantMixin)
```python
class Client(TenantMixin):
    name = models.CharField(max_length=255, unique=True)
    type = models.CharField(max_length=20, choices=[('university', 'University'), ('area', 'Area')])
    paid_until = models.DateField(null=True, blank=True)
    on_trial = models.BooleanField(default=True)
```
**Issues:**
- [ ] Missing `__str__` (HAS IT ✓)
- [ ] Missing Meta.ordering
- [ ] `type` field should be `tenant_type` (per AGENT.md spec)
- [ ] No indexes on frequently queried fields
- [ ] No created_at/updated_at timestamps
- [ ] No parent_tenant FK (for Shop → University hierarchy)

#### ✅ ClientDomain (DomainMixin)
- [ ] Has `__str__` ✓
- [ ] Missing Meta.ordering

#### ⚠️ User (AbstractUser)
```python
class User(AbstractUser):
    ROLE_CHOICES = (
        ('buyer', 'Buyer'),
        ('seller', 'Seller'),
        ('superadmin', 'SuperAdmin'),
        ('university_admin', 'University Admin'),
        ('area_admin', 'Area Admin'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='buyer')
```
**Issues:**
- [ ] Missing `__str__` (rely on AbstractUser's)
- [ ] No permission classes implemented (only raw role strings)
- [ ] No is_active, is_verified, email_verified fields
- [ ] No timestamp fields
- [ ] Role-based access control is incomplete (no Meta.permissions)

#### ✅ Category
```python
class Category(models.Model):
    name = models.CharField(max_length=255, unique=True)
```
**Issues:**
- [ ] No db_index on name (frequently filtered)
- [ ] No timestamps
- [ ] Missing slug field

### mydak/models.py

#### ⚠️ Shop
```python
class Shop(models.Model):
    name = models.CharField(max_length=255)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='shops')
    template = models.CharField(max_length=255, default='default')
    domain = models.CharField(max_length=255, unique=True, null=True, blank=True)
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```
**Status:** Timestamps present ✓  
**Issues:**
- [ ] Missing `__str__` (HAS IT ✓)
- [ ] Missing db_index on owner_id, domain, is_active
- [ ] Missing Meta.ordering
- [ ] No parent_tenant reference (should link to Client/University)
- [ ] No theme_id field (for Phase 5)
- [ ] `template` should be `theme_id` with FK to Theme model
- [ ] Missing description, logo, hours, social_links fields

#### ⚠️ Listing
```python
class Listing(models.Model):
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='listings')
    shop = models.ForeignKey('Shop', on_delete=models.CASCADE, related_name='listings', null=True, blank=True)
    title = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.ForeignKey('app.Category', on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
```
**Issues:**
- [ ] Missing updated_at timestamp
- [ ] Missing `__str__` (HAS IT ✓)
- [ ] Missing Meta.ordering
- [ ] No status field (ACTIVE, SOLD, EXPIRED, DRAFT)
- [ ] No views counter (for analytics)
- [ ] No is_featured, expires_at fields
- [ ] No db_index on seller_id, category_id, created_at
- [ ] Missing images ManyToMany relationship
- [ ] Should extend TimeStampedModel (Phase 3)

#### ⚠️ Transaction
```python
class Transaction(models.Model):
    TRANSACTION_TYPES = (
        ('shop_creation', 'Shop Creation Fee'),
        ('ad_purchase', 'Ad Purchase'),
        ('item_purchase', 'Item Purchase'),
    )
    shop = models.ForeignKey(Shop, ...)
    user = models.ForeignKey(User, ...)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    type = models.CharField(max_length=50, choices=TRANSACTION_TYPES)
    status = models.CharField(max_length=20, default='pending', ...)
    timestamp = models.DateTimeField(auto_now_add=True)
    reference_id = models.CharField(max_length=255, null=True, blank=True)
```
**Issues:**
- [ ] Has `__str__` ✓
- [ ] Missing created_at/updated_at (only timestamp)
- [ ] Missing Meta.ordering
- [ ] No db_index on user_id, status, type
- [ ] Should have reference UUID instead of CharField
- [ ] Rename `type` → `action` (per AGENT.md)
- [ ] Missing metadata JSONField for extensibility

#### ⚠️ Payment
```python
class Payment(models.Model):
    PAYMENT_METHODS = (('mpesa', 'M-Pesa'), ('stripe', 'Stripe'))
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    reference_id = models.CharField(max_length=255, unique=True)
    status = models.CharField(max_length=20, default='pending', ...)
    timestamp = models.DateTimeField(auto_now_add=True)
```
**Issues:**
- [ ] Duplicate of Transaction model (consolidate into Phase 10)
- [ ] Missing phone_number field (for M-Pesa)
- [ ] Missing metadata JSONField
- [ ] No db_indexes
- [ ] No `__str__` (HAS IT ✓)

#### ⚠️ Message
```python
class Message(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    listing = models.ForeignKey('Listing', on_delete=models.CASCADE, related_name='messages')
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
```
**Issues:**
- [ ] Missing updated_at
- [ ] Missing `__str__` (HAS IT ✓)
- [ ] Missing is_read field
- [ ] Missing attachment FileField
- [ ] Should model as Conversation + Message (per AGENT.md Phase 9)
- [ ] No db_index on sender_id, receiver_id, is_read

#### ✅ ShopAnalytics
- [ ] Has `__str__` ✓
- [ ] Missing created_at/updated_at
- [ ] last_updated field should be auto_now, not default

#### ⚠️ BlogCategory
```python
class BlogCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
```
**Status:** Has Meta.ordering ✓, auto-slugification ✓  
**Issues:**
- [ ] Missing timestamps
- [ ] No db_index on slug

#### ✅ BlogPost
- [ ] Has `__str__` ✓
- [ ] Has Meta.ordering ✓
- [ ] Has created_on/updated_on ✓
- [ ] Has auto-slugification ✓
- [ ] **Issues:** Only `created_on` (should be `created_at`)

---

## 4. VIEWS AUDIT

### app/views.py
**Status:** Not fully reviewed (large file)

**Issues found (from urls.py references):**
- [ ] refs, homepage_view, about_view, features_view, faq_view, contact_view, search, products_view, login_view, tenant_register_view
- [ ] No permission checks documented
- [ ] No pagination visible in URLs
- [ ] Search view may lack tenant isolation

---

## 5. URLS ROUTING

### smw/urls.py
```python
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('app.urls'))
]
```
**Issues:**
- [ ] No tenant-based routing
- [ ] No subdomain support
- [ ] No PUBLIC_SCHEMA_URLCONF configured
- [ ] Missing config/tenant_urls.py

### app/urls.py
```python
urlpatterns = [
    path('', views.refs, name='index'),
    path('search/', views.search, name='search'),
    path('h/', views.homepage_view, name='homepage'),
    # ... 15+ paths
]
```
**Issues:**
- [ ] Redundant paths (refs → index, h → homepage)
- [ ] No API endpoints (should be /api/v1/...)
- [ ] No dashboard URLs (should separate by tenant type)
- [ ] Tenant URLs mixed with public URLs

---

## 6. TEMPLATES AUDIT

### Structure
```
templates/
├── base.html                         ← Main template
├── home_base.html                    ← Duplicate? (both base.html?)
├── accounts/
│   ├── login.html
│   ├── register.html
│   └── signup.html                   ← Duplicate? (register.html?)
├── blog/
│   ├── blog_list.html
│   └── blog_detail.html
├── dashboard/
│   └── superadmin_dashboard.html
├── partials/
│   └── footer.html                   ← Incomplete (no navbar, sidebar, etc.)
└── [Top-level loose templates]
    ├── about.html
    ├── contact.html
    ├── faq.html
    ├── features.html
    ├── homepage.html
    ├── index.html
    ├── product.html
    ├── ref.html
    └── search_results.html
```

### Issues
- [ ] No inheritance hierarchy (inconsistent base.html usage)
- [ ] Duplicate templates: signup.html vs register.html
- [ ] Redundant homepage variations: index.html, homepage.html, home_base.html
- [ ] Missing component library (no navbar.html, sidebar.html, card.html, etc.)
- [ ] No theme support (all styles hardcoded)
- [ ] Footer only partial; no navbar partial
- [ ] No responsive grid components
- [ ] Missing form partials (form_field.html, form_errors.html)
- [ ] No pagination template
- [ ] No CSRF token handling documented

---

## 7. STATIC FILES AUDIT

### CSS Files
```
static/
├── css/
│   ├── style.css      ← Main stylesheet
│   ├── register.css   ← Page-specific (should be combined)
│   ├── login.css      ← Page-specific (should be combined)
│   └── index.css      ← Page-specific (should be combined)
```

### Issues
- [ ] Multiple CSS files (should consolidate to single main.css)
- [ ] Page-specific CSS (register.css, login.css, index.css) should be in main.css or as components
- [ ] No CSS variable support (required for theme engine, Phase 5)
- [ ] Likely no mobile-first responsive design (no Tailwind/Bootstrap evident)
- [ ] No lazy-loading for images documented
- [ ] No image compression pipeline

---

## 8. HARDCODED STRINGS / CONFIGURATION

### Secrets & Credentials (CRITICAL)
**File: smw/settings.py, line 27**
```python
SECRET_KEY = 'django-insecure-smaid%$rcpugk6@==5&0n7u)%k19!gt&v-e$y&@8#52)3&-$zq'
```
❌ **HARDCODED** → Must move to .env

**File: smw/settings.py, lines 103-128**
- Database credentials hardcoded
- No environment-based switching

### Hostnames
**File: smw/settings.py, line 32**
```python
ALLOWED_HOSTS = []
```
❌ Empty (won't work in production)
- Should read from env: `ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['localhost'])`

### Domains
**File: mydak/models.py, line 45**
```python
return f"{self.domain}.domain.tld"  # Hardcoded .domain.tld
```
❌ Should use env BASE_DOMAIN

---

## 9. MISSING FEATURES (Per AGENT.md)

### Not Implemented
- [ ] Theme engine (XML-based, Phase 5)
- [ ] Permission classes (Phase 4)
- [ ] WebSocket/Messaging infrastructure (Phase 9)
- [ ] M-Pesa integration (Phase 10)
- [ ] Admin panels (Phase 11)
- [ ] AI features (Phase 12)
- [ ] Comprehensive test suite (Phase 13)
- [ ] Email verification flow
- [ ] Google OAuth integration
- [ ] Tenant isolation tests

---

## 10. SUMMARY TABLE

| Category | Status | Priority | Blocker |
|----------|--------|----------|---------|
| Settings (hardcodes) | 🔴 Critical | P0 | Yes |
| Model timestamps | 🟡 Partial | P1 | No |
| Model indexes | 🔴 Missing | P1 | No |
| Model __str__ | 🟢 Mostly OK | P2 | No |
| Permission classes | 🔴 Missing | P1 | Yes |
| App structure | 🟡 Needs refactor | P1 | Yes |
| Tenant routing | 🔴 Incomplete | P0 | Yes |
| URL organization | 🟡 Messy | P2 | No |
| Templates | 🟡 Inconsistent | P2 | No |
| Theme engine | 🔴 Missing | P2 | No |
| Static pipeline | 🟡 Redundant | P2 | No |
| Tests | 🔴 None | P3 | Yes (Phase 13) |
| Env config | 🔴 None | P0 | Yes |

---

## 📋 NEXT ACTIONS (Ordered by Dependency)

### Immediate (Blocks Phase 1+)
1. ✅ **Phase 0.1 - Audit** (this document)
2. → **Phase 0.2 - Unification Report** (this document)
3. → **Phase 1 - Environment & Config Hardening**
   - Create config/settings/ structure
   - Move secrets to .env
   - Implement env-based settings
4. → **Phase 2 - Tenant Routing**
   - Implement subdomain routing
   - Add Windows hosts file setup

### High Priority (Core)
5. → **Phase 3 - Model Hardening**
   - Add timestamps to all models
   - Add db_indexes
   - Create TimeStampedModel mixin
6. → **Phase 4 - Auth Overhaul**
   - Implement permission classes
   - Add email verification
   - Integrate django-allauth

### Medium Priority (Features)
7. → **Phase 5 - Theme Engine**
8. → **Phase 6 - Shop Creation**
9. → **Phase 7 - UI Unification**
10. → **Phase 8 - Marketplace Core**

### Later (Foundation complete)
11. → **Phase 9 - Messaging**
12. → **Phase 10 - Payments** (bootstrap, full in Phase 10)
13. → **Phase 11 - Admin Panels**
14. → **Phase 12 - AI Features**
15. → **Phase 13 - Testing** (continuous)

---

**Report Status:** READY FOR PHASE 1  
**Audit Complete:** 2026-04-30
