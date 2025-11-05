from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Sum
from django.utils import timezone
from accounts.decorators import sacco_admin_required
from .models import SaccoReviewPeriod, SaccoKRA, SaccoKPI, SaccoKPIResult
from .forms import ReviewPeriodForm, KRAForm, KPIForm, KPIResultForm


def _get_or_create_active_quarter(sacco):
    # Auto-create current quarter if none exists (best-practice default)
    if not sacco:
        raise ValueError("Sacco cannot be None when creating review period")
    
    today = timezone.now().date()
    q = (today.month - 1) // 3 + 1
    start_month = 3 * (q - 1) + 1
    start_date = today.replace(month=start_month, day=1)
    if start_month + 3 > 12:
        # end of year
        end_date = today.replace(month=12, day=31)
    else:
        from datetime import date
        next_start_month = start_month + 3
        end_date = date(today.year, next_start_month, 1) - timezone.timedelta(days=1)
    name = f"Q{q} {today.year}"
    period = SaccoReviewPeriod.objects.filter(sacco=sacco, name=name).first()
    if not period:
        period = SaccoReviewPeriod.objects.create(
            sacco=sacco, name=name, start_date=start_date, end_date=end_date, status='active'
        )
    elif period.status != 'active':
        # Make it active if no other active period
        if not SaccoReviewPeriod.objects.filter(sacco=sacco, status='active').exclude(id=period.id).exists():
            period.status = 'active'
            period.save(update_fields=['status'])
    return period


@sacco_admin_required
def performance_overview(request):
    from accounts.models import Sacco
    
    # Handle system admin - allow sacco selection
    if request.user.is_system_admin:
        sacco_id = request.GET.get('sacco')
        if not sacco_id:
            # Get first active sacco as default, or show selection
            first_sacco = Sacco.objects.filter(is_active=True).select_related('region').first()
            if first_sacco:
                sacco = first_sacco
            else:
                saccos = Sacco.objects.filter(is_active=True).select_related('region').order_by('name')
                return render(request, 'reports/select_sacco.html', {'saccos': saccos})
        else:
            sacco = get_object_or_404(Sacco, id=sacco_id, is_active=True)
    else:
        sacco = request.user.sacco
        if not sacco:
            messages.error(request, 'No Sacco assigned to your account. Please contact your administrator.')
            return redirect('dashboard')
    
    # Ensure there's an active period by default
    active_period = SaccoReviewPeriod.objects.filter(sacco=sacco, status='active').first() or _get_or_create_active_quarter(sacco)

    selected_period_id = request.GET.get('period')
    if selected_period_id:
        period = get_object_or_404(SaccoReviewPeriod, id=selected_period_id, sacco=sacco)
    else:
        period = active_period

    kras = SaccoKRA.objects.filter(sacco=sacco, is_active=True).prefetch_related('kpis')
    kpis = SaccoKPI.objects.filter(kra__sacco=sacco, is_active=True)
    results = SaccoKPIResult.objects.filter(period=period, kpi__kra__sacco=sacco).select_related('kpi', 'kpi__kra')

    # Build scoring
    kpi_id_to_result = {r.kpi_id: r for r in results}
    kra_rows = []
    overall_score = 0.0
    for kra in kras:
        kra_score_sum = 0.0
        kra_achievements = []
        kpi_rows = []
        for kpi in kra.kpis.filter(is_active=True):
            res = kpi_id_to_result.get(kpi.id)
            achievement = res.achievement_percent if res else 0.0
            score = res.weighted_score if res else 0.0
            kra_score_sum += score
            kra_achievements.append(achievement)
            kpi_rows.append({
                'kpi': kpi,
                'result': res,
                'achievement': round(achievement, 2),
                'score': round(score, 2),
            })
        kra_achievement_avg = round(sum(kra_achievements) / len(kra_achievements), 2) if kra_achievements else 0.0
        kra_rows.append({
            'kra': kra,
            'kpis': kpi_rows,
            'kra_score': round(kra_score_sum, 2),
            'kra_achievement': kra_achievement_avg,
        })
        overall_score += kra_score_sum

    periods = SaccoReviewPeriod.objects.filter(sacco=sacco).order_by('-start_date')
    
    # Get all accessible saccos for system admin dropdown
    accessible_saccos = None
    if request.user.is_system_admin:
        from accounts.permissions import get_accessible_saccos
        accessible_saccos = get_accessible_saccos(request.user).select_related('region').order_by('name')

    # Build score trend over recent periods (overall score)
    trend_labels = []
    trend_scores = []
    recent_periods = list(periods[:6])[::-1]
    for p in recent_periods:
        p_results = SaccoKPIResult.objects.filter(period=p, kpi__kra__sacco=sacco).select_related('kpi')
        total = 0.0
        for r in p_results:
            total += r.weighted_score
        trend_labels.append(p.name)
        trend_scores.append(round(total, 2))

    context = {
        'period': period,
        'periods': periods,
        'kra_rows': kra_rows,
        'overall_score': round(overall_score, 2),
        'trend_labels': trend_labels,
        'trend_scores': trend_scores,
        'sacco': sacco,
        'accessible_saccos': accessible_saccos,
    }
    return render(request, 'reports/performance_overview.html', context)


