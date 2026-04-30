# 🎨 FRONT.md — UniMarket Public Site UI Plan
> **Palette:** Deep Navy · Electric Blue · Champagne Gold · Emerald Green  
> **Aesthetic:** Editorial Luxury Marketplace — think Bloomberg meets Etsy meets a university alumni magazine  
> **Stack:** Django/Blade templates + Vanilla JS (no framework) + CSS custom properties  
> **Fonts:** Canela (display) + Sora (body) — both via Google Fonts  

---

## 🎨 DESIGN SYSTEM

### Color Tokens

```css
:root {
  /* === PRIMARY PALETTE (Blue / Gold / Green only) === */

  /* Blue family */
  --blue-950:  #020A1A;   /* near-black navy, page bg */
  --blue-900:  #061428;   /* deep navy, section bg */
  --blue-800:  #0A2240;   /* dark navy, card bg */
  --blue-700:  #0D3366;   /* strong navy */
  --blue-600:  #1050A0;   /* medium blue */
  --blue-500:  #1A72E8;   /* primary action blue */
  --blue-400:  #4A94F0;   /* hover blue */
  --blue-300:  #82B8F8;   /* light blue */
  --blue-200:  #B8D6FB;   /* pale blue */
  --blue-100:  #E0EFFE;   /* lightest blue tint */
  --blue-50:   #F0F7FF;   /* near-white blue */

  /* Gold family */
  --gold-900:  #1A1000;   /* deep gold-black */
  --gold-800:  #3D2800;   /* very dark gold */
  --gold-700:  #6B4500;   /* dark gold */
  --gold-600:  #9B6400;   /* medium gold */
  --gold-500:  #C9920A;   /* primary gold */
  --gold-400:  #E8B030;   /* bright gold */
  --gold-300:  #F0CA70;   /* light gold */
  --gold-200:  #F5DC9E;   /* pale gold */
  --gold-100:  #FAF0D0;   /* lightest gold tint */
  --gold-50:   #FEFBF0;   /* near-white gold */

  /* Green family */
  --green-900: #011208;   /* deepest green-black */
  --green-800: #032B12;   /* very dark green */
  --green-700: #064A20;   /* dark green */
  --green-600: #0A6B2D;   /* forest green */
  --green-500: #0F9640;   /* primary green */
  --green-400: #26B857;   /* bright green */
  --green-300: #5CD48A;   /* light green */
  --green-200: #99E8B8;   /* pale green */
  --green-100: #CEFAE0;   /* lightest green tint */
  --green-50:  #EDFFF5;   /* near-white green */

  /* Neutrals (derived from blue) */
  --surface-0:  #020B1C;  /* page background */
  --surface-1:  #071830;  /* elevated surface */
  --surface-2:  #0C2540;  /* card surface */
  --surface-3:  #132E50;  /* hover surface */
  --border-dim: rgba(255,255,255,0.06);
  --border-mid: rgba(255,255,255,0.12);
  --border-hi:  rgba(255,255,255,0.22);
  --text-1:     #F2F7FF;  /* primary text */
  --text-2:     #A8BDD8;  /* secondary text */
  --text-3:     #5C7A99;  /* muted text */

  /* === SEMANTIC ALIASES === */
  --color-primary:   var(--blue-500);
  --color-accent:    var(--gold-400);
  --color-success:   var(--green-400);
  --color-primary-hover: var(--blue-400);
  --color-accent-hover:  var(--gold-300);

  /* === TYPOGRAPHY === */
  --font-display: 'Canela', 'Georgia', serif;
  --font-body:    'Sora', sans-serif;
  --font-mono:    'JetBrains Mono', monospace;

  /* === SPACING === */
  --space-1: 4px;   --space-2: 8px;   --space-3: 12px;
  --space-4: 16px;  --space-5: 24px;  --space-6: 32px;
  --space-7: 48px;  --space-8: 64px;  --space-9: 96px;

  /* === LAYOUT === */
  --radius-sm: 6px;   --radius-md: 10px;
  --radius-lg: 16px;  --radius-xl: 24px;
  --radius-pill: 9999px;
  --container-max: 1280px;
  --container-padding: clamp(16px, 4vw, 48px);

  /* === EFFECTS === */
  --glass-bg: rgba(12, 37, 64, 0.72);
  --glass-border: rgba(255,255,255,0.10);
  --glass-blur: blur(16px);
  --glow-blue:  0 0 40px rgba(26, 114, 232, 0.25);
  --glow-gold:  0 0 40px rgba(232, 176, 48, 0.20);
  --glow-green: 0 0 40px rgba(38, 184, 87, 0.18);
  --shadow-card: 0 4px 24px rgba(2, 10, 26, 0.6), 0 1px 0 rgba(255,255,255,0.04) inset;
}
```

