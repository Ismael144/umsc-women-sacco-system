from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count, Avg
from .models import Funding, FundingSource, FundsAllocation, ExpenditureLog
from accounts.decorators import sacco_admin_required
from accounts.permissions import filter_queryset_by_user_scope, get_accessible_saccos
from accounts.models import Sacco




@login_required
def funds_allocation(request):
    if request.method == 'POST':
        try:
            # Handle enhanced allocation form submission
            funding_id = request.POST.get('funding_id')
            allocation_items_json = request.POST.get('allocation_items')
            
            if not funding_id or not allocation_items_json:
                messages.error(request, 'Please select a funding source and add allocation items.')
                return redirect('enhanced_funds_allocation')
            
            funding = Funding.objects.get(id=funding_id, sacco=request.user.sacco)
            
            # Parse allocation items
            import json
            allocation_items = json.loads(allocation_items_json)
            
            if not allocation_items:
                messages.error(request, 'Please add at least one allocation item.')
                return redirect('enhanced_funds_allocation')
            
            # Calculate total allocated amount
            total_allocated = sum(item['amount'] for item in allocation_items)
            
            if total_allocated > funding.amount:
                messages.error(request, f'Total allocated amount (${total_allocated:.2f}) cannot exceed available funding (${funding.amount:.2f}).')
                return redirect('enhanced_funds_allocation')
            
            # Create allocation record
            allocation = FundsAllocation.objects.create(
                funding=funding,
                allocated_amount=total_allocated,
                purpose=f"Allocated to {len(allocation_items)} items: " + ", ".join([item['name'] for item in allocation_items]),
                allocated_by=request.user
            )
            
            # Update funding status
            funding.status = 'allocated'
            funding.save()
            
            messages.success(request, f'Funds of ${total_allocated:.2f} allocated successfully across {len(allocation_items)} items!')
            return redirect('enhanced_funds_allocation')
            
        except Exception as e:
            messages.error(request, f'Error allocating funds: {str(e)}')
    
    # Get available funding for allocation
    available_funding = Funding.objects.filter(
        sacco=request.user.sacco,
        status__in=['received', 'pending']
    )
    
    allocations = FundsAllocation.objects.filter(funding__sacco=request.user.sacco)
    return render(request, 'funding/funds_allocation.html', {
        'allocations': allocations,
        'available_funding': available_funding
    })


@login_required
def enhanced_funds_allocation(request):
    """Enhanced funds allocation with dynamic items"""
    if request.method == 'POST':
        try:
            # Handle enhanced allocation form submission
            funding_id = request.POST.get('funding_id')
            allocation_items_json = request.POST.get('allocation_items')
            
            if not funding_id or not allocation_items_json:
                messages.error(request, 'Please select a funding source and add allocation items.')
                return redirect('enhanced_funds_allocation')
            
            funding = Funding.objects.get(id=funding_id, sacco=request.user.sacco)
            
            # Parse allocation items
            import json
            allocation_items = json.loads(allocation_items_json)
            
            if not allocation_items:
                messages.error(request, 'Please add at least one allocation item.')
                return redirect('enhanced_funds_allocation')
            
            # Calculate total allocated amount
            total_allocated = sum(item['amount'] for item in allocation_items)
            
            if total_allocated > funding.amount:
                messages.error(request, f'Total allocated amount (${total_allocated:.2f}) cannot exceed available funding (${funding.amount:.2f}).')
                return redirect('enhanced_funds_allocation')
            
            # Create allocation record
            allocation = FundsAllocation.objects.create(
                funding=funding,
                allocated_amount=total_allocated,
                purpose=f"Allocated to {len(allocation_items)} items: " + ", ".join([item['name'] for item in allocation_items]),
                allocated_by=request.user
            )
            
            # Update funding status
            funding.status = 'allocated'
            funding.save()
            
            messages.success(request, f'Funds of ${total_allocated:.2f} allocated successfully across {len(allocation_items)} items!')
            return redirect('enhanced_funds_allocation')
            
        except Exception as e:
            messages.error(request, f'Error allocating funds: {str(e)}')
    
    # Get available funding for allocation
    available_funding = Funding.objects.filter(
        sacco=request.user.sacco,
        status__in=['received', 'pending']
    )
    
    allocations = FundsAllocation.objects.filter(funding__sacco=request.user.sacco)
    return render(request, 'funding/enhanced_funds_allocation.html', {
        'allocations': allocations,
        'available_funding': available_funding
    })


@sacco_admin_required
def funding_overview(request):
    """Overview page showing funding summary for all saccos (system admin) or regional saccos (regional admin)"""
    accessible_saccos = get_accessible_saccos(request.user)
    
    # Get selected sacco from query parameter
    selected_sacco_id = request.GET.get('sacco')
    
    # Get all funding for overview
    all_funding = filter_queryset_by_user_scope(
        Funding.objects.select_related('sacco', 'source').all(),
        request.user,
        'funding'
    )
    
    # Build summary by sacco
    sacco_summaries = []
    for sacco in accessible_saccos:
        sacco_funding = all_funding.filter(sacco=sacco)
        total_funding = sacco_funding.count()
        pending = sacco_funding.filter(status='pending').count()
        received = sacco_funding.filter(status='received').count()
        allocated = sacco_funding.filter(status='allocated').count()
        spent = sacco_funding.filter(status='spent').count()
        
        total_amount = sacco_funding.aggregate(total=Sum('amount'))['total'] or 0
        avg_amount = sacco_funding.aggregate(avg=Avg('amount'))['avg'] or 0
        
        sacco_summaries.append({
            'sacco': sacco,
            'total_funding': total_funding,
            'pending': pending,
            'received': received,
            'allocated': allocated,
            'spent': spent,
            'total_amount': total_amount,
            'avg_amount': avg_amount,
        })
    
    # Overall totals
    total_all_funding = all_funding.count()
    total_all_amount = all_funding.aggregate(total=Sum('amount'))['total'] or 0
    
    return render(request, 'funding/funding_overview.html', {
        'sacco_summaries': sacco_summaries,
        'accessible_saccos': accessible_saccos,
        'selected_sacco_id': selected_sacco_id,
        'total_all_funding': total_all_funding,
        'total_all_amount': total_all_amount,
    })