@sacco_admin_required
def manage_kras(request):
    from accounts.models import Sacco
    
    # Handle system admin - allow sacco selection
    if request.user.is_system_admin:
        sacco_id = request.GET.get('sacco')
        if not sacco_id:
            # Get first active sacco as default, or show selection
            first_sacco = Sacco.objects.filter(is_active=True).select_related('region').first()
            if first_sacco:
                sacco = first_sacco
            else:
                saccos = Sacco.objects.filter(is_active=True).select_related('region').order_by('name')
                return render(request, 'reports/select_sacco.html', {'saccos': saccos})
        else:
            sacco = get_object_or_404(Sacco, id=sacco_id, is_active=True)
    else:
        sacco = request.user.sacco
        if not sacco:
            messages.error(request, 'No Sacco assigned to your account. Please contact your administrator.')
            return redirect('dashboard')
    form = KRAForm()
    if request.method == 'POST':
        action = request.POST.get('action', 'create_or_update')
        kra_id = request.POST.get('kra_id')

        if action == 'delete' and kra_id:
            kra = get_object_or_404(SaccoKRA, id=kra_id, sacco=sacco)
            kra.delete()
            messages.success(request, 'KRA deleted successfully')
            if request.user.is_system_admin:
                from django.urls import reverse
                return redirect(f"{reverse('reports_performance_kras')}?sacco={sacco.id}")
            return redirect('reports_performance_kras')

        if action == 'toggle' and kra_id:
            kra = get_object_or_404(SaccoKRA, id=kra_id, sacco=sacco)
            kra.is_active = not kra.is_active
            kra.save(update_fields=['is_active'])
            messages.success(request, f"KRA set to {'Active' if kra.is_active else 'Inactive'}")
            if request.user.is_system_admin:
                from django.urls import reverse
                return redirect(f"{reverse('reports_performance_kras')}?sacco={sacco.id}")
            return redirect('reports_performance_kras')

        # create or update
        instance = None
        if kra_id:
            instance = get_object_or_404(SaccoKRA, id=kra_id, sacco=sacco)
        form = KRAForm(request.POST, instance=instance)
        if form.is_valid():
            kra = form.save(commit=False)
            kra.sacco = sacco
            kra.save()
            messages.success(request, 'KRA saved successfully')
            if request.user.is_system_admin:
                from django.urls import reverse
                return redirect(f"{reverse('reports_performance_kras')}?sacco={sacco.id}")
            return redirect('reports_performance_kras')
        else:
            messages.error(request, 'Please correct the errors below.')

    kras = SaccoKRA.objects.filter(sacco=sacco)
    # Get accessible saccos for system admin dropdown
    accessible_saccos = None
    if request.user.is_system_admin:
        from accounts.permissions import get_accessible_saccos
        accessible_saccos = get_accessible_saccos(request.user).select_related('region').order_by('name')
    return render(request, 'reports/performance_kras.html', {'form': form, 'kras': kras, 'sacco': sacco, 'accessible_saccos': accessible_saccos})


