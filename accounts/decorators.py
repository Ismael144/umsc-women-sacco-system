from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.http import JsonResponse
from django.core.exceptions import PermissionDenied


def sacco_admin_required(view_func):
    """
    Decorator to ensure user is a Sacco Admin, Regional Admin, or System Admin
    Also checks if sacco admin's sacco is active
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'error': 'Authentication required'}, status=401)
            return redirect('login')
        
        if not (request.user.is_sacco_admin or request.user.is_system_admin or request.user.is_regional_admin):
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'error': 'Admin access required'}, status=403)
            messages.error(request, 'Access denied. Admin privileges required.')
            return redirect('dashboard')
        
        # Check if sacco admin's sacco is active
        if request.user.is_sacco_admin and request.user.sacco:
            if not request.user.sacco.is_active:
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({'error': 'Your Sacco has been deactivated'}, status=403)
                messages.error(request, 'Your Sacco has been deactivated. Please contact your regional administrator.')
                from django.contrib.auth import logout
                logout(request)
                return redirect('login')
        
        return view_func(request, *args, **kwargs)
    return wrapper


def regional_admin_required(view_func):
    """
    Decorator to ensure user is a Regional Admin or System Admin
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'error': 'Authentication required'}, status=401)
            return redirect('login')
        
        if not (request.user.is_regional_admin or request.user.is_system_admin):
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'error': 'Regional Admin access required'}, status=403)
            messages.error(request, 'Access denied. Regional Admin privileges required.')
            return redirect('dashboard')
        
        return view_func(request, *args, **kwargs)
    return wrapper


def system_admin_required(view_func):
    """
    Decorator to ensure user is a System Admin
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'error': 'Authentication required'}, status=401)
            return redirect('login')
        
        if not request.user.is_system_admin:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'error': 'System Admin access required'}, status=403)
            messages.error(request, 'Access denied. System Admin privileges required.')
            return redirect('dashboard')
        
        return view_func(request, *args, **kwargs)
    return wrapper


def admin_or_member_owner_required(view_func):
    """
    Decorator to ensure user is an admin or the owner of the member record
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'error': 'Authentication required'}, status=401)
            return redirect('login')
        
        # Allow admins
        if request.user.is_sacco_admin or request.user.is_regional_admin or request.user.is_system_admin:
            return view_func(request, *args, **kwargs)
        
        # Check if user is a member and owns the record
        member_id = kwargs.get('member_id')
        if member_id:
            try:
                from members.models import Member
                member = Member.objects.get(id=member_id, user_account=request.user)
                return view_func(request, *args, **kwargs)
            except Member.DoesNotExist:
                pass
        
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'error': 'Access denied'}, status=403)
        messages.error(request, 'Access denied. You can only access your own records.')
        return redirect('dashboard')
    return wrapper


def admin_required(view_func):
    """
    Decorator to ensure user is any type of admin (Sacco, Regional, or System)
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'error': 'Authentication required'}, status=401)
            return redirect('login')
        
        if not (request.user.is_sacco_admin or request.user.is_regional_admin or request.user.is_system_admin):
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'error': 'Admin access required'}, status=403)
            messages.error(request, 'Access denied. Admin privileges required.')
            return redirect('dashboard')
        
        return view_func(request, *args, **kwargs)
    return wrapper


def member_search_required(view_func):
    """
    Decorator for member search functionality - Sacco Admin, Regional Admin, or System Admin
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'error': 'Authentication required'}, status=401)
            return redirect('login')
        
        if not (request.user.is_sacco_admin or request.user.is_regional_admin or request.user.is_system_admin):
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'error': 'Access denied'}, status=403)
            messages.error(request, 'Access denied. Admin privileges required for member search.')
            return redirect('dashboard')
        
        return view_func(request, *args, **kwargs)
    return wrapper









