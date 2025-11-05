from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib import messages
from django.http import JsonResponse
from django.conf import settings
from django.db.models import Q, Count, Sum
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import timedelta
from .models import Sacco, User, Region, ActivityLog
from members.models import Member
from .utils import log_activity, get_client_ip, get_user_agent
import json


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    # Check if user was redirected due to inactivity
    if request.GET.get('inactive') == '1':
        messages.warning(request, 'You have been logged out due to inactivity (30 minutes). Please log in again.')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        remember_me = request.POST.get('remember_me')
        
        user = authenticate(request, username=username, password=password)
        if user:
            # Check if sacco admin's sacco is active
            if user.is_sacco_admin and user.sacco:
                if not user.sacco.is_active:
                    messages.error(request, 'Your Sacco has been deactivated. Please contact your regional administrator.')
                    return render(request, 'accounts/login.html')
            
            login(request, user)
            
            # Initialize last activity time for inactivity tracking
            from django.utils import timezone
            request.session['last_activity'] = timezone.now().isoformat()
            
            # Store "Remember Me" preference in session
            request.session['remember_me'] = bool(remember_me)
            
            # Log login activity
            log_activity(
                user=user,
                action='login',
                model_name='User',
                object_id=user.id,
                object_name=user.username,
                description=f'User {user.username} logged in',
                ip_address=get_client_ip(request),
                user_agent=get_user_agent(request)
            )
            
            # Handle "Remember Me" functionality
            # Note: Even with "Remember Me", inactivity timeout still applies for security
            if remember_me:
                # Set session to expire in 30 days (but inactivity middleware will still log out after 30 min)
                request.session.set_expiry(30 * 24 * 60 * 60)  # 30 days
            else:
                # Set session to expire when browser is closed
                request.session.set_expiry(0)
            
            if user.is_system_admin:
                return redirect('admin_dashboard')
            elif user.is_regional_admin:
                return redirect('regional_admin_dashboard')
            else:
                return redirect('dashboard')
        else:
            messages.error(request, 'Invalid credentials')
    
    return render(request, 'accounts/login.html')


@login_required
def dashboard(request):
    if request.user.is_system_admin:
        return redirect('admin_dashboard')
    
    if request.user.is_regional_admin:
        return redirect('regional_admin_dashboard')
    
    if request.user.is_sacco_admin:
        # Check if sacco is active
        if request.user.sacco and not request.user.sacco.is_active:
            messages.error(request, 'Your Sacco has been deactivated. Please contact your regional administrator.')
            from django.contrib.auth import logout
            logout(request)
            return redirect('login')
        return redirect('sacco_admin_dashboard')
    
    # Check if user is a member (has a member record)
    try:
        from members.models import Member
        member = Member.objects.get(user_account=request.user)
        # If user is a member, redirect to member dashboard
        return redirect('member_dashboard')
    except:
        # If user is not a member, redirect to login
        messages.error(request, 'Access denied. Please contact your administrator.')
        return redirect('login')
    
    return redirect('login')


@login_required
def admin_dashboard(request):
    if not request.user.is_system_admin:
        return redirect('dashboard')
    
    from .services import DashboardStatsService
    
    # Get comprehensive system statistics using service
    system_stats = DashboardStatsService.get_system_stats()
    financial_metrics = DashboardStatsService.get_financial_metrics()
    loan_stats = DashboardStatsService.get_loan_statistics()
    member_stats = DashboardStatsService.get_member_statistics()
    recent_activity = DashboardStatsService.get_recent_activity()
    
    # Get saccos with stats
    saccos_with_stats = DashboardStatsService.get_saccos_with_stats()
    
    # Get recent objects
    recent_objects = DashboardStatsService.get_recent_objects()
    
    # System performance metrics
    active_saccos = Sacco.objects.filter(is_active=True).count()
    inactive_saccos = Sacco.objects.filter(is_active=False).count()
    
    # Monthly growth trends
    current_month = timezone.now().month
    current_year = timezone.now().year
    
    # Member growth by month (last 6 months)
    member_growth = []
    for i in range(6):
        month = current_month - i
        year = current_year
        if month <= 0:
            month += 12
            year -= 1
        
        count = Member.objects.filter(
            date_joined__year=year,
            date_joined__month=month
        ).count()
        member_growth.append({
            'month': f"{year}-{month:02d}",
            'count': count
        })
    
    member_growth.reverse()
    
    # Loan status distribution
    loan_status_distribution = {
        'pending': loan_stats['pending_loans'],
        'approved': loan_stats['approved_loans'],
        'rejected': loan_stats['rejected_loans'],
        'active': loan_stats['active_loans'],
    }
    
    # Financial health metrics
    total_assets = financial_metrics['total_savings_balance'] + financial_metrics['total_funding_amount']
    total_liabilities = financial_metrics['total_loan_amount']
    net_worth = total_assets - total_liabilities
    
    # Get system alerts
    system_alerts = DashboardStatsService.get_system_alerts()
    
    # CSV Export functionality
    if request.GET.get('export') == 'csv':
        import csv
        from django.http import HttpResponse
        
        response = HttpResponse(content_type='text/csv')
        filename = f'system_report_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv'
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        writer = csv.writer(response)
        
        # System Summary Section
        writer.writerow(['SYSTEM ADMINISTRATOR REPORT'])
        writer.writerow(['Generated:', timezone.now().strftime('%Y-%m-%d %H:%M:%S')])
        writer.writerow([])
        
        writer.writerow(['SYSTEM SUMMARY'])
        writer.writerow(['Total Saccos', system_stats['total_saccos']])
        writer.writerow(['Active Saccos', active_saccos])
        writer.writerow(['Inactive Saccos', inactive_saccos])
        writer.writerow(['Total Members', system_stats['total_members']])
        writer.writerow(['Active Members', member_stats['active_members']])
        writer.writerow(['Inactive Members', member_stats['inactive_members']])
        writer.writerow(['New Members This Month', member_stats['new_members_this_month']])
        writer.writerow(['Total Loans', system_stats['total_loans']])
        writer.writerow(['Pending Loans', loan_stats['pending_loans']])
        writer.writerow(['Approved Loans', loan_stats['approved_loans']])
        writer.writerow(['Active Loans', loan_stats['active_loans']])
        writer.writerow(['Rejected Loans', loan_stats['rejected_loans']])
        writer.writerow(['Total Savings Accounts', system_stats['total_savings']])
        writer.writerow([])
        
        # Financial Overview Section
        writer.writerow(['FINANCIAL OVERVIEW'])
        writer.writerow(['Total Savings Balance', f"{financial_metrics['total_savings_balance']:.2f}"])
        writer.writerow(['Total Loan Amount', f"{financial_metrics['total_loan_amount']:.2f}"])
        writer.writerow(['Total Funding Amount', f"{financial_metrics['total_funding_amount']:.2f}"])
        writer.writerow(['Net Worth', f"{net_worth:.2f}"])
        writer.writerow([])
        
        # Recent Activity Section
        writer.writerow(['RECENT ACTIVITY (30 Days)'])
        writer.writerow(['New Members', recent_activity['recent_members_count']])
        writer.writerow(['New Loans', recent_activity['recent_loans_count']])
        writer.writerow(['New Savings Accounts', recent_activity['recent_savings_count']])
        writer.writerow([])
        
        # Saccos with Statistics Section
        writer.writerow(['SACCO DETAILS'])
        writer.writerow(['Sacco Name', 'Registration Number', 'Email', 'Members', 'Loans', 'Savings Accounts', 'Funding', 'Savings Balance', 'Loan Amount', 'Status'])
        for item in saccos_with_stats:
            sacco = item['sacco']
            writer.writerow([
                sacco.name,
                sacco.registration_number,
                sacco.email or 'N/A',
                item['total_members'],
                item['total_loans'],
                item['total_savings'],
                item['total_funding'],
                f"{item['total_savings_balance']:.2f}",
                f"{item['total_loan_amount']:.2f}",
                'Active' if sacco.is_active else 'Inactive'
            ])
        writer.writerow([])
        
        # Recent Members Section
        writer.writerow(['RECENT MEMBERS'])
        writer.writerow(['Member Number', 'Full Name', 'Sacco', 'Phone', 'Email', 'Status', 'Date Joined'])
        for member in recent_objects['recent_members']:
            full_name = f"{member.first_name} {member.last_name}"
            if hasattr(member, 'other_names') and member.other_names:
                full_name += f" {member.other_names}"
            writer.writerow([
                member.member_number,
                full_name,
                member.sacco.name if member.sacco else 'N/A',
                member.phone or 'N/A',
                member.email or 'N/A',
                member.status,
                member.date_joined.strftime('%Y-%m-%d') if member.date_joined else 'N/A'
            ])
        writer.writerow([])
        
        # Recent Loans Section
        writer.writerow(['RECENT LOANS'])
        writer.writerow(['Loan Number', 'Member Name', 'Sacco', 'Amount Requested', 'Product', 'Status', 'Application Date'])
        for loan in recent_objects['recent_loans']:
            writer.writerow([
                loan.loan_number or 'N/A',
                f"{loan.member.first_name} {loan.member.last_name}",
                loan.member.sacco.name if loan.member.sacco else 'N/A',
                f"{loan.amount_requested:.2f}",
                loan.product.name if loan.product else 'N/A',
                loan.get_status_display() if hasattr(loan, 'get_status_display') else loan.status,
                loan.application_date.strftime('%Y-%m-%d') if loan.application_date else 'N/A'
            ])
        writer.writerow([])
        
        # Recent Savings Section
        writer.writerow(['RECENT SAVINGS ACCOUNTS'])
        writer.writerow(['Account Number', 'Member Name', 'Sacco', 'Product', 'Balance', 'Status', 'Created Date'])
        for saving in recent_objects['recent_savings']:
            writer.writerow([
                saving.account_number,
                f"{saving.member.first_name} {saving.member.last_name}",
                saving.member.sacco.name if saving.member.sacco else 'N/A',
                saving.product.name if saving.product else 'N/A',
                f"{saving.balance:.2f}",
                'Active' if saving.is_active else 'Inactive',
                saving.created_at.strftime('%Y-%m-%d') if saving.created_at else 'N/A'
            ])
        
        return response
    
    context = {
        # Basic counts
        **system_stats,
        
        # Financial metrics
        **financial_metrics,
        'net_worth': net_worth,
        
        # Loan statistics
        **loan_stats,
        
        # Member statistics
        **member_stats,
        
        # Recent activity
        **recent_activity,
        
        # Data for tables
        'saccos_with_stats': saccos_with_stats,
        'recent_members': recent_objects['recent_members'],
        'recent_loans': recent_objects['recent_loans'],
        'recent_savings': recent_objects['recent_savings'],
        
        # System status
        'active_saccos': active_saccos,
        'inactive_saccos': inactive_saccos,
        
        # Analytics data
        'member_growth': member_growth,
        'loan_status_distribution': loan_status_distribution,
        'system_alerts': system_alerts,
    }
    return render(request, 'admin_dashboard.html', context)