@sacco_admin_required
def manage_kpis(request, kra_id):
    from accounts.models import Sacco
    
    # Handle system admin - need sacco from KRA
    if request.user.is_system_admin:
        kra = get_object_or_404(SaccoKRA, id=kra_id)
        sacco = kra.sacco
    else:
        sacco = request.user.sacco
        if not sacco:
            messages.error(request, 'No Sacco assigned to your account. Please contact your administrator.')
            return redirect('dashboard')
    kra = get_object_or_404(SaccoKRA, id=kra_id, sacco=sacco)
    form = KPIForm()
    if request.method == 'POST':
        action = request.POST.get('action', 'create_or_update')
        kpi_id = request.POST.get('kpi_id')

        if action == 'delete' and kpi_id:
            kpi = get_object_or_404(SaccoKPI, id=kpi_id, kra__sacco=sacco, kra=kra)
            kpi.delete()
            messages.success(request, 'KPI deleted successfully')
            if request.user.is_system_admin:
                from django.urls import reverse
                return redirect(f"{reverse('reports_performance_kpis', args=[kra.id])}?sacco={sacco.id}")
            return redirect('reports_performance_kpis', kra_id=kra.id)

        if action == 'toggle' and kpi_id:
            kpi = get_object_or_404(SaccoKPI, id=kpi_id, kra__sacco=sacco, kra=kra)
            kpi.is_active = not kpi.is_active
            kpi.save(update_fields=['is_active'])
            messages.success(request, f"KPI set to {'Active' if kpi.is_active else 'Inactive'}")
            if request.user.is_system_admin:
                from django.urls import reverse
                return redirect(f"{reverse('reports_performance_kpis', args=[kra.id])}?sacco={sacco.id}")
            return redirect('reports_performance_kpis', kra_id=kra.id)

        # create or update
        instance = None
        if kpi_id:
            instance = get_object_or_404(SaccoKPI, id=kpi_id, kra__sacco=sacco, kra=kra)
        form = KPIForm(request.POST, instance=instance)
        if form.is_valid():
            kpi = form.save(commit=False)
            kpi.kra = kra
            kpi.save()
            messages.success(request, 'KPI saved successfully')
            if request.user.is_system_admin:
                from django.urls import reverse
                return redirect(f"{reverse('reports_performance_kpis', args=[kra.id])}?sacco={sacco.id}")
            return redirect('reports_performance_kpis', kra_id=kra.id)
        else:
            messages.error(request, 'Please correct the errors below.')

    kpis = SaccoKPI.objects.filter(kra=kra)
    # Get accessible saccos for system admin dropdown
    accessible_saccos = None
    if request.user.is_system_admin:
        from accounts.permissions import get_accessible_saccos
        accessible_saccos = get_accessible_saccos(request.user).select_related('region').order_by('name')
    return render(request, 'reports/performance_kpis.html', {'kra': kra, 'form': form, 'kpis': kpis, 'sacco': sacco, 'accessible_saccos': accessible_saccos})


@sacco_admin_required
def manage_periods(request):
    from accounts.models import Sacco
    
    # Handle system admin - allow sacco selection
    if request.user.is_system_admin:
        sacco_id = request.GET.get('sacco')
        if not sacco_id:
            # Get first active sacco as default, or show selection
            first_sacco = Sacco.objects.filter(is_active=True).select_related('region').first()
            if first_sacco:
                sacco = first_sacco
            else:
                saccos = Sacco.objects.filter(is_active=True).select_related('region').order_by('name')
                return render(request, 'reports/select_sacco.html', {'saccos': saccos})
        else:
            sacco = get_object_or_404(Sacco, id=sacco_id, is_active=True)
    else:
        sacco = request.user.sacco
        if not sacco:
            messages.error(request, 'No Sacco assigned to your account. Please contact your administrator.')
            return redirect('dashboard')
    if request.method == 'POST':
        # For system admin, get sacco from POST if provided
        if request.user.is_system_admin:
            post_sacco_id = request.POST.get('sacco')
            if post_sacco_id:
                sacco = get_object_or_404(Sacco, id=post_sacco_id, is_active=True)
        form = ReviewPeriodForm(request.POST)
        if form.is_valid():
            period = form.save(commit=False)
            period.sacco = sacco
            # ensure only one active period
            if period.status == 'active':
                SaccoReviewPeriod.objects.filter(sacco=sacco, status='active').update(status='draft')
            period.save()
            messages.success(request, 'Review period saved')
            if request.user.is_system_admin:
                from django.urls import reverse
                return redirect(f"{reverse('reports_performance_periods')}?sacco={sacco.id}")
            return redirect('reports_performance_periods')
    else:
        form = ReviewPeriodForm()
    periods = SaccoReviewPeriod.objects.filter(sacco=sacco)
    # Get accessible saccos for system admin dropdown
    accessible_saccos = None
    if request.user.is_system_admin:
        from accounts.permissions import get_accessible_saccos
        accessible_saccos = get_accessible_saccos(request.user).select_related('region').order_by('name')
    return render(request, 'reports/performance_periods.html', {'form': form, 'periods': periods, 'sacco': sacco, 'accessible_saccos': accessible_saccos})


