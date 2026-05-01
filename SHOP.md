# 🏪 SHOP.md — Shop Creation Wizard Plan
> **Aesthetic:** Dark editorial luxury · blue/gold/green palette  
> **UX Pattern:** 6-step progressive wizard with live shop preview pane  
> **Stack:** Django + vanilla JS + CSS custom properties  
> **Template:** `templates/wizard/create_shop.html`

---

## 🧠 WIZARD PHILOSOPHY

> The wizard is not a form. It's a **studio experience**.  
> The user is building something — they should feel like a creator, not a data-entry clerk.

**Core UX principles:**
- Every step has ONE primary question — no cognitive overload
- Live preview pane updates in real-time as user fills fields
- Progress is always visible — user knows exactly where they are
- Validation is inline and friendly — never jarring
- Can go back to any previous step without losing data
- Step state is saved to `localStorage` — refreshing doesn't lose progress
- Final payment is the last gate — commitment comes last, delight comes first

---

## 🗂️ WIZARD STEPS OVERVIEW

```
Step 1: Identity        → Name, tagline, category
Step 2: Affiliation     → University or location link
Step 3: Design          → Theme selection + color accent
Step 4: Branding        → Logo upload + banner upload
Step 5: Details         → Description, contact, social links
Step 6: Launch          → Review + M-Pesa payment
```

**Right pane:** Live shop preview — updates as each step is filled  
**Progress:** Top stepper bar (6 circles, connecting lines, labels)

---

## 📐 LAYOUT STRUCTURE

```
┌──────────────────────────────────────────────────────────────────────┐
│  NAVBAR                                                              │
├─────────────────────────────────────────────────────────────────────-┤
│  [Step Progress Bar — full width, always visible]                    │
│  ①──────②──────③──────④──────⑤──────⑥                              │
│  Identity Affiliate Design  Brand  Details Launch                    │
├──────────────────────────────┬───────────────────────────────────────┤
│                              │                                       │
│   LEFT PANE (form area)      │   RIGHT PANE (live preview)          │
│   min-width: 420px           │   sticky, scrolls with page          │
│   flex: 0 0 45%              │   flex: 1                            │
│                              │                                       │
│   [Step Content renders here]│   [Mini shop preview renders here]   │
│                              │                                       │
│   [← Back]     [Next →]      │                                       │
│                              │                                       │
└──────────────────────────────┴───────────────────────────────────────┘
```

**Mobile:** Preview pane collapses to a collapsible "Preview" button at top-right. Tapping it slides a full-screen preview in from bottom.

---

## 🎨 STEP 1 — IDENTITY

### What it asks:
- Shop name (required, 3–48 chars)
- Tagline / short description (optional, max 80 chars)
- Primary category (required, single select)

### UI Spec:

```
┌─────────────────────────────────────────────┐
│                                             │
│   What's your shop called?                  │
│                                             │
│   ┌─────────────────────────────────────┐   │
│   │  e.g. Juju's Electronics            │   │  ← large input, 52px height
│   └─────────────────────────────────────┘   │
│   Your shop URL will be:                    │
│   ✦ juju-electronics.unimarket.ke           │  ← live slug preview, gold
│     [Available ✓]  or  [Taken ✗]           │  ← async availability check
│                                             │
│   Tagline (optional)                        │
│   ┌─────────────────────────────────────┐   │
│   │  e.g. Quality tech, student prices  │   │  ← smaller input, 44px
│   └─────────────────────────────────────┘   │
│   45 characters remaining                   │  ← live counter
│                                             │
│   What will you be selling?                 │
│                                             │
│   ┌──────────┐ ┌──────────┐ ┌──────────┐   │
│   │ 💻       │ │ 📚       │ │ 👗       │   │
│   │Electronics│ │  Books   │ │ Fashion  │   │
│   └──────────┘ └──────────┘ └──────────┘   │
│   ┌──────────┐ ┌──────────┐ ┌──────────┐   │
│   │ 🍱       │ │ 🛠️       │ │ ✦        │   │
│   │   Food   │ │ Services │ │  Other   │   │
│   └──────────┘ └──────────┘ └──────────┘   │
│                                             │
└─────────────────────────────────────────────┘
```

### Validation:
- Name: min 3 chars, no special characters except hyphens/apostrophes
- Slug uniqueness: debounced AJAX to `/api/check-slug/?slug=juju-electronics`
- Response: `{ available: true }` → show green tick, `available: false` → red X + suggestion
- Category: required before Next is enabled