### Typography Scale

```css
/* Display — Canela, for heroes and section titles */
.text-display-xl  { font: 700 clamp(48px, 6vw, 80px)/1.08 var(--font-display); letter-spacing: -0.03em; }
.text-display-lg  { font: 700 clamp(36px, 4vw, 56px)/1.12 var(--font-display); letter-spacing: -0.025em; }
.text-display-md  { font: 600 clamp(28px, 3vw, 40px)/1.18 var(--font-display); letter-spacing: -0.02em; }

/* Body — Sora, for everything else */
.text-heading-lg  { font: 600 24px/1.3 var(--font-body); }
.text-heading-md  { font: 600 18px/1.4 var(--font-body); }
.text-heading-sm  { font: 600 15px/1.4 var(--font-body); }
.text-body-lg     { font: 400 17px/1.7 var(--font-body); }
.text-body-md     { font: 400 15px/1.65 var(--font-body); }
.text-body-sm     { font: 400 13px/1.6 var(--font-body); }
.text-label       { font: 500 12px/1 var(--font-body); letter-spacing: 0.08em; text-transform: uppercase; }
.text-price       { font: 700 20px/1 var(--font-body); letter-spacing: -0.01em; }
```

---

## 🗺️ PAGE MAP

```
Public Site (baseurl.com)
├── / ─────────────── Homepage (hero + featured shops + active listings + CTA)
├── /explore ──────── All Shops Directory (browse + filter by university/location/category)
├── /shops/:slug ──── Individual Shop Storefront (products, about, contact seller)
├── /listings ─────── All Listings Feed (search + filter + sort)
├── /listings/:id ─── Listing Detail (full product page, contact seller)
├── /create-shop ──── Shop Creation Wizard (3-step, authenticated)
├── /universities ─── University Index (grid of affiliated universities)
├── /locations ────── Location Index (grid of location-based markets)
├── /register ─────── Sign Up
├── /login ─────────── Sign In
└── /about ─────────── About + How It Works
```

---

## 🧩 COMPONENT LIBRARY

### 1. `<Navbar />`

```
┌─────────────────────────────────────────────────────────────────┐
│  ◈ UniMarket    Explore  Universities  Locations  How It Works  │
│                                        [Open a Shop] [Sign In]  │
└─────────────────────────────────────────────────────────────────┘
```

**Specs:**
- `position: sticky; top: 0; z-index: 100`
- Glassmorphism: `background: var(--glass-bg); backdrop-filter: var(--glass-blur)`
- Border bottom: `1px solid var(--border-dim)`
- Logo: wordmark in `var(--font-display)` weight 700, gold accent on "◈" symbol
- Nav links: `text-body-sm` weight 500, color `var(--text-2)`, hover → `var(--text-1)` with gold underline `::after`
- CTA "Open a Shop": pill button, gold gradient bg, navy text
- "Sign In": ghost button, blue border
- Mobile: hamburger → slide-in drawer from right, full height

**Template:** `templates/components/navbar.html`

---

### 2. Hero Section (Homepage only)

