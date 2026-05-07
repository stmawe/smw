# Platform TODO — SMW (UniMarket)
# Created: 2026-05-07
# Ordered: simplest → hardest
# Status legend: [ ] not started  [-] in progress  [x] done

---

## TIER 1 — Simple (1-2 files, no new models)

### T1-1 — Login redirects to dashboard, not subdomain root
**Files:** `accounts/views.py`
**What:** After login, redirect to `https://{username}.smw.pgwiz.cloud/dashboard/`
instead of the subdomain root. Dashboard requires login; root is public.
- [ ] Change login redirect URL from `/{username}/` to `/{username}/dashboard/`
- [ ] Add `?next=` support so @login_required redirects work correctly

### T1-2 — Navbar dropdown: add Dashboard link
**Files:** `templates/components/navbar.html`
**What:** When logged in, the user dropdown should have:
- My Dashboard → `https://{username}.smw.pgwiz.cloud/dashboard/`
- My Shops → `https://{username}.smw.pgwiz.cloud/`
- Create Shop → `/create-shop/`
- Admin Panel (staff only) → `https://admin.smw.pgwiz.cloud/dashboard/`
- Sign Out
- [ ] Update navbar dropdown links to use correct URLs

### T1-3 — Wizard: pre-fill slug with username, lock subdomain display
**Files:** `templates/wizard/create_shop.html`, `static/js/wizard.js`
**What:** Step 1 of wizard:
- Slug field pre-filled with `{{ request.user.username }}`
- Show: "Your shop will be at: `{username}.smw.pgwiz.cloud/{slug}/`"
- Subdomain part is read-only display — user only edits the path segment
- [ ] Pass `user_username` to wizard context in `create_shop_view`
- [ ] Update Step 1 template to show subdomain + editable path
- [ ] Update wizard.js slug preview to show full URL format

### T1-4 — Wizard: Tier 1 blocks second shop creation
**Files:** `app/views.py → create_shop_view`
**What:** If user has a root-promoted shop (`is_root_shop=True`), block creating
a second shop with a clear message: "Upgrade required to create multiple shops."
- [ ] Check `Shop.objects.filter(owner=user, is_root_shop=True).exists()` before allowing wizard
- [ ] Show upgrade CTA instead of wizard if blocked

### T1-5 — Registration "setting up" page
**Files:** `accounts/views.py`, `accounts/templates/accounts/register.html`
**What:** After successful registration, instead of redirecting to login immediately,
show a "Setting up your account..." page that:
- Displays username and subdomain being created
- Shows progress steps (DNS, SSL, account ready)
- Auto-redirects to login after 5 seconds
- [ ] Create `templates/accounts/setup_pending.html`
- [ ] Return this template from `register_view` after user creation
- [ ] JS countdown + auto-redirect

---

## TIER 2 — Medium (new views, existing models)

### T2-1 — `{username}.smw.pgwiz.cloud/dashboard/` — seller dashboard
**Files:** `mydak/shop_routing_views.py`, `config/tenant_urls.py`, `templates/shops/dashboard.html`
**What:** Private seller dashboard at `/dashboard/` on the user's subdomain.
- Login required (redirect to login if not authenticated)
- Shows: user's shops list, total listings, recent orders, messages count, payment history
- Links to: create shop, manage listings, view public profile
- [ ] Add `seller_dashboard_view` to `mydak/shop_routing_views.py`
- [ ] Add `path('dashboard/', seller_dashboard_view)` to `config/tenant_urls.py`
- [ ] Create `templates/shops/dashboard.html`

### T2-2 — `{username}.smw.pgwiz.cloud/` — public profile / shop display
**Files:** `mydak/shop_routing_views.py`, `templates/shops/user_profile.html`
**What:** Public page — no login required.
- If user has `is_root_shop=True` shop → show that shop's storefront
- Otherwise → show user's profile with all their active shops listed
- [ ] `tenant_root_view` already exists — verify it works correctly
- [ ] Create/update `templates/shops/user_profile.html` with shop cards
- [ ] Create `templates/shops/storefront.html` for individual shop display

### T2-3 — Wizard: upgrade request section (post-creation)
**Files:** `templates/wizard/create_shop.html`, `app/slug_request_service.py`
**What:** After shop is created (payment confirmed), show upgrade options:
- "Request root promotion" (Tier 1) — make this shop serve at `/`
- "Request custom slug" (Tier 2) — change path to something cleaner
- Both submit a `ShopSlugRequest` — non-blocking, shop already live
- [ ] Add upgrade section to wizard Step 6 post-payment state
- [ ] Wire to `SlugRequestService.submit_root_promotion()` and `submit_custom_slug()`
- [ ] Show pending request status if one already exists

