"""
Notification views
"""

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.utils import timezone
from .models import Notification
from .services import NotificationService


@login_required
def notification_list(request):
    """List all notifications for the current user"""
    notifications = Notification.objects.filter(user=request.user)
    
    # Filter by read status
    is_read = request.GET.get('read')
    if is_read == 'true':
        notifications = notifications.filter(is_read=True)
    elif is_read == 'false':
        notifications = notifications.filter(is_read=False)
    
    # Pagination
    paginator = Paginator(notifications, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'unread_count': notifications.filter(is_read=False).count(),
    }
    return render(request, 'notifications/notification_list.html', context)


@login_required
def mark_as_read(request, notification_id):
    """Mark a notification as read"""
    try:
        notification = Notification.objects.get(id=notification_id, user=request.user)
        notification.is_read = True
        notification.save()
        return JsonResponse({'success': True})
    except Notification.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Notification not found'})


@login_required
def mark_all_as_read(request):
    """Mark all notifications as read"""
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return JsonResponse({'success': True})


@login_required
def delete_notification(request, notification_id):
    """Delete a notification"""
    try:
        notification = Notification.objects.get(id=notification_id, user=request.user)
        notification.delete()
        messages.success(request, 'Notification deleted successfully')
    except Notification.DoesNotExist:
        messages.error(request, 'Notification not found')
    
    return redirect('notification_list')


# API Endpoints for Polling
@login_required
def api_unread_count(request):
    """API endpoint to get unread notification count"""
    count = NotificationService.get_unread_count(request.user)
    return JsonResponse({'count': count})


@login_required
def api_recent_notifications(request):
    """API endpoint to get recent notifications"""
    limit = int(request.GET.get('limit', 10))
    notifications = NotificationService.get_recent_notifications(request.user, limit)
    
    notifications_data = []
    for notification in notifications:
        notifications_data.append({
            'id': str(notification.id),
            'title': notification.title,
            'message': notification.message,
            'is_read': notification.is_read,
            'sent_at': notification.sent_at.isoformat(),
            'action_type': notification.action_type,
            'action_url': notification.action_url,
            'priority': notification.priority,
        })
    
    return JsonResponse({'notifications': notifications_data})


@login_required
def api_mark_read(request, notification_id):
    """API endpoint to mark a single notification as read"""
    try:
        notification = Notification.objects.get(id=notification_id, user=request.user)
        notification.mark_as_read()
        return JsonResponse({'success': True})
    except Notification.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Notification not found'})


@login_required
def api_mark_all_read(request):
    """API endpoint to mark all notifications as read"""
    count = NotificationService.mark_all_as_read(request.user)
    return JsonResponse({'success': True, 'count': count})


@login_required
def api_notifications_by_type(request, action_type):
    """API endpoint to get notifications by type"""
    limit = int(request.GET.get('limit', 10))
    notifications = NotificationService.get_notifications_by_type(request.user, action_type, limit)
    
    notifications_data = []
    for notification in notifications:
        notifications_data.append({
            'id': str(notification.id),
            'title': notification.title,
            'message': notification.message,
            'is_read': notification.is_read,
            'sent_at': notification.sent_at.isoformat(),
            'action_type': notification.action_type,
            'action_url': notification.action_url,
            'priority': notification.priority,
        })
    
    return JsonResponse({'notifications': notifications_data})
