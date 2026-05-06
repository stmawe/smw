# AGENT.md — SMW (UniMarket)
# Location: project root
# Purpose: Entry point for any agent session on this project

---

## READ THIS FIRST

This file is the session entry point. Do not start any task without reading the files below in order.

---

## MANDATORY SESSION START SEQUENCE

```
1. E:\Backup\pgwiz\agent-system\GLOBAL_PROTOCOL.md   ← global rules
2. E:\Backup\pgwiz\agent-system\GLOBAL_WARNINGS.md   ← global gotchas
3. E:\Backup\pgwiz\agent-system\CONVENTIONS.md        ← global code style
4. .agent/MEMORY.md                                   ← project context + patterns
5. .agent/CODEBASE.md                                 ← file map + services
6. .agent/WARNINGS.md                                 ← project-specific gotchas
7. .agent/CURRENT_TASK.md                             ← what is currently in progress
```

If any `.agent/` file is missing → run bootstrap from:
`E:\Backup\pgwiz\agent-system\AGENT_BOOTSTRAP.md`

---

## .agent/ FILE REFERENCE

| File | Purpose |
|------|---------|
| `.agent/MEMORY.md` | Project overview, established patterns, key decisions |
| `.agent/CODEBASE.md` | Directory map, models, services, URL confs, deployment notes |
| `.agent/WARNINGS.md` | Fragile files, known broken things, env gotchas |
| `.agent/CURRENT_TASK.md` | Active task scope — files to touch / not touch |
| `.agent/DONE.md` | Append-only log of completed tasks |

---

## PROJECT SNAPSHOT

- **Name:** SMW (UniMarket)
- **Stack:** Django + django-tenants | PostgreSQL | Python 3.11 | WSGI
- **Hosting:** Serv00 (FreeBSD, Phusion Passenger) — no Docker, no systemd
- **Domain:** smw.pgwiz.cloud
- **Shop subdomains:** `{slug}.smw.pgwiz.cloud`
- **Admin panel:** `admin.smw.pgwiz.cloud`
- **DNS/SSL:** Cloudflare wildcard `*.smw.pgwiz.cloud`
- **Branch:** `main`
- **Deploy:** `python deploy.py deploy` (paramiko SSH)

---

## QUICK FILE MAP

```
app/                        ← shared schema: Client, User, admin, shop services
  shop_creation_service.py  ← ShopCreationService.launch_shop()
  shop_urls.py              ← generate_shop_slug(), validate_shop_slug()
  ssl_manager.py            ← SSLCertificateManager (certbot + CF DNS)
  mpesa_gateway.py          ← M-Pesa Daraja API client
  admin_views.py            ← admin panel views

mydak/                      ← tenant schema: Shop, Listing, Transaction, Chat
  models.py                 ← Shop, Listing, Transaction, Conversation, Message
  mpesa.py                  ← MpesaBootstrap, get_transaction_amount()

accounts/                   ← auth views, allauth adapter
config/settings/            ← base.py, dev.py, prod.py
smw/urls.py                 ← public schema URL conf
config/tenant_urls.py       ← tenant schema URL conf
deploy.py                   ← SSH deployer (Serv00)
passenger_wsgi.py           ← WSGI entry point — DO NOT TOUCH without confirmation
```

---

## CRITICAL WARNINGS (summary — full list in .agent/WARNINGS.md)

- `*.smw.pgwiz.cloud` wildcard covers ONE level only — no deeper nesting
- `mydak/` is TENANT schema — models live per-tenant, not in public
- `app/` is SHARED schema — models live in public schema
- `Shop.domain` is the slug, not the full domain — use `Shop.full_domain` property
- `MpesaTransaction` (app/) ≠ `Transaction` (mydak/) — different models, different purposes
- `Payment` (mydak/) is LEGACY — use `Transaction` for new work
- NEVER touch `.env` on the server
- NEVER suggest Docker or systemd for Serv00

---

*This file is read-only for the agent. Only pgwiz patches it manually.*