```
┌──────────────────────────────────────────────────────────────────┐
│                    [animated particle field]                      │
│                                                                   │
│         The Campus Marketplace                                    │
│         ─────────── for ───────────                              │
│         Students, Sellers & Communities                           │
│                                                                   │
│    Browse 1,200+ listings across 48 university shops              │
│                                                                   │
│    [  Explore Shops  ]   [  Sell Something  ]                     │
│                                                                   │
│    ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│    │ 48 Shops │  │  3 Unis  │  │ 1,200+   │  │  KES 50  │       │
│    │  Active  │  │Partnered │  │ Listings │  │ to Post  │       │
│    └──────────┘  └──────────┘  └──────────┘  └──────────┘       │
└──────────────────────────────────────────────────────────────────┘
```

**Specs:**
- Full viewport height (`100dvh`), navy bg `var(--surface-0)`
- Headline: `text-display-xl`, white, with gold highlight on "Campus"
- Particle field: CSS-only floating dots via `@keyframes`, 20–30 tiny circles, blue/gold, low opacity
- Sub-headline: `text-body-lg`, color `var(--text-2)`
- Primary CTA: pill button, blue 500 bg, box-shadow `var(--glow-blue)`
- Secondary CTA: ghost pill, gold border + gold text
- Stat cards: glassmorphism cards in a 4-col row, border `var(--border-mid)`, number in `text-display-md` gold, label in `text-label` muted

---

### 3. `<ShopCard />` — used in grids across site

```
┌──────────────────────────────────┐
│  [Shop Banner Image / Gradient]  │  ← aspect-ratio 16/7, object-fit cover
│                                  │     or gradient fallback (blue→green)
├──────────────────────────────────┤
│  ◉ Juju's Electronics            │  ← shop logo circle + name
│  📍 University of Nairobi        │  ← affiliation badge
│                                  │
│  Electronics · Tech · Gadgets    │  ← category tags (pill, blue tint)
│                                  │
│  ★★★★☆  4.2 · 34 listings       │  ← rating + count
│                                  │
│  [ Visit Shop → ]                │  ← full-width CTA
└──────────────────────────────────┘
```

**Specs:**
- Background: `var(--surface-2)`, border `1px solid var(--border-dim)`, radius `var(--radius-lg)`
- Hover: `border-color: var(--border-mid)`, `transform: translateY(-2px)`, shadow `var(--shadow-card)`
- Logo circle: 36px, border `2px solid var(--gold-500)`
- Affiliation badge: `background: var(--blue-900)`, text `var(--blue-300)`, icon prefix
- Category tags: pill, `background: rgba(26,114,232,0.12)`, color `var(--blue-300)`
- Rating: gold stars (Unicode ★) + `var(--text-3)` meta text
- CTA: full-width, `background: transparent`, border top `var(--border-mid)`, hover → `var(--blue-500)` bg

**Template:** `templates/components/shop_card.html`  
**Context vars:** `shop.name`, `shop.slug`, `shop.logo`, `shop.banner`, `shop.affiliation`, `shop.categories`, `shop.rating`, `shop.listing_count`

---

### 4. `<ListingCard />` — product cards in grids/feeds

```
┌──────────────────────────────────┐
│   [Product Image]                │  ← 1:1 or 4:3, object-fit contain
│                      [♡ Save]    │  ← positioned top-right
├──────────────────────────────────┤
│  MacBook Pro 2021 M1             │  ← title, heading-sm, 2-line clamp
│                                  │
│  KES 85,000                      │  ← price, gold, text-price size
│  ~~KES 120,000~~                 │  ← crossed out original (optional)
│                                  │
│  💻 Electronics · 3 hrs ago      │  ← category + time, muted small
│                                  │
│  [Shop: Juju's Electronics →]    │  ← shop attribution, ghost pill
└──────────────────────────────────┘
```

