from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Sum, Count, Avg
from django.utils import timezone
from django.urls import reverse
from accounts.decorators import sacco_admin_required, admin_or_member_owner_required
from accounts.permissions import filter_queryset_by_user_scope, can_access_member_data, get_accessible_saccos
from accounts.models import Sacco
from notifications.services import NotificationService
from .models import Loan, LoanProduct, LoanRepayment
from .forms import LoanForm, LoanProductForm, RepaymentForm
from .constants import (
    LOAN_STATUS_PENDING_APPROVAL, LOAN_STATUS_APPROVED, LOAN_STATUS_DECLINED,
    LOAN_STATUS_WITHDRAWN, LOAN_STATUS_WRITTEN_OFF, LOAN_STATUS_CLOSED,
    LOAN_STATUS_DISBURSED, LOAN_STATUS_ACTIVE
)


@sacco_admin_required
def add_loan(request):
    if request.method == 'POST':
        print("POST request received")
        print("POST data:", request.POST)
        form = LoanForm(request.POST)
        # Ensure selects are scoped and populated on POST as well
        sacco = getattr(request.user, 'sacco', None)
        members_qs = form.fields['member'].queryset
        products_qs = form.fields['product'].queryset
        if sacco:
            members_qs = members_qs.filter(sacco=sacco)
            products_qs = products_qs.filter(sacco=sacco)
        form.fields['member'].queryset = members_qs
        form.fields['product'].queryset = products_qs
        print("Form is valid:", form.is_valid())
        if not form.is_valid():
            print("Form errors:", form.errors)
        
        if form.is_valid():
            loan = form.save(commit=False)
            loan.created_by = request.user
            loan.save()
            print("Loan saved successfully:", loan.id)
            
            # Send notification to admins about new loan application
            NotificationService.create_notification(
                user=request.user,
                title="New Loan Application",
                message=f"New loan application from {loan.member.full_name} for UGX {loan.amount_requested:,.2f}",
                action_type='loan_application',
                action_url=reverse('loan_profile', args=[loan.id]),
                priority='High',
                sacco=request.user.sacco
            )
            
            messages.success(request, 'Loan application submitted successfully!')
            return redirect('view_all_loans')
    else:
        form = LoanForm()
        sacco = getattr(request.user, 'sacco', None)
        members_qs = form.fields['member'].queryset
        products_qs = form.fields['product'].queryset
        if sacco:
            members_qs = members_qs.filter(sacco=sacco)
            products_qs = products_qs.filter(sacco=sacco)
        form.fields['member'].queryset = members_qs
        form.fields['product'].queryset = products_qs

        # Prefill member if provided via query param
        member_id = request.GET.get('member_id')
        if member_id:
            try:
                from members.models import Member
                member = Member.objects.get(id=member_id, sacco=sacco)
                form.initial['member'] = member.id
            except Member.DoesNotExist:
                pass
    
    return render(request, 'loans/add_loan.html', {'form': form})


@sacco_admin_required
def edit_loan(request, loan_id):
    loan = get_object_or_404(Loan, id=loan_id, member__sacco=request.user.sacco)
    
    if request.method == 'POST':
        form = LoanForm(request.POST, instance=loan)
        # Ensure selects are scoped and populated on POST as well
        sacco = getattr(request.user, 'sacco', None)
        members_qs = form.fields['member'].queryset
        products_qs = form.fields['product'].queryset
        if sacco:
            members_qs = members_qs.filter(sacco=sacco)
            products_qs = products_qs.filter(sacco=sacco)
        form.fields['member'].queryset = members_qs
        form.fields['product'].queryset = products_qs
        if form.is_valid():
            form.save()
            messages.success(request, 'Loan updated successfully!')
            return redirect('loan_profile', loan_id=loan.id)
    else:
        form = LoanForm(instance=loan)
        sacco = getattr(request.user, 'sacco', None)
        members_qs = form.fields['member'].queryset
        products_qs = form.fields['product'].queryset
        if sacco:
            members_qs = members_qs.filter(sacco=sacco)
            products_qs = products_qs.filter(sacco=sacco)
        form.fields['member'].queryset = members_qs
        form.fields['product'].queryset = products_qs
    
    context = {
        'form': form,
        'loan': loan,
        'breadcrumbs': [
            {'name': 'Loans', 'url': 'view_all_loans'},
            {'name': 'Edit Loan', 'url': ''}
        ]
    }
    return render(request, 'loans/edit_loan.html', context)