@sacco_admin_required
def enter_results(request):
    from accounts.models import Sacco
    
    # Handle system admin - allow sacco selection
    if request.user.is_system_admin:
        sacco_id = request.GET.get('sacco')
        if not sacco_id:
            # Get first active sacco as default, or show selection
            first_sacco = Sacco.objects.filter(is_active=True).select_related('region').first()
            if first_sacco:
                sacco = first_sacco
            else:
                saccos = Sacco.objects.filter(is_active=True).select_related('region').order_by('name')
                return render(request, 'reports/select_sacco.html', {'saccos': saccos})
        else:
            sacco = get_object_or_404(Sacco, id=sacco_id, is_active=True)
    else:
        sacco = request.user.sacco
        if not sacco:
            messages.error(request, 'No Sacco assigned to your account. Please contact your administrator.')
            return redirect('dashboard')
    
    period_id = request.GET.get('period')
    if period_id:
        period = get_object_or_404(SaccoReviewPeriod, id=period_id, sacco=sacco)
    else:
        period = SaccoReviewPeriod.objects.filter(sacco=sacco, status='active').first() or _get_or_create_active_quarter(sacco)

    kpis = SaccoKPI.objects.filter(kra__sacco=sacco, is_active=True).select_related('kra')
    existing_results = {r.kpi_id: r for r in SaccoKPIResult.objects.filter(period=period, kpi__in=kpis)}

    if request.method == 'POST':
        # Bulk submit, iterate over posted KPI fields like actual_value_<kpi_id>
        saved = 0
        for kpi in kpis:
            field_name = f"actual_value_{kpi.id}"
            if field_name in request.POST and request.POST.get(field_name) != '':
                try:
                    val = float(request.POST.get(field_name))
                except ValueError:
                    continue
                obj = existing_results.get(kpi.id)
                if obj is None:
                    obj = SaccoKPIResult(kpi=kpi, period=period, entered_by=request.user)
                obj.actual_value = val
                obj.save()
                saved += 1
        messages.success(request, f'Saved {saved} KPI result(s) for {period.name}.')
        if request.user.is_system_admin:
            from django.urls import reverse
            return redirect(f"{reverse('reports_performance_results')}?sacco={sacco.id}")
        return redirect('reports_performance_results')

    # Prepare rows per KRA
    kra_to_kpis = {}
    for kpi in kpis:
        kra_to_kpis.setdefault(kpi.kra, []).append(kpi)

    # Get accessible saccos for system admin dropdown
    accessible_saccos = None
    if request.user.is_system_admin:
        from accounts.permissions import get_accessible_saccos
        accessible_saccos = get_accessible_saccos(request.user).select_related('region').order_by('name')
    
    context = {
        'period': period,
        'kra_to_kpis': kra_to_kpis,
        'existing_results': existing_results,
        'sacco': sacco,
        'accessible_saccos': accessible_saccos,
    }
    return render(request, 'reports/performance_results.html', context)
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count
from funding.models import Funding, FundingSource, FundsAllocation
from expenses.models import Expense
from loans.models import Loan, LoanRepayment


@login_required
def reports_index(request):
    """Reports index page showing available reports"""
    return render(request, 'reports/reports_index.html')


