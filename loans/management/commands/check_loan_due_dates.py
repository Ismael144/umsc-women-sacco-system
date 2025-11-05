"""
Management command to check for loans approaching or past due dates
and send notifications to relevant parties.
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Q
from datetime import timedelta
from loans.models import Loan
from notifications.services import NotificationService
from accounts.models import Sacco


class Command(BaseCommand):
    help = 'Check for loans approaching or past due dates and send notifications'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days-before',
            type=int,
            default=7,
            help='Number of days before due date to send reminder (default: 7)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without actually sending notifications'
        )

    def handle(self, *args, **options):
        days_before = options['days_before']
        dry_run = options['dry_run']
        
        today = timezone.now().date()
        reminder_date = today + timedelta(days=days_before)
        
        # Find loans approaching due date
        approaching_due = Loan.objects.filter(
            maturity_date__date=reminder_date,
            status__in=['active', 'disbursed']
        ).exclude(maturity_date__isnull=True)
        
        # Find overdue loans
        overdue_loans = Loan.objects.filter(
            maturity_date__date__lt=today,
            status__in=['active', 'disbursed']
        ).exclude(maturity_date__isnull=True)
        
        self.stdout.write(f"Found {approaching_due.count()} loans approaching due date")
        self.stdout.write(f"Found {overdue_loans.count()} overdue loans")
        
        if dry_run:
            self.stdout.write("DRY RUN - No notifications will be sent")
            return
        
        # Send notifications for approaching due dates
        for loan in approaching_due:
            self.send_reminder_notification(loan, days_before)
        
        # Send notifications for overdue loans
        for loan in overdue_loans:
            self.send_overdue_notification(loan)
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully processed {approaching_due.count() + overdue_loans.count()} loans'
            )
        )

    def send_reminder_notification(self, loan, days_before):
        """Send reminder notification for loan approaching due date"""
        try:
            # Notify the member
            if loan.member.user_account:
                NotificationService.create_notification(
                    user=loan.member.user_account,
                    title=f"Loan Payment Reminder - {days_before} days",
                    message=f"Your loan {loan.loan_number} is due in {days_before} days. "
                           f"Amount: {loan.amount_requested} UGX. Please ensure payment is made on time.",
                    action_type='payment_reminder',
                    action_url=f"/loans/profile/{loan.id}/",
                    priority='High',
                    sacco=loan.member.sacco
                )
            
            # Notify sacco admins
            sacco_admins = loan.member.sacco.user_set.filter(is_sacco_admin=True)
            for admin in sacco_admins:
                NotificationService.create_notification(
                    user=admin,
                    title=f"Loan Payment Reminder - {loan.member.full_name}",
                    message=f"Loan {loan.loan_number} for {loan.member.full_name} is due in {days_before} days. "
                           f"Amount: {loan.amount_requested} UGX",
                    action_type='payment_reminder',
                    action_url=f"/loans/profile/{loan.id}/",
                    priority='Medium',
                    sacco=loan.member.sacco
                )
            
            self.stdout.write(f"Sent reminder for loan {loan.loan_number}")
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Failed to send reminder for loan {loan.loan_number}: {e}")
            )

    def send_overdue_notification(self, loan):
        """Send overdue notification for past due loans"""
        try:
            days_overdue = (timezone.now().date() - loan.maturity_date.date()).days
            
            # Notify the member
            if loan.member.user_account:
                NotificationService.create_notification(
                    user=loan.member.user_account,
                    title=f"URGENT: Loan Payment Overdue",
                    message=f"Your loan {loan.loan_number} is {days_overdue} days overdue. "
                           f"Amount: {loan.amount_requested} UGX. Please contact the office immediately.",
                    action_type='loan_overdue',
                    action_url=f"/loans/profile/{loan.id}/",
                    priority='Critical',
                    sacco=loan.member.sacco
                )
            
            # Notify sacco admins
            sacco_admins = loan.member.sacco.user_set.filter(is_sacco_admin=True)
            for admin in sacco_admins:
                NotificationService.create_notification(
                    user=admin,
                    title=f"URGENT: Overdue Loan - {loan.member.full_name}",
                    message=f"Loan {loan.loan_number} for {loan.member.full_name} is {days_overdue} days overdue. "
                           f"Amount: {loan.amount_requested} UGX. Immediate action required.",
                    action_type='loan_overdue',
                    action_url=f"/loans/profile/{loan.id}/",
                    priority='Critical',
                    sacco=loan.member.sacco
                )
            
            self.stdout.write(f"Sent overdue notification for loan {loan.loan_number}")
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Failed to send overdue notification for loan {loan.loan_number}: {e}")
            )
