# Project Structure Guidelines

## Overview
This document outlines the project organization structure and guidelines for maintaining a clean repository.

## Folder Structure

```
smw/
├── app/                    # Django app (core application)
├── accounts/              # Django accounts app
├── apps/                  # Additional Django apps
├── config/                # Django settings
├── mydak/                 # Marketplace app
├── smw/                   # Project configuration
├── templates/             # HTML templates
├── static/                # Static assets (CSS, JS, images)
├── scripts/               # Deployment and setup scripts
├── debug/                 # Debug and test files (NOT in version control)
├── md/                    # Documentation and markdown files (NOT in version control)
├── manage.py              # Django management script
├── deploy.py              # Production deployment script
├── requirements.txt       # Python dependencies
├── .gitignore             # Git ignore rules
├── README.md              # Main project README (in root only)
└── [other config files]   # .env, vercel.json, etc.
```

## File Organization Rules

### ✅ KEEP IN VERSION CONTROL (Root Level)
- `README.md` - Main project documentation
- `requirements.txt` - Python dependencies
- `manage.py` - Django management
- `.gitignore` - Git configuration
- `config/settings/` - Django settings
- Application code: `app/`, `accounts/`, `apps/`, `mydak/`, `smw/`
- Templates: `templates/`
- Scripts: `scripts/` (deployment-ready, no hardcoded credentials)

### ❌ DO NOT COMMIT (Move to `/debug/` folder)
- Test files: `test_*.py`, `verify_*.py`, `check_*.py`, `diagnostic_*.py`
- Temporary/scratch files: `temp_*.py`, `scratch_*.py`
- Debug utilities: `debug_*.py`
- Example: Move `test_admin_login.sh` → `debug/test_admin_login.sh`

### ❌ DO NOT COMMIT (Move to `/md/` folder)
- Archive documentation: All historical `.md` files except `README.md`
- Setup guides: `SETUP_*.md`, `INSTALL_*.md`
- Documentation: Keep only essential docs in repo root
- Note: These are not needed in version control; developers can access them locally
- Examples:
  - `ADMIN_SSL_QUICK_START.txt` → `md/ADMIN_SSL_QUICK_START.txt`
  - `DEPLOYMENT_CHECKLIST.md` → `md/DEPLOYMENT_CHECKLIST.md`
  - `SSL_SETUP_GUIDE.md` → `md/SSL_SETUP_GUIDE.md`

### ❌ SENSITIVE FILES (Must be in `.gitignore`)
- `.env` - Environment variables with credentials
- `server.env` - Server environment
- `cf.ini` - Cloudflare credentials
- `*.pem`, `*.key` - SSL/TLS keys
- `secrets.json`, `secrets/` - Secrets
- `db.sqlite3` - Local database

## How to Move Files Properly

### Move Test/Debug Files
```bash
# Create debug folder if not exists
mkdir -p debug/

# Move individual test files
mv test_admin_login.sh debug/
mv verify_admin.py debug/
mv check_tenants.py debug/

# Remove from git
git rm --cached test_admin_login.sh verify_admin.py check_tenants.py
git status  # Verify files are staged for removal
```

### Move Documentation Files
```bash
# Create md folder if not exists
mkdir -p md/

# Move markdown files (except README.md)
mv ADMIN_SSL_QUICK_START.txt md/
mv DEPLOYMENT_CHECKLIST.md md/
mv THEME_SYSTEM.md md/

# Remove from git
git rm --cached ADMIN_SSL_QUICK_START.txt DEPLOYMENT_CHECKLIST.md THEME_SYSTEM.md
git status  # Verify files are staged for removal
```

### Commit Changes
```bash
# Update .gitignore with new folders
# Add these lines to .gitignore:
# debug/
# md/

git add .gitignore
git commit -m "Reorganize project structure: move test files to debug/, docs to md/, update .gitignore"
git push origin main
```

