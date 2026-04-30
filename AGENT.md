# 🧠 AGENT.md — UniMarket Platform Build Contract
> **Stack:** Django + django-tenants + WSGI | PostgreSQL | Python  
> **Source of Truth:** Mermaid diagram + original feature spec  
> **Agent Rules:** No out-of-scope work. Modular. Test-heavy. Env-driven. Refactor > rewrite.

---

## 📐 SYSTEM ARCHITECTURE OVERVIEW

```
baseurl.com                    → Public schema (landing, blog, FAQ)
university.baseurl.com         → University tenant (console + shop mgmt)
location.baseurl.com           → Location tenant (console + shop mgmt)
shopname.baseurl.com           → Shop tenant (buyer/seller flows)
```

**Multi-tenancy model:** `django-tenants` with PostgreSQL schemas  
**Routing:** Subdomain-based via `ALLOWED_HOSTS` wildcard + tenant middleware  
**DNS (prod):** Cloudflare wildcard `*.baseurl.com → server IP`  
**DNS (dev):** Windows `hosts` file entries (see §LOCAL DEV SETUP)

---

## 🗂️ PHASE STRUCTURE

| Phase | Name | Priority |
|-------|------|----------|
| 0 | Audit & Unification | CRITICAL |
| 1 | Env & Config Hardening | CRITICAL |
| 2 | Tenant Routing (Windows-safe) | CRITICAL |
| 3 | Schema & Model Audit | HIGH |
| 4 | Auth Overhaul | HIGH |
| 5 | Theme Engine (XML-based) | HIGH |
| 6 | Shop Creation Flow | HIGH |
| 7 | UI Unification & Refactor | MEDIUM |
| 8 | Marketplace Core | MEDIUM |
| 9 | Messaging (WebSocket) | MEDIUM |
| 10 | Payments (M-Pesa) | MEDIUM |
| 11 | Admin Panels | MEDIUM |
| 12 | AI Agent Features | LOW |
| 13 | Testing Suite | CONTINUOUS |

---

## ⚙️ PHASE 0 — AUDIT & UNIFICATION

> Agent reads ALL existing code before touching anything.

### TODO-0.1 — Full Codebase Inventory
```
[ ] List all installed apps in settings.py
[ ] Map all existing models → which schema they belong to
[ ] List all URL patterns across all apps
[ ] List all templates and identify duplicates / inconsistencies
[ ] List all static files (CSS/JS) — identify redundancy
[ ] Identify all hardcoded strings (DB URLs, secrets, hostnames)
[ ] Note all existing views (CBV vs FBV)
[ ] Document existing tenant structure (public vs tenant schemas)
```

### TODO-0.2 — Unification Report (output: AUDIT.md)
```
[ ] Summarize findings in AUDIT.md
[ ] Flag models with missing __str__, Meta, indexes
[ ] Flag views with no permission checks
[ ] Flag templates with no base inheritance
[ ] Flag any app not wired into tenants correctly
```

---

## ⚙️ PHASE 1 — ENV & CONFIG HARDENING

> All DB refs, secrets, and hostnames must come from `.env`. Zero hardcodes.

### TODO-1.1 — Environment Variables
Create `.env` (never commit) and `.env.example` (always commit):

```env
# .env.example
SECRET_KEY=your-secret-key-here
DEBUG=True

# Database
DB_NAME=unimarket
DB_USER=postgres
DB_PASSWORD=admin
DB_HOST=localhost
DB_PORT=5432

# Tenant
PUBLIC_SCHEMA_DOMAIN=localhost
BASE_DOMAIN=localhost

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
DEFAULT_FROM_EMAIL=noreply@unimarket.local

# M-Pesa
MPESA_CONSUMER_KEY=
MPESA_CONSUMER_SECRET=
MPESA_SHORTCODE=
MPESA_PASSKEY=
MPESA_CALLBACK_URL=

# Storage
USE_S3=False
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_STORAGE_BUCKET_NAME=

# Redis (for WebSockets/Celery)
REDIS_URL=redis://localhost:6379/0
```