### Preview pane updates:
- Shop name appears as storefront header
- URL shows in address bar mockup
- Category badge appears on the preview card

---

## 🏫 STEP 2 — AFFILIATION

### What it asks:
- Are you affiliated with a university or location? (toggle)
- Select university OR location from dropdown
- Optional: student/staff verification (email)

### UI Spec:

```
┌─────────────────────────────────────────────┐
│                                             │
│   Is your shop tied to a place?             │
│                                             │
│   ┌────────────────────┐  ┌──────────────┐  │
│   │ 🎓 University       │  │ 📍 Location  │  │  ← toggle cards
│   │  (student shops)   │  │  (community) │  │
│   └────────────────────┘  └──────────────┘  │
│                      [Skip this step →]      │
│                                             │
│   Select your university:                   │
│   ┌─────────────────────────────────────┐   │
│   │  🔍 Search universities…     ▾      │   │  ← searchable dropdown
│   └─────────────────────────────────────┘   │
│                                             │
│   ┌──────────────────────────────────────┐  │
│   │  🎓 University of Nairobi            │  │  ← suggestion chips
│   │  🎓 Kenyatta University              │  │
│   │  🎓 Strathmore University            │  │
│   └──────────────────────────────────────┘  │
│                                             │
│   Verify with student email (optional)      │
│   ┌─────────────────────────────────────┐   │
│   │  yourname@students.uon.ac.ke        │   │
│   └─────────────────────────────────────┘   │
│   Verification earns a ✓ badge on your shop │
│                                             │
└─────────────────────────────────────────────┘
```

### Logic:
- Selecting university → dropdown populates from `Client.objects.filter(tenant_type='UNIVERSITY')`
- Selecting location → dropdown populates from `Client.objects.filter(tenant_type='LOCATION')`
- Email verify: sends OTP to `.ac.ke` or `.edu` domain → "Verified Student" badge on shop
- Skip: shop created as independent, no parent tenant link

### Preview pane updates:
- University badge appears below shop name
- "Verified ✓" ribbon appears if email verified

---

## 🎨 STEP 3 — DESIGN (Theme)

### What it asks:
- Choose a theme (5 options, full-size previews)
- Choose an accent color override (optional, 6 presets)

### UI Spec:

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│   Choose your shop's look                                   │
│                                                             │
│   ┌─────────────────────┐   ┌─────────────────────┐        │
│   │  [Dark Noir]        │   │  [Campus Light]     │        │
│   │  ─────────────────  │   │  ─────────────────  │        │
│   │  ██ ██ ██ ██ cards  │   │  □□ □□ □□ □□ cards │        │  ← mini mockups
│   │  navy bg, gold text │   │  white bg, blue     │        │
│   │  ✓ SELECTED         │   │                     │        │
│   └─────────────────────┘   └─────────────────────┘        │
│                                                             │
│   ┌─────────────────────┐   ┌─────────────────────┐        │
│   │  [Sunset Market]    │   │  [Forest Minimal]   │        │
│   │  ─────────────────  │   │  ─────────────────  │        │
│   │  warm amber tones   │   │  earthy deep green  │        │
│   │                     │   │                     │        │
│   └─────────────────────┘   └─────────────────────┘        │
│                                                             │
│   ┌─────────────────────┐                                   │
│   │  [Neon Pulse]       │                                   │
│   │  cyan on black      │                                   │
│   └─────────────────────┘                                   │
│                                                             │
│   Accent color                                              │
│   ● Electric Blue  ○ Champagne Gold  ○ Emerald              │
│   ○ Coral Red      ○ Violet          ○ Slate                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Theme Cards (each 240px × 160px):

**Dark Noir:**
- Background chip: `#120F1E`
- Accent chip: `#E8B030`
- Mini card preview: dark glassmorphism cards
- Mood tag: "Sleek · Professional"

**Campus Light:**
- Background chip: `#F8FAFF`
- Accent chip: `#1A72E8`
- Mini card preview: clean white cards, blue accents
- Mood tag: "Fresh · Academic"

**Sunset Market:**
- Background chip: `#1A0E05`
- Accent chip: `#E8721A`
- Mini card preview: warm amber glow cards
- Mood tag: "Warm · Vibrant"

**Forest Minimal:**
- Background chip: `#061208`
- Accent chip: `#26B857`
- Mini card preview: deep green cards, gold text
- Mood tag: "Earthy · Calm"