@login_required
def regional_admin_dashboard(request):
    if not request.user.is_regional_admin:
        messages.error(request, 'Access denied. Only regional administrators can access this page.')
        return redirect('dashboard')
    
    # Log dashboard access
    log_activity(
        user=request.user,
        action='view',
        model_name='Dashboard',
        description=f'Regional admin {request.user.username} accessed regional dashboard',
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request)
    )
    
    # Get statistics for the region
    from members.models import Member
    from loans.models import Loan
    from savings.models import SavingsAccount
    from funding.models import Funding
    from expenses.models import Expense
    from projects.models import Project
    from django.db.models import Sum, Count, Avg
    from django.utils import timezone
    from datetime import timedelta
    from accounts.permissions import get_accessible_saccos
    
    # Get accessible saccos for selector
    accessible_saccos = get_accessible_saccos(request.user)
    
    # Get selected sacco from query parameter
    selected_sacco_id = request.GET.get('sacco')
    # Normalize to string for proper comparison
    if selected_sacco_id:
        try:
            selected_sacco_id = str(int(selected_sacco_id))
        except (ValueError, TypeError):
            selected_sacco_id = None
    selected_sacco = None
    
    # Regional statistics
    region = request.user.region
    regional_saccos = Sacco.objects.filter(region=region, is_active=True)
    
    # If a specific sacco is selected, filter by it; otherwise show all regional data
    if selected_sacco_id:
        try:
            selected_sacco = Sacco.objects.get(id=selected_sacco_id, region=region)
            # Verify user has access to this sacco
            if selected_sacco in accessible_saccos:
                # Filter all queries by selected sacco
                members_filter = Member.objects.filter(sacco=selected_sacco)
                loans_filter = Loan.objects.filter(member__sacco=selected_sacco)
                savings_filter = SavingsAccount.objects.filter(member__sacco=selected_sacco)
                funding_filter = Funding.objects.filter(sacco=selected_sacco)
                expenses_filter = Expense.objects.filter(sacco=selected_sacco)
                projects_filter = Project.objects.filter(sacco=selected_sacco)
            else:
                selected_sacco = None
        except Sacco.DoesNotExist:
            selected_sacco = None
    
    # Use filtered or regional queries
    if selected_sacco:
        members_query = members_filter
        loans_query = loans_filter
        savings_query = savings_filter
        funding_query = funding_filter
        expenses_query = expenses_filter
        projects_query = projects_filter
    else:
        members_query = Member.objects.filter(sacco__region=region)
        loans_query = Loan.objects.filter(member__sacco__region=region)
        savings_query = SavingsAccount.objects.filter(member__sacco__region=region)
        funding_query = Funding.objects.filter(sacco__region=region)
        expenses_query = Expense.objects.filter(sacco__region=region)
        projects_query = Project.objects.filter(sacco__region=region)
    
    total_saccos = regional_saccos.count() if not selected_sacco else 1
    total_members = members_query.count()
    total_loans = loans_query.count()
    total_savings = savings_query.count()
    total_funding = funding_query.count()
    
    # Financial metrics
    total_loan_amount = loans_query.aggregate(total=Sum('amount_requested'))['total'] or 0
    total_savings_balance = savings_query.aggregate(total=Sum('balance'))['total'] or 0
    total_funding_amount = funding_query.aggregate(total=Sum('amount'))['total'] or 0
    total_expenses = expenses_query.aggregate(total=Sum('amount'))['total'] or 0
    total_project_budget = projects_query.aggregate(total=Sum('budget'))['total'] or 0
    
    # Loan statistics
    from loans.constants import LOAN_STATUS_PENDING_APPROVAL, LOAN_STATUS_APPROVED, LOAN_STATUS_DECLINED, LOAN_STATUS_ACTIVE
    pending_loans = loans_query.filter(status=LOAN_STATUS_PENDING_APPROVAL).count()
    approved_loans = loans_query.filter(status=LOAN_STATUS_APPROVED).count()
    rejected_loans = loans_query.filter(status=LOAN_STATUS_DECLINED).count()
    active_loans = loans_query.filter(status=LOAN_STATUS_ACTIVE).count()
    
    # Member statistics
    from members.constants import MEMBER_STATUS_ACTIVE, MEMBER_STATUS_INACTIVE
    active_members = members_query.filter(status=MEMBER_STATUS_ACTIVE).count()
    inactive_members = members_query.filter(status=MEMBER_STATUS_INACTIVE).count()
    new_members_this_month = members_query.filter(
        date_joined__gte=timezone.now().replace(day=1)
    ).count()
    
    # Recent activity (last 30 days)
    thirty_days_ago = timezone.now() - timedelta(days=30)
    recent_members_count = members_query.filter(date_joined__gte=thirty_days_ago).count()
    recent_loans_count = loans_query.filter(application_date__gte=thirty_days_ago).count()
    recent_savings_count = savings_query.filter(created_at__gte=thirty_days_ago).count()
    
    # Saccos in the region with statistics
    saccos_with_stats = []
    saccos_to_display = [selected_sacco] if selected_sacco else regional_saccos
    for sacco in saccos_to_display:
        sacco_members = Member.objects.filter(sacco=sacco).count()
        sacco_loans = Loan.objects.filter(member__sacco=sacco).count()
        sacco_savings = SavingsAccount.objects.filter(member__sacco=sacco).count()
        sacco_funding = Funding.objects.filter(sacco=sacco).count()
        sacco_loan_amount = Loan.objects.filter(member__sacco=sacco).aggregate(
            total=Sum('amount_requested'))['total'] or 0
        sacco_savings_balance = SavingsAccount.objects.filter(member__sacco=sacco).aggregate(
            total=Sum('balance'))['total'] or 0
        
        saccos_with_stats.append({
            'sacco': sacco,
            'members_count': sacco_members,
            'loans_count': sacco_loans,
            'savings_count': sacco_savings,
            'funding_count': sacco_funding,
            'loan_amount': sacco_loan_amount,
            'savings_balance': sacco_savings_balance,
        })
    
    # Sort by total financial activity
    saccos_with_stats.sort(key=lambda x: x['loan_amount'] + x['savings_balance'], reverse=True)
    
    # Recent activity
    recent_members = members_query.select_related('sacco').order_by('-date_joined')[:10]
    recent_loans = loans_query.select_related('member__sacco').order_by('-application_date')[:10]
    recent_savings = savings_query.select_related('member__sacco').order_by('-created_at')[:10]
    
    # Regional alerts
    regional_alerts = []
    
    # Check for inactive Saccos in region (only show if no specific sacco selected)
    if not selected_sacco:
        inactive_saccos = Sacco.objects.filter(region=region, is_active=False).count()
        if inactive_saccos > 0:
            regional_alerts.append({
                'type': 'warning',
                'message': f'{inactive_saccos} inactive Saccos in your region need attention',
                'icon': 'bx-error'
            })
    else:
        # If specific sacco selected and it's inactive
        if not selected_sacco.is_active:
            regional_alerts.append({
                'type': 'warning',
                'message': f'{selected_sacco.name} is currently inactive',
                'icon': 'bx-error'
            })
    
    # Check for pending loans
    if pending_loans > 0:
        alert_message = f'{pending_loans} loan applications pending approval'
        if selected_sacco:
            alert_message += f' for {selected_sacco.name}'
        else:
            alert_message += ' in your region'
        regional_alerts.append({
            'type': 'info',
            'message': alert_message,
            'icon': 'bx-time'
        })
    
    # Check for low funding (only warn if significantly low)
    if total_funding_amount < 10000:  # Less than 10k
        alert_message = 'Total funding amount is below recommended threshold'
        if selected_sacco:
            alert_message += f' for {selected_sacco.name}'
        else:
            alert_message += ' in your region'
        regional_alerts.append({
            'type': 'info',
            'message': alert_message,
            'icon': 'bx-money'
        })
    
    context = {
        'region': region,
        'total_saccos': total_saccos,
        'total_members': total_members,
        'total_loans': total_loans,
        'total_savings': total_savings,
        'total_funding': total_funding,
        'total_loan_amount': total_loan_amount,
        'total_savings_balance': total_savings_balance,
        'total_funding_amount': total_funding_amount,
        'total_expenses': total_expenses,
        'total_project_budget': total_project_budget,
        'pending_loans': pending_loans,
        'approved_loans': approved_loans,
        'rejected_loans': rejected_loans,
        'active_loans': active_loans,
        'active_members': active_members,
        'inactive_members': inactive_members,
        'new_members_this_month': new_members_this_month,
        'recent_members_count': recent_members_count,
        'recent_loans_count': recent_loans_count,
        'recent_savings_count': recent_savings_count,
        'saccos_with_stats': saccos_with_stats,
        'recent_members': recent_members,
        'recent_loans': recent_loans,
        'recent_savings': recent_savings,
        'regional_alerts': regional_alerts,
        'accessible_saccos': accessible_saccos,
        'selected_sacco_id': selected_sacco_id,
        'selected_sacco': selected_sacco,
    }
    return render(request, 'regional_admin_dashboard.html', context)