### TODO-1.2 — Settings Refactor
```
[ ] Install python-decouple or django-environ
[ ] Replace ALL hardcoded values in settings.py with env reads
[ ] Split settings: base.py / dev.py / prod.py
[ ] Confirm DATABASES block reads from env
[ ] Confirm ALLOWED_HOSTS reads from env (wildcard for dev)
[ ] Add TENANT_SUBFOLDER_PREFIX if using subfolder mode fallback
```

### TODO-1.3 — Settings Structure
```python
# config/settings/base.py
DATABASES = {
    "default": {
        "ENGINE": "django_tenants.postgresql_backend",
        "NAME": env("DB_NAME"),
        "USER": env("DB_USER"),
        "PASSWORD": env("DB_PASSWORD"),
        "HOST": env("DB_HOST", default="localhost"),
        "PORT": env("DB_PORT", default="5432"),
    }
}

DATABASE_ROUTERS = ["django_tenants.routers.TenantSyncRouter"]
```

---

## ⚙️ PHASE 2 — TENANT ROUTING (WINDOWS-SAFE)

> The main pain point on Windows dev. This phase makes subdomains work locally.

### TODO-2.1 — Windows Hosts File Setup

Agent generates a PowerShell script `scripts/setup_hosts.ps1`:

```powershell
# Run as Administrator
$hostsPath = "C:\Windows\System32\drivers\etc\hosts"
$entries = @(
    "127.0.0.1  localhost",
    "127.0.0.1  public.localhost",
    "127.0.0.1  university.localhost",
    "127.0.0.1  location.localhost",
    "127.0.0.1  testshop.localhost"
)
foreach ($entry in $entries) {
    if (-not (Select-String -Path $hostsPath -Pattern $entry -Quiet)) {
        Add-Content -Path $hostsPath -Value $entry
        Write-Host "Added: $entry"
    }
}
Write-Host "Done. Hosts file updated."
```

> **Note to agent:** Each new shop/tenant created during dev requires a new entry. Automate this via a management command.

### TODO-2.2 — Management Command: `add_dev_host`
```
[ ] Create management/commands/add_dev_host.py
[ ] Accepts --domain argument
[ ] Appends 127.0.0.1 <domain> to hosts file (Windows path detection)
[ ] Detects OS (Windows vs Linux/Mac) and uses correct hosts path
[ ] Prints instruction if elevation needed
```

### TODO-2.3 — Django-Tenants Routing Config
```python
# config/urls.py (PUBLIC schema)
urlpatterns = [
    path("", include("apps.public.urls")),
    path("admin/", admin.site.urls),
]

# config/tenant_urls.py (TENANT schemas)
urlpatterns = [
    path("", include("apps.shops.urls")),
    path("dashboard/", include("apps.dashboard.urls")),
    path("auth/", include("apps.accounts.urls")),
]
```

```python
# settings/base.py
ROOT_URLCONF = "config.urls"
PUBLIC_SCHEMA_URLCONF = "config.urls"
```

### TODO-2.4 — Tenant Model Audit
```
[ ] Confirm Client model extends TenantMixin
[ ] Confirm Domain model extends DomainMixin
[ ] Confirm tenant_type field exists (choices: UNIVERSITY, LOCATION, SHOP)
[ ] Add parent_tenant FK (Shop → University or Location)
[ ] Confirm TENANT_APPS vs SHARED_APPS separation is correct
[ ] Write migration if schema changes needed
[ ] Run: python manage.py migrate_schemas --shared
```

---

## ⚙️ PHASE 3 — SCHEMA & MODEL AUDIT

### Current Expected Schema (verify vs actual)

```
PUBLIC SCHEMA
├── tenants_client (id, schema_name, name, tenant_type, created_on)
├── tenants_domain (id, domain, tenant_id, is_primary)
├── public_pages (blog, FAQ, contact)
└── tenant_registry (links shops → parent university/location)

UNIVERSITY SCHEMA (e.g., schema: university_ku)
├── shops (id, name, domain, template_id, owner_id)
├── analytics (views, sales, traffic)
└── console_settings

LOCATION SCHEMA (e.g., schema: location_nairobi)
├── shops (id, name, domain, template_id, owner_id)
├── analytics
└── console_settings

SHOP SCHEMA (e.g., schema: shop_juju)
├── users (buyers, sellers)
├── listings (id, title, price, category, images, seller_id)
├── orders
├── messages
├── transactions
└── shop_config (template, theme, XML config)
```

