"""
Notification service for creating and sending notifications
"""

from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone
from .models import Notification, NotificationTemplate
from accounts.models import Sacco

User = get_user_model()


class NotificationService:
    """Service for creating and managing notifications"""
    
    @staticmethod
    def create_notification(
        user, 
        title, 
        message, 
        action_type=None,
        action_url=None,
        related_object_id=None,
        related_object_type=None,
        priority='Medium', 
        channel='InApp',
        send_email=True,
        sacco=None
    ):
        """Create a new notification with enhanced functionality"""
        notification = Notification.objects.create(
            user=user,
            title=title,
            message=message,
            action_type=action_type,
            action_url=action_url,
            related_object_id=related_object_id,
            related_object_type=related_object_type,
            priority=priority,
            channel=channel,
            sacco=sacco
        )
        
        # Send email if requested and user has email
        if send_email and user.email and channel in ['Email', 'InApp']:
            NotificationService.send_email_notification(notification)
        
        return notification
    
    @staticmethod
    def send_email_notification(notification):
        """Send email notification"""
        if not notification.user.email:
            return False
        
        try:
            # Determine email template based on action type
            template_name = f'emails/{notification.action_type}.html' if notification.action_type else 'emails/generic_notification.html'
            
            # Try to render specific template, fallback to generic
            try:
                html_message = render_to_string(template_name, {
                    'notification': notification,
                    'user': notification.user,
                    'action_url': notification.action_url,
                })
            except:
                html_message = render_to_string('emails/generic_notification.html', {
                    'notification': notification,
                    'user': notification.user,
                    'action_url': notification.action_url,
                })
            
            # Send email
            send_mail(
                subject=f"[SACCO] {notification.title}",
                message=notification.message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[notification.user.email],
                html_message=html_message,
                fail_silently=False,
            )
            
            # Mark email as sent
            notification.email_sent = True
            notification.email_sent_at = timezone.now()
            notification.save(update_fields=['email_sent', 'email_sent_at'])
            
            return True
            
        except Exception as e:
            print(f"Failed to send email notification: {e}")
            return False
    
    @staticmethod
    def notify_member_registration(member, sacco):
        """Send notification when a new member is registered"""
        title = "New Member Registration"
        message = f"New member {member.full_name} has been registered in {sacco.name}"
        
        # Notify sacco admins
        sacco_admins = User.objects.filter(sacco=sacco, is_sacco_admin=True)
        for admin in sacco_admins:
            NotificationService.create_notification(
                user=admin,
                title=title,
                message=message,
                priority='Medium',
                sacco=sacco
            )
    
    @staticmethod
    def notify_loan_application(loan, sacco):
        """Send notification when a loan application is submitted"""
        title = "New Loan Application"
        message = f"New loan application from {loan.member.full_name} for {loan.amount_requested}"
        
        # Notify sacco admins
        sacco_admins = User.objects.filter(sacco=sacco, is_sacco_admin=True)
        for admin in sacco_admins:
            NotificationService.create_notification(
                user=admin,
                title=title,
                message=message,
                priority='High',
                sacco=sacco
            )
    
    @staticmethod
    def notify_loan_approval(loan, sacco):
        """Send notification when a loan is approved"""
        title = "Loan Approved"
        message = f"Your loan application for {loan.amount_approved} has been approved"
        
        # Notify the member
        if loan.member.user_account:
            NotificationService.create_notification(
                user=loan.member.user_account,
                title=title,
                message=message,
                priority='High',
                sacco=sacco
            )
    
    @staticmethod
    def notify_loan_rejection(loan, sacco, reason=""):
        """Send notification when a loan is rejected"""
        title = "Loan Application Rejected"
        message = f"Your loan application for {loan.amount_requested} has been rejected"
        if reason:
            message += f". Reason: {reason}"
        
        # Notify the member
        if loan.member.user_account:
            NotificationService.create_notification(
                user=loan.member.user_account,
                title=title,
                message=message,
                priority='Medium',
                sacco=sacco
            )
    
    @staticmethod
    def notify_savings_deposit(savings_account, amount, sacco):
        """Send notification when a savings deposit is made"""
        title = "Savings Deposit"
        message = f"Deposit of {amount} has been made to your {savings_account.product.name} account"
        
        # Notify the member
        if savings_account.member.user_account:
            NotificationService.create_notification(
                user=savings_account.member.user_account,
                title=title,
                message=message,
                priority='Low',
                sacco=sacco
            )
    
    @staticmethod
    def notify_system_alert(alert_message, priority='Medium', sacco=None):
        """Send system-wide alert notification"""
        title = "System Alert"
        
        # Notify all system admins
        system_admins = User.objects.filter(is_system_admin=True)
        for admin in system_admins:
            NotificationService.create_notification(
                user=admin,
                title=title,
                message=alert_message,
                priority=priority,
                sacco=sacco
            )
    
    @staticmethod
    def get_unread_count(user):
        """Get unread notification count for a user"""
        return Notification.objects.filter(user=user, is_read=False).count()
    
    @staticmethod
    def get_recent_notifications(user, limit=5):
        """Get recent notifications for a user"""
        return Notification.objects.filter(user=user).order_by('-sent_at')[:limit]
    
    @staticmethod
    def mark_notifications_read(user, notification_ids=None):
        """Mark notifications as read"""
        if notification_ids:
            notifications = Notification.objects.filter(
                user=user, 
                id__in=notification_ids, 
                is_read=False
            )
        else:
            notifications = Notification.objects.filter(user=user, is_read=False)
        
        for notification in notifications:
            notification.mark_as_read()
        
        return notifications.count()
    
    @staticmethod
    def mark_all_as_read(user):
        """Mark all notifications as read for a user"""
        return NotificationService.mark_notifications_read(user)
    
    @staticmethod
    def delete_notification(notification_id, user):
        """Delete a specific notification"""
        try:
            notification = Notification.objects.get(id=notification_id, user=user)
            notification.delete()
            return True
        except Notification.DoesNotExist:
            return False
    
    @staticmethod
    def get_notifications_by_type(user, action_type, limit=10):
        """Get notifications filtered by action type"""
        return Notification.objects.filter(
            user=user, 
            action_type=action_type
        ).order_by('-sent_at')[:limit]
    
    @staticmethod
    def get_unread_notifications(user, limit=10):
        """Get unread notifications for a user"""
        return Notification.objects.filter(
            user=user, 
            is_read=False
        ).order_by('-sent_at')[:limit]