@login_required
def sacco_admin_dashboard(request):
    if not request.user.is_sacco_admin:
        return redirect('dashboard')
    
    # Check if sacco exists and is active
    sacco = request.user.sacco
    if not sacco:
        messages.error(request, 'No Sacco assigned to your account. Please contact your administrator.')
        from django.contrib.auth import logout
        logout(request)
        return redirect('login')
    
    if not sacco.is_active:
        messages.error(request, 'Your Sacco has been deactivated. Please contact your regional administrator.')
        from django.contrib.auth import logout
        logout(request)
        return redirect('login')
    
    # Get statistics for the Sacco
    from django.db.models import Sum, Count
    from django.utils import timezone
    from datetime import date, timedelta
    from members.models import Member
    from loans.models import Loan
    from savings.models import SavingsAccount, SavingsTransaction
    from funding.models import Funding
    from expenses.models import Expense
    
    # Core counts
    total_members = Member.objects.filter(sacco=sacco).count()
    total_loans = Loan.objects.filter(member__sacco=sacco).count()
    total_savings_accounts = SavingsAccount.objects.filter(member__sacco=sacco).count()
    total_funding_sources = Funding.objects.filter(sacco=sacco).count()
    
    # Aggregated amounts
    total_savings_balance = SavingsAccount.objects.filter(member__sacco=sacco).aggregate(total=Sum('balance'))['total'] or 0
    loans_disbursed_amount = Loan.objects.filter(member__sacco=sacco, amount_disbursed__isnull=False).aggregate(total=Sum('amount_disbursed'))['total'] or 0
    funds_received_amount = Funding.objects.filter(sacco=sacco, status__in=['received', 'allocated', 'spent']).aggregate(total=Sum('amount'))['total'] or 0
    
    # Expenses over time (last 6 months)
    today = date.today()
    first_of_this_month = today.replace(day=1)
    six_months_ago = first_of_this_month - timedelta(days=5*31)  # approx 6 months window
    expenses_qs = Expense.objects.filter(sacco=sacco, expense_date__gte=six_months_ago)
    expenses_over_time = (
        expenses_qs
        .values('expense_date__year', 'expense_date__month')
        .annotate(total=Sum('amount'))
        .order_by('expense_date__year', 'expense_date__month')
    )
    
    # Gender distribution
    gender_counts_qs = Member.objects.filter(sacco=sacco).values('gender').annotate(total=Count('id'))
    gender_counts = {item['gender'] or 'Other': item['total'] for item in gender_counts_qs}
    
    # Recent savings deposits (last 10) - case-insensitive; fallback to any recent transactions if none
    recent_savings_deposits = (
        SavingsTransaction.objects
        .filter(account__member__sacco=sacco, txn_type__iexact='Deposit')
        .select_related('account__member')
        .order_by('-performed_at')[:10]
    )
    if not recent_savings_deposits:
        recent_savings_deposits = (
            SavingsTransaction.objects
            .filter(account__member__sacco=sacco)
            .select_related('account__member')
            .order_by('-performed_at')[:10]
        )
    
    # Existing recent lists
    recent_members = Member.objects.filter(sacco=sacco).order_by('-date_joined')[:5]
    recent_loans = Loan.objects.filter(member__sacco=sacco).order_by('-application_date')[:5]
    
    context = {
        'sacco': sacco,
        # counts
        'total_members': total_members,
        'total_loans': total_loans,
        'total_savings': total_savings_accounts,  # keep existing variable name for count
        'total_funding': total_funding_sources,   # keep existing variable name for count
        # aggregated amounts
        'total_savings_balance': total_savings_balance,
        'loans_disbursed_amount': loans_disbursed_amount,
        'funds_received_amount': funds_received_amount,
        # charts data
        'expenses_over_time': list(expenses_over_time),
        'gender_counts': gender_counts,
        # tables
        'recent_savings_deposits': recent_savings_deposits,
        # existing
        'recent_members': recent_members,
        'recent_loans': recent_loans,
    }
    return render(request, 'sacco_admin_dashboard.html', context)