### T2-4 — `ALLOWED_HOSTS` wildcard for user subdomains
**Files:** `config/settings/prod.py`
**What:** `bwarex.smw.pgwiz.cloud` returns 400 Bad Request if not in ALLOWED_HOSTS.
Need `*.smw.pgwiz.cloud` in ALLOWED_HOSTS on prod.
- [ ] Check current prod ALLOWED_HOSTS
- [ ] Add `.smw.pgwiz.cloud` (with leading dot — Django wildcard format)
- [ ] Restart Passenger after change

### T2-5 — `ClientDomain` + tenant schema per user on activation
**Files:** `app/shop_creation_service.py → activate_shop_from_transaction`
**What:** When a shop is activated (payment confirmed), ensure the user's
`ClientDomain` record exists so django-tenants routes `{username}.smw.pgwiz.cloud`
to the correct schema. Currently this creates a Client per user — verify it works.
- [ ] Test that `bwarex.smw.pgwiz.cloud/` resolves to the correct tenant schema
- [ ] Fix any routing issues found

---

## TIER 3 — Hard (new models, complex wiring)

### T3-1 — `smw.pgwiz.cloud/` combined marketplace
**Files:** `app/views.py → homepage_view`, `templates/homepage.html`
**What:** Public homepage shows all active listings from all users/shops.
- Query: `Listing.objects.filter(status='active')` across all tenant schemas
  (requires `django_tenants.utils.tenant_context` loop or a shared listing cache)
- Fallback: if no listings, show admin-owned demo shops
- [ ] Research cross-tenant listing query approach
- [ ] Implement listing aggregation (either cross-schema query or denormalized public table)
- [ ] Update `homepage.html` with listing grid

### T3-2 — `smw.pgwiz.cloud/shop/{username}/` — user's public profile on main site
**Files:** `app/views.py`, `app/urls.py`, `templates/shop_detail.html`
**What:** `smw.pgwiz.cloud/shop/bwarex/` shows bwarex's shops and listings
on the main public site (for users who don't know the subdomain).
- [ ] Add `shop_profile_view(request, username)` to `app/views.py`
- [ ] Add URL pattern to `app/urls.py`
- [ ] Template showing user's shops + recent listings

### T3-3 — Tier system enforcement in wizard
**Files:** `app/views.py`, `mydak/models.py`, `templates/wizard/create_shop.html`
**What:** Full tier enforcement:
- Tier 0 (default): user sets path freely, max 2 shops
- Tier 1 (root): only 1 shop allowed, serves at `/`, requires approved `ShopSlugRequest`
- Tier 2 (custom slug): path changed after admin approval
- [ ] Add `user_tier` property to User or derive from ShopSlugRequest history
- [ ] Enforce shop count limits based on tier
- [ ] Show tier badge in dashboard

### T3-4 — Admin panel: domain management view
**Files:** `app/admin_console_views.py`, `templates/admin/console_domains.html`
**What:** `admin.smw.pgwiz.cloud/console/domains/` shows all registered user
subdomains with SSL status, DNS status, and ability to trigger `devil ssl www add`
for any domain.
- [ ] Query all `ClientDomain` records
- [ ] Show SSL cert status (from `devil ssl www list` output)
- [ ] Add "Issue SSL" button per domain
- [ ] Wire to `SSLCertificateManager.generate_certificate_for_domain()`

---

## CURRENT BLOCKERS (fix before anything else)

- [ ] **ALLOWED_HOSTS** — `bwarex.smw.pgwiz.cloud` likely returns 400 until `.smw.pgwiz.cloud` is in ALLOWED_HOSTS on prod (T2-4)
- [ ] **Tenant routing** — verify `bwarex.smw.pgwiz.cloud/` actually resolves via django-tenants (T2-5)
- [ ] **b.ware user** — has dots in username, SSL cert issued but subdomain won't work with wildcard. Should be deactivated or renamed.

---

## NOTES
- Start with T1 tasks — all are 1-2 file changes, no migrations
- T2-4 (ALLOWED_HOSTS) is technically simple but critical — do it first
- T3-1 (cross-tenant listings) is the hardest — needs research before implementation
- deploy.py commands available: `backfill-dns`, `backfill-ssl`, `migrate-tenant`, `migrate-shared`
