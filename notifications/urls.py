from django.urls import path
from . import views

urlpatterns = [
    path('', views.notification_list, name='notification_list'),
    path('mark-as-read/<uuid:notification_id>/', views.mark_as_read, name='mark_as_read'),
    path('mark-all-read/', views.mark_all_as_read, name='mark_all_notifications_read'),
    path('delete/<uuid:notification_id>/', views.delete_notification, name='delete_notification'),
    
    # API endpoints for polling
    path('api/unread-count/', views.api_unread_count, name='api_unread_count'),
    path('api/recent/', views.api_recent_notifications, name='api_recent_notifications'),
    path('api/mark-read/<uuid:notification_id>/', views.api_mark_read, name='api_mark_read'),
    path('api/mark-all-read/', views.api_mark_all_read, name='api_mark_all_read'),
    path('api/by-type/<str:action_type>/', views.api_notifications_by_type, name='api_notifications_by_type'),
]