@login_required
def create_sacco(request):
    if not request.user.is_system_admin and not request.user.is_regional_admin:
        messages.error(request, 'Access denied. Only administrators can create Saccos.')
        return redirect('dashboard')
    
    # Get available regions based on user role
    from accounts.models import District
    if request.user.is_system_admin:
        regions = Region.objects.filter(is_active=True)
        districts = District.objects.filter(is_active=True, region__is_active=True).order_by('region__name', 'name')
    else:  # Regional admin
        regions = Region.objects.filter(id=request.user.region.id, is_active=True)
        districts = District.objects.filter(region=request.user.region, is_active=True).order_by('name')
    
    if request.method == 'POST':
        try:
            # Get form data
            name = request.POST.get('name')
            address = request.POST.get('address')
            region_id = request.POST.get('region')
            district_id = request.POST.get('district')
            admin_username = request.POST.get('admin_username')
            admin_email = request.POST.get('admin_email')
            admin_first_name = request.POST.get('admin_first_name')
            admin_last_name = request.POST.get('admin_last_name')
            admin_password = request.POST.get('admin_password')
            admin_password_confirm = request.POST.get('admin_password_confirm')
            
            # Validate password confirmation
            if admin_password != admin_password_confirm:
                messages.error(request, 'Passwords do not match.')
                return render(request, 'accounts/create_sacco.html', {'regions': regions, 'districts': districts})
            
            if len(admin_password) < 8:
                messages.error(request, 'Password must be at least 8 characters long.')
                return render(request, 'accounts/create_sacco.html', {'regions': regions, 'districts': districts})
            
            # Get district first, then get region from district
            district = None
            region = None
            
            if district_id:
                try:
                    district = District.objects.get(id=district_id)
                    # Get region from district
                    region = district.region
                except District.DoesNotExist:
                    messages.error(request, 'Invalid district selected.')
                    return render(request, 'accounts/create_sacco.html', {'regions': regions, 'districts': districts})
            elif region_id:
                # Fallback: if region is provided but not district, get region
                try:
                    region = Region.objects.get(id=region_id)
                except Region.DoesNotExist:
                    messages.error(request, 'Invalid region selected.')
                    return render(request, 'accounts/create_sacco.html', {'regions': regions, 'districts': districts})
            else:
                messages.error(request, 'Please select a district.')
                return render(request, 'accounts/create_sacco.html', {'regions': regions, 'districts': districts})
            
            # Generate a unique registration number if not provided
            # Use a timestamp-based approach to ensure uniqueness
            from django.utils.text import slugify
            from datetime import datetime
            base_reg_number = slugify(name)[:50]  # Use first 50 chars of slugified name
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            registration_number = f"{base_reg_number}-{timestamp}"
            
            # Ensure uniqueness by checking if it exists
            while Sacco.objects.filter(registration_number=registration_number).exists():
                timestamp = datetime.now().strftime('%Y%m%d%H%M%S%f')
                registration_number = f"{base_reg_number}-{timestamp}"
            
            # Create Sacco with auto-generated registration number and placeholder contact info
            sacco = Sacco.objects.create(
                name=name,
                registration_number=registration_number,
                address=address,
                phone='N/A',  # Placeholder since field is required
                email=f'sacco-{registration_number}@system.local',  # Placeholder email since field is required
                region=region,
                district=district,
                is_active=True,
                created_by=request.user
            )
            
            # Create Sacco Admin user with provided password
            admin_user = User.objects.create_user(
                username=admin_username,
                email=admin_email,
                password=admin_password,
                first_name=admin_first_name,
                last_name=admin_last_name,
                sacco=sacco,
                is_sacco_admin=True,
                is_active=True
            )
            
            # Log activity
            log_activity(
                user=request.user,
                action='create',
                model_name='Sacco',
                object_id=sacco.id,
                object_name=sacco.name,
                description=f'Created Sacco "{sacco.name}" in region {region.name}',
                ip_address=get_client_ip(request),
                user_agent=get_user_agent(request),
                sacco=sacco,
                region=region
            )
            
            messages.success(request, 
                f'Sacco "{name}" created successfully! '
                f'Admin Username: {admin_username} - Password has been set as provided.'
            )
            
            if request.user.is_system_admin:
                return redirect('admin_dashboard')
            else:
                return redirect('regional_admin_dashboard')
            
        except Exception as e:
            messages.error(request, f'Error creating Sacco: {str(e)}')
    
    return render(request, 'accounts/create_sacco.html', {'regions': regions, 'districts': districts})


@login_required
def logout_view(request):
    # Log logout activity
    log_activity(
        user=request.user,
        action='logout',
        model_name='User',
        object_id=request.user.id,
        object_name=request.user.username,
        description=f'User {request.user.username} logged out',
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request)
    )
    
    # Clear inactivity tracking
    if 'last_activity' in request.session:
        del request.session['last_activity']
    if 'remember_me' in request.session:
        del request.session['remember_me']
    
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('login')


