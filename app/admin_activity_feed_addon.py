# Activity Feed Views - To be appended to admin_crud_views.py

@login_required
@permission_required(AdminPermission.VIEW_AUDIT_LOGS)
def admin_activity_feed_view(request):
    """Dedicated admin activity feed page."""
    activity = AdminActivityFeed.objects.select_related('admin_user').order_by('-created_at')
    page = int(request.GET.get('page', 1))
    per_page = 100
    total = activity.count()
    activity_page = activity[(page-1)*per_page:page*per_page]
    total_pages = (total + per_page - 1) // per_page
    context = {'activity': activity_page, 'total': total, 'page': page, 'total_pages': total_pages}
    return render(request, 'admin/activity_feed.html', context)


@login_required
@permission_required(AdminPermission.VIEW_AUDIT_LOGS)
def admin_changelog_view(request):
    """Changelog page with detailed change history."""
    logs = AdminAuditLog.objects.select_related('admin_user').order_by('-created_at')
    page = int(request.GET.get('page', 1))
    per_page = 50
    total = logs.count()
    logs_page = logs[(page-1)*per_page:page*per_page]
    total_pages = (total + per_page - 1) // per_page
    context = {'logs': logs_page, 'total': total, 'page': page, 'total_pages': total_pages}
    return render(request, 'admin/changelog.html', context)
