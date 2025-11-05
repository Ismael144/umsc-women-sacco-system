from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum
from django.http import JsonResponse, HttpResponse
from django.urls import reverse
from accounts.decorators import sacco_admin_required, admin_or_member_owner_required
from accounts.permissions import filter_queryset_by_user_scope, can_access_member_data, get_accessible_members, get_accessible_saccos
from accounts.models import Sacco
from notifications.services import NotificationService
from .models import SavingProduct, SavingsAccount, SavingsTransaction
from .forms import AddSavingsForm, SavingProductForm, SavingsAccountForm
from members.models import Member
from django.db.models import Count, Sum, Avg


@sacco_admin_required
def add_savings_transaction(request):
    """Add savings transaction (deposit/withdrawal)"""
    if request.method == 'POST':
        form = AddSavingsForm(request.POST)
        # Ensure account choices are populated on POST as well
        sacco = getattr(request.user, 'sacco', None)
        accounts_qs = SavingsAccount.objects.all()
        if sacco:
            accounts_qs = accounts_qs.filter(member__sacco=sacco)
        form.fields['account'].queryset = accounts_qs
        if form.is_valid():
            savings = form.save(commit=False)
            savings.created_by = request.user
            savings.save()
            
            # Send notification to member about transaction
            if savings.account.member.user_account:
                action_type = 'savings_deposit' if savings.txn_type == 'Deposit' else 'savings_withdrawal'
                NotificationService.create_notification(
                    user=savings.account.member.user_account,
                    title=f"Savings {savings.txn_type}",
                    message=f"UGX {savings.amount:,.2f} {savings.txn_type.lower()}ed to your {savings.account.product.name} account",
                    action_type=action_type,
                    action_url=f"{reverse('savings_statements')}?account={savings.account.id}",
                    priority='Low',
                    sacco=request.user.sacco
                )
            
            messages.success(request, 'Savings transaction added successfully!')
            return redirect('savings_accounts')
    else:
        form = AddSavingsForm()
        sacco = getattr(request.user, 'sacco', None)
        accounts_qs = SavingsAccount.objects.all()
        if sacco:
            accounts_qs = accounts_qs.filter(member__sacco=sacco)
        form.fields['account'].queryset = accounts_qs
    
    context = {
        'form': form,
        'breadcrumbs': [
            {'name': 'Savings', 'url': 'savings_accounts'},
            {'name': 'Add Transaction', 'url': ''}
        ]
    }
    return render(request, 'savings/add_savings_transaction.html', context)


@sacco_admin_required
def create_savings_account(request):
    """Create new savings account"""
    # Get accessible saccos for system admin or regional admin
    accessible_saccos = get_accessible_saccos(request.user) if (request.user.is_system_admin or request.user.is_regional_admin) else None
    
    # For regional admins, check if there are any accessible saccos
    if request.user.is_regional_admin:
        if not accessible_saccos or accessible_saccos.count() == 0:
            messages.error(request, 'No Saccos are available in your region. Please create a Sacco first before creating savings accounts.')
            return redirect('savings_accounts')
    
    selected_sacco_id = request.POST.get('sacco') if request.method == 'POST' else request.GET.get('sacco')
    # Ensure selected_sacco_id is a string for proper comparison
    if selected_sacco_id:
        try:
            selected_sacco_id = str(int(selected_sacco_id))  # Normalize to string
        except (ValueError, TypeError):
            selected_sacco_id = None
    selected_sacco = None
    
    # For system admin or regional admin, get sacco from form or default to first accessible
    if request.user.is_system_admin or request.user.is_regional_admin:
        if selected_sacco_id:
            try:
                selected_sacco = Sacco.objects.get(id=selected_sacco_id)
                # Verify user has access to this sacco
                if accessible_saccos and selected_sacco not in accessible_saccos:
                    messages.error(request, 'You do not have access to this sacco.')
                    selected_sacco = None
            except Sacco.DoesNotExist:
                pass
        elif accessible_saccos:
            selected_sacco = accessible_saccos.first()
    else:
        # For non-system admin, use their sacco
        selected_sacco = request.user.sacco
    
    if request.method == 'POST':
        form = SavingsAccountForm(request.POST)
        # Populate selects on POST as well
        if selected_sacco:
            members = get_accessible_members(request.user).filter(sacco=selected_sacco)
            products = SavingProduct.objects.filter(is_active=True, sacco=selected_sacco)
        else:
            members = get_accessible_members(request.user)
            products = SavingProduct.objects.filter(is_active=True)
        form.fields['member'].queryset = members
        form.fields['product'].queryset = products
        if form.is_valid():
            account = form.save(commit=False)
            account.created_by = request.user
            account.save()
            messages.success(request, 'Savings account created successfully!')
            return redirect('savings_accounts')
    else:
        form = SavingsAccountForm()
        
        # Get members and products based on selected sacco
        if selected_sacco:
            members = get_accessible_members(request.user).filter(sacco=selected_sacco)
            products = SavingProduct.objects.filter(is_active=True, sacco=selected_sacco)
        else:
            members = get_accessible_members(request.user)
            products = SavingProduct.objects.filter(is_active=True)
        form.fields['member'].queryset = members
        form.fields['product'].queryset = products
    
    context = {
        'form': form,
        'accessible_saccos': accessible_saccos,
        'selected_sacco_id': selected_sacco_id,
        'selected_sacco': selected_sacco,
        'breadcrumbs': [
            {'name': 'Savings', 'url': 'savings_accounts'},
            {'name': 'Create Account', 'url': ''}
        ]
    }
    return render(request, 'savings/create_savings_account.html', context)


