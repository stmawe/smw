"""Custom debug error pages with modern styling."""

import traceback
import sys
from django.shortcuts import render
from django.conf import settings
from django.http import JsonResponse


def custom_error_view(request, error_code=500, exception=None):
    """
    Custom error view with modern debug page.
    """
    error_messages = {
        400: {
            'title': 'Bad Request',
            'message': 'The request could not be understood by the server.',
            'icon': 'exclamation-triangle',
            'color': 'warning',
        },
        403: {
            'title': 'Access Forbidden',
            'message': 'You do not have permission to access this resource.',
            'icon': 'lock',
            'color': 'danger',
        },
        404: {
            'title': 'Page Not Found',
            'message': 'The requested resource could not be found on this server.',
            'icon': 'question-circle',
            'color': 'info',
        },
        500: {
            'title': 'Internal Server Error',
            'message': 'Something went wrong on the server.',
            'icon': 'exclamation-circle',
            'color': 'danger',
        },
        503: {
            'title': 'Service Unavailable',
            'message': 'The server is currently unavailable.',
            'icon': 'cloud-slash',
            'color': 'danger',
        },
    }
    
    error_info = error_messages.get(error_code, error_messages[500])
    
    context = {
        'error_code': error_code,
        'error_title': error_info['title'],
        'error_message': error_info['message'],
        'error_icon': error_info['icon'],
        'error_color': error_info['color'],
        'exception': exception,
        'debug': settings.DEBUG,
    }
    
    # Add debug information if DEBUG is True
    if settings.DEBUG and exception:
        context['exception_type'] = type(exception).__name__
        context['exception_message'] = str(exception)
        context['traceback'] = traceback.format_exc()
        context['exc_info'] = sys.exc_info()
    
    return render(request, 'errors/debug_error.html', context, status=error_code)


def custom_404_view(request, exception=None):
    """Handle 404 errors."""
    return custom_error_view(request, 404, exception)


def custom_500_view(request):
    """Handle 500 errors."""
    try:
        exception = sys.exc_info()[1]
    except:
        exception = None
    return custom_error_view(request, 500, exception)


def custom_403_view(request, reason=""):
    """Handle 403 errors."""
    return custom_error_view(request, 403)


def custom_400_view(request, reason="", exception=None):
    """Handle 400 errors."""
    return custom_error_view(request, 400, exception)
