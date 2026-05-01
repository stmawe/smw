"""
Global search functionality for admin panel.
Searches across users, shops, listings, transactions, categories, and more.
"""

from django.db.models import Q, Value
from django.db.models.functions import Concat
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.models import User
from django.db.models import DecimalField, CharField
from django.db.models.functions import Cast
from mydak.models import Shop, Listing, Transaction, Category
from app.models import AdminAuditLog
from app.admin_utils import permission_required
from app.admin_permissions import AdminPermission


class AdminGlobalSearch:
    """Handles global search across admin resources."""
    
    MAX_RESULTS_PER_TYPE = 5
    
    @staticmethod
    def search_users(query):
        """Search users by username, email, name."""
        return User.objects.filter(
            Q(username__icontains=query) |
            Q(email__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query)
        ).values('id', 'username', 'email', 'first_name', 'last_name')[:AdminGlobalSearch.MAX_RESULTS_PER_TYPE]
    
    @staticmethod
    def search_shops(query):
        """Search shops by name, owner."""
        return Shop.objects.filter(
            Q(name__icontains=query) |
            Q(owner__username__icontains=query) |
            Q(owner__email__icontains=query)
        ).select_related('owner').values(
            'id', 'name', 'owner__username', 'is_active'
        )[:AdminGlobalSearch.MAX_RESULTS_PER_TYPE]
    
    @staticmethod
    def search_listings(query):
        """Search listings by title, category."""
        return Listing.objects.filter(
            Q(title__icontains=query) |
            Q(category__name__icontains=query)
        ).select_related('shop', 'category').values(
            'id', 'title', 'shop__name', 'category__name', 'price', 'status'
        )[:AdminGlobalSearch.MAX_RESULTS_PER_TYPE]
    
    @staticmethod
    def search_categories(query):
        """Search categories by name."""
        return Category.objects.filter(
            name__icontains=query
        ).values('id', 'name')[:AdminGlobalSearch.MAX_RESULTS_PER_TYPE]
    
    @staticmethod
    def search_transactions(query):
        """Search transactions by ID, user, shop."""
        return Transaction.objects.filter(
            Q(id__icontains=query) |
            Q(user__username__icontains=query) |
            Q(shop__name__icontains=query)
        ).select_related('user', 'shop').values(
            'id', 'user__username', 'shop__name', 'amount', 'status'
        )[:AdminGlobalSearch.MAX_RESULTS_PER_TYPE]
    
    @staticmethod
    def search_audit_logs(query):
        """Search audit logs by admin, action, resource."""
        return AdminAuditLog.objects.filter(
            Q(admin__username__icontains=query) |
            Q(action__icontains=query) |
            Q(resource_type__icontains=query)
        ).values(
            'id', 'admin__username', 'action', 'resource_type', 'created_at'
        )[:AdminGlobalSearch.MAX_RESULTS_PER_TYPE]
    
    @staticmethod
    def perform_search(query):
        """Perform global search across all resources."""
        if not query or len(query.strip()) < 2:
            return {}
        
        query = query.strip()
        results = {}
        
        try:
            users = list(AdminGlobalSearch.search_users(query))
            if users:
                results['users'] = {
                    'label': 'Users',
                    'icon': 'fa-user',
                    'items': users
                }
        except Exception:
            pass
        
        try:
            shops = list(AdminGlobalSearch.search_shops(query))
            if shops:
                results['shops'] = {
                    'label': 'Shops',
                    'icon': 'fa-store',
                    'items': shops
                }
        except Exception:
            pass
        
        try:
            listings = list(AdminGlobalSearch.search_listings(query))
            if listings:
                results['listings'] = {
                    'label': 'Listings',
                    'icon': 'fa-list',
                    'items': listings
                }
        except Exception:
            pass
        
        try:
            categories = list(AdminGlobalSearch.search_categories(query))
            if categories:
                results['categories'] = {
                    'label': 'Categories',
                    'icon': 'fa-tag',
                    'items': categories
                }
        except Exception:
            pass
        
        try:
            transactions = list(AdminGlobalSearch.search_transactions(query))
            if transactions:
                results['transactions'] = {
                    'label': 'Transactions',
                    'icon': 'fa-credit-card',
                    'items': transactions
                }
        except Exception:
            pass
        
        try:
            audit_logs = list(AdminGlobalSearch.search_audit_logs(query))
            if audit_logs:
                results['audit_logs'] = {
                    'label': 'Audit Logs',
                    'icon': 'fa-history',
                    'items': audit_logs
                }
        except Exception:
            pass
        
        return results


