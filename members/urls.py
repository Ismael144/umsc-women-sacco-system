from django.urls import path
from . import views

urlpatterns = [
    path('overview/', views.members_overview, name='members_overview'),
    path('', views.member_list, name='member_list'),
    path('register/', views.register_member, name='register_member'),
    path('edit/<int:member_id>/', views.edit_member, name='edit_member'),
    path('bulk-import/', views.bulk_import_members, name='bulk_import_members'),
    path('profile/<int:member_id>/', views.member_profile, name='member_profile'),
    path('groups/', views.member_groups, name='member_groups'),
    path('groups/edit/<int:group_id>/', views.edit_member_group, name='edit_member_group'),
    path('groups/view/<int:group_id>/', views.view_member_group, name='view_member_group'),
    path('groups/delete/<int:group_id>/', views.delete_member_group, name='delete_member_group'),
    path('inactive/', views.inactive_members, name='inactive_members'),
    path('dashboard/', views.member_dashboard, name='member_dashboard'),
    path('search/', views.search_members, name='search_members'),
    # API endpoints
    path('api/members/', views.api_members, name='members_api_members'),
    path('api/create-group/', views.api_create_group, name='members_api_create_group'),
]
