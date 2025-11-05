from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class Region(models.Model):
    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['name']


class District(models.Model):
    name = models.CharField(max_length=200)
    region = models.ForeignKey(Region, on_delete=models.CASCADE, related_name='districts')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} - {self.region.name}"
    
    class Meta:
        ordering = ['name']
        unique_together = ['name', 'region']


class Sacco(models.Model):
    name = models.CharField(max_length=200)
    registration_number = models.CharField(max_length=100, unique=True)
    branch_name = models.CharField(max_length=100, blank=True, null=True)
    address = models.TextField()
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    region = models.ForeignKey(Region, on_delete=models.SET_NULL, null=True, blank=True, related_name='saccos')
    district = models.ForeignKey('District', on_delete=models.SET_NULL, null=True, blank=True, related_name='saccos')
    default_currency = models.CharField(max_length=3, default='UGX')
    fiscal_year_start = models.IntegerField(default=1)  # Month (1-12)
    loan_min_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    loan_max_amount = models.DecimalField(max_digits=14, decimal_places=2, default=1000000)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey('User', on_delete=models.SET_NULL, null=True, related_name='created_saccos')
    
    def __str__(self):
        return self.name


class User(AbstractUser):
    sacco = models.ForeignKey(Sacco, on_delete=models.CASCADE, null=True, blank=True)
    region = models.ForeignKey(Region, on_delete=models.SET_NULL, null=True, blank=True, related_name='regional_admins')
    is_sacco_admin = models.BooleanField(default=False)
    is_system_admin = models.BooleanField(default=False)
    is_regional_admin = models.BooleanField(default=False)
    phone = models.CharField(max_length=20, blank=True)
    
    def __str__(self):
        return self.username


class ActivityLog(models.Model):
    ACTION_CHOICES = [
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('view', 'View'),
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('approve', 'Approve'),
        ('reject', 'Reject'),
        ('activate', 'Activate'),
        ('deactivate', 'Deactivate'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    model_name = models.CharField(max_length=100)  # e.g., 'Sacco', 'Member', 'Loan'
    object_id = models.PositiveIntegerField(null=True, blank=True)
    object_name = models.CharField(max_length=200, blank=True)  # Human readable name
    description = models.TextField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    sacco = models.ForeignKey(Sacco, on_delete=models.SET_NULL, null=True, blank=True, related_name='activities')
    region = models.ForeignKey(Region, on_delete=models.SET_NULL, null=True, blank=True, related_name='activities')
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['sacco', 'timestamp']),
            models.Index(fields=['region', 'timestamp']),
            models.Index(fields=['action', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.action} - {self.model_name} - {self.timestamp}"