@sacco_admin_required
def edit_savings_account(request, account_id):
    """Edit savings account"""
    # Get accessible saccos for system admin or regional admin
    accessible_saccos = get_accessible_saccos(request.user) if (request.user.is_system_admin or request.user.is_regional_admin) else None
    
    # For regional admins, check if there are any accessible saccos
    if request.user.is_regional_admin:
        if not accessible_saccos or accessible_saccos.count() == 0:
            messages.error(request, 'No Saccos are available in your region. Please create a Sacco first.')
            return redirect('savings_accounts')
    
    # Get account - for system/regional admins, allow access to any accessible sacco
    if request.user.is_system_admin or request.user.is_regional_admin:
        account = get_object_or_404(SavingsAccount, id=account_id)
        # Verify user has access to this account's sacco
        if accessible_saccos and account.member.sacco not in accessible_saccos:
            messages.error(request, 'You do not have access to this account.')
            return redirect('savings_accounts')
    else:
        account = get_object_or_404(SavingsAccount, id=account_id, member__sacco=request.user.sacco)
    
    # Get selected sacco from query parameter (for system/regional admins)
    selected_sacco_id = request.POST.get('sacco') if request.method == 'POST' else request.GET.get('sacco')
    # Ensure selected_sacco_id is a string for proper comparison
    if selected_sacco_id:
        try:
            selected_sacco_id = str(int(selected_sacco_id))  # Normalize to string
        except (ValueError, TypeError):
            selected_sacco_id = None
    
    # For system admin or regional admin, use selected sacco or account's sacco
    if request.user.is_system_admin or request.user.is_regional_admin:
        if selected_sacco_id:
            try:
                selected_sacco = Sacco.objects.get(id=selected_sacco_id)
                # Verify user has access to this sacco
                if accessible_saccos and selected_sacco not in accessible_saccos:
                    messages.error(request, 'You do not have access to this sacco.')
                    selected_sacco = account.member.sacco
            except Sacco.DoesNotExist:
                selected_sacco = account.member.sacco
        else:
            # Default to account's sacco
            selected_sacco = account.member.sacco
    else:
        # For non-system admin, use their sacco
        selected_sacco = request.user.sacco
    
    # Get members and products based on selected sacco
    if selected_sacco:
        members = get_accessible_members(request.user).filter(sacco=selected_sacco)
        products = SavingProduct.objects.filter(is_active=True, sacco=selected_sacco)
    else:
        members = get_accessible_members(request.user)
        products = SavingProduct.objects.filter(is_active=True)
    
    # Ensure current instance values are present even if not active
    if account.member_id and not members.filter(id=account.member_id).exists():
        members = members | Member.objects.filter(id=account.member_id)
    if account.product_id and not products.filter(id=account.product_id).exists():
        products = products | SavingProduct.objects.filter(id=account.product_id)
    
    if request.method == 'POST':
        form = SavingsAccountForm(request.POST, instance=account)
        # Set querysets after form creation
        form.fields['member'].queryset = members
        form.fields['product'].queryset = products
        if form.is_valid():
            form.save()
            messages.success(request, 'Savings account updated successfully!')
            return redirect('savings_accounts')
    else:
        form = SavingsAccountForm(instance=account)
        # Set querysets after form creation
        form.fields['member'].queryset = members
        form.fields['product'].queryset = products
    
    context = {
        'form': form,
        'account': account,
        'accessible_saccos': accessible_saccos,
        'selected_sacco_id': str(selected_sacco.id) if selected_sacco else None,
        'selected_sacco': selected_sacco,
        'breadcrumbs': [
            {'name': 'Savings', 'url': 'savings_accounts'},
            {'name': 'Edit Account', 'url': ''}
        ]
    }
    return render(request, 'savings/edit_savings_account.html', context)


