from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import Sacco, User, Region, District, ActivityLog


@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['name']


@admin.register(District)
class DistrictAdmin(admin.ModelAdmin):
    list_display = ['name', 'region', 'is_active', 'created_at']
    list_filter = ['is_active', 'region', 'created_at']
    search_fields = ['name', 'region__name']
    ordering = ['region__name', 'name']


@admin.register(Sacco)
class SaccoAdmin(admin.ModelAdmin):
    list_display = ['name', 'registration_number', 'region', 'district', 'phone', 'email', 'is_active']
    list_filter = ['is_active', 'region', 'district', 'created_at']
    search_fields = ['name', 'registration_number', 'email']
    raw_id_fields = ['region', 'district', 'created_by']


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'sacco', 'region', 'is_sacco_admin', 'is_system_admin', 'is_regional_admin']
    list_filter = ['is_sacco_admin', 'is_system_admin', 'is_regional_admin', 'sacco', 'region']
    search_fields = ['username', 'email', 'sacco__name', 'region__name']
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Sacco Information', {'fields': ('sacco', 'is_sacco_admin', 'phone')}),
        ('Regional Information', {'fields': ('region', 'is_regional_admin')}),
        ('System Information', {'fields': ('is_system_admin',)}),
    )


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'action', 'model_name', 'object_name', 'sacco', 'region', 'timestamp']
    list_filter = ['action', 'model_name', 'sacco', 'region', 'timestamp']
    search_fields = ['user__username', 'object_name', 'description']
    readonly_fields = ['timestamp']
    date_hierarchy = 'timestamp'
    ordering = ['-timestamp']