### TODO-3.1 — Model Hardening
```
[ ] Add db_index=True to all FK and frequently queried fields
[ ] Add __str__ to every model
[ ] Add Meta.ordering to list-heavy models
[ ] Add created_at / updated_at to all models (use TimeStampedModel mixin)
[ ] Add is_active flag to Listing, Shop, User models
[ ] Audit all CharField — add max_length where missing
[ ] Add unique constraints where appropriate (e.g., domain, schema_name)
```

### TODO-3.2 — TimeStampedModel Mixin
```python
# apps/core/models.py
class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True
```

---

## ⚙️ PHASE 4 — AUTH OVERHAUL

### Flow (per diagram):
```
ShopDashboard → New User → ShopRegistration → VerifyEmail → CreateShopUser
```

### TODO-4.1 — Auth Strategy
```
[ ] Use django-allauth for email/social auth
[ ] Support: email+password, Google OAuth
[ ] University email domain validation (e.g., @ku.ac.ke only for KU shops)
[ ] Email verification mandatory before full access
[ ] Separate user roles: BUYER, SELLER, SHOP_ADMIN, UNIVERSITY_ADMIN, LOCATION_MANAGER, SUPER_ADMIN
```

### TODO-4.2 — Permission Classes
```python
# apps/accounts/permissions.py
class IsShopSeller(BasePermission): ...
class IsUniversityAdmin(BasePermission): ...
class IsLocationManager(BasePermission): ...
class IsVerifiedUser(BasePermission): ...
```

### TODO-4.3 — Auth Views
```
[ ] Register view (tenant-aware — registers within current schema)
[ ] Login view (redirects based on role)
[ ] Email verification view
[ ] Password reset flow
[ ] Google OAuth callback (schema-aware)
[ ] Profile edit view
```

---

## ⚙️ PHASE 5 — THEME ENGINE (XML-BASED)

> Themes are defined in XML. Agent reads XML → applies CSS vars. Clean, portable, editable without Python.

### TODO-5.1 — XML Theme Spec

```xml
<!-- themes/dark_noir.xml -->
<theme id="dark_noir" name="Dark Noir" version="1.0">
  <meta>
    <author>UniMarket</author>
    <description>Sleek dark editorial for urban shops</description>
    <preview>themes/previews/dark_noir.png</preview>
  </meta>
  <colors>
    <primary>#1a1a2e</primary>
    <secondary>#16213e</secondary>
    <accent>#e94560</accent>
    <surface>#0f3460</surface>
    <text_primary>#eaeaea</text_primary>
    <text_secondary>#a8a8b3</text_secondary>
    <border>#2a2a4a</border>
    <success>#00b894</success>
    <danger>#e17055</danger>
  </colors>
  <typography>
    <heading_font>Bebas Neue</heading_font>
    <body_font>DM Sans</body_font>
    <mono_font>JetBrains Mono</mono_font>
    <base_size>16px</base_size>
    <scale_ratio>1.25</scale_ratio>
  </typography>
  <layout>
    <border_radius>8px</border_radius>
    <card_shadow>0 4px 24px rgba(0,0,0,0.4)</card_shadow>
    <navbar_height>64px</navbar_height>
    <sidebar_width>240px</sidebar_width>
  </layout>
  <effects>
    <glassmorphism>true</glassmorphism>
    <blur_amount>12px</blur_amount>
    <grain_overlay>true</grain_overlay>
  </effects>
</theme>
```

### TODO-5.2 — Built-in Themes (minimum 5)
```
[ ] dark_noir.xml       — dark editorial, red accents
[ ] campus_light.xml    — clean academic white/blue
[ ] sunset_market.xml   — warm orange/amber, marketplace energy
[ ] forest_minimal.xml  — earthy green, minimal borders
[ ] neon_pulse.xml      — cyberpunk neon on black
```