# System Admin Management Views
@login_required
def manage_regions(request):
    """System admin view to manage regions"""
    if not request.user.is_system_admin:
        messages.error(request, 'Access denied. Only system administrators can manage regions.')
        return redirect('dashboard')
    
    regions = Region.objects.all().order_by('name')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create':
            name = request.POST.get('name')
            description = request.POST.get('description')
            
            if Region.objects.filter(name=name).exists():
                messages.error(request, 'A region with this name already exists.')
            else:
                region = Region.objects.create(name=name, description=description)
                log_activity(
                    user=request.user,
                    action='create',
                    model_name='Region',
                    object_id=region.id,
                    object_name=region.name,
                    description=f'Created region "{region.name}"',
                    ip_address=get_client_ip(request),
                    user_agent=get_user_agent(request)
                )
                messages.success(request, f'Region "{name}" created successfully.')
        
        elif action == 'update':
            region_id = request.POST.get('region_id')
            name = request.POST.get('name')
            description = request.POST.get('description')
            
            try:
                region = Region.objects.get(id=region_id)
                old_name = region.name
                region.name = name
                region.description = description
                region.save()
                
                log_activity(
                    user=request.user,
                    action='update',
                    model_name='Region',
                    object_id=region.id,
                    object_name=region.name,
                    description=f'Updated region from "{old_name}" to "{region.name}"',
                    ip_address=get_client_ip(request),
                    user_agent=get_user_agent(request)
                )
                messages.success(request, f'Region updated successfully.')
            except Region.DoesNotExist:
                messages.error(request, 'Region not found.')
        
        elif action == 'toggle_status':
            region_id = request.POST.get('region_id')
            try:
                region = Region.objects.get(id=region_id)
                region.is_active = not region.is_active
                region.save()
                
                status = 'activated' if region.is_active else 'deactivated'
                log_activity(
                    user=request.user,
                    action='activate' if region.is_active else 'deactivate',
                    model_name='Region',
                    object_id=region.id,
                    object_name=region.name,
                    description=f'Region "{region.name}" {status}',
                    ip_address=get_client_ip(request),
                    user_agent=get_user_agent(request)
                )
                messages.success(request, f'Region {status} successfully.')
            except Region.DoesNotExist:
                messages.error(request, 'Region not found.')
        
        return redirect('manage_regions')
    
    return render(request, 'admin/manage_regions.html', {'regions': regions})


@login_required
def manage_regional_admins(request):
    """System admin view to manage regional administrators"""
    if not request.user.is_system_admin:
        messages.error(request, 'Access denied. Only system administrators can manage regional admins.')
        return redirect('dashboard')
    
    regional_admins = User.objects.filter(is_regional_admin=True).select_related('region')
    regions = Region.objects.filter(is_active=True)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create':
            username = request.POST.get('username')
            email = request.POST.get('email')
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            password = request.POST.get('password')
            region_id = request.POST.get('region')
            
            if User.objects.filter(username=username).exists():
                messages.error(request, 'Username already exists.')
            elif User.objects.filter(email=email).exists():
                messages.error(request, 'Email already exists.')
            else:
                try:
                    region = Region.objects.get(id=region_id)
                    admin_user = User.objects.create_user(
                        username=username,
                        email=email,
                        password=password,
                        first_name=first_name,
                        last_name=last_name,
                        region=region,
                        is_regional_admin=True,
                        is_active=True
                    )
                    
                    log_activity(
                        user=request.user,
                        action='create',
                        model_name='User',
                        object_id=admin_user.id,
                        object_name=admin_user.username,
                        description=f'Created regional admin "{admin_user.username}" for region {region.name}',
                        ip_address=get_client_ip(request),
                        user_agent=get_user_agent(request),
                        region=region
                    )
                    messages.success(request, f'Regional admin "{username}" created successfully.')
                except Region.DoesNotExist:
                    messages.error(request, 'Invalid region selected.')
        
        elif action == 'reassign':
            admin_id = request.POST.get('admin_id')
            new_region_id = request.POST.get('new_region')
            
            try:
                admin_user = User.objects.get(id=admin_id, is_regional_admin=True)
                old_region = admin_user.region
                new_region = Region.objects.get(id=new_region_id)
                
                admin_user.region = new_region
                admin_user.save()
                
                log_activity(
                    user=request.user,
                    action='update',
                    model_name='User',
                    object_id=admin_user.id,
                    object_name=admin_user.username,
                    description=f'Reassigned regional admin "{admin_user.username}" from {old_region.name} to {new_region.name}',
                    ip_address=get_client_ip(request),
                    user_agent=get_user_agent(request),
                    region=new_region
                )
                messages.success(request, f'Regional admin reassigned successfully.')
            except (User.DoesNotExist, Region.DoesNotExist):
                messages.error(request, 'Invalid selection.')
        
        elif action == 'toggle_status':
            admin_id = request.POST.get('admin_id')
            try:
                admin_user = User.objects.get(id=admin_id, is_regional_admin=True)
                admin_user.is_active = not admin_user.is_active
                admin_user.save()
                
                status = 'activated' if admin_user.is_active else 'deactivated'
                log_activity(
                    user=request.user,
                    action='activate' if admin_user.is_active else 'deactivate',
                    model_name='User',
                    object_id=admin_user.id,
                    object_name=admin_user.username,
                    description=f'Regional admin "{admin_user.username}" {status}',
                    ip_address=get_client_ip(request),
                    user_agent=get_user_agent(request),
                    region=admin_user.region
                )
                messages.success(request, f'Regional admin {status} successfully.')
            except User.DoesNotExist:
                messages.error(request, 'Regional admin not found.')
        
        return redirect('manage_regional_admins')
    
    return render(request, 'admin/manage_regional_admins.html', {
        'regional_admins': regional_admins,
        'regions': regions
    })


@login_required
def manage_saccos(request):
    """System admin view to manage all Saccos"""
    if not request.user.is_system_admin:
        messages.error(request, 'Access denied. Only system administrators can manage all Saccos.')
        return redirect('dashboard')
    
    saccos = Sacco.objects.select_related('region', 'created_by').all().order_by('-created_at')
    regions = Region.objects.filter(is_active=True)
    
    # Apply filters
    region_filter = request.GET.get('region')
    status_filter = request.GET.get('status')
    
    if region_filter:
        saccos = saccos.filter(region_id=region_filter)
    if status_filter:
        if status_filter == 'active':
            saccos = saccos.filter(is_active=True)
        elif status_filter == 'inactive':
            saccos = saccos.filter(is_active=False)
    
    # Pagination
    paginator = Paginator(saccos, 20)
    page_number = request.GET.get('page')
    saccos_page = paginator.get_page(page_number)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'toggle_status':
            sacco_id = request.POST.get('sacco_id')
            try:
                sacco = Sacco.objects.get(id=sacco_id)
                sacco.is_active = not sacco.is_active
                sacco.save()
                
                status = 'activated' if sacco.is_active else 'deactivated'
                log_activity(
                    user=request.user,
                    action='activate' if sacco.is_active else 'deactivate',
                    model_name='Sacco',
                    object_id=sacco.id,
                    object_name=sacco.name,
                    description=f'Sacco "{sacco.name}" {status}',
                    ip_address=get_client_ip(request),
                    user_agent=get_user_agent(request),
                    sacco=sacco,
                    region=sacco.region
                )
                messages.success(request, f'Sacco {status} successfully.')
            except Sacco.DoesNotExist:
                messages.error(request, 'Sacco not found.')
        
        elif action == 'reassign_region':
            sacco_id = request.POST.get('sacco_id')
            new_region_id = request.POST.get('new_region')
            
            try:
                sacco = Sacco.objects.get(id=sacco_id)
                old_region = sacco.region
                new_region = Region.objects.get(id=new_region_id)
                
                sacco.region = new_region
                sacco.save()
                
                log_activity(
                    user=request.user,
                    action='update',
                    model_name='Sacco',
                    object_id=sacco.id,
                    object_name=sacco.name,
                    description=f'Reassigned Sacco "{sacco.name}" from {old_region.name} to {new_region.name}',
                    ip_address=get_client_ip(request),
                    user_agent=get_user_agent(request),
                    sacco=sacco,
                    region=new_region
                )
                messages.success(request, f'Sacco reassigned successfully.')
            except (Sacco.DoesNotExist, Region.DoesNotExist):
                messages.error(request, 'Invalid selection.')
        
        return redirect('manage_saccos')
    
    return render(request, 'admin/manage_saccos.html', {
        'saccos': saccos_page,
        'regions': regions
    })


