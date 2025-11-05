from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib.auth import get_user_model
from django.utils.crypto import get_random_string
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from django.urls import reverse
from accounts.decorators import sacco_admin_required, admin_or_member_owner_required, member_search_required
from accounts.permissions import filter_queryset_by_user_scope, can_access_member_data, get_accessible_members
from notifications.services import NotificationService
from .models import Member, MemberGroup, MemberProfile
from .forms import MemberForm, MemberGroupForm, ComprehensiveMemberForm, UmscWomenMemberRegistrationForm
from .bulk_import import MemberBulkImportForm, MemberBulkImporter

User = get_user_model()


@sacco_admin_required
def members_overview(request):
    """Overview page showing member summary for all saccos (system admin) or regional saccos (regional admin)"""
    from accounts.permissions import get_accessible_saccos
    from accounts.models import Sacco
    from django.db.models import Count, Avg
    
    accessible_saccos = get_accessible_saccos(request.user)
    
    # Get selected sacco from query parameter
    selected_sacco_id = request.GET.get('sacco')
    
    # Get all members for overview
    all_members = get_accessible_members(request.user).select_related('sacco', 'group')
    
    # Build summary by sacco
    sacco_summaries = []
    for sacco in accessible_saccos:
        sacco_members = all_members.filter(sacco=sacco)
        total_members = sacco_members.count()
        active_members = sacco_members.filter(status='Active').count()
        inactive_members = sacco_members.filter(status='Inactive').count()
        
        sacco_summaries.append({
            'sacco': sacco,
            'total_members': total_members,
            'active_members': active_members,
            'inactive_members': inactive_members,
        })
    
    # Overall totals
    total_all_members = all_members.count()
    total_active_members = all_members.filter(status='Active').count()
    
    return render(request, 'members/members_overview.html', {
        'sacco_summaries': sacco_summaries,
        'accessible_saccos': accessible_saccos,
        'selected_sacco_id': selected_sacco_id,
        'total_all_members': total_all_members,
        'total_active_members': total_active_members,
    })


@sacco_admin_required
def member_list(request):
    from accounts.permissions import get_accessible_saccos
    from accounts.models import Sacco
    
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
    
    # Filter members based on selected sacco
    members = get_accessible_members(request.user).select_related('sacco', 'group').order_by('-date_joined')
    
    # If system admin or regional admin selected a specific sacco, filter by it
    if selected_sacco_id and (request.user.is_system_admin or request.user.is_regional_admin):
        try:
            selected_sacco = Sacco.objects.get(id=selected_sacco_id)
            # Verify user has access to this sacco
            if selected_sacco in accessible_saccos:
                members = members.filter(sacco=selected_sacco)
        except Sacco.DoesNotExist:
            pass

    # CSV export
    if request.GET.get('export') == 'csv':
        import csv
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="members.csv"'
        writer = csv.writer(response)
        writer.writerow(['Member Number', 'Full Name', 'Sacco', 'Phone', 'Email', 'Status', 'District', 'Join Date'])
        for m in members:
            full_name = f"{m.first_name} {m.last_name}" + (f" {m.other_names}" if getattr(m, 'other_names', None) else '')
            writer.writerow([
                m.member_number,
                full_name,
                m.sacco.name if m.sacco else 'N/A',
                m.phone or '',
                m.email or '',
                m.status,
                m.district or '',
                m.date_joined.strftime('%Y-%m-%d') if getattr(m, 'date_joined', None) else ''
            ])
        return response

    context = {
        'members': members,
        'accessible_saccos': accessible_saccos,
        'selected_sacco_id': selected_sacco_id,
        'selected_sacco': selected_sacco,
    }
    return render(request, 'members/member_list.html', context)


