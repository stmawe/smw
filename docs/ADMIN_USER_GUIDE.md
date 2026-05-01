# Admin Panel User Guide

## Welcome to the Admin Panel

The Admin Panel is your central hub for managing the platform. This guide walks you through common tasks and features.

## Quick Start

### Logging In

1. Navigate to `https://yourdomain.com/admin/login`
2. Enter your username and password
3. You'll be directed to the dashboard

### Dashboard Overview

The dashboard shows key metrics:
- **Total Users**: Active user accounts
- **Active Shops**: Verified merchants
- **Pending Listings**: Awaiting approval
- **Recent Transactions**: Financial activity
- **Activity Feed**: Recent admin actions

## User Management

### Creating a New User

1. Go to **Users** → **Add User**
2. Fill in the form:
   - **Username**: Unique identifier (alphanumeric, no spaces)
   - **Email**: Valid email address
   - **Password**: Meets security requirements
   - **First/Last Name**: Optional but recommended
3. Click **Create User**

**Password Requirements:**
- Minimum 12 characters
- At least one uppercase letter (A-Z)
- At least one lowercase letter (a-z)
- At least one digit (0-9)
- At least one special character (!@#$%^&*()_+-=[]{};:'",.&lt;&gt;?/`~\\|)

### Editing User Information

1. Go to **Users** → Find the user
2. Click on their username to open details
3. Click **Edit** button
4. Update fields as needed
5. Click **Save Changes**

### Suspending a User

Temporarily disable an account:

1. Go to **Users** → Find the user
2. Click **More** → **Suspend User**
3. Provide a reason (optional)
4. Confirm suspension

The user cannot log in, but their data is preserved.

### Resetting User Password

1. Go to **Users** → Find the user
2. Click **More** → **Reset Password**
3. A temporary password is generated
4. Share with the user (they'll be prompted to change it)

### Viewing User Activity

1. Go to **Audit Logs**
2. Filter by user to see their admin actions
3. Click on log entry for details

## Shop Management

### Approving/Verifying Shops

1. Go to **Shops** → Find the shop
2. Review shop details:
   - Shop name and description
   - Owner information
   - Active listings count
   - Transaction history
3. Click **Verify** to mark as trusted merchant
4. Click **Activate** to allow operations

### Managing SSL Domains

1. Go to **Shops** → **SSL Domains**
2. To add domain:
   - Click **Add Domain**
   - Enter domain name
   - Choose SSL certificate type
   - Click **Generate**
3. To renew:
   - Click **Renew** on existing domain
   - System updates certificate

### Deactivating a Shop

If a shop violates policies:

1. Go to **Shops** → Find shop
2. Click **Deactivate**
3. Provide reason for records
4. Existing listings are unpublished

## Listing Moderation

### Review Pending Listings

1. Go to **Moderation** → **Pending Listings**
2. Click on listing to review:
   - Title, description, images
   - Category and pricing
   - Shop owner information
   - Any reported issues

### Approving Listings

**To approve** a listing:

1. Click the listing
2. Review details carefully
3. Click **Approve**
4. Listing becomes visible to users

### Rejecting Listings

**To reject** if it violates policies:

1. Click the listing
2. Click **Reject**
3. Provide rejection reason
4. Shop owner receives notification
5. They can revise and resubmit

### Flagging Suspicious Content

1. Click the listing
2. Click **Flag for Review**
3. Add details about concern
4. Item goes to review queue
5. Report reviewer investigates

### Featuring Listings

Promote high-quality listings:

1. Click the listing
2. Click **Feature Listing**
3. Can feature multiple listings
4. Featured items get prominent placement

## Transaction Management

### Viewing Transactions

1. Go to **Transactions**
2. See all financial activity:
   - Transaction ID
   - Buyer and seller
   - Amount and status
   - Timestamp

### Processing Refunds

If customer disputes or merchant agrees:

1. Go to **Transactions**
2. Find the transaction
3. Click **Refund**
4. Enter refund amount (full or partial)
5. Add reason/notes
6. Confirm refund

Amount is returned to buyer's account.

### Investigating Disputes

1. Go to **Moderation** → **Disputes**
2. Review evidence from both parties:
   - Messages between buyer/seller
   - Proof of payment/delivery
   - Photos or documentation
3. Make decision: Buyer wins, Seller wins, or Partial refund
4. Document decision with explanation

## Categories & Tags

### Creating Categories

1. Go to **Categories** → **Add Category**
2. Fill in:
   - **Name**: Category title
   - **Description**: What items go here
   - **Icon**: Optional (for display)
3. Click **Create**

### Managing Categories

1. Go to **Categories**
2. To edit: Click category name
3. To delete: Click **Delete** (only if no listings)
4. To organize: Drag to reorder

## Themes & Appearance

### Activating Themes

1. Go to **Theme Management**
2. See list of available themes
3. Click **Activate** on desired theme
4. Changes apply immediately to all users

### Creating Custom Theme

1. Go to **Theme Management** → **Create Theme**
2. Upload custom CSS or configure:
   - Primary color
   - Background color
   - Font family
3. Preview changes
4. Click **Save & Activate**

### Publishing for Users

1. Go to **Theme Management**
2. Click **Publish** on theme
3. Theme appears in user theme switcher
4. Users can choose to apply it

## Reporting & Analytics

### Dashboard Metrics

Main dashboard shows:
- New users this period
- Active shops count
- Pending items
- Recent transactions
- Top sellers
- Activity heat map

### Running Reports

1. Go to **Analytics** → **Reports**
2. Select report type:
   - User growth
   - Shop activity
   - Transaction volume
   - Category performance
3. Choose date range
4. Click **Generate**

### Exporting Data

1. Go to any list page (Users, Shops, Listings, etc.)
2. Click **Export to CSV**
3. Optional: Choose fields to include
4. File downloads to your computer

### Viewing Audit Logs

Complete history of all admin actions:

1. Go to **Audit Logs**
2. See what changed, who changed it, and when
3. Click entry for before/after details
4. Export for external audit

## Announcements

### Creating Announcements

1. Go to **Announcements** → **New**
2. Fill in:
   - **Title**: Headline (optional)
   - **Message**: Content (can include HTML)
   - **Visibility**: Who sees it (Everyone, Admins only, Specific roles)
   - **Style**: Info, Warning, Success, or Danger
   - **Display dates**: When to show
3. Click **Create**

### Managing Announcements

1. Go to **Announcements**
2. To edit: Click announcement
3. To disable: Uncheck **Active**
4. To delete: Click **Delete**

Admins see announcements on dashboard. Users see on applicable pages.

## Help & Documentation

### Getting Help

1. Click **?** icon (Help) in top navigation
2. Search for topic
3. View documentation and FAQ
4. Contact support if needed

### Using Global Search

1. Use search box in top navigation
2. Type 2+ characters to search:
   - Users by name/email
   - Shops by name/owner
   - Listings by title
   - Transactions
   - Audit logs
3. Click result to jump to detail page

## Common Tasks

### Adding Multiple Users

1. Go to **Users**
2. Click **Import Users**
3. Upload CSV with columns: username, email, password (optional)
4. Review preview
5. Click **Import**

### Bulk Approving Listings

1. Go to **Moderation** → **Pending**
2. Check boxes next to listings
3. Click **Bulk Approve**
4. Reason is optional
5. All selected listings are approved

### Banning a User

1. Go to **Users** → Find user
2. Click **More** → **Ban User**
3. Provide reason for records
4. User cannot log in or access platform

### Unbanning a User

1. Go to **Users** → **Banned Users**
2. Find the user
3. Click **Unban**
4. User regains access

## Troubleshooting

### Can't access admin panel?

- Verify username and password
- Check if your account is suspended
- Contact admin if forgotten password
- Clear browser cache/cookies

### Listing doesn't show after approval?

- Check shop is active (not deactivated)
- Verify listing details are complete
- Check category exists
- Wait a few minutes for cache refresh

### Refund not received?

- Check transaction ID is correct
- Verify refund was processed (check audit logs)
- Allow 24-48 hours for payment processing
- Contact payment provider if needed

### Performance issues?

- Clear browser cache
- Try different browser
- Use hardwired internet connection
- Contact support with details

## Tips & Best Practices

### Moderation Best Practices

✓ Always leave detailed notes for decisions
✓ Be consistent with policy application
✓ Review flagged items within 24 hours
✓ Communicate clearly with users about issues
✓ Document unusual situations

### Security Best Practices

✓ Change password every 90 days
✓ Never share admin credentials
✓ Log out when leaving workstation
✓ Don't give unnecessary permissions
✓ Report suspicious activity

### Performance Tips

✓ Use filters to narrow list views
✓ Export large datasets instead of viewing
✓ Avoid opening multiple detail pages
✓ Close unused browser tabs
✓ Use keyboard shortcuts for common tasks

## Keyboard Shortcuts

- `Ctrl + K` or `Cmd + K`: Open global search
- `Ctrl + /`: Open help
- `Escape`: Close dialogs/modals
- `Enter`: Submit forms
- `Tab`: Move between form fields

## Getting Support

### For Technical Issues

1. Check **Help** documentation first
2. Review **Audit Logs** for error context
3. Contact your admin or support team
4. Provide:
   - What you were trying to do
   - Error message received
   - Timestamp
   - Your user ID

### For Feature Requests

1. Contact your admin team
2. Describe the feature and use case
3. Suggest how it should work
4. Provide examples if possible

## Account Settings

### Changing Your Password

1. Click your username (top right)
2. Click **Settings**
3. Click **Change Password**
4. Enter current password
5. Enter new password (must meet requirements)
6. Confirm new password
7. Click **Update**

### Configuring Notifications

1. Go to **Settings** → **Notifications**
2. Choose what notifications to receive:
   - New listings pending review
   - User reports/disputes
   - Transaction issues
   - System alerts
3. Save preferences

### Viewing Your Activity

1. Go to **Audit Logs**
2. Filter by your username
3. See everything you've done
4. Review for any unauthorized actions

---

**Last Updated:** May 2026
**Version:** 1.0
**Support:** admin-support@yourdomain.com