### TODO-5.3 — Theme Engine (Python)
```python
# apps/themes/engine.py
import xml.etree.ElementTree as ET

class ThemeEngine:
    THEMES_DIR = settings.BASE_DIR / "themes"
    
    @classmethod
    def load(cls, theme_id: str) -> dict:
        """Parse XML theme → dict of CSS vars"""
        path = cls.THEMES_DIR / f"{theme_id}.xml"
        tree = ET.parse(path)
        root = tree.getroot()
        return {
            "colors": {el.tag: el.text for el in root.find("colors")},
            "typography": {el.tag: el.text for el in root.find("typography")},
            "layout": {el.tag: el.text for el in root.find("layout")},
            "effects": {el.tag: el.text for el in root.find("effects")},
        }
    
    @classmethod
    def list_themes(cls) -> list[dict]:
        """Return all available themes with metadata"""
        ...
    
    @classmethod
    def to_css_vars(cls, theme_data: dict) -> str:
        """Convert theme dict → :root { --var: value; } CSS string"""
        ...
```

### TODO-5.4 — Theme Context Processor
```python
# apps/themes/context_processors.py
def theme(request):
    shop_config = getattr(request, "shop_config", None)
    theme_id = getattr(shop_config, "theme_id", "campus_light")
    return {"theme": ThemeEngine.load(theme_id)}
```

### TODO-5.5 — Theme Switcher UI
```
[ ] Theme preview grid (shows all available themes)
[ ] Live preview via CSS var injection (no page reload)
[ ] Confirm + save button → stores theme_id in ShopConfig
[ ] Theme switcher available in: shop seller dashboard, university console
```

### TODO-5.6 — Template Integration
```html
<!-- base.html -->
<style>
  :root {
    {% for key, val in theme.colors.items %}
    --color-{{ key }}: {{ val }};
    {% endfor %}
    {% for key, val in theme.typography.items %}
    --font-{{ key }}: {{ val }};
    {% endfor %}
  }
</style>
```

---

## ⚙️ PHASE 6 — SHOP CREATION FLOW

> Per diagram: ManageUniversityShops / ManageLocationShops → CreateShop → SetShopDomain → RegisterDomain → ConfigureTenant

### TODO-6.1 — Shop Creation Wizard (3 steps)
```
Step 1: Shop Identity
  - Shop name (auto-generates slug/subdomain suggestion)
  - Category (Books, Electronics, Food, Fashion, Services, Other)
  - Description

Step 2: Theme Selection
  - Theme picker (XML-driven, live preview)
  - Logo upload (optional)

Step 3: Domain + Confirm
  - Shows: shopname.baseurl.com
  - Validates uniqueness in public schema
  - On confirm: creates tenant schema, registers domain
```

### TODO-6.2 — Shop Creation Backend
```python
# apps/shops/services.py
class ShopCreationService:
    def create(self, name, owner, parent_tenant, theme_id) -> Client:
        """
        1. Generate unique schema_name
        2. Create Client (tenant) record
        3. Create Domain record
        4. Run migrate_schemas for new tenant
        5. Create ShopConfig with selected theme
        6. Create owner ShopUser in new schema
        7. Trigger: add_dev_host management command (dev only)
        8. Return tenant
        """
```

### TODO-6.3 — Dev Host Auto-Registration
```
[ ] After shop creation in DEBUG mode → call add_dev_host automatically
[ ] Display instructions: "Add to hosts file: 127.0.0.1 shopname.localhost"
[ ] In prod: trigger Cloudflare API to add DNS record
```

---

## ⚙️ PHASE 7 — UI UNIFICATION & REFACTOR

> Agent reads all existing templates → unifies under single design system.

### TODO-7.1 — Template Hierarchy
```
templates/
├── base.html                    ← master layout (loads theme vars)
├── public/
│   ├── home.html
│   ├── about.html
│   ├── blog/
│   ├── faq.html
│   └── contact.html
├── university/
│   ├── console.html
│   ├── shops.html
│   └── analytics.html
├── location/
│   ├── console.html
│   ├── shops.html
│   └── analytics.html
├── shop/
│   ├── storefront.html          ← buyer view
│   ├── dashboard.html           ← seller view
│   ├── listing_detail.html
│   └── edit_template.html
├── accounts/
│   ├── login.html
│   ├── register.html
│   └── verify_email.html
└── components/
    ├── navbar.html
    ├── sidebar.html
    ├── listing_card.html
    ├── shop_card.html
    ├── theme_switcher.html
    ├── notification_bell.html
    └── pagination.html
```

