"""
Admin announcement and banner system.
Allows admins to create, manage, and display announcements to users and admins.
"""

from django.db import models
from django.utils import timezone
from django.template.loader import render_to_string


class AdminAnnouncement(models.Model):
    """Model for admin announcements and banners."""
    
    VISIBILITY_CHOICES = [
        ('admins', 'Admins Only'),
        ('users', 'Users Only'),
        ('all', 'All Users and Admins'),
        ('specific_roles', 'Specific Roles'),
    ]
    
    STYLE_CHOICES = [
        ('info', 'Info (Blue)'),
        ('success', 'Success (Green)'),
        ('warning', 'Warning (Yellow)'),
        ('danger', 'Danger (Red)'),
    ]
    
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=200)
    message = models.TextField()
    style = models.CharField(max_length=20, choices=STYLE_CHOICES, default='info')
    visibility = models.CharField(max_length=20, choices=VISIBILITY_CHOICES, default='all')
    target_roles = models.JSONField(default=list, blank=True, help_text='Roles to show announcement to (if specific_roles selected)')
    
    created_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, related_name='announcements_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    start_date = models.DateTimeField(help_text='When to start showing announcement')
    end_date = models.DateTimeField(help_text='When to stop showing announcement')
    
    is_active = models.BooleanField(default=True)
    show_close_button = models.BooleanField(default=True, help_text='Allow users to dismiss announcement')
    priority = models.IntegerField(default=0, help_text='Higher priority shows first')
    
    class Meta:
        ordering = ['-priority', '-created_at']
        verbose_name = 'Admin Announcement'
        verbose_name_plural = 'Admin Announcements'
    
    def __str__(self):
        return f"{self.title} ({self.get_visibility_display()})"
    
    def is_currently_active(self):
        """Check if announcement should currently be displayed."""
        now = timezone.now()
        return (
            self.is_active and
            self.start_date <= now <= self.end_date
        )
    
    def can_user_see(self, user):
        """Check if user can see this announcement."""
        if not self.is_currently_active():
            return False
        
        if self.visibility == 'all':
            return True
        elif self.visibility == 'admins':
            return user.is_staff or user.is_superuser
        elif self.visibility == 'users':
            return not (user.is_staff or user.is_superuser)
        elif self.visibility == 'specific_roles':
            if user.is_staff:
                # Check if user's admin role is in target roles
                from app.admin_permissions import AdminRole
                user_role = AdminRole.get_user_role(user)
                return user_role.value in self.target_roles
            return False
        
        return False


class AnnouncementService:
    """Service for managing announcements."""
    
    @staticmethod
    def get_active_announcements(user=None):
        """Get currently active announcements visible to user."""
        announcements = AdminAnnouncement.objects.filter(is_active=True)
        
        now = timezone.now()
        announcements = announcements.filter(
            start_date__lte=now,
            end_date__gte=now
        )
        
        if user:
            announcements = [
                a for a in announcements
                if a.can_user_see(user)
            ]
        
        return announcements.order_by('-priority', '-created_at')
    
    @staticmethod
    def create_announcement(title, message, visibility='all', style='info', 
                          start_date=None, end_date=None, created_by=None, target_roles=None):
        """Create a new announcement."""
        if start_date is None:
            start_date = timezone.now()
        if end_date is None:
            end_date = timezone.now() + timezone.timedelta(days=7)
        
        announcement = AdminAnnouncement.objects.create(
            title=title,
            message=message,
            visibility=visibility,
            style=style,
            start_date=start_date,
            end_date=end_date,
            created_by=created_by,
            target_roles=target_roles or []
        )
        
        return announcement
    
    @staticmethod
    def dismiss_announcement(user, announcement_id):
        """Mark announcement as dismissed for user (client-side via localStorage)."""
        pass  # Handled client-side
    
    @staticmethod
    def get_admin_announcements():
        """Get announcements visible to admin users."""
        announcements = AdminAnnouncement.objects.filter(
            is_active=True,
            visibility__in=['admins', 'all', 'specific_roles']
        )
        
        now = timezone.now()
        return announcements.filter(
            start_date__lte=now,
            end_date__gte=now
        ).order_by('-priority', '-created_at')