@login_required
def loan_report(request):
    """Comprehensive loan report with statistics and data"""
    # Get loan statistics for the current user's sacco
    loans = Loan.objects.filter(member__sacco=request.user.sacco)
    
    # Calculate statistics
    total_loans = loans.count()
    
    # Total disbursed (loans that have been disbursed)
    total_disbursed = loans.filter(status='disbursed').aggregate(
        total=Sum('amount_approved')
    )['total'] or 0
    
    # Total repayments
    total_repayments = LoanRepayment.objects.filter(
        loan__member__sacco=request.user.sacco
    ).aggregate(
        total=Sum('amount')
    )['total'] or 0
    
    # Outstanding balance (disbursed - repaid)
    outstanding = total_disbursed - total_repayments
    
    # Get loan status breakdown
    status_breakdown = loans.values('status').annotate(
        count=Count('id'),
        total_amount=Sum('amount_approved')
    )
    
    # Get recent loans
    recent_loans = loans.order_by('-created_at')[:10]
    
    # Get overdue loans (placeholder - would need proper due date logic)
    overdue_loans = loans.filter(status='disbursed').count()  # Simplified
    
    stats = {
        'total_loans': total_loans,
        'total_disbursed': total_disbursed,
        'total_repayments': total_repayments,
        'outstanding': outstanding,
        'overdue_loans': overdue_loans,
        'status_breakdown': status_breakdown,
        'recent_loans': recent_loans,
    }
    
    return render(request, 'reports/loan_report.html', {'stats': stats})


@login_required
def member_report(request):
    """Comprehensive member report with statistics and data"""
    from members.models import Member
    from savings.models import SavingsAccount
    from loans.models import Loan
    from django.utils import timezone
    from datetime import timedelta
    
    # Get member statistics for the current user's sacco
    members = Member.objects.filter(sacco=request.user.sacco)
    
    # Calculate statistics
    total_members = members.count()
    active_members = members.filter(status='Active').count()
    
    # Get new members this month
    current_month_start = timezone.now().replace(day=1)
    new_this_month = members.filter(date_joined__gte=current_month_start).count()
    
    # Get inactive members
    inactive_members = members.filter(status='Inactive').count()
    
    # Get member status breakdown
    status_breakdown = members.values('status').annotate(
        count=Count('id')
    )
    
    # Get recent members
    recent_members = members.order_by('-date_joined')[:10]
    
    # Calculate total savings for members
    total_savings = SavingsAccount.objects.filter(
        member__sacco=request.user.sacco
    ).aggregate(
        total=Sum('balance')
    )['total'] or 0
    
    # Get members with loans
    members_with_loans = members.filter(
        id__in=Loan.objects.filter(member__sacco=request.user.sacco).values_list('member_id', flat=True).distinct()
    ).count()
    
    stats = {
        'total_members': total_members,
        'active_members': active_members,
        'new_this_month': new_this_month,
        'inactive_members': inactive_members,
        'status_breakdown': status_breakdown,
        'recent_members': recent_members,
        'total_savings': total_savings,
        'members_with_loans': members_with_loans,
    }
    
    return render(request, 'reports/member_report.html', {'stats': stats})


@login_required
def funding_report(request):
    """Comprehensive funding report with statistics and data"""
    # Get funding statistics
    total_funding = Funding.objects.filter(sacco=request.user.sacco).aggregate(
        total=Sum('amount')
    )['total'] or 0
    
    # Get funding by status
    funding_by_status = Funding.objects.filter(sacco=request.user.sacco).values('status').annotate(
        count=Count('id'),
        total_amount=Sum('amount')
    )
    
    # Get funding sources
    funding_sources = FundingSource.objects.filter(sacco=request.user.sacco)
    
    # Get recent funding
    recent_funding = Funding.objects.filter(sacco=request.user.sacco).order_by('-created_at')[:10]
    
    # Get allocations
    total_allocated = FundsAllocation.objects.filter(funding__sacco=request.user.sacco).aggregate(
        total=Sum('allocated_amount')
    )['total'] or 0
    
    # Get expenses
    total_expenses = Expense.objects.filter(sacco=request.user.sacco).aggregate(
        total=Sum('amount')
    )['total'] or 0
    
    # Calculate remaining balance
    remaining_balance = total_funding - total_allocated - total_expenses
    
    context = {
        'total_funding': total_funding,
        'funding_by_status': funding_by_status,
        'funding_sources': funding_sources,
        'recent_funding': recent_funding,
        'total_allocated': total_allocated,
        'total_expenses': total_expenses,
        'remaining_balance': remaining_balance,
    }
    
    return render(request, 'reports/funding_report.html', context)