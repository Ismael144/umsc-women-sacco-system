"""
Notification models for the system
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from accounts.models import Sacco
import uuid

User = get_user_model()


class Notification(models.Model):
    """System notifications and alerts"""
    CHANNEL_CHOICES = [
        ('Email', 'Email'),
        ('SMS', 'SMS'),
        ('InApp', 'In-App'),
        ('Push', 'Push Notification')
    ]
    
    ACTION_TYPE_CHOICES = [
        ('loan_approval', 'Loan Approval'),
        ('loan_rejection', 'Loan Rejection'),
        ('loan_disbursement', 'Loan Disbursement'),
        ('savings_deposit', 'Savings Deposit'),
        ('savings_withdrawal', 'Savings Withdrawal'),
        ('member_registration', 'Member Registration'),
        ('payment_reminder', 'Payment Reminder'),
        ('loan_overdue', 'Loan Overdue'),
        ('password_reset', 'Password Reset'),
        ('system_alert', 'System Alert'),
        ('group_contribution', 'Group Contribution'),
        ('emergency_loan', 'Emergency Loan'),
        ('training_completion', 'Training Completion'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    sent_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)
    channel = models.CharField(max_length=20, choices=CHANNEL_CHOICES, default='InApp')
    priority = models.CharField(max_length=20, choices=[
        ('Low', 'Low'),
        ('Medium', 'Medium'),
        ('High', 'High'),
        ('Critical', 'Critical')
    ], default='Medium')
    
    # Enhanced functionality fields
    action_type = models.CharField(max_length=30, choices=ACTION_TYPE_CHOICES, null=True, blank=True)
    action_url = models.URLField(max_length=500, null=True, blank=True)
    related_object_id = models.PositiveIntegerField(null=True, blank=True)
    related_object_type = models.CharField(max_length=50, null=True, blank=True)
    email_sent = models.BooleanField(default=False)
    email_sent_at = models.DateTimeField(null=True, blank=True)
    sacco = models.ForeignKey(Sacco, on_delete=models.CASCADE, null=True, blank=True)
    
    class Meta:
        ordering = ['-sent_at']
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"
        indexes = [
            models.Index(fields=['user', 'is_read']),
            models.Index(fields=['action_type']),
            models.Index(fields=['sent_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.title}"
    
    def mark_as_read(self):
        """Mark notification as read"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])


class NotificationTemplate(models.Model):
    """Email and SMS templates for notifications"""
    TEMPLATE_TYPE_CHOICES = [
        ('Email', 'Email'),
        ('SMS', 'SMS'),
        ('InApp', 'In-App')
    ]
    
    name = models.CharField(max_length=100, unique=True)
    template_type = models.CharField(max_length=20, choices=TEMPLATE_TYPE_CHOICES)
    subject = models.CharField(max_length=200, blank=True)
    body = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Notification Template"
        verbose_name_plural = "Notification Templates"
    
    def __str__(self):
        return self.name
