from django.urls import path
from . import views

urlpatterns = [
    path('logout/', views.logout_view, name='logout'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('reset-password/<str:uidb64>/<str:token>/', views.reset_password, name='reset_password'),
    path('sacco-admin/', views.sacco_admin_dashboard, name='sacco_admin_dashboard'),
    path('regional-admin/', views.regional_admin_dashboard, name='regional_admin_dashboard'),
    path('create-sacco/', views.create_sacco, name='create_sacco'),
    
    # System Admin Management URLs
    path('manage-regions/', views.manage_regions, name='manage_regions'),
    path('manage-regional-admins/', views.manage_regional_admins, name='manage_regional_admins'),
    path('manage-saccos/', views.manage_saccos, name='manage_saccos'),
    path('regional-overview/', views.regional_overview, name='regional_overview'),
    path('region-detail/<int:region_id>/', views.region_detail, name='region_detail'),
    path('documents-update/', views.documents_update, name='documents_update'),
    path('activity-logs/', views.activity_logs, name='activity_logs'),
    
    # Regional Admin Management URLs
    path('regional-manage-saccos/', views.regional_manage_saccos, name='regional_manage_saccos'),
    
    # User Profile
    path('profile/', views.user_profile, name='user_profile'),
]
