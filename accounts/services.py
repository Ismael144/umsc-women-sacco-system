"""
Service layer for common dashboard statistics and queries
"""

from django.db.models import Sum, Count, Avg
from django.utils import timezone
from datetime import timedelta
from members.models import Member
from loans.models import Loan
from savings.models import SavingsAccount
from funding.models import Funding
from expenses.models import Expense
from projects.models import Project
from .models import Sacco, Region
from members.constants import MEMBER_STATUS_ACTIVE, MEMBER_STATUS_INACTIVE
from loans.constants import (
    LOAN_STATUS_PENDING_APPROVAL, LOAN_STATUS_APPROVED, 
    LOAN_STATUS_DECLINED, LOAN_STATUS_ACTIVE
)


class DashboardStatsService:
    """Service class for dashboard statistics"""
    
    @staticmethod
    def get_system_stats():
        """Get system-wide statistics"""
        return {
            'total_saccos': Sacco.objects.filter(is_active=True).count(),
            'total_members': Member.objects.count(),
            'total_loans': Loan.objects.count(),
            'total_savings': SavingsAccount.objects.count(),
            'total_funding': Funding.objects.count(),
        }
    
    @staticmethod
    def get_financial_metrics():
        """Get financial metrics"""
        return {
            'total_loan_amount': Loan.objects.aggregate(total=Sum('amount_requested'))['total'] or 0,
            'total_savings_balance': SavingsAccount.objects.aggregate(total=Sum('balance'))['total'] or 0,
            'total_funding_amount': Funding.objects.aggregate(total=Sum('amount'))['total'] or 0,
            'total_expenses': Expense.objects.aggregate(total=Sum('amount'))['total'] or 0,
            'total_project_budget': Project.objects.aggregate(total=Sum('budget'))['total'] or 0,
        }
    
    @staticmethod
    def get_loan_statistics():
        """Get loan statistics"""
        return {
            'pending_loans': Loan.objects.filter(status=LOAN_STATUS_PENDING_APPROVAL).count(),
            'approved_loans': Loan.objects.filter(status=LOAN_STATUS_APPROVED).count(),
            'rejected_loans': Loan.objects.filter(status=LOAN_STATUS_DECLINED).count(),
            'active_loans': Loan.objects.filter(status=LOAN_STATUS_ACTIVE).count(),
        }
    
    @staticmethod
    def get_member_statistics():
        """Get member statistics"""
        return {
            'active_members': Member.objects.filter(status=MEMBER_STATUS_ACTIVE).count(),
            'inactive_members': Member.objects.filter(status=MEMBER_STATUS_INACTIVE).count(),
            'new_members_this_month': Member.objects.filter(
                date_joined__gte=timezone.now().replace(day=1)
            ).count(),
        }
    
    @staticmethod
    def get_recent_activity(days=30):
        """Get recent activity statistics"""
        thirty_days_ago = timezone.now() - timedelta(days=days)
        return {
            'recent_members_count': Member.objects.filter(date_joined__gte=thirty_days_ago).count(),
            'recent_loans_count': Loan.objects.filter(application_date__gte=thirty_days_ago).count(),
            'recent_savings_count': SavingsAccount.objects.filter(created_at__gte=thirty_days_ago).count(),
        }
    
    @staticmethod
    def get_sacco_stats(sacco):
        """Get statistics for a specific sacco"""
        return {
            'total_members': Member.objects.filter(sacco=sacco).count(),
            'total_loans': Loan.objects.filter(member__sacco=sacco).count(),
            'total_savings': SavingsAccount.objects.filter(member__sacco=sacco).count(),
            'total_funding': Funding.objects.filter(sacco=sacco).count(),
            'total_loan_amount': Loan.objects.filter(member__sacco=sacco).aggregate(
                total=Sum('amount_requested'))['total'] or 0,
            'total_savings_balance': SavingsAccount.objects.filter(member__sacco=sacco).aggregate(
                total=Sum('balance'))['total'] or 0,
        }
    
    @staticmethod
    def get_regional_stats(region):
        """Get statistics for a specific region"""
        return {
            'total_saccos': Sacco.objects.filter(region=region, is_active=True).count(),
            'total_members': Member.objects.filter(sacco__region=region).count(),
            'total_loans': Loan.objects.filter(member__sacco__region=region).count(),
            'total_savings': SavingsAccount.objects.filter(member__sacco__region=region).count(),
            'total_funding': Funding.objects.filter(sacco__region=region).count(),
            'total_loan_amount': Loan.objects.filter(member__sacco__region=region).aggregate(
                total=Sum('amount_requested'))['total'] or 0,
            'total_savings_balance': SavingsAccount.objects.filter(member__sacco__region=region).aggregate(
                total=Sum('balance'))['total'] or 0,
        }
    
    @staticmethod
    def get_saccos_with_stats():
        """Get all saccos with their statistics"""
        saccos_with_stats = []
        for sacco in Sacco.objects.filter(is_active=True).select_related('region'):
            stats = DashboardStatsService.get_sacco_stats(sacco)
            saccos_with_stats.append({
                'sacco': sacco,
                **stats
            })
        
        # Sort by total financial activity
        saccos_with_stats.sort(
            key=lambda x: x['total_loan_amount'] + x['total_savings_balance'], 
            reverse=True
        )
        return saccos_with_stats
    
    @staticmethod
    def get_recent_objects(limit=10):
        """Get recent objects across the system"""
        return {
            'recent_members': Member.objects.select_related('sacco').order_by('-date_joined')[:limit],
            'recent_loans': Loan.objects.select_related('member__sacco').order_by('-application_date')[:limit],
            'recent_savings': SavingsAccount.objects.select_related('member__sacco').order_by('-created_at')[:limit],
        }
    
    @staticmethod
    def get_system_alerts():
        """Get system alerts and notifications"""
        alerts = []
        
        # Check for inactive Saccos
        inactive_saccos = Sacco.objects.filter(is_active=False).count()
        if inactive_saccos > 0:
            alerts.append({
                'type': 'warning',
                'message': f'{inactive_saccos} inactive Saccos need attention',
                'icon': 'bx-error'
            })
        
        # Check for pending loans
        pending_loans = Loan.objects.filter(status=LOAN_STATUS_PENDING_APPROVAL).count()
        if pending_loans > 0:
            alerts.append({
                'type': 'info',
                'message': f'{pending_loans} loan applications pending approval',
                'icon': 'bx-time'
            })
        
        # Check for low funding (only for system-wide alerts, not per-region)
        # This check is now handled in regional_admin_dashboard view instead
        # total_funding = Funding.objects.aggregate(total=Sum('amount'))['total'] or 0
        # if total_funding < 100000:  # Less than 100k
        #     alerts.append({
        #         'type': 'warning',
        #         'message': 'Total funding amount is below recommended threshold',
        #         'icon': 'bx-money'
        #     })
        
        return alerts