**Neon Pulse:**
- Background chip: `#020810`
- Accent chip: `#00F5CC`
- Mini card preview: cyan-on-black, glowing borders
- Mood tag: "Bold · Electric"

### Selection behavior:
- Click card → gold ring border `2px solid var(--gold-500)` + inner checkmark badge
- Accent color pills update the preview pane in real-time via CSS var injection
- Selected theme + accent stored in wizard state

### Preview pane updates:
- Entire preview re-themes — background, card colors, typography change instantly
- No page reload — pure CSS var swap via JS

---

## 🖼️ STEP 4 — BRANDING

### What it asks:
- Upload shop logo (optional, recommended)
- Upload banner image (optional)
- OR choose a generated banner

### UI Spec:

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│   Add your shop's identity                                  │
│                                                             │
│   Logo                                                      │
│   ┌───────────────────────────────────────────────────┐    │
│   │                                                   │    │
│   │         ┌──────────┐                              │    │
│   │         │    ◉     │  ← 96px circle preview       │    │
│   │         │   Logo   │                              │    │
│   │         └──────────┘                              │    │
│   │                                                   │    │
│   │   [ Upload Logo ]   or   [ Use initials ]         │    │
│   │   PNG, JPG, SVG · Max 2MB · Square preferred      │    │
│   │                                                   │    │
│   └───────────────────────────────────────────────────┘    │
│                                                             │
│   Banner Image                                              │
│   ┌───────────────────────────────────────────────────┐    │
│   │  ─────────────────────────────────────────────── │    │
│   │  [                                             ] │    │  ← 16:5 banner
│   │  [ Drop image here or click to upload          ] │    │
│   │  [                                             ] │    │
│   │  ─────────────────────────────────────────────── │    │
│   │                                                   │    │
│   │  OR pick a generated banner:                      │    │
│   │  ┌───────┐  ┌───────┐  ┌───────┐  ┌───────┐     │    │
│   │  │ Navy  │  │ Gold  │  │ Green │  │Mosaic │     │    │  ← gradient presets
│   │  │Gradient│  │ Glow  │  │ Forest│  │       │     │    │
│   │  └───────┘  └───────┘  └───────┘  └───────┘     │    │
│   └───────────────────────────────────────────────────┘    │
│                                                             │
│   Logo initials style (if no logo uploaded)                 │
│   ┌───────────┐  ┌───────────┐  ┌───────────┐             │
│   │ [JE]      │  │ ❰JE❱      │  │  J·E      │             │  ← 3 initials styles
│   │ Bold pill │  │ Bordered  │  │ Minimal   │             │
│   └───────────┘  └───────────┘  └───────────┘             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Logic:
- Logo upload: `FileReader` API → display preview circle immediately
- Banner upload: `FileReader` → display in banner slot immediately
- Initials auto-generated from shop name (first letter of each word, max 2)
- Generated banners: CSS gradient definitions, no external image needed
- Image validation: check file type (accept=".jpg,.jpeg,.png,.svg,.webp") + size < 2MB client-side
- Actual upload: multipart form, saved to `MEDIA_ROOT/shops/logos/` and `shops/banners/`
- Pillow resizing: logo → 300×300px max, banner → 1200×400px max

### Generated banner presets (CSS gradients):

```css
.banner-navy-gradient { background: linear-gradient(135deg, #020A1A 0%, #0D3366 60%, #1050A0 100%); }
.banner-gold-glow     { background: linear-gradient(135deg, #1A1000 0%, #3D2800 50%, #9B6400 100%); }
.banner-green-forest  { background: linear-gradient(135deg, #011208 0%, #064A20 60%, #0F9640 100%); }
.banner-mosaic        { background: conic-gradient(from 45deg, #020A1A, #0D3366, #C9920A, #0A6B2D, #020A1A); }
```

### Preview pane updates:
- Logo circle updates live
- Banner updates live
- Initials style reflects immediately

---

## 📝 STEP 5 — DETAILS

### What it asks:
- Full description (rich-ish textarea, markdown-lite)
- WhatsApp number (for buyer contact)
- Location / campus area (freetext)
- Social links (Instagram, Twitter/X, TikTok — optional)
- Operating hours (optional, day toggles + time pickers)