**Specs:**
- Background: `var(--surface-2)`, hover lifts + brightens border
- Image container: `background: var(--surface-1)`, overflow hidden
- Save button (wishlist): `position: absolute; top: 8px; right: 8px`, glass pill, heart icon
- Price: `color: var(--gold-400)`, weight 700
- Strikethrough: `var(--text-3)`, `text-decoration: line-through`
- Meta row: `var(--text-3)`, 12px, flex row with dot separator
- Shop pill: link to shop storefront, blue text, border `var(--border-mid)`

**Template:** `templates/components/listing_card.html`

---

### 5. Shop Storefront Page (`/shops/:slug`)

```
┌────────────────────────────────────────────────────────────────┐
│  [Full-Width Banner — 280px tall]                              │
│                          [Shop Logo] Shop Name                 │
│                          University of Nairobi · Electronics   │
│                          ★ 4.2 · 34 listings · Joined Jan 2024│
│                          [Message Seller]  [Follow Shop]       │
├────────────────────────────────────────────────────────────────┤
│  About ─ Listings ─ Categories ─ Reviews                       │  ← sticky tabs
├────────────────────────────────────────────────────────────────┤
│  [Filter bar: search, category, price range, sort]             │
├────────────────────────────────────────────────────────────────┤
│  [Masonry / 3-col listing grid]                                │
└────────────────────────────────────────────────────────────────┘
```

**Specs:**
- Banner: full bleed, `object-fit: cover`, gradient overlay at bottom (`→ transparent to var(--surface-0)`)
- Logo: 72px circle, elevated on banner, `border: 3px solid var(--gold-500)`
- Shop header: flex row, shop info left, action buttons right
- Tabs: sticky `top: 64px` (below navbar), `background: var(--surface-1)`, `border-bottom: 1px solid var(--border-dim)`
- Active tab: gold underline `::after`, `color: var(--text-1)`
- Filter bar: horizontal, glass bg, inputs styled in system tokens
- Listing grid: CSS grid, `repeat(auto-fill, minmax(220px, 1fr))`

---

### 6. Shop Creation Wizard (`/create-shop`)

**Step 1: Identity**
```
┌─────────────────────────────────────────────────────┐
│  ① Identity   ② Appearance   ③ Launch              │  ← step indicator
├─────────────────────────────────────────────────────┤
│                                                     │
│   Give your shop a name                             │
│   ┌─────────────────────────────────────────────┐  │
│   │  My Shop Name                               │  │
│   └─────────────────────────────────────────────┘  │
│   Your shop will live at: myshopname.unimarket.ke   │  ← live preview
│                                                     │
│   What will you sell?                               │
│   [Electronics] [Books] [Fashion] [Food] [Other]    │  ← pill toggles
│                                                     │
│   Affiliated university / location                  │
│   ┌─────────────────────────────────────────────┐  │
│   │  Select university…                ▾        │  │
│   └─────────────────────────────────────────────┘  │
│                                                     │
│                              [ Next → ]             │
└─────────────────────────────────────────────────────┘
```

**Step 2: Appearance (Theme Picker)**
```
┌───────────────────────────────────────────────────────────────┐
│   Choose your shop's look                                     │
│                                                               │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │ 🌙 Dark  │  │ 📚 Acad  │  │ 🌿 Earth │  │ ⚡ Neon  │    │
│  │  Noir    │  │  Light   │  │  Market  │  │  Pulse   │    │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘    │
│  [Selected: Dark Noir — highlighted with gold ring]          │
│                                                               │
│  Live Preview ───────────────────────────────────────────    │
│  ┌────────────────────────────────────────┐                  │
│  │  [Mini shop preview rendering]         │                  │
│  └────────────────────────────────────────┘                  │
│                                                               │
│   [ ← Back ]                          [ Next → ]             │
└───────────────────────────────────────────────────────────────┘
```