@login_required
def regional_manage_saccos(request):
    """Regional admin view to manage Saccos in their region"""
    if not request.user.is_regional_admin:
        messages.error(request, 'Access denied. Only regional administrators can manage Saccos.')
        return redirect('dashboard')
    
    saccos = Sacco.objects.filter(region=request.user.region).select_related('created_by').order_by('-created_at')
    
    # Pagination
    paginator = Paginator(saccos, 20)
    page_number = request.GET.get('page')
    saccos_page = paginator.get_page(page_number)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'toggle_status':
            sacco_id = request.POST.get('sacco_id')
            try:
                sacco = Sacco.objects.get(id=sacco_id, region=request.user.region)
                sacco.is_active = not sacco.is_active
                sacco.save()
                
                status = 'activated' if sacco.is_active else 'deactivated'
                log_activity(
                    user=request.user,
                    action='activate' if sacco.is_active else 'deactivate',
                    model_name='Sacco',
                    object_id=sacco.id,
                    object_name=sacco.name,
                    description=f'Sacco "{sacco.name}" {status}',
                    ip_address=get_client_ip(request),
                    user_agent=get_user_agent(request),
                    sacco=sacco,
                    region=request.user.region
                )
                messages.success(request, f'Sacco {status} successfully.')
            except Sacco.DoesNotExist:
                messages.error(request, 'Sacco not found.')
        
        return redirect('regional_manage_saccos')
    
    return render(request, 'admin/regional_manage_saccos.html', {
        'saccos': saccos_page,
        'region': request.user.region
    })


@login_required
def regional_overview(request):
    """System admin view to see all regions and their Saccos"""
    if not request.user.is_system_admin:
        messages.error(request, 'Access denied. Only system administrators can view regional overview.')
        return redirect('dashboard')
    
    # Log dashboard access
    log_activity(
        user=request.user,
        action='view',
        model_name='RegionalOverview',
        description=f'System admin {request.user.username} accessed regional overview',
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request)
    )
    
    # Get selected region from query parameter
    selected_region_id = request.GET.get('region')
    selected_region = None
    
    # Filter regions if a specific region is selected
    regions_to_display = Region.objects.filter(is_active=True).order_by('name')
    if selected_region_id:
        try:
            selected_region = Region.objects.get(id=selected_region_id, is_active=True)
            regions_to_display = Region.objects.filter(id=selected_region_id, is_active=True)
        except Region.DoesNotExist:
            pass
    
    # Get all regions with their statistics
    from members.models import Member
    from loans.models import Loan
    from savings.models import SavingsAccount
    from funding.models import Funding
    from django.db.models import Sum, Count
    
    regions_with_stats = []
    for region in regions_to_display:
        # Get Saccos in this region
        regional_saccos = Sacco.objects.filter(region=region, is_active=True)
        total_saccos = regional_saccos.count()
        inactive_saccos = Sacco.objects.filter(region=region, is_active=False).count()
        
        # Get regional statistics
        total_members = Member.objects.filter(sacco__region=region).count()
        total_loans = Loan.objects.filter(member__sacco__region=region).count()
        total_savings = SavingsAccount.objects.filter(member__sacco__region=region).count()
        total_funding = Funding.objects.filter(sacco__region=region).count()
        
        # Financial metrics
        total_loan_amount = Loan.objects.filter(member__sacco__region=region).aggregate(total=Sum('amount_requested'))['total'] or 0
        total_savings_balance = SavingsAccount.objects.filter(member__sacco__region=region).aggregate(total=Sum('balance'))['total'] or 0
        total_funding_amount = Funding.objects.filter(sacco__region=region).aggregate(total=Sum('amount'))['total'] or 0
        
        # Regional admin info
        regional_admin = User.objects.filter(region=region, is_regional_admin=True, is_active=True).first()
        
        regions_with_stats.append({
            'region': region,
            'total_saccos': total_saccos,
            'inactive_saccos': inactive_saccos,
            'total_members': total_members,
            'total_loans': total_loans,
            'total_savings': total_savings,
            'total_funding': total_funding,
            'total_loan_amount': total_loan_amount,
            'total_savings_balance': total_savings_balance,
            'total_funding_amount': total_funding_amount,
            'regional_admin': regional_admin,
            'saccos': regional_saccos,
        })
    
    # System-wide statistics
    total_regions = Region.objects.filter(is_active=True).count()
    total_saccos_system = Sacco.objects.filter(is_active=True).count()
    total_members_system = Member.objects.count()
    total_loans_system = Loan.objects.count()
    
    # Get all regions for the selector dropdown
    all_regions = Region.objects.filter(is_active=True).order_by('name')
    
    return render(request, 'admin/regional_overview.html', {
        'regions_with_stats': regions_with_stats,
        'total_regions': total_regions,
        'total_saccos_system': total_saccos_system,
        'total_members_system': total_members_system,
        'total_loans_system': total_loans_system,
        'all_regions': all_regions,
        'selected_region_id': selected_region_id,
        'selected_region': selected_region,
    })


