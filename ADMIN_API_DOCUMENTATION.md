# Admin Panel API Documentation

## Overview

The Admin Panel provides RESTful APIs for managing platform resources including users, shops, listings, transactions, themes, and more. All API endpoints require authentication and role-based permissions.

## Base URL

```
https://yourdomain.com/admin/api/
```

## Authentication

All API requests require authentication. Include your session cookie or API token in the request headers:

```
Authorization: Bearer <your-api-token>
```

Or use session-based auth (default):

```
Cookie: sessionid=<session-id>
```

## Rate Limiting

- Default: 100 requests/minute per user
- Burst: Up to 200 requests/minute
- Response includes rate limit headers:
  - `X-RateLimit-Limit`: Maximum requests
  - `X-RateLimit-Remaining`: Remaining requests
  - `X-RateLimit-Reset`: Reset time (Unix timestamp)

## Response Format

All responses are JSON:

```json
{
  "success": true,
  "data": {},
  "message": "Operation successful",
  "timestamp": "2026-05-01T16:45:00Z"
}
```

Error responses:

```json
{
  "success": false,
  "error": "Error code",
  "message": "Error description",
  "details": {}
}
```

## Common HTTP Status Codes

- `200 OK`: Success
- `201 Created`: Resource created
- `204 No Content`: Success with no content
- `400 Bad Request`: Invalid parameters
- `401 Unauthorized`: Missing/invalid authentication
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `409 Conflict`: Resource conflict/duplicate
- `500 Server Error`: Server error

## Pagination

List endpoints support pagination:

```
GET /admin/api/users/?page=1&per_page=50
```

Response includes pagination info:

```json
{
  "success": true,
  "data": [...],
  "pagination": {
    "page": 1,
    "per_page": 50,
    "total": 1000,
    "total_pages": 20
  }
}
```

## Users API

### List Users

```
GET /admin/api/users/
```

**Query Parameters:**
- `page`: Page number (default: 1)
- `per_page`: Results per page (default: 50, max: 100)
- `search`: Search by username, email, name
- `is_active`: Filter by status (true/false)
- `is_staff`: Filter by admin status

**Example:**

```bash
curl -H "Authorization: Bearer token" \
  "https://yourdomain.com/admin/api/users/?search=john&is_active=true"
```

**Response:**

```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "username": "john_doe",
      "email": "john@example.com",
      "first_name": "John",
      "last_name": "Doe",
      "is_active": true,
      "is_staff": true,
      "date_joined": "2026-01-01T00:00:00Z"
    }
  ],
  "pagination": {...}
}
```

### Get User

```
GET /admin/api/users/<id>/
```

### Update User

```
POST /admin/api/users/<id>/update/
```

**Request Body:**

```json
{
  "email": "newemail@example.com",
  "first_name": "Jane",
  "is_active": true
}
```

### Get User Permissions

```
GET /admin/api/users/<id>/permissions/
```

**Response:**

```json
{
  "success": true,
  "data": {
    "user": {...},
    "role": "admin",
    "permissions": ["view_users", "edit_users", "create_users", ...]
  }
}
```

## Shops API

### List Shops

```
GET /admin/api/shops/
```

**Query Parameters:**
- `page`: Page number
- `per_page`: Results per page
- `search`: Search by shop name
- `is_active`: Filter by status
- `owner__username`: Filter by owner

**Example:**

```bash
curl -H "Authorization: Bearer token" \
  "https://yourdomain.com/admin/api/shops/?search=amazon"
```

### Get Shop

```
GET /admin/api/shops/<id>/
```

### Update Shop

```
POST /admin/api/shops/<id>/update/
```

**Request Body:**

```json
{
  "name": "New Shop Name",
  "is_active": true,
  "description": "Shop description"
}
```

## Listings API

### List Listings

```
GET /admin/api/listings/
```

**Query Parameters:**
- `page`: Page number
- `per_page`: Results per page
- `search`: Search by title
- `status`: Filter by status (pending, approved, rejected, featured)
- `shop_id`: Filter by shop

### Take Action on Listing

```
POST /admin/api/listings/<id>/action/
```

**Request Body:**

```json
{
  "action": "approve",
  "reason": "Approved by admin"
}
```

**Possible actions:**
- `approve`: Approve listing
- `reject`: Reject listing
- `feature`: Mark as featured
- `unflag`: Remove flag

## Transactions API

### List Transactions

```
GET /admin/api/transactions/
```

**Query Parameters:**
- `page`: Page number
- `per_page`: Results per page
- `status`: Filter by status (pending, completed, failed)
- `start_date`: Filter from date (ISO 8601)
- `end_date`: Filter to date (ISO 8601)

### Process Refund

```
POST /admin/api/transactions/<id>/refund/
```

**Request Body:**

```json
{
  "reason": "Customer requested refund",
  "amount": 100.00
}
```

## Audit Logs API

### List Audit Logs

```
GET /admin/api/audit-logs/
```

