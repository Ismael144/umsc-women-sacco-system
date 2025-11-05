from django.utils import timezone
from .models import ActivityLog, User, Sacco, Region


def log_activity(user, action, model_name, object_id=None, object_name="", description="", 
                ip_address=None, user_agent="", sacco=None, region=None):
    """
    Log user activity in the system
    
    Args:
        user: User instance performing the action
        action: Action type (create, update, delete, view, etc.)
        model_name: Name of the model being acted upon
        object_id: ID of the object being acted upon
        object_name: Human readable name of the object
        description: Detailed description of the activity
        ip_address: IP address of the user
        user_agent: User agent string
        sacco: Sacco instance (if applicable)
        region: Region instance (if applicable)
    """
    try:
        # Determine sacco and region if not provided
        if not sacco and hasattr(user, 'sacco') and user.sacco:
            sacco = user.sacco
        if not region and hasattr(user, 'region') and user.region:
            region = user.region
        
        ActivityLog.objects.create(
            user=user,
            action=action,
            model_name=model_name,
            object_id=object_id,
            object_name=object_name,
            description=description,
            ip_address=ip_address,
            user_agent=user_agent,
            sacco=sacco,
            region=region
        )
    except Exception as e:
        # Log the error but don't break the main functionality
        print(f"Error logging activity: {e}")


def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_user_agent(request):
    """Get user agent from request"""
    return request.META.get('HTTP_USER_AGENT', '')