### UI Spec:

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│   Tell buyers about your shop                               │
│                                                             │
│   Description                                               │
│   ┌───────────────────────────────────────────────────┐    │
│   │  Tell buyers what you sell, how you operate,      │    │
│   │  and why they should choose you. Be specific!     │    │
│   │                                                   │    │
│   │                                                   │    │
│   └───────────────────────────────────────────────────┘    │
│   [B] [I] [•] quick formatting toolbar                      │
│   240 / 500 characters                                      │
│                                                             │
│   Contact WhatsApp                                          │
│   ┌─────┐  ┌────────────────────────────────────────┐      │
│   │ +254│  │  712 345 678                           │      │
│   └─────┘  └────────────────────────────────────────┘      │
│                                                             │
│   Campus / Area                                             │
│   ┌───────────────────────────────────────────────────┐    │
│   │  e.g. UoN Main Campus, Gate C                     │    │
│   └───────────────────────────────────────────────────┘    │
│                                                             │
│   Social links (optional)                                   │
│   Instagram: instagram.com/ [username            ]          │
│   TikTok:    tiktok.com/@   [username            ]          │
│   X/Twitter: x.com/         [username            ]          │
│                                                             │
│   Operating hours (optional)                                │
│   Mon ● [08:00] – [18:00]                                   │
│   Tue ● [08:00] – [18:00]                                   │
│   Wed ● [08:00] – [18:00]                                   │
│   Thu ● [08:00] – [18:00]                                   │
│   Fri ● [08:00] – [17:00]                                   │
│   Sat ○ [closed]                                            │
│   Sun ○ [closed]                                            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Logic:
- Description: textarea with char counter, simple formatting toolbar (bold/italic/list via `execCommand` or manual `**wrapping**`)
- WhatsApp: country code prefix selector, validates Kenyan format `07XX` or `+2547XX`
- Social links: prefix locked (e.g. `instagram.com/`) → user types only handle
- Hours: Mon–Sun toggles. Active day → time pickers appear (HTML `<input type="time">`)
- All optional except description (min 20 chars) and WhatsApp

### Preview pane updates:
- "About" section of shop preview fills with description
- WhatsApp button appears on preview
- Hours show on preview sidebar
- Social icons appear if links provided

---

## 🚀 STEP 6 — LAUNCH (Review + Payment)

### What it asks:
- Review all info (read-only summary)
- Pay setup fee (KES 500) via M-Pesa STK Push

### UI Spec:

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│   ✦  Review your shop                                       │
│                                                             │
│   ┌───────────────────────────────────────────────────┐    │
│   │  Shop name:     Juju's Electronics          [Edit]│    │
│   │  URL:           juju-electronics.unimarket.ke     │    │
│   │  Category:      Electronics                 [Edit]│    │
│   │  Affiliation:   University of Nairobi       [Edit]│    │
│   │  Theme:         Dark Noir                   [Edit]│    │
│   │  Description:   "Quality tech at student…" [Edit]│    │
│   │  WhatsApp:      +254 712 345 678            [Edit]│    │
│   └───────────────────────────────────────────────────┘    │
│                                                             │
│   ┌───────────────────────────────────────────────────┐    │
│   │                                                   │    │
│   │   Setup fee                          KES 500      │    │
│   │   ─────────────────────────────────────────────  │    │
│   │   Includes:                                       │    │
│   │   ✓ Permanent shop URL                            │    │
│   │   ✓ Unlimited listings (KES 50 each)              │    │
│   │   ✓ University/location affiliation badge         │    │
│   │   ✓ Custom theme & branding                       │    │
│   │   ✓ Seller dashboard & analytics                  │    │
│   │                                                   │    │
│   │   Pay via M-Pesa                                  │    │
│   │   ┌───────────────────────────────────────────┐   │    │
│   │   │  📱  07XX XXX XXX                         │   │    │
│   │   └───────────────────────────────────────────┘   │    │
│   │                                                   │    │
│   │   [ 🚀 Launch My Shop — Pay KES 500 ]             │    │  ← gold gradient button
│   │                                                   │    │
│   │   A payment prompt will be sent to your phone.    │    │
│   │   Enter your M-Pesa PIN to complete.              │    │
│   │                                                   │    │
│   └───────────────────────────────────────────────────┘    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Payment Flow States:

**State 1: Idle** — "Launch My Shop — Pay KES 500" button

**State 2: Sending** (after click)
```
  [ ⏳ Sending payment prompt to 07XX XXX XXX… ]
  Please check your phone and enter your M-Pesa PIN
```