@sacco_admin_required
def register_member(request):
    from accounts.permissions import get_accessible_saccos
    from accounts.models import Sacco
    
    # Get accessible saccos for system admin or regional admin
    accessible_saccos = get_accessible_saccos(request.user) if (request.user.is_system_admin or request.user.is_regional_admin) else None
    
    # For regional admins, check if there are any accessible saccos
    if request.user.is_regional_admin:
        if not accessible_saccos or accessible_saccos.count() == 0:
            messages.error(request, 'No Saccos are available in your region. Please create a Sacco first before registering members.')
            return redirect('member_list')
    
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
            except Sacco.DoesNotExist:
                pass
        elif accessible_saccos:
            selected_sacco = accessible_saccos.first()
    else:
        # For non-system admin, use their sacco
        selected_sacco = request.user.sacco
    
    if request.method == 'POST':
        # Get sacco from POST data if available
        post_sacco_id = request.POST.get('sacco')
        if post_sacco_id:
            try:
                post_sacco_id = str(int(post_sacco_id))
                if (request.user.is_system_admin or request.user.is_regional_admin):
                    try:
                        selected_sacco = Sacco.objects.get(id=post_sacco_id)
                        # Verify user has access
                        if selected_sacco in accessible_saccos:
                            pass  # Keep selected_sacco
                        else:
                            selected_sacco = None
                    except Sacco.DoesNotExist:
                        selected_sacco = None
            except (ValueError, TypeError):
                pass
        
        form = UmscWomenMemberRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                # For system admin or regional admin, use selected sacco; for others, use user's sacco
                if (request.user.is_system_admin or request.user.is_regional_admin):
                    if selected_sacco:
                        sacco_for_member = selected_sacco
                    elif accessible_saccos:
                        sacco_for_member = accessible_saccos.first()
                    else:
                        messages.error(request, 'Please select a Sacco for member registration.')
                        return render(request, 'members/register_member.html', {
                            'form': form,
                            'accessible_saccos': accessible_saccos,
                            'selected_sacco_id': selected_sacco_id,
                            'selected_sacco': selected_sacco,
                        })
                else:
                    if not request.user.sacco:
                        messages.error(request, 'You must be associated with a Sacco to register members.')
                        return redirect('member_list')
                    sacco_for_member = request.user.sacco
                
                # Create Member record from UMSC form
                member, initial_deposit = form.save(request_user=request.user, commit=True, sacco=sacco_for_member)

                # Extract for user creation
                first_name = member.first_name
                last_name = member.last_name
                email = member.email
                phone = member.phone
                
                # Generate unique member number
                from django.db import transaction
                with transaction.atomic():
                    # Get the highest existing member number for this sacco
                    last_member = Member.objects.filter(
                        sacco=sacco_for_member,
                        member_number__startswith='MEM'
                    ).order_by('-member_number').first()
                    
                    if last_member and last_member.member_number:
                        try:
                            # Extract the number part and increment
                            last_number = int(last_member.member_number[3:])  # Skip 'MEM' prefix
                            new_number = last_number + 1
                        except (ValueError, IndexError):
                            new_number = 1
                    else:
                        new_number = 1
                    
                    member_number = f"MEM{new_number:04d}"
                    
                    # Double-check uniqueness (in case of race condition)
                    while Member.objects.filter(member_number=member_number).exists():
                        new_number += 1
                        member_number = f"MEM{new_number:04d}"
                
                # Generate username (email or first_name + last_name)
                if email:
                    username = email.split('@')[0]
                else:
                    username = f"{first_name.lower()}{last_name.lower()}"
                
                # Check if username exists and make it unique
                original_username = username
                counter = 1
                while User.objects.filter(username=username).exists():
                    username = f"{original_username}{counter}"
                    counter += 1
                
                # Generate temporary password
                temp_password = get_random_string(12)
                
                # Create User account
                user = User.objects.create_user(
                    username=username,
                    email=email or f"{username}@sacco.com",
                    password=temp_password,
                    first_name=first_name,
                    last_name=last_name,
                    phone=phone,
                    sacco=sacco_for_member,
                    is_active=True
                )
                
                # Create Member record using the comprehensive form
                member.member_number = member_number
                member.save(update_fields=['member_number'])
                
                # Link member to user account
                member.user_account = user
                member.save()
                
                # Create default savings product/account and initial deposit transaction
                from savings.models import SavingProduct, SavingsAccount, SavingsTransaction
                from django.utils.crypto import get_random_string
                product, _ = SavingProduct.objects.get_or_create(
                    sacco=sacco_for_member,
                    defaults={
                        'name': 'UMSC Women Savings',
                        'product_code': f'UMSC-WMN-{get_random_string(4).upper()}',
                        'description': 'Default women savings product'
                    },
                )
                # Generate account number: SACCOCODE-YYYY-XXXXX
                year = timezone.now().year
                prefix = f"{sacco_for_member.name.upper().replace(' ', '')[:6]}-{year}-"
                last_account = SavingsAccount.objects.filter(
                    account_number__startswith=prefix
                ).order_by('-account_number').first()
                if last_account and last_account.account_number:
                    try:
                        last_number = int(last_account.account_number.split('-')[-1])
                        new_number = last_number + 1
                    except (ValueError, IndexError):
                        new_number = 1
                else:
                    new_number = 1
                account_number = f"{prefix}{new_number:05d}"

                account = SavingsAccount.objects.create(
                    member=member,
                    product=product,
                    account_number=account_number,
                    balance=0,
                    created_by=request.user
                )

                SavingsTransaction.objects.create(
                    account=account,
                    txn_type='Deposit',
                    amount=initial_deposit,
                    running_balance=initial_deposit,
                    reference='Initial Deposit',
                    narration=f"Initial deposit via {member.preferred_payment_method or 'N/A'}",
                    performed_by=request.user
                )
                account.balance = initial_deposit
                account.save(update_fields=['balance'])
                
                # Send welcome notification to new member
                NotificationService.create_notification(
                    user=user,
                    title="Welcome to UMSC Sacco!",
                    message=f"Welcome {first_name}! Your account has been created successfully. Your member number is {member_number}.",
                    action_type='member_registration',
                    action_url=reverse('member_profile', args=[member.id]),
                    priority='Medium',
                    sacco=sacco_for_member
                )
                
                # Notify admins about new member registration
                NotificationService.create_notification(
                    user=request.user,
                    title="New Member Registered",
                    message=f"New member {first_name} {last_name} (Member #{member_number}) has been registered.",
                    action_type='member_registration',
                    action_url=reverse('member_profile', args=[member.id]),
                    priority='Low',
                    sacco=sacco_for_member
                )
                
                messages.success(request, 
                    f'Member {first_name} {last_name} registered successfully! '
                    f'Username: {username}, Temporary Password: {temp_password}'
                )
                return redirect('member_list')
                
            except Exception as e:
                import traceback
                messages.error(request, f'Error registering member: {str(e)}')
                # Log the full traceback for debugging
                print(f"Error in register_member: {traceback.format_exc()}")
    else:
        form = UmscWomenMemberRegistrationForm()
    
    # Display form errors if any
    if request.method == 'POST' and not form.is_valid():
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(request, f'{field}: {error}')
    
    return render(request, 'members/register_member.html', {
        'form': form,
        'accessible_saccos': accessible_saccos,
        'selected_sacco_id': selected_sacco_id,
        'selected_sacco': selected_sacco,
    })