@login_required
def funding_list(request):
    """View all funding records with inline add form"""
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
    
    # Filter funding based on selected sacco
    funding_records = filter_queryset_by_user_scope(
        Funding.objects.select_related('sacco', 'source').all(),
        request.user,
        'funding'
    ).order_by('-created_at')
    
    # If system admin or regional admin selected a specific sacco, filter by it
    if selected_sacco_id and (request.user.is_system_admin or request.user.is_regional_admin):
        try:
            selected_sacco = Sacco.objects.get(id=selected_sacco_id)
            # Verify user has access to this sacco
            if selected_sacco in accessible_saccos:
                funding_records = funding_records.filter(sacco=selected_sacco)
        except Sacco.DoesNotExist:
            pass
    else:
        # For non-admin users, use their sacco
        funding_records = funding_records.filter(sacco=request.user.sacco)
    
    # Get status filter from query params
    status_filter = request.GET.get('filter_status')
    if status_filter:
        funding_records = funding_records.filter(status=status_filter)
    
    # Get source filter from query params
    source_filter = request.GET.get('filter_source')
    if source_filter:
        funding_records = funding_records.filter(source_id=source_filter)
    
    # Get all sources for filter dropdown
    sacco_for_sources = selected_sacco if selected_sacco else request.user.sacco
    sources = FundingSource.objects.filter(sacco=sacco_for_sources)
    
    # Get status counts for summary
    status_counts = {}
    sacco_for_counts = selected_sacco if selected_sacco else request.user.sacco
    for status, _ in Funding.STATUS_CHOICES:
        status_counts[status] = funding_records.filter(status=status).count()
    
    # Handle add funding form submission
    if request.method == 'POST':
        try:
            # Check if user has a sacco
            if not request.user.sacco:
                messages.error(request, 'You must be associated with a Sacco to add funding.')
                return redirect('funding_list')
            
            # Get form data
            source_name = request.POST.get('source')
            amount = request.POST.get('amount')
            purpose = request.POST.get('purpose')
            received_date = request.POST.get('received_date')
            status = request.POST.get('status')
            
            # Validate required fields
            if not all([source_name, amount, purpose]):
                messages.error(request, 'Please fill in all required fields.')
                return redirect('funding_list')
            
            # Try to get existing funding source first
            try:
                source = FundingSource.objects.get(name=source_name, sacco=request.user.sacco)
            except FundingSource.DoesNotExist:
                # Create new funding source
                source = FundingSource.objects.create(
                    name=source_name,
                    sacco=request.user.sacco,
                    contact_person='Unknown',
                    email='unknown@example.com',
                    phone='000-000-0000',
                    address='Address not provided'
                )
            
            # Create funding record
            funding = Funding.objects.create(
                sacco=request.user.sacco,
                source=source,
                amount=amount,
                purpose=purpose,
                status=status,
                received_date=received_date if received_date else None,
                created_by=request.user
            )
            
            messages.success(request, f'Funding of UGX {amount:,.2f} from {source_name} added successfully!')
            return redirect('funding_list')
            
        except Exception as e:
            messages.error(request, f'Error adding funding: {str(e)}')
    
    return render(request, 'funding/funding_list.html', {
        'funding_records': funding_records,
        'sources': sources,
        'status_counts': status_counts,
        'current_status': status_filter,
        'current_source': source_filter,
        'accessible_saccos': accessible_saccos,
        'selected_sacco_id': selected_sacco_id,
        'selected_sacco': selected_sacco,
    })


@login_required
def expenditure_logs(request):
    logs = ExpenditureLog.objects.filter(sacco=request.user.sacco)
    return render(request, 'funding/expenditure_logs.html', {'logs': logs})


@login_required
def funding_sources(request):
    sources = FundingSource.objects.filter(sacco=request.user.sacco)
    return render(request, 'funding/funding_sources.html', {'sources': sources})


@sacco_admin_required
def add_funding_source(request):
    """Add funding source"""
    if request.method == 'POST':
        try:
            name = request.POST.get('name')
            contact_person = request.POST.get('contact_person')
            email = request.POST.get('email')
            phone = request.POST.get('phone')
            FundingSource.objects.create(
                name=name,
                contact_person=contact_person,
                email=email,
                phone=phone,
                sacco=request.user.sacco
            )
            messages.success(request, 'Funding source created successfully!')
        except Exception as e:
            messages.error(request, f'Error creating source: {str(e)}')
    return redirect('funding_sources')


@sacco_admin_required
def edit_funding_source(request, source_id):
    """Edit funding source"""
    source = get_object_or_404(FundingSource, id=source_id, sacco=request.user.sacco)
    if request.method == 'POST':
        try:
            source.name = request.POST.get('name')
            source.contact_person = request.POST.get('contact_person')
            source.email = request.POST.get('email')
            source.phone = request.POST.get('phone')
            source.save()
            messages.success(request, 'Funding source updated successfully!')
            return redirect('funding_sources')
        except Exception as e:
            messages.error(request, f'Error updating source: {str(e)}')
    context = {
        'source': source,
        'breadcrumbs': [
            {'name': 'Funding Sources', 'url': 'funding_sources'},
            {'name': 'Edit Source', 'url': ''}
        ]
    }
    return render(request, 'funding/edit_funding_source.html', context)