**State 3: Waiting** (STK sent, polling)
```
  ┌──────────────────────────────────────────┐
  │   📱 Check your phone                    │
  │                                          │
  │   We sent a payment request to           │
  │   +254 712 345 678                       │
  │                                          │
  │   Enter your M-Pesa PIN to complete      │
  │                                          │
  │   ████████████░░░░  Waiting…             │  ← animated progress bar
  │                                          │
  │   [ Use a different number ]             │
  └──────────────────────────────────────────┘
```

**State 4a: Success** 🎉
```
  ┌──────────────────────────────────────────┐
  │   ✓  Payment confirmed!                  │
  │   Receipt: QJH7834K                      │
  │                                          │
  │   Your shop is being created…            │
  │   ████████████████████ 100%              │
  │                                          │
  │   Redirecting to your new shop in 3s…   │
  └──────────────────────────────────────────┘
```

**State 4b: Failure**
```
  ┌──────────────────────────────────────────┐
  │   ✗  Payment failed or timed out         │
  │   (wrong PIN / insufficient funds)       │
  │                                          │
  │   [ Try Again ]   [ Change Number ]      │
  └──────────────────────────────────────────┘
```

### Backend on success:
1. `ShopCreationService.create(...)` → creates tenant schema
2. `migrate_schemas --schema=shopname` runs
3. `ShopConfig` created with selected theme + branding
4. Owner `ShopUser` created in new schema
5. `Transaction` recorded with M-Pesa receipt
6. Redirect to `http://shopname.baseurl.com/dashboard/` (or show "Add to hosts" in dev)

---

## 🖥️ LIVE PREVIEW PANE SPEC

The right pane is a **miniaturized shop storefront mockup** that updates in real-time.

### Preview anatomy:
```
┌──────────────────────────────────────┐
│  [Banner Image / Gradient]           │  ← 100% width, 90px tall
│              [◉ Logo] Shop Name      │  ← overlay on banner
│              Category · University   │
├──────────────────────────────────────┤
│  [theme-colored background begins]   │
│                                      │
│  ┌──────────┐  ┌──────────┐         │
│  │ Listing  │  │ Listing  │         │  ← placeholder cards
│  │  Card    │  │  Card    │         │
│  └──────────┘  └──────────┘         │
│                                      │
│  ┌──────────┐  ┌──────────┐         │
│  │ Listing  │  │ Listing  │         │
│  │  Card    │  │  Card    │         │
│  └──────────┘  └──────────┘         │
│                                      │
│  About: [description preview…]       │
│  📱 WhatsApp · 📍 Location           │
│                                      │
└──────────────────────────────────────┘
│  juju-electronics.unimarket.ke       │  ← URL shown below preview
└──────────────────────────────────────┘
```

### Real-time update triggers:

| Step | What triggers | What updates in preview |
|------|---------------|------------------------|
| 1 | Name typed | Shop name header, URL bar |
| 1 | Category selected | Category badge |
| 2 | University selected | Affiliation badge |
| 2 | Email verified | "✓ Verified" ribbon |
| 3 | Theme card clicked | Entire preview recolors |
| 3 | Accent color clicked | Accent elements recolor |
| 4 | Logo uploaded | Logo circle |
| 4 | Banner uploaded/chosen | Banner strip |
| 5 | Description typed | About section fills |
| 5 | WhatsApp entered | Contact button appears |
| 5 | Social links entered | Social icons appear |

### Preview CSS injection (JS):
```js
// When user picks theme
function applyTheme(themeId) {
  const themes = {
    dark_noir:      { '--preview-bg': '#120F1E', '--preview-surface': '#1E1530', '--preview-accent': '#E8B030', '--preview-text': '#F2EFF8' },
    campus_light:   { '--preview-bg': '#F8FAFF', '--preview-surface': '#FFFFFF', '--preview-accent': '#1A72E8', '--preview-text': '#0A1628' },
    sunset_market:  { '--preview-bg': '#1A0E05', '--preview-surface': '#2A1A0A', '--preview-accent': '#E8721A', '--preview-text': '#F5E8D8' },
    forest_minimal: { '--preview-bg': '#061208', '--preview-surface': '#0D2415', '--preview-accent': '#26B857', '--preview-text': '#E8F5EC' },
    neon_pulse:     { '--preview-bg': '#020810', '--preview-surface': '#080F20', '--preview-accent': '#00F5CC', '--preview-text': '#E0F8FF' },
  };
  const vars = themes[themeId];
  const preview = document.getElementById('shop-preview');
  Object.entries(vars).forEach(([k, v]) => preview.style.setProperty(k, v));
}
```