**Step 3: Launch**
```
┌────────────────────────────────────────────────────────────┐
│   🎉 Ready to launch!                                      │
│                                                            │
│   Shop name:       Juju's Electronics                      │
│   URL:             juju-electronics.unimarket.ke           │
│   Affiliation:     University of Nairobi                   │
│   Category:        Electronics                             │
│   Theme:           Dark Noir                               │
│                                                            │
│   Setup fee: KES 500                                       │
│   ┌──────────────────────────────────┐                    │
│   │  📱 Pay via M-Pesa               │                    │
│   │  Enter your Safaricom number:    │                    │
│   │  07XX XXX XXX                    │                    │
│   └──────────────────────────────────┘                    │
│                                                            │
│   [ ← Back ]           [ Launch My Shop ✓ ]               │
└────────────────────────────────────────────────────────────┘
```

**Specs:**
- Step indicator: horizontal stepper, circles connected by lines, completed = filled gold, active = outlined gold, future = gray
- Form inputs: `height: 48px`, `background: var(--surface-1)`, border `var(--border-mid)`, focus → `border-color: var(--blue-500)`, `box-shadow: var(--glow-blue)`
- Category pills: multi-select toggles, selected = `background: var(--blue-800)`, border `var(--blue-500)`
- Theme cards: 160px × 110px preview cards, selected = ring `2px solid var(--gold-500)`, `box-shadow: var(--glow-gold)`
- Back/Next: ghost (back) + filled blue (next), pill shape
- Launch button: gold gradient, navy text, `box-shadow: var(--glow-gold)`

---

### 7. Listings Feed Page (`/listings`)

**Layout:**
```
┌────────────────────────────────────────────────────────────────────┐
│  [Sticky Search Bar — full width, prominent]                       │
│  🔍  Search listings…               [Filter ▾]  [Sort ▾]          │
├───────────────┬────────────────────────────────────────────────────┤
│  FILTERS      │  RESULTS                                           │
│  ─────────    │  Showing 1,247 listings                            │
│  Category     │                                                    │
│  □ Electronics│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐            │
│  □ Books      │  │Card  │ │Card  │ │Card  │ │Card  │            │
│  □ Fashion    │  └──────┘ └──────┘ └──────┘ └──────┘            │
│  □ Food       │  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐            │
│  □ Services   │  │Card  │ │Card  │ │Card  │ │Card  │            │
│               │  └──────┘ └──────┘ └──────┘ └──────┘            │
│  Price Range  │                                                    │
│  [0]──●──[∞]  │  [Load More]                                      │
│               │                                                    │
│  University   │                                                    │
│  □ UoN        │                                                    │
│  □ KU         │                                                    │
└───────────────┴────────────────────────────────────────────────────┘
```

**Specs:**
- Sidebar filters: `width: 220px`, sticky `top: 64px`, `height: calc(100vh - 64px)`, `overflow-y: auto`
- Mobile: filters collapse into bottom sheet (triggered by "Filter" button)
- Search bar: glass pill, `height: 52px`, search icon left, clear × right
- Results count: `text-label`, gold accent on number
- Grid: `repeat(auto-fill, minmax(200px, 1fr))`, `gap: var(--space-4)`
- Price range slider: dual handle, track fills gold between handles
- Load more: ghost pill button, centered, lazy-loads next page

---

### 8. `<Footer />`

```
┌──────────────────────────────────────────────────────────────────┐
│  ◈ UniMarket                                                     │
│  The campus marketplace connecting students and communities       │
│                                                                   │
│  Platform          Sellers          Connect                       │
│  ─────────         ────────         ────────                     │
│  Browse Shops      Open a Shop      About Us                      │
│  All Listings      Pricing          Blog                          │
│  Universities      Seller Guide     Contact                       │
│  Locations         M-Pesa Payments  Privacy Policy                │
│                                                                   │
│  ───────────────────────────────────────────────────────────     │
│  © 2025 UniMarket · Built for Kenyan students                    │
└──────────────────────────────────────────────────────────────────┘
```