@sacco_admin_required
def loans_overview(request):
    """Overview page showing loan summary for all saccos (system admin) or regional saccos (regional admin)"""
    accessible_saccos = get_accessible_saccos(request.user)
    
    # Get selected sacco from query parameter
    selected_sacco_id = request.GET.get('sacco')
    
    # Get all loans for overview
    all_loans = filter_queryset_by_user_scope(
        Loan.objects.select_related('member__sacco', 'product').all(),
        request.user,
        'loan'
    )
    
    # Build summary by sacco
    sacco_summaries = []
    for sacco in accessible_saccos:
        sacco_loans = all_loans.filter(member__sacco=sacco)
        total_loans = sacco_loans.count()
        pending = sacco_loans.filter(status=LOAN_STATUS_PENDING_APPROVAL).count()
        approved = sacco_loans.filter(status=LOAN_STATUS_APPROVED).count()
        disbursed = sacco_loans.filter(status=LOAN_STATUS_DISBURSED).count()
        active = sacco_loans.filter(status=LOAN_STATUS_ACTIVE).count()
        closed = sacco_loans.filter(status=LOAN_STATUS_CLOSED).count()
        declined = sacco_loans.filter(status=LOAN_STATUS_DECLINED).count()
        
        total_requested = sacco_loans.aggregate(total=Sum('amount_requested'))['total'] or 0
        total_disbursed = sacco_loans.filter(amount_disbursed__isnull=False).aggregate(total=Sum('amount_disbursed'))['total'] or 0
        avg_loan_amount = sacco_loans.aggregate(avg=Avg('amount_requested'))['avg'] or 0
        
        sacco_summaries.append({
            'sacco': sacco,
            'total_loans': total_loans,
            'pending': pending,
            'approved': approved,
            'disbursed': disbursed,
            'active': active,
            'closed': closed,
            'declined': declined,
            'total_requested': total_requested,
            'total_disbursed': total_disbursed,
            'avg_loan_amount': avg_loan_amount,
        })
    
    # Overall totals
    total_all_loans = all_loans.count()
    total_all_requested = all_loans.aggregate(total=Sum('amount_requested'))['total'] or 0
    total_all_disbursed = all_loans.filter(amount_disbursed__isnull=False).aggregate(total=Sum('amount_disbursed'))['total'] or 0
    
    return render(request, 'loans/loans_overview.html', {
        'sacco_summaries': sacco_summaries,
        'accessible_saccos': accessible_saccos,
        'selected_sacco_id': selected_sacco_id,
        'total_all_loans': total_all_loans,
        'total_all_requested': total_all_requested,
        'total_all_disbursed': total_all_disbursed,
    })


@sacco_admin_required
def view_all_loans(request):
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
    
    # Filter loans based on selected sacco
    loans = filter_queryset_by_user_scope(
        Loan.objects.select_related('member', 'product', 'member__sacco').order_by('-application_date'), 
        request.user, 
        'loan'
    )
    
    # If system admin or regional admin selected a specific sacco, filter by it
    if selected_sacco_id and (request.user.is_system_admin or request.user.is_regional_admin):
        try:
            selected_sacco = Sacco.objects.get(id=selected_sacco_id)
            # Verify user has access to this sacco
            if selected_sacco in accessible_saccos:
                loans = loans.filter(member__sacco=selected_sacco)
        except Sacco.DoesNotExist:
            pass
    
    # CSV export
    if request.GET.get('export') == 'csv':
        import csv
        from django.http import HttpResponse
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="loans.csv"'
        writer = csv.writer(response)
        writer.writerow(['Loan Number', 'Member', 'Sacco', 'Amount Requested', 'Product', 'Status', 'Application Date'])
        for loan in loans:
            writer.writerow([
                loan.loan_number or 'N/A',
                loan.member.full_name,
                loan.member.sacco.name if loan.member.sacco else 'N/A',
                f"{loan.amount_requested:.2f}",
                loan.product.name if loan.product else 'N/A',
                loan.get_status_display(),
                loan.application_date.strftime('%Y-%m-%d') if loan.application_date else ''
            ])
        return response

    context = {
        'loans': loans,
        'accessible_saccos': accessible_saccos,
        'selected_sacco_id': selected_sacco_id,
        'selected_sacco': selected_sacco,
    }
    return render(request, 'loans/view_all_loans.html', context)


@sacco_admin_required
def loan_statistics(request):
    loans = filter_queryset_by_user_scope(Loan.objects.all(), request.user, 'loan')
    
    stats = {
        'total_loans': loans.count(),
        'total_disbursed': loans.filter(status=LOAN_STATUS_DISBURSED).aggregate(
            total=Sum('amount_disbursed')
        )['total'] or 0,
        'pending_approval': loans.filter(status=LOAN_STATUS_PENDING_APPROVAL).count(),
        'active_loans': loans.filter(status=LOAN_STATUS_ACTIVE).count(),
        'overdue_loans': 0,  # Will be calculated based on payment dates
    }
    
    return render(request, 'loans/loan_statistics.html', {'stats': stats})