**Query Parameters:**
- `page`: Page number
- `per_page`: Results per page
- `action`: Filter by action type
- `resource_type`: Filter by resource type
- `admin__username`: Filter by admin
- `start_date`: From date
- `end_date`: To date

### Get Audit Log Detail

```
GET /admin/api/audit-logs/<id>/
```

**Response:**

```json
{
  "success": true,
  "data": {
    "id": 1,
    "admin": "admin_username",
    "action": "UPDATE_USER",
    "resource_type": "User",
    "resource_id": 123,
    "status": "success",
    "before": {
      "email": "old@example.com",
      "is_active": true
    },
    "after": {
      "email": "new@example.com",
      "is_active": false
    },
    "created_at": "2026-05-01T16:45:00Z"
  }
}
```

## Analytics API

### Get Analytics Summary

```
GET /admin/api/analytics/summary/
```

**Query Parameters:**
- `days`: Number of days to report (default: 30)

**Response:**

```json
{
  "success": true,
  "data": {
    "period": {
      "start_date": "2026-04-01T00:00:00Z",
      "end_date": "2026-05-01T00:00:00Z",
      "days": 30
    },
    "users": {
      "new_users": 42,
      "total_active": 1250
    },
    "shops": {
      "new_shops": 8,
      "total_active": 320
    },
    "listings": {
      "new_listings": 245,
      "total_featured": 78
    },
    "transactions": {
      "count": 1520,
      "total_amount": 45230.50
    }
  }
}
```

### Get Top Sellers

```
GET /admin/api/analytics/top-sellers/
```

**Query Parameters:**
- `limit`: Number of results (default: 10, max: 100)
- `days`: Days to analyze (default: 30)

## Global Search API

### Search All Resources

```
GET /admin/api/search/?q=<query>
```

**Query Parameters:**
- `q`: Search query (minimum 2 characters)

**Response:**

```json
{
  "success": true,
  "query": "search term",
  "results": {
    "users": {
      "label": "Users",
      "icon": "fa-user",
      "items": [...]
    },
    "shops": {...},
    "listings": {...}
  },
  "total": 15
}
```

## Activity Feed API

### Get Activity Feed

```
GET /admin/api/activity-feed/
```

**Query Parameters:**
- `page`: Page number
- `per_page`: Results per page
- `severity`: Filter by severity (low, medium, high, critical)

## Data Export API

### Export Users to CSV

```
GET /admin/api/export/users/
```

**Query Parameters:**
- All filtering options from list API (search, is_active, etc.)

**Response:** CSV file attachment

### Export Transactions to CSV

```
GET /admin/api/export/transactions/
```

### Export Analytics Report

```
GET /admin/api/export/analytics/
```

**Query Parameters:**
- `days`: Number of days (default: 30)

**Response:** JSON file attachment

## Error Handling

All errors follow the standard format:

```json
{
  "success": false,
  "error": "PERMISSION_DENIED",
  "message": "You do not have permission to access this resource",
  "details": {
    "required_permission": "view_users",
    "your_role": "support"
  }
}
```

## Common Error Codes

- `INVALID_REQUEST`: Invalid request format
- `INVALID_PARAMETER`: Invalid parameter value
- `PERMISSION_DENIED`: Insufficient permissions
- `RESOURCE_NOT_FOUND`: Resource doesn't exist
- `RESOURCE_CONFLICT`: Resource conflict (duplicate, etc.)
- `VALIDATION_ERROR`: Validation failed
- `SERVER_ERROR`: Internal server error

## SDK/Client Libraries

### Python

```python
import requests

client = requests.Session()
client.headers['Authorization'] = 'Bearer token'

# Get users
response = client.get('https://yourdomain.com/admin/api/users/')
users = response.json()['data']

# Update user
client.post('https://yourdomain.com/admin/api/users/1/update/', json={
    'email': 'newemail@example.com'
})
```

### JavaScript

```javascript
const API_URL = 'https://yourdomain.com/admin/api';
const token = 'your-token';

// Get users
fetch(`${API_URL}/users/`, {
  headers: { 'Authorization': `Bearer ${token}` }
})
.then(r => r.json())
.then(data => console.log(data.data));

// Update user
fetch(`${API_URL}/users/1/update/`, {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({ email: 'newemail@example.com' })
})
```

## Rate Limit Headers

Every response includes rate limit information:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 87
X-RateLimit-Reset: 1619885400
```

## Webhook Events (Future)

Subscribe to webhook events for real-time updates:

- `user.created`: New user created
- `user.updated`: User updated
- `shop.approved`: Shop approved
- `listing.rejected`: Listing rejected
- `transaction.completed`: Transaction completed
- `admin.action`: Any admin action

## Support & Issues

For API issues:
1. Check this documentation
2. Review error codes and messages
3. Check Django error logs
4. Contact support team with:
   - Request URL and parameters
   - Response status code
   - Error message
   - Timestamp
   - Your user ID