@sacco_admin_required
def edit_member(request, member_id):
    member = get_object_or_404(Member, id=member_id, sacco=request.user.sacco)
    
    if request.method == 'POST':
        form = ComprehensiveMemberForm(request.POST, request.FILES, instance=member)
        if form.is_valid():
            form.save()
            messages.success(request, 'Member updated successfully!')
            return redirect('member_profile', member_id=member.id)
    else:
        form = ComprehensiveMemberForm(instance=member)
    
    context = {
        'form': form,
        'member': member,
        'breadcrumbs': [
            {'name': 'Members', 'url': 'member_list'},
            {'name': 'Edit Member', 'url': ''}
        ]
    }
    return render(request, 'members/edit_member.html', context)


@admin_or_member_owner_required
def member_profile(request, member_id):
    member = get_object_or_404(Member, id=member_id)
    
    # Additional permission check for member data access
    if not can_access_member_data(request.user, member):
        messages.error(request, 'Access denied. You can only view your own member profile.')
        return redirect('dashboard')
    # Compute dynamic stats
    try:
        from loans.models import Loan
        from savings.models import SavingsAccount
        from django.db.models import Sum
        active_loans_count = Loan.objects.filter(
            member=member,
            status__in=[
                'Approved',
                'Disbursed',
                'Active'
            ]
        ).count()
        total_savings = SavingsAccount.objects.filter(member=member).aggregate(
            total=Sum('balance')
        )['total'] or 0
    except Exception:
        active_loans_count = 0
        total_savings = 0

    return render(request, 'members/member_profile.html', {
        'member': member,
        'active_loans_count': active_loans_count,
        'total_savings': total_savings,
    })


