from django.contrib import admin
from .models import Member, MemberGroup


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ['member_number', 'full_name', 'email', 'phone', 'status', 'date_joined']
    list_filter = ['status', 'gender', 'date_joined', 'sacco']
    search_fields = ['member_number', 'first_name', 'last_name', 'email', 'id_number']
    readonly_fields = ['member_number', 'date_joined']


@admin.register(MemberGroup)
class MemberGroupAdmin(admin.ModelAdmin):
    list_display = ['name', 'sacco', 'created_at']
    list_filter = ['sacco', 'created_at']
    search_fields = ['name', 'description']