def get_announcements_template():
    """Return template for rendering announcements."""
    return """
    {% load static %}
    <div id="announcements-container">
        {% for announcement in announcements %}
        <div class="alert alert-{{ announcement.get_style_display|lower }} alert-dismissible fade show mb-3" 
             role="alert"
             data-announcement-id="{{ announcement.id }}"
             data-dismissible="{% if announcement.show_close_button %}true{% else %}false{% endif %}">
            <div class="d-flex align-items-start">
                <div class="flex-grow-1">
                    {% if announcement.title %}
                    <strong>{{ announcement.title }}</strong><br>
                    {% endif %}
                    {{ announcement.message|safe }}
                </div>
                {% if announcement.show_close_button %}
                <button type="button" class="btn-close ms-2" 
                        data-bs-dismiss="alert" 
                        aria-label="Close"></button>
                {% endif %}
            </div>
        </div>
        {% endfor %}
    </div>
    
    <script>
    (function() {
        // Store dismissed announcements in localStorage
        document.addEventListener('DOMContentLoaded', function() {
            const dismissed = JSON.parse(localStorage.getItem('dismissedAnnouncements') || '[]');
            
            document.querySelectorAll('[data-announcement-id]').forEach(el => {
                const id = el.getAttribute('data-announcement-id');
                if (dismissed.includes(parseInt(id))) {
                    el.style.display = 'none';
                }
            });
            
            // Handle close button
            document.querySelectorAll('[data-bs-dismiss="alert"][data-announcement-id]').forEach(btn => {
                btn.addEventListener('click', function() {
                    const announcement = this.closest('[data-announcement-id]');
                    const id = announcement.getAttribute('data-announcement-id');
                    dismissed.push(parseInt(id));
                    localStorage.setItem('dismissedAnnouncements', JSON.stringify(dismissed));
                });
            });
        });
    })();
    </script>
    """


def get_announcements_management_views():
    """Return view functions for managing announcements."""
    return """
    from django.shortcuts import render, redirect, get_object_or_404
    from django.views.decorators.http import require_http_methods
    from app.admin_permissions import AdminPermission
    from app.admin_utils import permission_required, log_admin_action
    
    @require_http_methods(["GET"])
    @permission_required(AdminPermission.VIEW_AUDIT_LOGS)
    def announcements_list(request):
        '''List all announcements.'''
        announcements = AdminAnnouncement.objects.all().order_by('-created_at')
        
        context = {
            'announcements': announcements,
            'title': 'Announcements',
        }
        return render(request, 'admin/announcements.html', context)
    
    @require_http_methods(["GET", "POST"])
    @permission_required(AdminPermission.CREATE_USER)
    def announcements_create(request):
        '''Create new announcement.'''
        if request.method == 'POST':
            form = AnnouncementForm(request.POST)
            if form.is_valid():
                announcement = form.save(commit=False)
                announcement.created_by = request.user
                announcement.save()
                
                log_admin_action(
                    request,
                    'CREATE_ANNOUNCEMENT',
                    'AdminAnnouncement',
                    announcement.id,
                    'success'
                )
                
                return redirect('announcements_list')
        else:
            form = AnnouncementForm()
        
        context = {
            'form': form,
            'title': 'Create Announcement',
        }
        return render(request, 'admin/announcements_form.html', context)
    
    @require_http_methods(["GET", "POST"])
    @permission_required(AdminPermission.EDIT_USER)
    def announcements_edit(request, pk):
        '''Edit announcement.'''
        announcement = get_object_or_404(AdminAnnouncement, pk=pk)
        
        if request.method == 'POST':
            form = AnnouncementForm(request.POST, instance=announcement)
            if form.is_valid():
                announcement = form.save()
                
                log_admin_action(
                    request,
                    'UPDATE_ANNOUNCEMENT',
                    'AdminAnnouncement',
                    announcement.id,
                    'success'
                )
                
                return redirect('announcements_list')
        else:
            form = AnnouncementForm(instance=announcement)
        
        context = {
            'form': form,
            'announcement': announcement,
            'title': f'Edit Announcement: {announcement.title}',
        }
        return render(request, 'admin/announcements_form.html', context)
    
    @require_http_methods(["POST"])
    @permission_required(AdminPermission.DELETE_USER)
    def announcements_delete(request, pk):
        '''Delete announcement.'''
        announcement = get_object_or_404(AdminAnnouncement, pk=pk)
        announcement.delete()
        
        log_admin_action(
            request,
            'DELETE_ANNOUNCEMENT',
            'AdminAnnouncement',
            pk,
            'success'
        )
        
        return redirect('announcements_list')
    """