### TODO-7.2 — Component Library Rules
```
[ ] Every component accepts context vars — no hardcoded content
[ ] Every component has a CSS class prefix (e.g., um-card, um-nav)
[ ] All colors use CSS vars from theme engine (never hardcoded hex)
[ ] All spacing uses CSS custom properties
[ ] Mobile-first responsive (breakpoints: 640px, 768px, 1024px, 1280px)
[ ] Every interactive element has hover + focus states
[ ] Dark/light mode supported via theme XML (not system preference)
```

### TODO-7.3 — Static Asset Pipeline
```
[ ] Single main.css compiled from component partials
[ ] Single main.js (vanilla JS or lightweight Alpine.js)
[ ] No jQuery unless already deeply integrated
[ ] Lazy load images (loading="lazy" + IntersectionObserver for JS)
[ ] Compress all images on upload (Pillow)
```

---

## ⚙️ PHASE 8 — MARKETPLACE CORE

### TODO-8.1 — Listing Model
```python
class Listing(TimeStampedModel):
    title = models.CharField(max_length=200, db_index=True)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.ForeignKey("Category", on_delete=models.SET_NULL, null=True)
    seller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    images = models.ManyToManyField("ListingImage", blank=True)
    status = models.CharField(choices=ListingStatus.choices, default=ListingStatus.ACTIVE)
    views = models.PositiveIntegerField(default=0)
    is_featured = models.BooleanField(default=False)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["category", "status"]),
            models.Index(fields=["seller", "status"]),
        ]
```

### TODO-8.2 — Search & Filter
```
[ ] Full-text search via PostgreSQL (SearchVector + SearchQuery)
[ ] Filter by: category, price range, condition, date posted
[ ] Sort by: newest, price asc/desc, most viewed
[ ] Search is tenant-scoped (only searches current shop's listings)
[ ] University console: search across all shops in university
```

### TODO-8.3 — Listing CRUD
```
[ ] Create listing (sellers only, verified users)
[ ] Edit listing (owner only)
[ ] Delete listing (owner + admin)
[ ] Mark as sold
[ ] Renew listing (resets expires_at, may charge fee)
[ ] Report listing (buyer → admin review queue)
```

---

## ⚙️ PHASE 9 — MESSAGING (WebSocket)

### TODO-9.1 — Stack
```
Django Channels + Redis channel layer
ASGI server: Daphne or Uvicorn
```

### TODO-9.2 — Conversation Model
```python
class Conversation(TimeStampedModel):
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE)
    buyer = models.ForeignKey(User, related_name="buyer_convos")
    seller = models.ForeignKey(User, related_name="seller_convos")
    is_active = models.BooleanField(default=True)

class Message(TimeStampedModel):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE)
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    body = models.TextField(max_length=2000)
    is_read = models.BooleanField(default=False)
    attachment = models.FileField(upload_to="messages/", blank=True)
```

### TODO-9.3 — WebSocket Consumer
```
[ ] ChatConsumer: handles send/receive, marks read
[ ] Auth middleware for WS connections (session-based)
[ ] Typing indicator event
[ ] Unread count badge (real-time via WS)
[ ] Message notification push to seller when buyer initiates
```

---

## ⚙️ PHASE 10 — PAYMENTS (M-PESA)

### TODO-10.1 — Billable Actions
| Action | Fee |
|--------|-----|
| Post a listing | KES 50 |
| Feature a listing | KES 100/week |
| Create a shop (one-time) | KES 500 |
| Premium shop template | KES 200 |

### TODO-10.2 — M-Pesa STK Push Flow
```
[ ] Trigger STK push (Daraja API)
[ ] Callback URL receives confirmation
[ ] On success: activate listing/shop/feature
[ ] On failure: notify user, log error
[ ] Transaction model with status (PENDING, SUCCESS, FAILED, REFUNDED)
[ ] Receipt number storage
```

### TODO-10.3 — Transaction Model
```python
class Transaction(TimeStampedModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    action = models.CharField(choices=BillableAction.choices)
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    phone_number = models.CharField(max_length=15)
    mpesa_receipt = models.CharField(max_length=50, blank=True)
    status = models.CharField(choices=TransactionStatus.choices, default="PENDING")
    reference = models.UUIDField(default=uuid.uuid4, unique=True)
    metadata = models.JSONField(default=dict)
```