@sacco_admin_required
def member_groups(request):
    from accounts.permissions import get_accessible_saccos, filter_queryset_by_user_scope
    from accounts.models import Sacco
    
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
    
    # Filter groups based on selected sacco
    groups = filter_queryset_by_user_scope(
        MemberGroup.objects.select_related('sacco').all(),
        request.user,
        'member_group'
    )
    
    # If system admin or regional admin selected a specific sacco, filter by it
    if selected_sacco_id and (request.user.is_system_admin or request.user.is_regional_admin):
        try:
            selected_sacco = Sacco.objects.get(id=selected_sacco_id)
            # Verify user has access to this sacco
            if selected_sacco in accessible_saccos:
                groups = groups.filter(sacco=selected_sacco)
        except Sacco.DoesNotExist:
            pass
    
    # Get sacco for form (selected or user's sacco)
    sacco_for_form = selected_sacco if selected_sacco else request.user.sacco
    
    if request.method == 'POST':
        # For POST, get sacco from form or use selected
        post_sacco_id = request.POST.get('sacco')
        if post_sacco_id and (request.user.is_system_admin or request.user.is_regional_admin):
            try:
                post_sacco = Sacco.objects.get(id=post_sacco_id)
                if post_sacco in accessible_saccos:
                    sacco_for_form = post_sacco
            except Sacco.DoesNotExist:
                pass
        
        form = MemberGroupForm(request.POST, sacco=sacco_for_form)
        if form.is_valid():
            try:
                group = form.save(commit=False)
                group.sacco = sacco_for_form
                group.save()
                messages.success(request, f'Group "{group.name}" created successfully!')
                redirect_url = 'member_groups'
                if selected_sacco_id:
                    redirect_url += f'?sacco={selected_sacco_id}'
                return redirect(redirect_url)
            except Exception as e:
                messages.error(request, f'Error creating group: {str(e)}')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = MemberGroupForm(sacco=sacco_for_form)
    
    context = {
        'groups': groups,
        'form': form,
        'accessible_saccos': accessible_saccos,
        'selected_sacco_id': selected_sacco_id,
        'selected_sacco': selected_sacco,
    }
    return render(request, 'members/member_groups.html', context)


@sacco_admin_required
def edit_member_group(request, group_id):
    """Edit member group"""
    group = get_object_or_404(MemberGroup, id=group_id, sacco=request.user.sacco)
    if request.method == 'POST':
        form = MemberGroupForm(request.POST, instance=group, sacco=request.user.sacco)
        if form.is_valid():
            form.save()
            messages.success(request, 'Member group updated successfully!')
            return redirect('member_groups')
    else:
        form = MemberGroupForm(instance=group, sacco=request.user.sacco)
    context = {
        'form': form,
        'group': group,
        'breadcrumbs': [
            {'name': 'Member Groups', 'url': 'member_groups'},
            {'name': 'Edit Group', 'url': ''}
        ]
    }
    return render(request, 'members/edit_member_group.html', context)