@sacco_admin_required
def all_borrowers(request):
    from members.models import Member
    borrowers = filter_queryset_by_user_scope(
        Member.objects.filter(loan__isnull=False).distinct(), 
        request.user, 
        'member'
    )
    return render(request, 'loans/all_borrowers.html', {'borrowers': borrowers})


@sacco_admin_required
def pending_approval(request):
    loans = filter_queryset_by_user_scope(
        Loan.objects.filter(status=LOAN_STATUS_PENDING_APPROVAL),
        request.user,
        'loan'
    )
    return render(request, 'loans/pending_approval.html', {'loans': loans})


@sacco_admin_required
def pending_disbursement(request):
    loans = filter_queryset_by_user_scope(
        Loan.objects.filter(status=LOAN_STATUS_APPROVED),
        request.user,
        'loan'
    )
    return render(request, 'loans/pending_disbursement.html', {'loans': loans})


@sacco_admin_required
def loans_declined(request):
    loans = filter_queryset_by_user_scope(
        Loan.objects.filter(status=LOAN_STATUS_DECLINED),
        request.user,
        'loan'
    )
    return render(request, 'loans/loans_declined.html', {'loans': loans})


@sacco_admin_required
def loans_withdrawn(request):
    loans = filter_queryset_by_user_scope(
        Loan.objects.filter(status=LOAN_STATUS_WITHDRAWN),
        request.user,
        'loan'
    )
    return render(request, 'loans/loans_withdrawn.html', {'loans': loans})


@sacco_admin_required
def loans_written_off(request):
    loans = filter_queryset_by_user_scope(
        Loan.objects.filter(status=LOAN_STATUS_WRITTEN_OFF),
        request.user,
        'loan'
    )
    return render(request, 'loans/loans_written_off.html', {'loans': loans})


@sacco_admin_required
def loans_closed(request):
    loans = filter_queryset_by_user_scope(
        Loan.objects.filter(status=LOAN_STATUS_CLOSED),
        request.user,
        'loan'
    )
    return render(request, 'loans/loans_closed.html', {'loans': loans})


@sacco_admin_required
def loans_approved(request):
    loans = filter_queryset_by_user_scope(
        Loan.objects.filter(status=LOAN_STATUS_APPROVED),
        request.user,
        'loan'
    )
    return render(request, 'loans/loans_approved.html', {'loans': loans})


@sacco_admin_required
def disbursed_loans(request):
    loans = filter_queryset_by_user_scope(
        Loan.objects.filter(status=LOAN_STATUS_DISBURSED),
        request.user,
        'loan'
    )
    return render(request, 'loans/disbursed_loans.html', {'loans': loans})


@sacco_admin_required
def repayments(request):
    qs = filter_queryset_by_user_scope(
        LoanRepayment.objects.select_related('loan', 'loan__member'),
        request.user,
        'loan_repayment'
    )
    # Loans available for selection (used when no loan filter is provided)
    loans_for_select = filter_queryset_by_user_scope(
        Loan.objects.select_related('member'),
        request.user,
        'loan'
    ).order_by('-application_date')
    loan_id = request.GET.get('loan')
    loan = None
    if loan_id:
        loan = get_object_or_404(Loan, id=loan_id)
        qs = qs.filter(loan=loan)

    # Handle inline add repayment
    if request.method == 'POST' and request.POST.get('loan_id'):
        from .forms import RepaymentForm
        loan = get_object_or_404(Loan, id=request.POST.get('loan_id'))
        
        # Check if loan is closed/fully repaid
        if loan.status == 'closed':
            messages.error(request, 'Cannot add repayments to a fully repaid loan.')
            return redirect(f"{reverse('repayments')}?loan={loan.id}")
        
        form = RepaymentForm(request.POST)
        if form.is_valid():
            repayment = form.save(commit=False)
            repayment.loan = loan
            repayment.save()
            messages.success(request, 'Repayment recorded successfully!')
            return redirect(f"{reverse('repayments')}?loan={loan.id}")
        else:
            messages.error(request, 'Please correct the errors below.')

    repayments_qs = qs.order_by('-payment_date')
    return render(request, 'loans/repayments.html', {
        'repayments': repayments_qs,
        'loan': loan,
        'loans': loans_for_select,
    })


@admin_or_member_owner_required
def loan_profile(request, loan_id):
    loan = get_object_or_404(Loan, id=loan_id)
    
    # Additional permission check for loan access
    if not can_access_member_data(request.user, loan.member):
        messages.error(request, 'Access denied. You can only view your own loan details.')
        return redirect('dashboard')
    repayments = loan.repayments.all().order_by('-payment_date')
    breadcrumbs = [
        {'name': 'Loans', 'url': 'view_all_loans'},
        {'name': 'Loan Profile', 'url': ''}
    ]
    return render(request, 'loans/loan_profile.html', {
        'loan': loan,
        'repayments': repayments,
        'breadcrumbs': breadcrumbs,
    })