@sacco_admin_required
def savings_accounts(request):
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
    
    # Filter accounts based on selected sacco
    accounts = filter_queryset_by_user_scope(
        SavingsAccount.objects.all(),
        request.user,
        'savings'
    )
    
    # If system admin or regional admin selected a specific sacco, filter by it
    if selected_sacco_id and (request.user.is_system_admin or request.user.is_regional_admin):
        try:
            selected_sacco = Sacco.objects.get(id=selected_sacco_id)
            # Verify user has access to this sacco
            if selected_sacco in accessible_saccos:
                accounts = accounts.filter(member__sacco=selected_sacco)
        except Sacco.DoesNotExist:
            pass
    
    # CSV export
    if request.GET.get('export') == 'csv':
        import csv
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="savings_accounts.csv"'
        writer = csv.writer(response)
        writer.writerow(['Account Number', 'Member', 'Sacco', 'Product', 'Balance', 'Status', 'Created'])
        for account in accounts:
            writer.writerow([
                account.account_number,
                account.member.full_name,
                account.member.sacco.name if account.member.sacco else 'N/A',
                account.product.name,
                f"{account.balance:.2f}",
                'Active' if account.is_active else 'Inactive',
                account.created_at.strftime('%Y-%m-%d') if account.created_at else ''
            ])
        return response
    
    return render(request, 'savings/savings_accounts.html', {
        'accounts': accounts,
        'accessible_saccos': accessible_saccos,
        'selected_sacco_id': selected_sacco_id,
        'selected_sacco': selected_sacco
    })


@sacco_admin_required
def savings_overview(request):
    """Overview page showing summary for all saccos (system admin) or regional saccos (regional admin)"""
    accessible_saccos = get_accessible_saccos(request.user)
    
    # Get selected sacco from query parameter
    selected_sacco_id = request.GET.get('sacco')
    
    # Get all accounts for overview
    all_accounts = filter_queryset_by_user_scope(
        SavingsAccount.objects.select_related('member__sacco', 'product').all(),
        request.user,
        'savings'
    )
    
    # Build summary by sacco
    sacco_summaries = []
    for sacco in accessible_saccos:
        sacco_accounts = all_accounts.filter(member__sacco=sacco)
        total_accounts = sacco_accounts.count()
        active_accounts = sacco_accounts.filter(is_active=True).count()
        total_balance = sacco_accounts.aggregate(total=Sum('balance'))['total'] or 0
        avg_balance = sacco_accounts.aggregate(avg=Avg('balance'))['avg'] or 0
        
        sacco_summaries.append({
            'sacco': sacco,
            'total_accounts': total_accounts,
            'active_accounts': active_accounts,
            'inactive_accounts': total_accounts - active_accounts,
            'total_balance': total_balance,
            'avg_balance': avg_balance,
        })
    
    # Overall totals
    total_all_accounts = all_accounts.count()
    total_all_balance = all_accounts.aggregate(total=Sum('balance'))['total'] or 0
    
    return render(request, 'savings/savings_overview.html', {
        'sacco_summaries': sacco_summaries,
        'accessible_saccos': accessible_saccos,
        'selected_sacco_id': selected_sacco_id,
        'total_all_accounts': total_all_accounts,
        'total_all_balance': total_all_balance,
    })