@sacco_admin_required
def view_member_group(request, group_id):
    """View member group details"""
    group = get_object_or_404(MemberGroup, id=group_id, sacco=request.user.sacco)
    members = group.members.all()
    context = {
        'group': group,
        'members': members,
        'breadcrumbs': [
            {'name': 'Member Groups', 'url': 'member_groups'},
            {'name': group.name, 'url': ''}
        ]
    }
    return render(request, 'members/view_member_group.html', context)


@sacco_admin_required
def delete_member_group(request, group_id):
    """Delete member group"""
    group = get_object_or_404(MemberGroup, id=group_id, sacco=request.user.sacco)
    if request.method == 'POST':
        try:
            group.delete()
            messages.success(request, 'Member group deleted successfully!')
        except Exception as e:
            messages.error(request, f'Error deleting group: {str(e)}')
    return redirect('member_groups')


@sacco_admin_required
def inactive_members(request):
    from .constants import MEMBER_STATUS_INACTIVE
    from accounts.permissions import get_accessible_saccos
    from accounts.models import Sacco
    
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
    
    # Filter members based on selected sacco
    members = get_accessible_members(request.user).filter(status=MEMBER_STATUS_INACTIVE)
    
    # If system admin or regional admin selected a specific sacco, filter by it
    if selected_sacco_id and (request.user.is_system_admin or request.user.is_regional_admin):
        try:
            selected_sacco = Sacco.objects.get(id=selected_sacco_id)
            # Verify user has access to this sacco
            if selected_sacco in accessible_saccos:
                members = members.filter(sacco=selected_sacco)
        except Sacco.DoesNotExist:
            pass
    
    return render(request, 'members/inactive_members.html', {
        'members': members,
        'accessible_saccos': accessible_saccos,
        'selected_sacco_id': selected_sacco_id,
        'selected_sacco': selected_sacco,
    })


@login_required
def member_dashboard(request):
    # This is for regular members to view their own dashboard
    if not request.user.is_authenticated:
        return redirect('login')
    
    # Check if user is a member
    try:
        member = Member.objects.get(user_account=request.user)
    except Member.DoesNotExist:
        messages.error(request, 'Member profile not found. Please contact your administrator.')
        return redirect('login')
    """Dashboard for individual members"""
    try:
        # Get the member record for this user
        member = Member.objects.get(user_account=request.user)
        
        # Get member's savings (if any)
        from savings.models import SavingsAccount
        savings_accounts = SavingsAccount.objects.filter(member=member)
        
        # Get member's loans (if any)
        from loans.models import Loan
        loans = Loan.objects.filter(member=member)
        
        context = {
            'member': member,
            'savings_accounts': savings_accounts,
            'loans': loans,
        }
        
        return render(request, 'members/member_dashboard.html', context)
        
    except Member.DoesNotExist:
        # If user is not a member, redirect to admin dashboard
        return redirect('dashboard')


