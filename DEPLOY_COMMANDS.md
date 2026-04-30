# Deploy Commands for Production Server

Run these commands on your production server (smw.pgwiz.cloud) to deploy the latest changes:

## Step 1: Navigate to project directory
```bash
cd /usr/home/wiptech/domains/smw.pgwiz.cloud/public_python
```

## Step 2: Pull latest code from GitHub
```bash
git pull origin main
```

This will pull:
- Updated homepage with hero + featured shops
- Redesigned login page
- New marketplace pages (explore, listings, shop detail, etc.)
- Updated navbar with marketplace links
- All route configurations

## Step 3: Restart the domain
```bash
devil www restart smw.pgwiz.cloud
```

This will restart the Phusion Passenger server and load all changes.

## Verification

After deploying, verify the changes:
1. Visit https://smw.pgwiz.cloud/ - Should show new homepage with hero section
2. Visit https://smw.pgwiz.cloud/explore/ - Should show explore page
3. Visit https://smw.pgwiz.cloud/login/ - Should show redesigned login
4. Check navbar - Should have marketplace links

## Optional: Run migrations (if needed)
If you haven't run migrations for the theme system yet:
```bash
python manage.py migrate
python manage.py init_theme_tokens
```

These create the theme database tables and initialize 45 design tokens.
