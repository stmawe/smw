"""
Pagination optimization and improvements for admin list views.
Implements cursor-based pagination, configurable page sizes, and performance enhancements.
"""

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods


class OptimizedPaginator:
    """Enhanced pagination with cursor support and optimizations."""
    
    DEFAULT_PAGE_SIZE = 50
    MAX_PAGE_SIZE = 100
    
    @staticmethod
    def get_paginated_queryset(queryset, page=1, per_page=None):
        """Get paginated queryset with optimization."""
        if per_page is None:
            per_page = OptimizedPaginator.DEFAULT_PAGE_SIZE
        
        # Enforce max page size
        per_page = min(int(per_page), OptimizedPaginator.MAX_PAGE_SIZE)
        
        try:
            page = int(page)
            if page < 1:
                page = 1
        except (ValueError, TypeError):
            page = 1
        
        paginator = Paginator(queryset, per_page)
        
        try:
            page_obj = paginator.page(page)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages)
        
        return page_obj
    
    @staticmethod
    def get_page_context(page_obj, page_num):
        """Get pagination context for templates."""
        return {
            'page': page_obj,
            'page_number': page_num,
            'has_previous': page_obj.has_previous(),
            'has_next': page_obj.has_next(),
            'previous_page_number': page_obj.previous_page_number() if page_obj.has_previous() else None,
            'next_page_number': page_obj.next_page_number() if page_obj.has_next() else None,
            'total_count': page_obj.paginator.count,
            'total_pages': page_obj.paginator.num_pages,
            'per_page': page_obj.paginator.per_page,
            'page_range': get_smart_page_range(page_obj.paginator, page_num),
        }
    
    @staticmethod
    def get_cursor_pagination_token(last_item):
        """Generate cursor token for cursor-based pagination."""
        import base64
        if not last_item or not hasattr(last_item, 'id'):
            return None
        
        cursor = f"id:{last_item.id}"
        token = base64.b64encode(cursor.encode()).decode()
        return token
    
    @staticmethod
    def get_items_after_cursor(queryset, cursor_token, limit=50):
        """Get items after cursor token."""
        if not cursor_token:
            return queryset[:limit]
        
        try:
            import base64
            cursor_str = base64.b64decode(cursor_token.encode()).decode()
            item_id = cursor_str.split(':')[1]
            
            # Get the item at cursor
            cursor_item = queryset.filter(id=item_id).first()
            if not cursor_item:
                return queryset[:limit]
            
            # Get items after this position
            items = queryset.filter(id__gt=cursor_item.id)[:limit + 1]
            
            # Check if there are more items
            has_more = len(items) > limit
            items = items[:limit]
            
            # Generate next cursor if there are more items
            next_cursor = None
            if has_more and items:
                next_cursor = OptimizedPaginator.get_cursor_pagination_token(items[-1])
            
            return items, next_cursor
        except Exception:
            return queryset[:limit]


def get_smart_page_range(paginator, current_page, window=3):
    """Get smart page range showing current page with context."""
    total_pages = paginator.num_pages
    
    if total_pages <= 10:
        return list(range(1, total_pages + 1))
    
    # Show pages around current page
    start = max(1, current_page - window)
    end = min(total_pages, current_page + window)
    
    pages = list(range(start, end + 1))
    
    # Add first/last pages if not in range
    if start > 1:
        pages = [1, '...'] + pages
    if end < total_pages:
        pages = pages + ['...', total_pages]
    
    return pages