@member_search_required
def search_members(request):
    """AJAX endpoint for member search - supports both navbar and Select2"""
    query = request.GET.get('q', '').strip()
    
    try:
        page = int(request.GET.get('page', 1))
    except (ValueError, TypeError):
        page = 1

    if len(query) < 2:
        return JsonResponse({'members': [], 'results': [], 'total_count': 0})

    try:
        # Get accessible members
        accessible_members = get_accessible_members(request.user)
        
        # Build search query
        base_qs = accessible_members.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(other_names__icontains=query) |
            Q(member_number__icontains=query) |
            Q(phone__icontains=query) |
            Q(email__icontains=query) |
            Q(district__icontains=query) |
            Q(village_town__icontains=query) |
            Q(subcounty__icontains=query) |
            Q(occupation__icontains=query) |
            Q(employer_name__icontains=query)
        ).order_by('first_name', 'last_name')

        paginator = Paginator(base_qs, 30)
        page_obj = paginator.get_page(page)

        members_for_nav = []
        results_for_select2 = []

        for m in page_obj.object_list:
            try:
                full_name = f"{m.first_name} {m.last_name}" + (f" {m.other_names}" if m.other_names else '')
                members_for_nav.append({
                    'id': m.id,
                    'full_name': full_name,
                    'member_number': m.member_number or '',
                    'phone': m.phone or '',
                    'district': m.district or '',
                    'village_town': m.village_town or '',
                    'status': m.status or 'Active',
                    'email': m.email or '',
                    'occupation': m.occupation or '',
                    'profile_url': reverse('member_profile', args=[m.id])
                })

                results_for_select2.append({
                    'id': m.id,
                    'text': full_name,
                    'member_number': m.member_number or '',
                    'phone': m.phone or ''
                })
            except Exception as e:
                # Skip problematic members and continue
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error processing member {m.id if hasattr(m, 'id') else 'unknown'}: {str(e)}")
                continue

        return JsonResponse({
            'members': members_for_nav,
            'results': results_for_select2,
            'total_count': paginator.count
        })
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Search members error: {str(e)}", exc_info=True)
        return JsonResponse({
            'members': [], 
            'results': [], 
            'total_count': 0, 
            'error': f'Error searching members: {str(e)}'
        }, status=500)


@sacco_admin_required
def bulk_import_members(request):
    """Bulk import members from CSV/Excel file"""
    if request.method == 'POST':
        form = MemberBulkImportForm(request.POST, request.FILES)
        if form.is_valid():
            file = form.cleaned_data['file']
            
            # Create importer instance
            importer = MemberBulkImporter(
                sacco=request.user.sacco,
                created_by=request.user
            )
            
            # Process the file
            success = importer.import_from_csv(file)
            summary = importer.get_summary()
            
            if success:
                messages.success(
                    request, 
                    f'Successfully imported {summary["success_count"]} members!'
                )
                return redirect('member_list')
            else:
                # Show errors
                for error in summary['errors']:
                    messages.error(request, error)
                
                messages.warning(
                    request,
                    f'Import completed with errors. '
                    f'Success: {summary["success_count"]}, '
                    f'Skipped: {summary["skipped_count"]}, '
                    f'Errors: {summary["error_count"]}'
                )
    else:
        form = MemberBulkImportForm()
    
    return render(request, 'members/bulk_import.html', {'form': form})


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
def api_create_group(request):
    """API endpoint to create member group via AJAX"""
    if request.method == 'POST':
        try:
            name = request.POST.get('name')
            code = request.POST.get('code')
            description = request.POST.get('description', '')
            leader_id = request.POST.get('leader', '')
            
            if not name or not code:
                return JsonResponse({
                    'success': False,
                    'error': 'Name and code are required'
                })
            
            # Check if group with same name or code exists
            if MemberGroup.objects.filter(sacco=request.user.sacco, name__iexact=name).exists():
                return JsonResponse({
                    'success': False,
                    'error': 'A group with this name already exists'
                })
            
            if MemberGroup.objects.filter(sacco=request.user.sacco, code__iexact=code).exists():
                return JsonResponse({
                    'success': False,
                    'error': 'A group with this code already exists'
                })
            
            # Get leader if provided
            leader = None
            if leader_id:
                leader = get_object_or_404(Member, id=leader_id, sacco=request.user.sacco)
            
            group = MemberGroup.objects.create(
                name=name,
                code=code,
                description=description,
                leader=leader,
                sacco=request.user.sacco
            )
            
            return JsonResponse({
                'success': True,
                'id': group.id,
                'text': f"{group.name} ({group.code})"
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})