---

## 🔧 DJANGO IMPLEMENTATION

### View

```python
# apps/public/views.py
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin

class CreateShopWizardView(LoginRequiredMixin, TemplateView):
    template_name = "wizard/create_shop.html"
    login_url = "/login/?next=/create-shop/"
    
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['universities'] = Client.objects.filter(
            tenant_type='UNIVERSITY', is_active=True
        ).order_by('name')
        ctx['locations'] = Client.objects.filter(
            tenant_type='LOCATION', is_active=True
        ).order_by('name')
        ctx['categories'] = Category.objects.filter(is_active=True)
        ctx['themes'] = ThemeEngine.list_themes()
        ctx['mpesa_fee'] = 500
        return ctx
```

### AJAX Endpoints

```python
# apps/public/urls.py (add these)
path("api/check-slug/",     views.CheckSlugView.as_view(),     name="check_slug"),
path("api/create-shop/",    views.CreateShopAPIView.as_view(), name="create_shop_api"),
path("api/mpesa-callback/", views.MpesaCallbackView.as_view(), name="mpesa_callback"),
path("api/poll-payment/",   views.PollPaymentView.as_view(),   name="poll_payment"),
```

```python
class CheckSlugView(View):
    def get(self, request):
        slug = request.GET.get("slug", "").lower().strip()
        # Clean slug
        slug = re.sub(r'[^a-z0-9-]', '-', slug)
        slug = re.sub(r'-+', '-', slug).strip('-')
        exists = Domain.objects.filter(domain__startswith=slug).exists()
        suggestion = f"{slug}-2" if exists else None
        return JsonResponse({
            "slug": slug,
            "available": not exists,
            "suggestion": suggestion,
        })

class CreateShopAPIView(LoginRequiredMixin, View):
    def post(self, request):
        data = json.loads(request.body)
        # Validate + create via service
        service = ShopCreationService()
        try:
            tenant = service.create(
                name=data['name'],
                slug=data['slug'],
                category=data['category'],
                parent_tenant_id=data.get('affiliation'),
                theme_id=data['theme'],
                logo=request.FILES.get('logo'),
                banner=request.FILES.get('banner'),
                description=data['description'],
                whatsapp=data['whatsapp'],
                owner=request.user,
            )
            # Initiate M-Pesa STK push
            txn = MpesaService().stk_push(
                phone=data['phone'],
                amount=500,
                reference=str(tenant.id),
                description=f"UniMarket shop setup: {data['name']}",
            )
            return JsonResponse({"status": "pending", "transaction_id": str(txn.reference)})
        except ValidationError as e:
            return JsonResponse({"error": str(e)}, status=400)
```

### Form Data Model (localStorage schema)

```js
// Persisted to localStorage key: 'um_wizard_state'
{
  step: 1,                    // current step
  completed: [1, 2],          // completed steps
  identity: {
    name: "Juju's Electronics",
    slug: "juju-electronics",
    tagline: "Quality tech, student prices",
    category: "electronics"
  },
  affiliation: {
    type: "university",       // 'university' | 'location' | null
    id: "uon-tenant-uuid",
    name: "University of Nairobi",
    verified: false
  },
  design: {
    theme_id: "dark_noir",
    accent: "gold"
  },
  branding: {
    logo_data_url: null,      // base64 for preview
    banner_data_url: null,
    banner_preset: "navy-gradient",
    initials_style: "bold-pill"
  },
  details: {
    description: "",
    whatsapp: "",
    location: "",
    instagram: "",
    tiktok: "",
    twitter: "",
    hours: {
      mon: { open: true, from: "08:00", to: "18:00" },
      tue: { open: true, from: "08:00", to: "18:00" },
      // ...
    }
  },
  payment: {
    phone: "",
    status: null              // null | 'pending' | 'success' | 'failed'
  }
}
```

---

## ✅ IMPLEMENTATION TODOS

### Foundation
```
[ ] Create templates/wizard/create_shop.html
[ ] Create static/css/wizard.css (all wizard-specific styles)
[ ] Create static/js/wizard.js (state machine + preview engine)
[ ] Wire URL: path("create-shop/", CreateShopWizardView.as_view())
[ ] Require auth: redirect to login if not authenticated
[ ] Load state from localStorage on mount
[ ] Save state to localStorage on every field change
```