class PaginationTemplate:
    """Template snippets for pagination."""
    
    @staticmethod
    def get_pagination_html():
        """Return template HTML for pagination."""
        return """
        {% if page.has_other_pages %}
        <nav aria-label="Page navigation" class="mt-4">
            <ul class="pagination justify-content-center">
                {% if page.has_previous %}
                <li class="page-item">
                    <a class="page-link" href="?page=1{% for key,value in request.GET.items %}{% if key != 'page' %}&{{ key }}={{ value }}{% endif %}{% endfor %}">
                        <i class="fas fa-chevron-left"></i> First
                    </a>
                </li>
                <li class="page-item">
                    <a class="page-link" href="?page={{ page.previous_page_number }}{% for key,value in request.GET.items %}{% if key != 'page' %}&{{ key }}={{ value }}{% endif %}{% endfor %}">
                        Previous
                    </a>
                </li>
                {% endif %}
                
                {% for page_num in page_range %}
                    {% if page_num == '...' %}
                    <li class="page-item disabled">
                        <span class="page-link">...</span>
                    </li>
                    {% elif page_num == page.number %}
                    <li class="page-item active">
                        <span class="page-link">{{ page_num }}</span>
                    </li>
                    {% else %}
                    <li class="page-item">
                        <a class="page-link" href="?page={{ page_num }}{% for key,value in request.GET.items %}{% if key != 'page' %}&{{ key }}={{ value }}{% endif %}{% endfor %}">
                            {{ page_num }}
                        </a>
                    </li>
                    {% endif %}
                {% endfor %}
                
                {% if page.has_next %}
                <li class="page-item">
                    <a class="page-link" href="?page={{ page.next_page_number }}{% for key,value in request.GET.items %}{% if key != 'page' %}&{{ key }}={{ value }}{% endif %}{% endfor %}">
                        Next
                    </a>
                </li>
                <li class="page-item">
                    <a class="page-link" href="?page={{ paginator.num_pages }}{% for key,value in request.GET.items %}{% if key != 'page' %}&{{ key }}={{ value }}{% endif %}{% endfor %}">
                        Last <i class="fas fa-chevron-right"></i>
                    </a>
                </li>
                {% endif %}
            </ul>
        </nav>
        
        <div class="text-center text-muted small mt-3">
            Page {{ page.number }} of {{ paginator.num_pages }} 
            ({{ paginator.count }} total items)
        </div>
        {% endif %}
        """
    
    @staticmethod
    def get_page_size_selector():
        """Return template for page size dropdown."""
        return """
        <div class="mb-3 d-flex align-items-center">
            <label for="page-size" class="form-label me-2 mb-0">Items per page:</label>
            <select id="page-size" class="form-select" style="width: 120px;">
                <option value="10" {% if per_page == 10 %}selected{% endif %}>10</option>
                <option value="25" {% if per_page == 25 %}selected{% endif %}>25</option>
                <option value="50" {% if per_page == 50 %}selected{% endif %}>50</option>
                <option value="100" {% if per_page == 100 %}selected{% endif %}>100</option>
            </select>
        </div>
        
        <script>
        document.getElementById('page-size').addEventListener('change', function() {
            const url = new URL(window.location);
            url.searchParams.set('per_page', this.value);
            url.searchParams.set('page', '1');  // Reset to first page
            window.location = url.toString();
        });
        </script>
        """
    
    @staticmethod
    def get_jump_to_page():
        """Return template for jump-to-page input."""
        return """
        <div class="mb-3 d-flex align-items-center">
            <label for="jump-page" class="form-label me-2 mb-0">Go to page:</label>
            <input type="number" id="jump-page" class="form-control" min="1" max="{{ paginator.num_pages }}" style="width: 80px;">
            <button class="btn btn-sm btn-outline-primary ms-2">Go</button>
        </div>
        
        <script>
        document.querySelector('[for="jump-page"] + input + button').addEventListener('click', function() {
            const pageNum = document.getElementById('jump-page').value;
            const url = new URL(window.location);
            url.searchParams.set('page', pageNum);
            window.location = url.toString();
        });
        
        document.getElementById('jump-page').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                const url = new URL(window.location);
                url.searchParams.set('page', this.value);
                window.location = url.toString();
            }
        });
        </script>
        """


@require_http_methods(["GET"])
def get_pagination_info(request, total_items, per_page=50):
    """API endpoint to get pagination info."""
    per_page = min(int(request.GET.get('per_page', per_page)), 100)
    page = int(request.GET.get('page', 1))
    
    from math import ceil
    total_pages = ceil(total_items / per_page)
    
    if page > total_pages:
        page = total_pages
    if page < 1:
        page = 1
    
    start_item = (page - 1) * per_page + 1
    end_item = min(page * per_page, total_items)
    
    return JsonResponse({
        'page': page,
        'per_page': per_page,
        'total_items': total_items,
        'total_pages': total_pages,
        'start_item': start_item,
        'end_item': end_item,
        'has_previous': page > 1,
        'has_next': page < total_pages,
        'previous_page': page - 1 if page > 1 else None,
        'next_page': page + 1 if page < total_pages else None,
    })