@sacco_admin_required
def savings_statements(request):
    accounts = filter_queryset_by_user_scope(
        SavingsAccount.objects.all(),
        request.user,
        'savings'
    )
    account_id = request.GET.get('account')
    if account_id:
        account = get_object_or_404(SavingsAccount, id=account_id)
        # Check if user can access this account
        if not can_access_member_data(request.user, account.member):
            messages.error(request, 'Access denied.')
            return redirect('savings_accounts')
        transactions = SavingsTransaction.objects.filter(account=account).order_by('-created_at')
    else:
        account = None
        transactions = filter_queryset_by_user_scope(
            SavingsTransaction.objects.all(),
            request.user,
            'savings_transaction'
        ).order_by('-created_at')
    
    return render(request, 'savings/statements.html', {
        'account': account,
        'transactions': transactions,
        'accounts': accounts
    })


@sacco_admin_required
def saving_products(request):
    products = filter_queryset_by_user_scope(
        SavingProduct.objects.all(),
        request.user,
        'saving_product'
    )
    return render(request, 'savings/saving_products.html', {'products': products})


@sacco_admin_required
def create_saving_product(request):
    if request.method == 'POST':
        form = SavingProductForm(request.POST)
        if form.is_valid():
            product = form.save(commit=False)
            product.sacco = request.user.sacco
            product.save()
            messages.success(request, 'Saving product created successfully!')
            return redirect('saving_products')
    else:
        form = SavingProductForm()
    
    return render(request, 'savings/create_saving_product.html', {'form': form})


@sacco_admin_required
def edit_saving_product(request, product_id):
    product = get_object_or_404(SavingProduct, id=product_id, sacco=request.user.sacco)
    
    if request.method == 'POST':
        form = SavingProductForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, 'Saving product updated successfully!')
            return redirect('saving_products')
    else:
        form = SavingProductForm(instance=product)
    
    context = {
        'form': form,
        'product': product,
        'breadcrumbs': [
            {'name': 'Saving Products', 'url': 'saving_products'},
            {'name': 'Edit Product', 'url': ''}
        ]
    }
    return render(request, 'savings/edit_saving_product.html', context)


# API Views for AJAX
@sacco_admin_required
def api_members(request):
    """API endpoint to get members for AJAX"""
    members = Member.objects.filter(
        sacco=request.user.sacco,
        status='Active'
    ).values('id', 'first_name', 'last_name')
    
    members_data = []
    for member in members:
        members_data.append({
            'id': member['id'],
            'full_name': f"{member['first_name']} {member['last_name']}"
        })
    
    return JsonResponse({'members': members_data})


@sacco_admin_required
def api_products(request):
    """API endpoint to get savings products for AJAX"""
    products = SavingProduct.objects.filter(
        sacco=request.user.sacco,
        is_active=True
    ).values('id', 'name')
    
    return JsonResponse({'products': list(products)})


@sacco_admin_required
def api_create_account(request):
    """API endpoint to create savings account via AJAX"""
    if request.method == 'POST':
        try:
            member_id = request.POST.get('member')
            product_id = request.POST.get('product')
            account_number = request.POST.get('account_number', '')
            balance = float(request.POST.get('balance', 0))
            
            member = get_object_or_404(Member, id=member_id, sacco=request.user.sacco)
            product = get_object_or_404(SavingProduct, id=product_id, sacco=request.user.sacco)
            
            # Auto-generate account number if not provided
            if not account_number:
                last_account = SavingsAccount.objects.filter(member__sacco=request.user.sacco).order_by('-id').first()
                if last_account and last_account.account_number:
                    try:
                        last_num = int(last_account.account_number)
                        account_number = str(last_num + 1).zfill(6)
                    except ValueError:
                        account_number = '100001'
                else:
                    account_number = '100001'
            
            account = SavingsAccount.objects.create(
                member=member,
                product=product,
                account_number=account_number,
                balance=balance,
                created_by=request.user
            )
            
            return JsonResponse({
                'success': True,
                'id': account.id,
                'text': f"{account.account_number} - {account.member.full_name}"
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})