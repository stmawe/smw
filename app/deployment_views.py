"""Deployment and site update admin views."""
import os
import subprocess
import logging
from datetime import datetime
from django.shortcuts import render
from django.http import JsonResponse, HttpResponseForbidden
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.http import require_http_methods
from django.conf import settings

logger = logging.getLogger(__name__)


def is_site_admin(user):
    """Check if user is a site administrator."""
    return user.is_authenticated and user.is_staff and (user.is_superuser or user.groups.filter(name='site_admin').exists())


def get_deployment_log_path():
    """Get deployment log file path."""
    log_dir = os.path.join(settings.BASE_DIR, 'logs', 'deployment')
    os.makedirs(log_dir, exist_ok=True)
    return log_dir


def get_update_script_path():
    """Get path to update_site.sh script."""
    return os.path.join(settings.BASE_DIR, 'scripts', 'update_site.sh')


def read_recent_logs(limit=50):
    """Read recent deployment logs."""
    log_dir = get_deployment_log_path()
    logs = []
    try:
        log_files = sorted(
            [f for f in os.listdir(log_dir) if f.endswith('.log')],
            reverse=True
        )[:limit]
        
        for log_file in log_files:
            log_path = os.path.join(log_dir, log_file)
            try:
                with open(log_path, 'r') as f:
                    content = f.read()
                    logs.append({
                        'filename': log_file,
                        'content': content[:2000],  # Limit to 2000 chars
                        'size': len(content),
                    })
            except Exception as e:
                logger.error(f"Error reading log {log_file}: {e}")
    except Exception as e:
        logger.error(f"Error reading logs directory: {e}")
    
    return logs


@login_required
@user_passes_test(is_site_admin)
@require_http_methods(["GET"])
def deployment_dashboard_view(request):
    """Display deployment dashboard for site admins."""
    context = {
        'page_title': 'Deployment Dashboard',
        'recent_logs': read_recent_logs(10),
        'update_script_exists': os.path.exists(get_update_script_path()),
    }
    return render(request, 'admin/deployment_dashboard.html', context)


@login_required
@user_passes_test(is_site_admin)
@require_http_methods(["POST"])
def trigger_site_update_view(request):
    """Trigger site update via update_site.sh script."""
    try:
        update_script = get_update_script_path()
        
        if not os.path.exists(update_script):
            logger.error(f"Update script not found: {update_script}")
            return JsonResponse({
                'success': False,
                'error': 'Update script not found',
                'timestamp': datetime.now().isoformat(),
            }, status=404)
        
        if not os.access(update_script, os.X_OK):
            logger.error(f"Update script not executable: {update_script}")
            return JsonResponse({
                'success': False,
                'error': 'Update script not executable',
                'timestamp': datetime.now().isoformat(),
            }, status=403)
        
        # Log the update request
        log_dir = get_deployment_log_path()
        log_file = os.path.join(log_dir, f"update-{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}.log")
        
        logger.info(f"Starting site update triggered by {request.user.username}")
        logger.info(f"Log file: {log_file}")
        
        # Execute the update script
        with open(log_file, 'w') as f:
            f.write(f"Update started at {datetime.now()}\n")
            f.write(f"Triggered by: {request.user.username} ({request.user.email})\n")
            f.write(f"User IP: {get_client_ip(request)}\n")
            f.write("-" * 80 + "\n\n")
        
        # Run the script in the background and capture output
        process = subprocess.Popen(
            ['bash', update_script],
            stdout=open(log_file, 'a'),
            stderr=subprocess.STDOUT,
            cwd=settings.BASE_DIR,
        )
        
        # Don't wait for completion - let it run in background
        return JsonResponse({
            'success': True,
            'message': 'Site update started',
            'log_file': os.path.basename(log_file),
            'process_id': process.pid,
            'timestamp': datetime.now().isoformat(),
        })
    
    except Exception as e:
        logger.exception(f"Error triggering site update: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat(),
        }, status=500)


@login_required
@user_passes_test(is_site_admin)
@require_http_methods(["GET"])
def get_deployment_logs_view(request):
    """Get recent deployment logs as JSON."""
    try:
        logs = read_recent_logs(int(request.GET.get('limit', 20)))
        return JsonResponse({
            'success': True,
            'logs': logs,
            'count': len(logs),
        })
    except Exception as e:
        logger.exception(f"Error fetching logs: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e),
        }, status=500)


def get_client_ip(request):
    """Get client IP from request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
