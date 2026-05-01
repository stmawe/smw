"""
Admin team management for managing admin users and their roles/permissions.
"""

from django.db import models
from django.contrib.auth.models import User
from app.admin_permissions import AdminRole


class AdminTeam(models.Model):
    """Team/group for organizing admin users."""
    
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    members = models.ManyToManyField(User, related_name='admin_teams')
    
    class Meta:
        verbose_name = 'Admin Team'
        verbose_name_plural = 'Admin Teams'
    
    def __str__(self):
        return self.name


class AdminTeamInvitation(models.Model):
    """Invitation for users to join admin team."""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
    ]
    
    team = models.ForeignKey(AdminTeam, on_delete=models.CASCADE)
    email = models.EmailField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    invited_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    
    class Meta:
        verbose_name = 'Admin Team Invitation'
        verbose_name_plural = 'Admin Team Invitations'
    
    def __str__(self):
        return f"{self.team.name} - {self.email} ({self.status})"


class AdminTeamService:
    """Service for managing admin teams."""
    
    @staticmethod
    def create_team(name, description='', created_by=None):
        """Create new admin team."""
        team = AdminTeam.objects.create(
            name=name,
            description=description
        )
        
        if created_by:
            team.members.add(created_by)
        
        return team
    
    @staticmethod
    def add_member(team, user):
        """Add user to team."""
        team.members.add(user)
    
    @staticmethod
    def remove_member(team, user):
        """Remove user from team."""
        team.members.remove(user)
    
    @staticmethod
    def get_team_members(team):
        """Get all members of team."""
        return team.members.all()
    
    @staticmethod
    def invite_user(team, email, invited_by):
        """Invite user to team by email."""
        from django.utils import timezone
        from datetime import timedelta
        
        expires_at = timezone.now() + timedelta(days=7)
        
        invitation = AdminTeamInvitation.objects.create(
            team=team,
            email=email,
            invited_by=invited_by,
            expires_at=expires_at
        )
        
        return invitation
    
    @staticmethod
    def accept_invitation(invitation):
        """Accept team invitation."""
        try:
            user = User.objects.get(email=invitation.email)
            invitation.team.members.add(user)
            invitation.status = 'accepted'
            invitation.save()
            return True
        except User.DoesNotExist:
            return False
    
    @staticmethod
    def decline_invitation(invitation):
        """Decline team invitation."""
        invitation.status = 'declined'
        invitation.save()


def get_team_management_views():
    """Return view functions for team management."""
    return """
    from django.shortcuts import render, redirect, get_object_or_404
    from django.views.decorators.http import require_http_methods
    from app.admin_permissions import AdminPermission
    from app.admin_utils import permission_required, log_admin_action
    
    @require_http_methods(["GET"])
    @permission_required(AdminPermission.VIEW_USERS)
    def teams_list(request):
        '''List all admin teams.'''
        teams = AdminTeam.objects.all()
        
        context = {
            'teams': teams,
            'title': 'Admin Teams',
        }
        return render(request, 'admin/teams_list.html', context)
    
    @require_http_methods(["GET", "POST"])
    @permission_required(AdminPermission.CREATE_USER)
    def teams_create(request):
        '''Create new admin team.'''
        if request.method == 'POST':
            name = request.POST.get('name')
            description = request.POST.get('description', '')
            
            team = AdminTeamService.create_team(name, description, request.user)
            
            log_admin_action(
                request,
                'CREATE_TEAM',
                'AdminTeam',
                team.id,
                'success'
            )
            
            return redirect('teams_detail', pk=team.id)
        
        context = {'title': 'Create Team'}
        return render(request, 'admin/teams_form.html', context)
    
    @require_http_methods(["GET"])
    @permission_required(AdminPermission.VIEW_USERS)
    def teams_detail(request, pk):
        '''View team details.'''
        team = get_object_or_404(AdminTeam, pk=pk)
        members = team.members.all()
        invitations = AdminTeamInvitation.objects.filter(team=team)
        
        context = {
            'team': team,
            'members': members,
            'invitations': invitations,
            'title': f'Team: {team.name}',
        }
        return render(request, 'admin/teams_detail.html', context)
    
    @require_http_methods(["POST"])
    @permission_required(AdminPermission.EDIT_USER)
    def teams_add_member(request, pk):
        '''Add member to team.'''
        team = get_object_or_404(AdminTeam, pk=pk)
        user_id = request.POST.get('user_id')
        
        try:
            user = User.objects.get(id=user_id)
            AdminTeamService.add_member(team, user)
            
            log_admin_action(
                request,
                'ADD_TEAM_MEMBER',
                'AdminTeam',
                team.id,
                'success'
            )
        except User.DoesNotExist:
            pass
        
        return redirect('teams_detail', pk=team.id)
    
    @require_http_methods(["POST"])
    @permission_required(AdminPermission.EDIT_USER)
    def teams_remove_member(request, pk, member_id):
        '''Remove member from team.'''
        team = get_object_or_404(AdminTeam, pk=pk)
        user = get_object_or_404(User, id=member_id)
        
        AdminTeamService.remove_member(team, user)
        
        log_admin_action(
            request,
            'REMOVE_TEAM_MEMBER',
            'AdminTeam',
            team.id,
            'success'
        )
        
        return redirect('teams_detail', pk=team.id)
    
    @require_http_methods(["POST"])
    @permission_required(AdminPermission.CREATE_USER)
    def teams_invite_user(request, pk):
        '''Invite user to team.'''
        team = get_object_or_404(AdminTeam, pk=pk)
        email = request.POST.get('email')
        
        invitation = AdminTeamService.invite_user(team, email, request.user)
        
        log_admin_action(
            request,
            'INVITE_TO_TEAM',
            'AdminTeam',
            team.id,
            'success'
        )
        
        return redirect('teams_detail', pk=team.id)
    """