---

## ⚙️ PHASE 11 — ADMIN PANELS

### University Admin (per diagram: `AuditAllUniversityShops`)
```
[ ] View all shops under university
[ ] Suspend / reinstate shops
[ ] View analytics across all shops
[ ] Manage university-wide categories
[ ] Export reports (CSV)
```

### Location Manager (per diagram: `ModerateLocationShops`)
```
[ ] View all shops in location
[ ] Moderate listings (approve/reject)
[ ] View location-wide analytics
[ ] Manage featured listings
```

### Shop Admin Dashboard
```
[ ] My listings (filter by status)
[ ] Sales analytics (views, inquiries, sold)
[ ] Messages inbox
[ ] Payment history
[ ] Shop appearance (theme switcher)
[ ] Shop settings (bio, logo, hours)
```

### Django Superadmin Enhancements
```
[ ] Custom admin theme (django-unfold or jazzmin)
[ ] Tenant overview (all schemas)
[ ] Global transaction dashboard
[ ] User management across schemas
```

---

## ⚙️ PHASE 12 — AI AGENT FEATURES

> Creative differentiators. Build after core is stable.

### TODO-12.1 — Listing Enhancement Agent
```
[ ] Seller uploads photo + enters title
[ ] AI generates: description, suggested price, category guess
[ ] Seller reviews and accepts/edits
[ ] Uses Claude API (claude-sonnet-4-20250514)
```

### TODO-12.2 — UI Unification Agent (internal)
```
[ ] Reads all templates
[ ] Identifies CSS inconsistencies
[ ] Suggests/applies unified class names
[ ] Generates AUDIT.md report of changes
```

### TODO-12.3 — Smart Search
```
[ ] Natural language search ("cheap laptop for programming under 10k")
[ ] Parsed → structured filters via AI
[ ] Falls back to standard search if AI unavailable
```

---

## ⚙️ PHASE 13 — TESTING SUITE

> Tests are not optional. Every phase ships with tests.

### Test Types Required

| Type | Tool | When |
|------|------|------|
| Unit | pytest + pytest-django | Every model, service, util |
| Integration | pytest + APIClient | Every view/endpoint |
| Tenant isolation | Custom fixtures | Every cross-schema operation |
| WebSocket | pytest-asyncio + channels | Chat consumer |
| Payment | Mock + Daraja sandbox | M-Pesa flows |
| Theme engine | Unit | XML parse + CSS output |
| UI | Playwright or Selenium | Critical user flows |

### TODO-13.1 — Test Infrastructure
```
[ ] Install: pytest pytest-django pytest-asyncio factory-boy faker
[ ] conftest.py: tenant fixtures (create_tenant, create_domain, switch_schema)
[ ] Factory classes for all models (UserFactory, ListingFactory, ShopFactory)
[ ] Separate test DB schema per test run
[ ] CI-ready: pytest.ini configured, all tests runnable via `pytest`
```

### TODO-13.2 — Tenant Isolation Tests (CRITICAL)
```python
# tests/test_tenant_isolation.py

def test_listing_not_visible_cross_tenant(university_tenant, shop_a, shop_b):
    """Listings in shop_a schema must NOT be accessible from shop_b"""
    with schema_context(shop_a.schema_name):
        listing = ListingFactory()
    
    with schema_context(shop_b.schema_name):
        assert Listing.objects.filter(id=listing.id).count() == 0

def test_user_cannot_login_cross_schema(shop_a_user, shop_b):
    """User from shop_a must not authenticate in shop_b"""
    ...
```

### TODO-13.3 — Theme Engine Tests
```python
def test_xml_theme_parses_correctly():
    theme = ThemeEngine.load("dark_noir")
    assert theme["colors"]["primary"] == "#1a1a2e"
    assert "heading_font" in theme["typography"]

def test_css_vars_output_is_valid():
    css = ThemeEngine.to_css_vars(ThemeEngine.load("dark_noir"))
    assert "--color-primary" in css
    assert "--font-heading_font" in css

def test_missing_theme_raises_not_found():
    with pytest.raises(ThemeNotFoundError):
        ThemeEngine.load("nonexistent_theme")
```