@login_required
def region_detail(request, region_id):
    """System admin view to see detailed information about a specific region"""
    if not request.user.is_system_admin:
        messages.error(request, 'Access denied. Only system administrators can view region details.')
        return redirect('dashboard')
    
    try:
        region = Region.objects.get(id=region_id)
    except Region.DoesNotExist:
        messages.error(request, 'Region not found.')
        return redirect('regional_overview')
    
    # Log region detail access
    log_activity(
        user=request.user,
        action='view',
        model_name='Region',
        object_id=region.id,
        object_name=region.name,
        description=f'System admin {request.user.username} viewed region details for {region.name}',
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
        region=region
    )
    
    # Get Districts in this region
    from accounts.models import District
    districts = District.objects.filter(region=region, is_active=True).order_by('name')
    
    # Get Saccos in this region
    saccos = Sacco.objects.filter(region=region).select_related('created_by', 'district').order_by('-created_at')
    
    # Get regional statistics
    from members.models import Member
    from loans.models import Loan
    from savings.models import SavingsAccount
    from funding.models import Funding
    from django.db.models import Sum, Count
    from django.utils import timezone
    from datetime import timedelta
    
    # Group saccos by district
    districts_with_saccos = []
    for district in districts:
        district_saccos = saccos.filter(district=district)
        district_saccos_with_stats = []
        
        for sacco in district_saccos:
            sacco_members = Member.objects.filter(sacco=sacco).count()
            sacco_loans = Loan.objects.filter(member__sacco=sacco).count()
            sacco_savings = SavingsAccount.objects.filter(member__sacco=sacco).count()
            sacco_loan_amount = Loan.objects.filter(member__sacco=sacco).aggregate(total=Sum('amount_requested'))['total'] or 0
            sacco_savings_balance = SavingsAccount.objects.filter(member__sacco=sacco).aggregate(total=Sum('balance'))['total'] or 0
            
            district_saccos_with_stats.append({
                'sacco': sacco,
                'members_count': sacco_members,
                'loans_count': sacco_loans,
                'savings_count': sacco_savings,
                'loan_amount': sacco_loan_amount,
                'savings_balance': sacco_savings_balance,
            })
        
        # District statistics
        district_members = Member.objects.filter(sacco__district=district).count()
        district_loans = Loan.objects.filter(member__sacco__district=district).count()
        district_savings = SavingsAccount.objects.filter(member__sacco__district=district).count()
        district_loan_amount = Loan.objects.filter(member__sacco__district=district).aggregate(total=Sum('amount_requested'))['total'] or 0
        district_savings_balance = SavingsAccount.objects.filter(member__sacco__district=district).aggregate(total=Sum('balance'))['total'] or 0
        
        districts_with_saccos.append({
            'district': district,
            'saccos': district_saccos_with_stats,
            'saccos_count': district_saccos.count(),
            'members_count': district_members,
            'loans_count': district_loans,
            'savings_count': district_savings,
            'loan_amount': district_loan_amount,
            'savings_balance': district_savings_balance,
        })
    
    # Saccos without district
    saccos_without_district = saccos.filter(district__isnull=True)
    saccos_without_district_stats = []
    for sacco in saccos_without_district:
        sacco_members = Member.objects.filter(sacco=sacco).count()
        sacco_loans = Loan.objects.filter(member__sacco=sacco).count()
        sacco_savings = SavingsAccount.objects.filter(member__sacco=sacco).count()
        sacco_loan_amount = Loan.objects.filter(member__sacco=sacco).aggregate(total=Sum('amount_requested'))['total'] or 0
        sacco_savings_balance = SavingsAccount.objects.filter(member__sacco=sacco).aggregate(total=Sum('balance'))['total'] or 0
        
        saccos_without_district_stats.append({
            'sacco': sacco,
            'members_count': sacco_members,
            'loans_count': sacco_loans,
            'savings_count': sacco_savings,
            'loan_amount': sacco_loan_amount,
            'savings_balance': sacco_savings_balance,
        })
    
    # Basic counts
    total_saccos = saccos.count()
    active_saccos = saccos.filter(is_active=True).count()
    inactive_saccos = saccos.filter(is_active=False).count()
    
    total_members = Member.objects.filter(sacco__region=region).count()
    total_loans = Loan.objects.filter(member__sacco__region=region).count()
    total_savings = SavingsAccount.objects.filter(member__sacco__region=region).count()
    total_funding = Funding.objects.filter(sacco__region=region).count()
    
    # Financial metrics
    total_loan_amount = Loan.objects.filter(member__sacco__region=region).aggregate(total=Sum('amount_requested'))['total'] or 0
    total_savings_balance = SavingsAccount.objects.filter(member__sacco__region=region).aggregate(total=Sum('balance'))['total'] or 0
    total_funding_amount = Funding.objects.filter(sacco__region=region).aggregate(total=Sum('amount'))['total'] or 0
    
    # Loan statistics
    pending_loans = Loan.objects.filter(member__sacco__region=region, status='pending').count()
    approved_loans = Loan.objects.filter(member__sacco__region=region, status='approved').count()
    active_loans = Loan.objects.filter(member__sacco__region=region, status='active').count()
    
    # Recent activity
    thirty_days_ago = timezone.now() - timedelta(days=30)
    recent_members = Member.objects.filter(sacco__region=region).select_related('sacco').order_by('-date_joined')[:10]
    recent_loans = Loan.objects.filter(member__sacco__region=region).select_related('member__sacco').order_by('-application_date')[:10]
    
    # Regional admin
    regional_admin = User.objects.filter(region=region, is_regional_admin=True, is_active=True).first()
    
    # Saccos with detailed stats
    saccos_with_stats = []
    for sacco in saccos:
        sacco_members = Member.objects.filter(sacco=sacco).count()
        sacco_loans = Loan.objects.filter(member__sacco=sacco).count()
        sacco_savings = SavingsAccount.objects.filter(member__sacco=sacco).count()
        sacco_loan_amount = Loan.objects.filter(member__sacco=sacco).aggregate(total=Sum('amount_requested'))['total'] or 0
        sacco_savings_balance = SavingsAccount.objects.filter(member__sacco=sacco).aggregate(total=Sum('balance'))['total'] or 0
        
        saccos_with_stats.append({
            'sacco': sacco,
            'members_count': sacco_members,
            'loans_count': sacco_loans,
            'savings_count': sacco_savings,
            'loan_amount': sacco_loan_amount,
            'savings_balance': sacco_savings_balance,
        })
    
    return render(request, 'admin/region_detail.html', {
        'region': region,
        'districts_with_saccos': districts_with_saccos,
        'saccos': saccos,
        'saccos_with_stats': saccos_with_stats,
        'saccos_without_district_stats': saccos_without_district_stats,
        'total_saccos': total_saccos,
        'active_saccos': active_saccos,
        'inactive_saccos': inactive_saccos,
        'total_members': total_members,
        'total_loans': total_loans,
        'total_savings': total_savings,
        'total_funding': total_funding,
        'total_loan_amount': total_loan_amount,
        'total_savings_balance': total_savings_balance,
        'total_funding_amount': total_funding_amount,
        'pending_loans': pending_loans,
        'approved_loans': approved_loans,
        'active_loans': active_loans,
        'recent_members': recent_members,
        'recent_loans': recent_loans,
        'regional_admin': regional_admin,
    })


@login_required
def user_profile(request):
    """User profile page"""
    user = request.user
    
    # Get user's role
    if user.is_system_admin:
        role = "System Administrator"
    elif user.is_regional_admin:
        role = "Regional Administrator"
    elif user.is_sacco_admin:
        role = "Sacco Administrator"
    else:
        role = "Member"
    
    # Get recent activity
    recent_activities = ActivityLog.objects.filter(user=user).order_by('-timestamp')[:10]
    
    # Get statistics based on role
    stats = {}
    if user.is_sacco_admin and user.sacco:
        from members.models import Member
        from loans.models import Loan
        from savings.models import SavingsAccount
        stats = {
            'total_members': Member.objects.filter(sacco=user.sacco).count(),
            'total_loans': Loan.objects.filter(member__sacco=user.sacco).count(),
            'total_savings': SavingsAccount.objects.filter(member__sacco=user.sacco).count(),
        }
    elif user.is_regional_admin and user.region:
        from members.models import Member
        from loans.models import Loan
        stats = {
            'total_saccos': Sacco.objects.filter(region=user.region).count(),
            'total_members': Member.objects.filter(sacco__region=user.region).count(),
            'total_loans': Loan.objects.filter(member__sacco__region=user.region).count(),
        }
    elif user.is_system_admin:
        stats = {
            'total_regions': Region.objects.filter(is_active=True).count(),
            'total_saccos': Sacco.objects.filter(is_active=True).count(),
            'total_users': User.objects.filter(is_active=True).count(),
        }
    
    return render(request, 'accounts/profile.html', {
        'profile_user': user,
        'role': role,
        'recent_activities': recent_activities,
        'stats': stats,
    })