### Step 1 — Identity
```
[ ] Name input with live slug generation
[ ] Slug preview display
[ ] Async slug availability check (debounced 400ms)
[ ] Category grid (6 pill-toggle cards)
[ ] Tagline input with char counter
[ ] Preview: update shop name + slug + category badge
[ ] Validation: name required, category required, slug available
```

### Step 2 — Affiliation
```
[ ] University/Location toggle cards
[ ] Searchable dropdown (filter from JSON or AJAX)
[ ] Skip step button
[ ] Student email verification (OTP send + verify)
[ ] Preview: university badge
```

### Step 3 — Design
```
[ ] 5 theme cards with mini mockup previews
[ ] Selected state: gold ring + checkmark
[ ] Accent color pill group (6 options)
[ ] Preview pane full re-theme on click
[ ] Theme data stored in state
```

### Step 4 — Branding
```
[ ] Logo upload with FileReader preview
[ ] Banner upload with FileReader preview
[ ] 4 gradient banner presets (CSS, no external assets)
[ ] 3 initials style options
[ ] Auto-generate initials from shop name
[ ] Pillow resize on backend (logo: 300×300, banner: 1200×400)
[ ] Preview: logo circle + banner strip update
```

### Step 5 — Details
```
[ ] Description textarea + char counter + simple formatting toolbar
[ ] WhatsApp: country code prefix + number input + Kenyan format validation
[ ] Campus/area freetext
[ ] 3 social link inputs (Instagram, TikTok, X)
[ ] Operating hours: 7-day toggle grid + time pickers
[ ] Preview: about section + contact button + social icons
```

### Step 6 — Launch
```
[ ] Read-only summary table with [Edit] links to each step
[ ] Pricing breakdown card
[ ] M-Pesa phone input
[ ] STK push trigger on submit
[ ] 4 payment states: idle / sending / waiting / success|failed
[ ] Polling: every 3s check /api/poll-payment/?ref=uuid (max 90s)
[ ] On success: tenant create + redirect to shop dashboard
[ ] On failure: retry or change number option
```

### Wizard Navigation
```
[ ] Progress stepper: 6 circles + labels + connecting lines
[ ] Completed steps: filled gold circle + checkmark
[ ] Active step: outlined gold circle
[ ] Future steps: gray
[ ] [← Back] button: never loses data, always usable
[ ] [Next →] button: disabled until step is valid
[ ] Clicking a completed step number jumps back to it
[ ] Keyboard: Enter advances, Escape goes back
[ ] Mobile: preview pane → full-screen slide-up modal on "Preview" tap
```

### Testing
```
[ ] Step 1: name generates correct slug (test 10 edge cases)
[ ] Step 1: slug availability check (mock AJAX)
[ ] Step 2: skip affiliation works, wizard continues
[ ] Step 3: theme switch updates preview CSS vars
[ ] Step 4: logo preview renders from FileReader
[ ] Step 5: WhatsApp validation rejects invalid formats
[ ] Step 6: payment states transition correctly
[ ] Full flow: Playwright end-to-end test (happy path)
[ ] Full flow: Playwright end-to-end test (payment failure path)
[ ] State persistence: localStorage save/restore after refresh
[ ] All steps: back button restores previous state correctly
```

---

## 🧩 SLUG GENERATION RULES

```js
function generateSlug(name) {
  return name
    .toLowerCase()
    .trim()
    .replace(/[''`]/g, '')           // remove apostrophes
    .replace(/[^a-z0-9\s-]/g, '')   // remove special chars
    .replace(/\s+/g, '-')            // spaces → hyphens
    .replace(/-+/g, '-')             // collapse multiple hyphens
    .replace(/^-|-$/g, '')           // trim edge hyphens
    .substring(0, 48);               // max 48 chars
}

// Examples:
// "Juju's Electronics" → "juJus-electronics" → "jujus-electronics"
// "Books & More!!"     → "books-more"
// "  My Cool Shop  "   → "my-cool-shop"
```

---

> **Agent note:** The wizard JS should be a clean state machine — one `state` object, one `render(step)` function, one `validate(step)` function. No spaghetti. Each step is a pure data transform: `state.identity.name → slug → check availability → update preview`. Keep it modular.