## Creating New Test/Debug Files

**Always create in `/debug/` folder:**
```bash
# Good ✅
touch debug/test_new_feature.py
bash debug/verify_deployment.sh

# Bad ❌ (Don't do this)
touch test_new_feature.py  # DON'T create in root
```

## Creating New Documentation

**Follow these guidelines:**
- **README.md**: Only in root, for main project documentation
- **Guides/Tutorials**: Create in `md/` folder, e.g., `md/SETUP_GUIDE.md`
- **Implementation docs**: Create in `md/` folder or within app-specific folders
- **Quick references**: Create in `md/` folder

## .gitignore Configuration

Current `./.gitignore` has:
```
# Debug scripts and temporary setup files
debug/

# Documentation folder (archived docs not needed in repo)
md/

# Sensitive files
.env
.env.production
*.key
*.pem
secrets.json
```

## Cleaning Up Repository History

If test files were accidentally committed, remove them from history:

```bash
# Option 1: Remove from last commit (before pushing)
git reset --soft HEAD~1
git restore --staged filename
git rm --cached filename

# Option 2: Remove from all history (BFG Repo Cleaner - advanced)
# Install: brew install bfg  (or download from https://rtyley.github.io/bfg-repo-cleaner/)
bfg --delete-files filename
git reflog expire --expire=now --all && git gc --prune=now
```

## Workflow for Developers

When working on the project:

1. **Writing tests?** → Create in `debug/` folder
2. **Adding documentation?** → Check if it's README or add to `md/`
3. **Creating temporary files?** → Use `debug/` folder
4. **Adding to version control?** → Only production code and essential docs

## Files Currently in `/debug/`

- `verify_admin.py` - Admin user verification script
- `test_admin_login.sh` - Admin login testing script
- `test_import.py` - Module import testing
- `test_domain_extract.py` - Domain extraction testing
- `check_tenants.py` - Django-tenants diagnostic
- `diagnostic_tenants.py` - Tenant diagnostics
- `temp_urls.py` - Temporary URL configuration

## Files Currently in `/md/`

- `ADMIN_SSL_QUICK_START.txt` - SSL setup quick reference
- `AGENT.md` - Agent documentation
- `AUDIT.md` - Audit trail documentation
- `DEPLOYMENT_CHECKLIST.md` - Deployment procedures
- `DEPLOY_COMMANDS.md` - Deployment commands reference
- `FRONT.md` - Frontend documentation
- `FRONTEND_SUMMARY.md` - Frontend summary
- `IMPLEMENTATION_COMPLETE.md` - Implementation status
- `PHASE_14_PLUS_PLAN.md` - Phase 14+ planning
- `PROGRESS.md` - Project progress tracking
- `QUICKSTART.md` - Quick start guide
- `SERV00_SSL_SETUP.md` - Server SSL setup
- `SERV00_SSL_STEP_BY_STEP.md` - Step-by-step server setup
- `SSL_DEPLOYMENT_READY.md` - SSL deployment status
- `SSL_QUICK_REFERENCE.md` - SSL reference
- `SSL_SETUP_GUIDE.md` - SSL setup guide
- `THEME_SYSTEM.md` - Theme system documentation

## Notes

- Files in `debug/` and `md/` are on local machines but NOT pushed to GitHub
- These folders should have `.gitkeep` or be created fresh when cloning
- Developers can add their own debug/test files locally without affecting the repo
- Use `git status` frequently to ensure you're not committing unwanted files

## Best Practices

✅ DO:
- Keep application code in the repo
- Keep production configs and settings
- Keep requirements.txt updated
- Use .gitignore effectively
- Create test files in debug/
- Store docs in md/ or root README

❌ DON'T:
- Commit test files to root
- Commit credentials or secrets
- Commit large binary files
- Commit .env or environment configs
- Commit debug/temporary files
- Commit database files (*.sqlite3, *.db)