@require_http_methods(["GET"])
@permission_required(AdminPermission.VIEW_USERS)
def global_search_api(request):
    """API endpoint for global search."""
    query = request.GET.get('q', '').strip()
    
    if not query or len(query) < 2:
        return JsonResponse({'error': 'Query must be at least 2 characters'}, status=400)
    
    results = AdminGlobalSearch.perform_search(query)
    
    return JsonResponse({
        'query': query,
        'results': results,
        'total': sum(len(r['items']) for r in results.values())
    })


@require_http_methods(["GET"])
@permission_required(AdminPermission.VIEW_USERS)
def global_search_page(request):
    """Global search page."""
    from django.shortcuts import render
    
    query = request.GET.get('q', '').strip()
    results = {}
    
    if query and len(query) >= 2:
        results = AdminGlobalSearch.perform_search(query)
    
    context = {
        'query': query,
        'results': results,
        'title': f'Search Results: {query}' if query else 'Global Search',
    }
    
    return render(request, 'admin/search.html', context)


def get_global_search_js():
    """Return JavaScript for global search autocomplete."""
    return """
    <script>
    (function() {
        const searchInput = document.getElementById('admin-global-search');
        if (!searchInput) return;
        
        let debounceTimer;
        const resultsContainer = document.getElementById('search-results-dropdown');
        
        searchInput.addEventListener('input', function() {
            clearTimeout(debounceTimer);
            const query = this.value.trim();
            
            if (query.length < 2) {
                if (resultsContainer) resultsContainer.style.display = 'none';
                return;
            }
            
            debounceTimer = setTimeout(function() {
                performSearch(query);
            }, 300);
        });
        
        function performSearch(query) {
            fetch(`/admin/api/search/?q=${encodeURIComponent(query)}`)
                .then(response => response.json())
                .then(data => displayResults(data))
                .catch(error => console.error('Search error:', error));
        }
        
        function displayResults(data) {
            if (!data.results || Object.keys(data.results).length === 0) {
                if (resultsContainer) {
                    resultsContainer.innerHTML = '<div class="p-3 text-muted">No results found</div>';
                    resultsContainer.style.display = 'block';
                }
                return;
            }
            
            let html = '';
            for (const [type, category] of Object.entries(data.results)) {
                html += `
                    <div class="search-category mb-2">
                        <small class="text-muted px-3 py-1 d-block">
                            <i class="fas ${category.icon}"></i> ${category.label}
                        </small>
                `;
                
                for (const item of category.items) {
                    html += buildResultItem(type, item);
                }
                
                html += '</div>';
            }
            
            if (resultsContainer) {
                resultsContainer.innerHTML = html;
                resultsContainer.style.display = 'block';
            }
        }
        
        function buildResultItem(type, item) {
            let url = '#';
            let label = '';
            
            switch(type) {
                case 'users':
                    url = `/admin/users/${item.id}/`;
                    label = item.username;
                    break;
                case 'shops':
                    url = `/admin/shops/${item.id}/`;
                    label = item.name;
                    break;
                case 'listings':
                    url = `/admin/listings/${item.id}/`;
                    label = item.title;
                    break;
                case 'categories':
                    url = `/admin/categories/${item.id}/`;
                    label = item.name;
                    break;
                case 'transactions':
                    url = `/admin/transactions/${item.id}/`;
                    label = `Transaction #${item.id}`;
                    break;
                case 'audit_logs':
                    url = `/admin/audit-logs/${item.id}/`;
                    label = `${item.action} on ${item.resource_type}`;
                    break;
            }
            
            return `
                <a href="${url}" class="dropdown-item">
                    <small>${label}</small>
                </a>
            `;
        }
        
        // Hide dropdown when clicking outside
        document.addEventListener('click', function(e) {
            if (!e.target.closest('#admin-global-search') && !e.target.closest('#search-results-dropdown')) {
                if (resultsContainer) resultsContainer.style.display = 'none';
            }
        });
    })();
    </script>
    """


def get_global_search_html_widget():
    """Return HTML for global search widget."""
    return """
    <div class="position-relative flex-grow-1 mx-2" style="max-width: 400px;">
        <input type="text" 
               id="admin-global-search"
               class="form-control form-control-sm" 
               placeholder="Search admins, users, shops, listings..."
               aria-label="Global search">
        <div id="search-results-dropdown" 
             class="dropdown-menu w-100 mt-1" 
             style="display: none; max-height: 400px; overflow-y: auto;">
            <!-- Results populated by JavaScript -->
        </div>
    </div>
    """