**Specs:**
- Background: `var(--surface-1)`, border-top `var(--border-dim)`
- Logo: same as navbar, white
- Tagline: `text-body-sm`, `var(--text-3)`
- Column headers: `text-label`, `var(--text-3)`
- Links: `text-body-sm`, `var(--text-2)`, hover → `var(--blue-400)`
- Bottom bar: border-top `var(--border-dim)`, flex space-between, meta text `var(--text-3)` 12px

---

## 🌐 PAGE-BY-PAGE SPECIFICATIONS

### Homepage (`/`)

**Sections in order:**
1. `<Navbar />`
2. **Hero** — full-viewport, animated
3. **Featured Categories** — horizontal scroll on mobile, 6-item row desktop
   - Cards: category icon (CSS shape, not img), label, listing count
   - Colors: Electronics=blue, Books=gold, Fashion=green, Food=gold, Services=blue, Other=gray
4. **Featured Shops** — `text-display-md` heading + "View All →" link, 3-col shop card grid
5. **Latest Listings** — `text-display-md` heading, 4-col listing card grid, "Browse All →"
6. **How It Works** — 4-step explainer, horizontal on desktop, vertical on mobile
   - Step 1: Browse shops and listings
   - Step 2: Message the seller directly  
   - Step 3: Agree on price and meetup
   - Step 4: Open your own shop in minutes
   - Each step: large number (display font, gold), title, body, connecting dashed line between steps
7. **Universities Banner** — horizontal scroll of affiliated university cards (logo + name + shop count)
8. **CTA Band** — full-width, blue gradient bg, "Ready to sell? Open a shop today" + gold CTA button
9. `<Footer />`

---

### Explore Page (`/explore`)

**Layout:** Hero strip (title + search) → Filter tabs (All / University / Location / Category) → Shop grid (infinite scroll or paginated)

**Hero strip:**
- `height: 200px`, gradient bg (navy → deep blue)
- Title: "Explore All Shops" in display font
- Search: centered pill, `width: min(600px, 90%)`, autofocus

**Filter tabs:**
- Horizontal, scrollable on mobile
- Active: `background: var(--blue-800)`, gold underline
- Tabs: All · Electronics · Books · Fashion · Food · Services · By University · By Location

**Shop grid:**
- `repeat(auto-fill, minmax(280px, 1fr))`, 24px gap
- Animate in: stagger with `animation-delay: calc(n * 60ms)`, slide-up + fade

---

### Listing Detail (`/listings/:id`)

```
┌──────────────────────────────────────────────────────────┐
│  ← Back to [Shop Name]                                   │
├────────────────────┬─────────────────────────────────────┤
│  [Image Gallery]   │  MacBook Pro M1 2021                │
│  ┌──────────────┐  │  KES 85,000                        │
│  │ Main Image   │  │  ~~KES 120,000~~ · 29% off         │
│  └──────────────┘  │                                     │
│  [◁] [img][img][▷] │  Condition: Like New                │
│                    │  Posted: 3 hours ago                 │
│                    │  Views: 47                           │
│                    │                                      │
│                    │  [  Message Seller  ]  [Save ♡]     │
│                    │                                      │
│                    │  Sold by: Juju's Electronics  →      │
├────────────────────┴─────────────────────────────────────┤
│  Description                                             │
│  Barely used, bought in 2022. All original accessories.  │
│  AppleCare expires Jan 2026. No dents or scratches.      │
├──────────────────────────────────────────────────────────┤
│  More from this shop                                     │
│  [Card] [Card] [Card] [Card]                             │
└──────────────────────────────────────────────────────────┘
```

**Specs:**
- Breadcrumb: `text-body-sm`, `var(--text-3)`
- Image gallery: main image + thumbnail strip, click to swap, swipe on mobile
- Price: `text-price` scale, `var(--gold-400)`
- Strikethrough + discount badge: green pill ("29% off")
- Meta grid: 2-col key-value pairs, `var(--text-3)` labels, `var(--text-1)` values
- Message button: full-width pill, `var(--blue-500)` bg, white text, `box-shadow: var(--glow-blue)`
- Save button: ghost pill, heart icon, gold border on hover
- "Sold by" row: shop logo + name, chevron →, links to shop storefront

