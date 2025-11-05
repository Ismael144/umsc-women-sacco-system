"""
Middleware for handling user inactivity and automatic logout
"""
from django.utils import timezone
from django.contrib.auth import logout
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse
from .utils import log_activity, get_client_ip, get_user_agent
from datetime import timedelta


class InactivityLogoutMiddleware:
    """
    Middleware to automatically log out users who have been inactive for 30 minutes
    """
    INACTIVITY_TIMEOUT = timedelta(minutes=30)  # 30 minutes
    
    def __init__(self, get_response):
        self.get_response = get_response
        # URLs that should not trigger inactivity checks (e.g., static files, API endpoints)
        self.excluded_paths = [
            '/static/',
            '/media/',
            '/favicon.ico',
            '/admin/jsi18n/',
        ]
    
    def __call__(self, request):
        # Check if user is authenticated
        if request.user.is_authenticated:
            # Skip inactivity check for excluded paths
            if not any(request.path.startswith(path) for path in self.excluded_paths):
                # Check if user has "Remember Me" enabled
                remember_me = request.session.get('remember_me', False)
                
                # Get last activity time from session
                last_activity = request.session.get('last_activity')
                
                if last_activity:
                    # Convert string back to datetime if stored as string
                    if isinstance(last_activity, str):
                        from django.utils.dateparse import parse_datetime
                        last_activity = parse_datetime(last_activity)
                    
                    # Check if inactivity timeout has been exceeded
                    if timezone.now() - last_activity > self.INACTIVITY_TIMEOUT:
                        # User has been inactive for more than 30 minutes
                        # Log the automatic logout BEFORE logout (so we have user context)
                        log_activity(
                            user=request.user,
                            action='logout',
                            model_name='User',
                            object_id=request.user.id,
                            object_name=request.user.username,
                            description=f'User {request.user.username} automatically logged out due to inactivity',
                            ip_address=get_client_ip(request),
                            user_agent=get_user_agent(request)
                        )
                        
                        # Logout the user
                        logout(request)
                        
                        # Redirect to login page with inactivity message
                        return redirect('login?inactive=1')
                
                # Update last activity time
                request.session['last_activity'] = timezone.now().isoformat()
            else:
                # For excluded paths, still update activity if user is authenticated
                # This prevents logout while loading static resources
                if request.user.is_authenticated:
                    request.session['last_activity'] = timezone.now().isoformat()
        else:
            # If user is not authenticated, clear any stale activity data
            if 'last_activity' in request.session:
                del request.session['last_activity']
        
        response = self.get_response(request)
        return response