def custom_404(request, exception):
    return render(request, 'errors/404.html', status=404)


def custom_500(request):
    return render(request, 'errors/500.html', status=500)


@login_required
def documents_update(request):
    """Documents update view for admin to review documents by sacco"""
    from accounts.permissions import get_accessible_saccos
    from members.models import Document
    from django.contrib.contenttypes.models import ContentType
    
    if not (request.user.is_system_admin or request.user.is_regional_admin):
        messages.error(request, 'Access denied. Only administrators can access this page.')
        return redirect('dashboard')
    
    # Get accessible saccos
    accessible_saccos = get_accessible_saccos(request.user)
    
    # Get selected sacco from query parameter
    selected_sacco_id = request.GET.get('sacco')
    # Normalize to string for proper comparison
    if selected_sacco_id:
        try:
            selected_sacco_id = str(int(selected_sacco_id))
        except (ValueError, TypeError):
            selected_sacco_id = None
    selected_sacco = None
    
    # Filter documents based on selected sacco
    # Documents are linked to members via ContentType
    from members.models import Member as MemberModel
    member_content_type = ContentType.objects.get_for_model(MemberModel)
    documents = Document.objects.filter(owner_content_type=member_content_type)
    
    # Get members from accessible saccos
    accessible_members = MemberModel.objects.filter(sacco__in=accessible_saccos)
    documents = documents.filter(object_id__in=accessible_members.values_list('id', flat=True))
    
    # If specific sacco selected, filter further
    if selected_sacco_id:
        try:
            selected_sacco = Sacco.objects.get(id=selected_sacco_id)
            if selected_sacco in accessible_saccos:
                sacco_members = MemberModel.objects.filter(sacco=selected_sacco)
                documents = documents.filter(object_id__in=sacco_members.values_list('id', flat=True))
        except Sacco.DoesNotExist:
            pass
    
    # Prefetch related data
    documents = documents.select_related('uploaded_by').prefetch_related('owner_content_type').order_by('-uploaded_at')
    
    # Group documents by member
    documents_by_member = {}
    for doc in documents:
        try:
            member = MemberModel.objects.get(id=doc.object_id)
            if member.sacco.name not in documents_by_member:
                documents_by_member[member.sacco.name] = {}
            if member.id not in documents_by_member[member.sacco.name]:
                documents_by_member[member.sacco.name][member.id] = {
                    'member': member,
                    'documents': []
                }
            documents_by_member[member.sacco.name][member.id]['documents'].append(doc)
        except Member.DoesNotExist:
            continue
    
    return render(request, 'accounts/documents_update.html', {
        'accessible_saccos': accessible_saccos,
        'selected_sacco_id': selected_sacco_id,
        'selected_sacco': selected_sacco,
        'documents_by_member': documents_by_member,
        'total_documents': documents.count(),
    })


@login_required
def activity_logs(request):
    """View activity logs - accessible by system and regional admins"""
    if not request.user.is_system_admin and not request.user.is_regional_admin:
        messages.error(request, 'Access denied. Only administrators can view activity logs.')
        return redirect('dashboard')
    
    # Get activities based on user role
    if request.user.is_system_admin:
        activities = ActivityLog.objects.select_related('user', 'sacco', 'region').all()
    else:  # Regional admin
        activities = ActivityLog.objects.filter(region=request.user.region).select_related('user', 'sacco')
    
    # Filtering
    action_filter = request.GET.get('action')
    model_filter = request.GET.get('model')
    sacco_filter = request.GET.get('sacco')
    region_filter = request.GET.get('region')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    if action_filter:
        activities = activities.filter(action=action_filter)
    if model_filter:
        activities = activities.filter(model_name=model_filter)
    if sacco_filter:
        activities = activities.filter(sacco_id=sacco_filter)
    if region_filter:
        activities = activities.filter(region_id=region_filter)
    if date_from:
        activities = activities.filter(timestamp__date__gte=date_from)
    if date_to:
        activities = activities.filter(timestamp__date__lte=date_to)
    
    # Pagination
    paginator = Paginator(activities, 50)
    page_number = request.GET.get('page')
    activities_page = paginator.get_page(page_number)
    
    # Get filter options
    actions = ActivityLog.ACTION_CHOICES
    models = ActivityLog.objects.values_list('model_name', flat=True).distinct().order_by('model_name')
    saccos = Sacco.objects.filter(region=request.user.region if request.user.is_regional_admin else None).order_by('name')
    regions = Region.objects.filter(is_active=True).order_by('name') if request.user.is_system_admin else None
    
    return render(request, 'admin/activity_logs.html', {
        'activities': activities_page,
        'actions': actions,
        'models': models,
        'saccos': saccos,
        'regions': regions,
        'current_filters': {
            'action': action_filter,
            'model': model_filter,
            'sacco': sacco_filter,
            'region': region_filter,
            'date_from': date_from,
            'date_to': date_to,
        }
    })


def forgot_password(request):
    """Handle forgot password requests"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            email = data.get('email')
            
            if not email:
                return JsonResponse({'success': False, 'message': 'Email address is required.'})
            
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                return JsonResponse({'success': False, 'message': 'No account found with this email address.'})
            
            # Generate password reset token
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            
            # Get current site
            current_site = get_current_site(request)
            
            # Create reset link
            reset_link = f"{request.scheme}://{current_site.domain}/accounts/reset-password/{uid}/{token}/"
            
            # Send email
            subject = 'Password Reset Request - UMSC Sacco Management System'
            message = render_to_string('accounts/password_reset_email.html', {
                'user': user,
                'reset_link': reset_link,
                'site_name': current_site.name,
            })
            
            try:
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    html_message=message,
                    fail_silently=False,
                )
                return JsonResponse({'success': True, 'message': 'Password reset link has been sent to your email.'})
            except Exception as e:
                return JsonResponse({'success': False, 'message': f'Failed to send email: {str(e)}'})
                
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'message': 'Invalid request data.'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'An error occurred: {str(e)}'})
    
    return JsonResponse({'success': False, 'message': 'Invalid request method.'})


def reset_password(request, uidb64, token):
    """Handle password reset"""
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    
    if user is not None and default_token_generator.check_token(user, token):
        if request.method == 'POST':
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')
            
            if new_password != confirm_password:
                messages.error(request, 'Passwords do not match.')
                return render(request, 'accounts/reset_password.html', {'valid_link': True})
            
            if len(new_password) < 8:
                messages.error(request, 'Password must be at least 8 characters long.')
                return render(request, 'accounts/reset_password.html', {'valid_link': True})
            
            # Set new password
            user.set_password(new_password)
            user.save()
            
            messages.success(request, 'Your password has been reset successfully. You can now log in with your new password.')
            return redirect('login')
        
        return render(request, 'accounts/reset_password.html', {'valid_link': True})
    else:
        messages.error(request, 'Invalid or expired password reset link.')
        return redirect('login')