---

## ⚡ ANIMATIONS & INTERACTIONS

### Page Load (homepage)
```css
/* Elements enter with staggered slide-up + fade */
.animate-in {
  animation: slideUp 0.5s ease-out both;
}
@keyframes slideUp {
  from { opacity: 0; transform: translateY(20px); }
  to   { opacity: 1; transform: translateY(0); }
}

/* Apply stagger via inline style or utility classes */
.stagger-1 { animation-delay: 0.05s; }
.stagger-2 { animation-delay: 0.10s; }
.stagger-3 { animation-delay: 0.15s; }
/* ... up to .stagger-8 */
```

### Hover on cards
```css
.shop-card, .listing-card {
  transition: transform 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
}
.shop-card:hover  { transform: translateY(-3px); border-color: var(--border-hi); }
.listing-card:hover { transform: translateY(-2px); }
```

### Gold shine on CTAs
```css
.btn-gold {
  position: relative;
  overflow: hidden;
  background: linear-gradient(135deg, var(--gold-400), var(--gold-500));
}
.btn-gold::after {
  content: '';
  position: absolute;
  top: -50%; left: -75%;
  width: 50%; height: 200%;
  background: rgba(255,255,255,0.15);
  transform: skewX(-20deg);
  transition: left 0.4s ease;
}
.btn-gold:hover::after { left: 125%; }
```

### Number counter (stats section)
```js
// Count up animation for stat numbers in hero
function countUp(el, target, duration = 1500) {
  const start = performance.now();
  const update = (now) => {
    const progress = Math.min((now - start) / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 3); // ease-out cubic
    el.textContent = Math.round(eased * target).toLocaleString();
    if (progress < 1) requestAnimationFrame(update);
  };
  requestAnimationFrame(update);
}
```

### Search — debounced live results
```js
const searchInput = document.getElementById('search');
let debounceTimer;

searchInput.addEventListener('input', (e) => {
  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(() => {
    const query = e.target.value.trim();
    if (query.length >= 2) fetchResults(query);
  }, 300);
});
```

---

## 📐 RESPONSIVE BREAKPOINTS

```css
/* Mobile first */
/* xs: < 480px  — 1-col, stack everything */
/* sm: 480–767px — 2-col cards */
/* md: 768–1023px — sidebar collapses, 3-col grid */
/* lg: 1024–1279px — full layout, 4-col grid */
/* xl: 1280px+ — max-width container, 4-col grid */

.shop-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: var(--space-4);
}
@media (min-width: 480px)  { .shop-grid { grid-template-columns: repeat(2, 1fr); } }
@media (min-width: 768px)  { .shop-grid { grid-template-columns: repeat(3, 1fr); } }
@media (min-width: 1024px) { .shop-grid { grid-template-columns: repeat(4, 1fr); } }
```

---

## 🔗 DJANGO TEMPLATE INTEGRATION

### Context Processors needed

```python
# apps/public/context_processors.py

def site_stats(request):
    """Injects live stats into every public page"""
    return {
        "stats": {
            "shop_count": Client.objects.filter(tenant_type="SHOP").count(),
            "listing_count": ...  # cross-schema count (cached via Redis)
            "university_count": Client.objects.filter(tenant_type="UNIVERSITY").count(),
        }
    }

def active_categories(request):
    """Top categories for nav/filter dropdowns"""
    return {"categories": Category.objects.filter(is_active=True).order_by("name")}
```

### Template Tags

```python
# apps/public/templatetags/market_tags.py

@register.inclusion_tag("components/shop_card.html")
def shop_card(shop):
    return {"shop": shop}

@register.inclusion_tag("components/listing_card.html")
def listing_card(listing):
    return {"listing": listing}

@register.filter
def kes_format(value):
    """Format number as KES currency"""
    return f"KES {value:,.0f}"

@register.filter
def time_since_short(dt):
    """'3 hrs ago', '2 days ago' etc."""
    ...
```

