"""
Shop cache utilities for 72-hour incomplete shop persistence.
Allows users to save shop data without completing setup immediately.
"""

from django.core.cache import cache
from django.contrib.auth import get_user_model
import json

User = get_user_model()


def cache_incomplete_shop(user_id, shop_data, ttl=259200):
    """
    Cache incomplete shop data for 72 hours (259200 seconds).
    
    Args:
        user_id: User ID to associate with the shop data
        shop_data: Dict with shop form data (name, description, category, location, etc.)
        ttl: Time to live in seconds (default 72 hours)
    
    Returns:
        cache_key: The cache key where data is stored
    """
    cache_key = f"incomplete_shop_{user_id}"
    
    # Ensure shop_data is JSON serializable
    if isinstance(shop_data, dict):
        cache.set(cache_key, shop_data, ttl)
    
    return cache_key


def get_incomplete_shop(user_id):
    """
    Retrieve cached incomplete shop data.
    
    Args:
        user_id: User ID to look up
    
    Returns:
        dict or None: Cached shop data or None if not found/expired
    """
    cache_key = f"incomplete_shop_{user_id}"
    return cache.get(cache_key)


def has_incomplete_shop(user_id):
    """
    Check if user has incomplete shop cached.
    
    Args:
        user_id: User ID to check
    
    Returns:
        bool: True if incomplete shop exists and hasn't expired
    """
    return get_incomplete_shop(user_id) is not None


def clear_incomplete_shop(user_id):
    """
    Clear cached incomplete shop data.
    
    Args:
        user_id: User ID to clear
    
    Returns:
        bool: True if cache key was deleted
    """
    cache_key = f"incomplete_shop_{user_id}"
    cache.delete(cache_key)
    return True


def cache_shop_progress(user_id, progress_data):
    """
    Cache shop creation progress (which step user is on, validation errors, etc).
    
    Args:
        user_id: User ID
        progress_data: Dict with progress info (current_step, errors, etc.)
    
    Returns:
        cache_key: The cache key where data is stored
    """
    cache_key = f"shop_progress_{user_id}"
    cache.set(cache_key, progress_data, 259200)  # 72 hours
    return cache_key


def get_shop_progress(user_id):
    """
    Retrieve shop creation progress.
    
    Args:
        user_id: User ID
    
    Returns:
        dict or None: Progress data or None if not found
    """
    cache_key = f"shop_progress_{user_id}"
    return cache.get(cache_key)


def cache_shop_resume_link(user_id, shop_id, ttl=259200):
    """
    Cache a resume link for incomplete shops.
    When user returns, they can resume their incomplete shop creation.
    
    Args:
        user_id: User ID
        shop_id: Shop ID that was partially created
        ttl: Time to live in seconds
    
    Returns:
        resume_token: Token to resume shop creation
    """
    import uuid
    resume_token = str(uuid.uuid4())
    cache_key = f"shop_resume_{resume_token}"
    cache.set(cache_key, {'user_id': user_id, 'shop_id': shop_id}, ttl)
    return resume_token


def get_shop_resume_data(resume_token):
    """
    Get resume data from token.
    
    Args:
        resume_token: Token returned from cache_shop_resume_link
    
    Returns:
        dict or None: Resume data with user_id and shop_id
    """
    cache_key = f"shop_resume_{resume_token}"
    return cache.get(cache_key)