@sacco_admin_required
def manage_loan_products(request):
    products = filter_queryset_by_user_scope(
        LoanProduct.objects.all(),
        request.user,
        'loan_product'
    )
    return render(request, 'loans/manage_loan_products.html', {'products': products})


@sacco_admin_required
def create_loan_product(request):
    if request.method == 'POST':
        form = LoanProductForm(request.POST)
        # Pass user's sacco to form for validation
        form.user_sacco = request.user.sacco
        if form.is_valid():
            product = form.save(commit=False)
            product.sacco = request.user.sacco
            product.save()
            messages.success(request, 'Loan product created successfully!')
            return redirect('manage_loan_products')
    else:
        form = LoanProductForm()
        # Pass user's sacco to form for validation
        form.user_sacco = request.user.sacco
    
    return render(request, 'loans/create_loan_product.html', {'form': form})


@sacco_admin_required
def edit_loan_product(request, product_id):
    product = get_object_or_404(LoanProduct, id=product_id, sacco=request.user.sacco)
    
    if request.method == 'POST':
        form = LoanProductForm(request.POST, instance=product)
        form.user_sacco = request.user.sacco
        if form.is_valid():
            form.save()
            messages.success(request, 'Loan product updated successfully!')
            return redirect('manage_loan_products')
    else:
        form = LoanProductForm(instance=product)
        form.user_sacco = request.user.sacco
    
    context = {
        'form': form,
        'product': product,
        'breadcrumbs': [
            {'name': 'Loan Products', 'url': 'manage_loan_products'},
            {'name': 'Edit Product', 'url': ''}
        ]
    }
    return render(request, 'loans/edit_loan_product.html', context)


@sacco_admin_required
def approve_loan(request, loan_id):
    """Approve a loan application"""
    loan = get_object_or_404(Loan, id=loan_id, member__sacco=request.user.sacco)
    
    if loan.status != LOAN_STATUS_PENDING_APPROVAL:
        messages.error(request, 'This loan cannot be approved.')
        return redirect('loan_profile', loan_id=loan_id)
    
    loan.status = LOAN_STATUS_APPROVED
    loan.approved_by = request.user
    loan.approved_at = timezone.now()
    loan.save()
    
    # Send notification to member
    if loan.member.user_account:
        NotificationService.create_notification(
            user=loan.member.user_account,
            title="Loan Approved",
            message=f"Your loan application for UGX {loan.amount_requested:,.2f} has been approved!",
            action_type='loan_approval',
            action_url=reverse('loan_profile', args=[loan.id]),
            priority='High',
            sacco=request.user.sacco
        )
    
    messages.success(request, 'Loan approved successfully!')
    return redirect('loan_profile', loan_id=loan_id)


@sacco_admin_required
def reject_loan(request, loan_id):
    """Reject a loan application"""
    loan = get_object_or_404(Loan, id=loan_id, member__sacco=request.user.sacco)
    
    if loan.status != LOAN_STATUS_PENDING_APPROVAL:
        messages.error(request, 'This loan cannot be rejected.')
        return redirect('loan_profile', loan_id=loan_id)
    
    loan.status = LOAN_STATUS_DECLINED
    loan.save()
    
    # Send notification to member
    if loan.member.user_account:
        NotificationService.create_notification(
            user=loan.member.user_account,
            title="Loan Application Rejected",
            message=f"Your loan application for UGX {loan.amount_requested:,.2f} has been rejected.",
            action_type='loan_rejection',
            action_url=reverse('loan_profile', args=[loan.id]),
            priority='Medium',
            sacco=request.user.sacco
        )
    
    messages.success(request, 'Loan rejected successfully!')
    return redirect('loan_profile', loan_id=loan_id)


@sacco_admin_required
def disburse_loan(request, loan_id):
    """Disburse an approved loan"""
    loan = get_object_or_404(Loan, id=loan_id, member__sacco=request.user.sacco)
    
    if loan.status != LOAN_STATUS_APPROVED:
        messages.error(request, 'This loan cannot be disbursed.')
        return redirect('loan_profile', loan_id=loan_id)
    
    loan.status = LOAN_STATUS_DISBURSED
    loan.disbursed_by = request.user
    loan.disbursed_at = timezone.now()
    loan.save()
    
    # Send notification to member
    if loan.member.user_account:
        amount = loan.amount_approved or loan.amount_requested
        NotificationService.create_notification(
            user=loan.member.user_account,
            title="Loan Disbursed",
            message=f"Your approved loan of UGX {amount:,.2f} has been disbursed to your account!",
            action_type='loan_disbursement',
            action_url=reverse('loan_profile', args=[loan.id]),
            priority='High',
            sacco=request.user.sacco
        )
    
    messages.success(request, 'Loan disbursed successfully!')
    return redirect('loan_profile', loan_id=loan_id)