### URL patterns

```python
# apps/public/urls.py
urlpatterns = [
    path("",                  views.HomepageView.as_view(),       name="home"),
    path("explore/",          views.ExploreView.as_view(),         name="explore"),
    path("shops/<slug:slug>/", views.ShopStorefrontView.as_view(), name="shop_detail"),
    path("listings/",         views.ListingsView.as_view(),        name="listings"),
    path("listings/<int:pk>/", views.ListingDetailView.as_view(),  name="listing_detail"),
    path("create-shop/",      views.CreateShopWizardView.as_view(), name="create_shop"),
    path("universities/",     views.UniversityIndexView.as_view(), name="universities"),
    path("locations/",        views.LocationIndexView.as_view(),   name="locations"),
    path("about/",            views.AboutView.as_view(),           name="about"),
]
```

---

## ✅ IMPLEMENTATION TODOS (ordered)

### Phase A — Foundation
```
[ ] Install Google Fonts: Canela + Sora
[ ] Create static/css/tokens.css (all CSS vars from §Design System)
[ ] Create static/css/base.css (reset, typography classes, layout utils)
[ ] Create static/css/components.css (all component styles)
[ ] Create static/js/main.js (search debounce, count-up, lazy load)
[ ] Create templates/base.html (loads fonts, CSS, meta tags, navbar, footer)
[ ] Wire STATICFILES_DIRS in settings
```

### Phase B — Core Components
```
[ ] templates/components/navbar.html (with mobile drawer)
[ ] templates/components/footer.html
[ ] templates/components/shop_card.html
[ ] templates/components/listing_card.html
[ ] templates/components/pagination.html
[ ] static/css/navbar.css
[ ] static/css/cards.css
```

### Phase C — Pages
```
[ ] Homepage: hero + categories + featured shops + listings + how-it-works + CTA + footer
[ ] Explore page: hero strip + filters + grid
[ ] Listings feed: sidebar filters + grid + search
[ ] Listing detail: gallery + info + contact + related
[ ] Shop storefront: banner + tabs + filter + grid
[ ] Create shop wizard: 3 steps + step indicator
[ ] Login + Register pages
```

### Phase D — Interactivity
```
[ ] Hero particle animation (CSS only)
[ ] Stat counter animation (JS)
[ ] Search debounce + HTMX or vanilla fetch
[ ] Image gallery on listing detail (JS)
[ ] Theme picker live preview (JS + CSS vars)
[ ] Mobile nav drawer (JS toggle)
[ ] Lazy image loading (IntersectionObserver)
[ ] Bottom sheet for mobile filters (JS)
```

### Phase E — Polish
```
[ ] Skeleton loaders for card grids (CSS animation)
[ ] Toast notifications (add to wishlist, shop created, etc.)
[ ] Empty states for no results (illustrated, not just text)
[ ] 404 page (on-brand, helpful links)
[ ] SEO: meta og tags, canonical, sitemap
[ ] Performance: defer non-critical JS, preload fonts
```

---

## 🧪 FRONTEND TESTS

```
[ ] Template renders without error for all views
[ ] ShopCard renders correctly with/without banner image
[ ] ListingCard handles missing price gracefully (should never happen but guard)
[ ] Search returns results for known query
[ ] Search returns empty state for no-match query
[ ] Wizard step 1 → step 2 → step 3 flow (Selenium/Playwright)
[ ] Mobile nav opens and closes correctly
[ ] Listing detail gallery image swap works
[ ] Filters update results without full page reload
[ ] All pages pass Lighthouse accessibility score > 80
```

---

> **Agent note:** Components are designed to work with Django template tags. Use `{% include "components/shop_card.html" with shop=shop %}` pattern everywhere. Keep JS in `main.js` modular — each feature in its own function, no global variable pollution.