### TODO-13.4 — Coverage Target
```
[ ] Minimum 80% coverage across all apps
[ ] 100% coverage on: auth flows, payment flows, tenant creation, theme engine
[ ] Coverage report: `pytest --cov=apps --cov-report=html`
```

---

## 🖥️ LOCAL DEV SETUP (Windows)

```bash
# 1. Clone + virtualenv
python -m venv venv
venv\Scripts\activate

# 2. Install deps
pip install -r requirements.txt

# 3. Copy env
copy .env.example .env
# Edit .env with your local values (DB_HOST=localhost, DB_PASSWORD=admin etc.)

# 4. Run as Administrator: setup hosts
powershell -ExecutionPolicy Bypass -File scripts/setup_hosts.ps1

# 5. Create DB
psql -U postgres -c "CREATE DATABASE unimarket;"

# 6. Migrate public schema
python manage.py migrate_schemas --shared

# 7. Create public tenant
python manage.py shell
>>> from apps.tenants.models import Client, Domain
>>> public = Client(schema_name='public', name='UniMarket Public')
>>> public.save()
>>> Domain(domain='localhost', tenant=public, is_primary=True).save()

# 8. Run
python manage.py runserver

# Access:
# http://localhost          → public homepage
# http://university.localhost → university console
# http://testshop.localhost   → test shop
```

### WSGI Config
```python
# config/wsgi.py
import os
from django.core.wsgi import get_wsgi_application
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
application = get_wsgi_application()
```

---

## 📁 PROJECT STRUCTURE (TARGET)

```
project/
├── config/
│   ├── settings/
│   │   ├── base.py
│   │   ├── dev.py
│   │   └── prod.py
│   ├── urls.py              ← public schema URLs
│   ├── tenant_urls.py       ← tenant schema URLs
│   └── wsgi.py
├── apps/
│   ├── core/               ← shared mixins, utils, base models
│   ├── tenants/            ← Client, Domain, TenantConfig models
│   ├── accounts/           ← User, auth, roles, permissions
│   ├── public/             ← homepage, blog, FAQ, contact
│   ├── university/         ← university console + analytics
│   ├── location/           ← location console + analytics
│   ├── shops/              ← shop creation, storefront, dashboard
│   ├── listings/           ← Listing, Category, ListingImage
│   ├── messaging/          ← Conversation, Message, WS consumer
│   ├── payments/           ← Transaction, M-Pesa integration
│   ├── themes/             ← ThemeEngine, XML themes
│   └── ai/                 ← AI-powered features
├── themes/                 ← XML theme files
│   ├── dark_noir.xml
│   ├── campus_light.xml
│   └── ...
├── templates/              ← all HTML templates
├── static/                 ← CSS, JS, images
├── scripts/
│   ├── setup_hosts.ps1
│   └── create_tenant.py
├── tests/
│   ├── conftest.py
│   ├── test_tenants.py
│   ├── test_themes.py
│   ├── test_listings.py
│   ├── test_auth.py
│   ├── test_payments.py
│   └── test_messaging.py
├── .env
├── .env.example
├── requirements.txt
├── pytest.ini
├── AGENT.md                ← this file
└── PROGRESS.md             ← agent updates here after each phase
```

---

## 🚫 AGENT CONSTRAINTS

```
❌ Do NOT create new apps outside the defined structure
❌ Do NOT use hardcoded DB credentials anywhere
❌ Do NOT skip tests for any phase
❌ Do NOT use jQuery (unless pre-existing and deeply coupled)
❌ Do NOT create tenant URLs in the public urlconf
❌ Do NOT modify .env (only .env.example)
❌ Do NOT use raw SQL unless django-tenants requires it
❌ Do NOT add external services not in this plan
```

---

## ✅ AGENT EXECUTION ORDER

```
Phase 0 (Audit) → Phase 1 (Env) → Phase 2 (Routing) → Phase 3 (Models)
→ Phase 4 (Auth) → Phase 5 (Themes) → Phase 6 (Shop Creation)
→ Phase 7 (UI Unification) → Phase 8 (Marketplace) → Phase 9 (Chat)
→ Phase 10 (Payments) → Phase 11 (Admin) → Phase 12 (AI)
→ Phase 13 runs continuously alongside every phase
```

**After each phase:** Update `PROGRESS.md` with completed TODOs, blockers, and next steps.
