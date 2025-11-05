from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Sum, Count, Avg
from accounts.decorators import sacco_admin_required
from accounts.permissions import filter_queryset_by_user_scope, get_accessible_saccos
from accounts.models import Sacco
import json
from .models import Expense, ExpenseCategory
from funding.models import Funding


@sacco_admin_required
def expenses_overview(request):
    """Overview page showing expense summary for all saccos (system admin) or regional saccos (regional admin)"""
    accessible_saccos = get_accessible_saccos(request.user)
    
    # Get selected sacco from query parameter
    selected_sacco_id = request.GET.get('sacco')
    
    # Get all expenses for overview
    all_expenses = filter_queryset_by_user_scope(
        Expense.objects.select_related('sacco', 'category').all(),
        request.user,
        'expense'
    )
    
    # Build summary by sacco
    sacco_summaries = []
    for sacco in accessible_saccos:
        sacco_expenses = all_expenses.filter(sacco=sacco)
        total_expenses = sacco_expenses.count()
        total_amount = sacco_expenses.aggregate(total=Sum('amount'))['total'] or 0
        avg_amount = sacco_expenses.aggregate(avg=Avg('amount'))['avg'] or 0
        
        # Count by category
        category_counts = sacco_expenses.values('category__name').annotate(
            count=Count('id'),
            total=Sum('amount')
        )[:5]  # Top 5 categories
        
        sacco_summaries.append({
            'sacco': sacco,
            'total_expenses': total_expenses,
            'total_amount': total_amount,
            'avg_amount': avg_amount,
            'category_counts': category_counts,
        })
    
    # Overall totals
    total_all_expenses = all_expenses.count()
    total_all_amount = all_expenses.aggregate(total=Sum('amount'))['total'] or 0
    
    return render(request, 'expenses/expenses_overview.html', {
        'sacco_summaries': sacco_summaries,
        'accessible_saccos': accessible_saccos,
        'selected_sacco_id': selected_sacco_id,
        'total_all_expenses': total_all_expenses,
        'total_all_amount': total_all_amount,
    })


@login_required
def expenses_list(request):
    from datetime import timedelta
    from django.utils import timezone
    
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
    
    # Filter expenses based on selected sacco
    expenses = filter_queryset_by_user_scope(
        Expense.objects.select_related('sacco', 'category').all(),
        request.user,
        'expense'
    )
    
    # If system admin or regional admin selected a specific sacco, filter by it
    if selected_sacco_id and (request.user.is_system_admin or request.user.is_regional_admin):
        try:
            selected_sacco = Sacco.objects.get(id=selected_sacco_id)
            # Verify user has access to this sacco
            if selected_sacco in accessible_saccos:
                expenses = expenses.filter(sacco=selected_sacco)
        except Sacco.DoesNotExist:
            pass
    else:
        # For non-admin users, use their sacco
        expenses = expenses.filter(sacco=request.user.sacco)
    
    # Get filter parameters
    period = request.GET.get('period', 'month')  # week, month, year
    category_filter = request.GET.get('category', '')
    
    # Apply category filter
    if category_filter:
        expenses = expenses.filter(category_id=category_filter)
    
    # Apply time period filter
    now = timezone.now()
    if period == 'week':
        start_date = now - timedelta(days=7)
        expenses = expenses.filter(expense_date__gte=start_date)
    elif period == 'month':
        start_date = now - timedelta(days=30)
        expenses = expenses.filter(expense_date__gte=start_date)
    elif period == 'year':
        start_date = now - timedelta(days=365)
        expenses = expenses.filter(expense_date__gte=start_date)
    
    # Get all categories for filter dropdown
    sacco_for_categories = selected_sacco if selected_sacco else request.user.sacco
    all_categories = ExpenseCategory.objects.filter(sacco=sacco_for_categories)
    
    # CSV export
    if request.GET.get('export') == 'csv':
        import csv
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="expenses_{period}.csv"'
        writer = csv.writer(response)
        writer.writerow(['Date', 'Description', 'Category', 'Amount', 'Receipt Number'])
        for exp in expenses:
            writer.writerow([
                exp.expense_date.strftime('%Y-%m-%d') if exp.expense_date else '',
                exp.description,
                exp.category.name if exp.category else '',
                f"{exp.amount:.2f}",
                exp.receipt_number or 'N/A'
            ])
        return response
    
    context = {
        'expenses': expenses,
        'all_categories': all_categories,
        'current_period': period,
        'current_category': category_filter,
        'accessible_saccos': accessible_saccos,
        'selected_sacco_id': selected_sacco_id,
        'selected_sacco': selected_sacco,
        'breadcrumbs': [
            {'name': 'Expenses', 'url': ''}
        ]
    }
    return render(request, 'expenses/expenses_list.html', context)


@login_required
def expense_statistics(request):
    from django.db.models import Sum, Count
    from datetime import timedelta
    from django.utils import timezone
    
    expenses = Expense.objects.filter(sacco=request.user.sacco)
    
    # Get filter parameters
    period = request.GET.get('period', 'month')  # week, month, year
    category_filter = request.GET.get('category', '')
    
    # Apply category filter
    if category_filter:
        expenses = expenses.filter(category_id=category_filter)
    
    # Apply time period filter
    now = timezone.now()
    if period == 'week':
        start_date = now - timedelta(days=7)
        expenses = expenses.filter(expense_date__gte=start_date)
    elif period == 'month':
        start_date = now - timedelta(days=30)
        expenses = expenses.filter(expense_date__gte=start_date)
    elif period == 'year':
        start_date = now - timedelta(days=365)
        expenses = expenses.filter(expense_date__gte=start_date)
    
    # Calculate statistics
    total_expenses = expenses.aggregate(total=Sum('amount'))['total'] or 0
    expense_count = expenses.count()
    
    # Calculate by category
    category_stats = expenses.values('category__name').annotate(
        total=Sum('amount'),
        count=Count('id')
    ).order_by('-total')
    
    # Calculate daily expenses for the last 7 days
    daily_expenses = []
    for i in range(7):
        date = now - timedelta(days=i)
        day_total = expenses.filter(expense_date=date.date()).aggregate(
            total=Sum('amount')
        )['total'] or 0
        daily_expenses.append({
            'date': date.strftime('%Y-%m-%d'),
            'day': date.strftime('%a'),
            'total': day_total
        })
    daily_expenses.reverse()
    
    # Get all categories for filter dropdown
    all_categories = ExpenseCategory.objects.filter(sacco=request.user.sacco)
    
    context = {
        'total_expenses': total_expenses,
        'expense_count': expense_count,
        'category_stats': category_stats,
        'daily_expenses': daily_expenses,
        'all_categories': all_categories,
        'current_period': period,
        'current_category': category_filter,
        'breadcrumbs': [
            {'name': 'Expenses', 'url': 'expenses_list'},
            {'name': 'Expense Statistics', 'url': ''}
        ]
    }
    return render(request, 'expenses/expense_statistics.html', context)


@login_required
def enhanced_expenditure_logs(request):
    """Enhanced expenditure logs with inflow selection and dual allocations"""
    if request.method == 'POST':
        try:
            # Handle expense creation
            allocation_type = request.POST.get('allocation_type')
            amount = request.POST.get('amount')
            date = request.POST.get('date')
            receipt_id = request.POST.get('receipt_id')
            narration = request.POST.get('narration')
            funding_id = request.POST.get('funding_id')
            
            # Get or create expense category for allocation type
            category, created = ExpenseCategory.objects.get_or_create(
                sacco=request.user.sacco,
                name=f"Allocation {allocation_type}",
                defaults={'description': f'Expense category for allocation {allocation_type}'}
            )
            
            # Create expense record
            expense = Expense.objects.create(
                sacco=request.user.sacco,
                amount=amount,
                expense_date=date,
                receipt_number=receipt_id,
                description=narration,
                category=category,
                created_by=request.user
            )
            
            messages.success(request, f'Expense of UGX {float(amount):,.2f} added successfully to allocation {allocation_type}!')
            return redirect('enhanced_expenditure_logs')
            
        except Exception as e:
            messages.error(request, f'Error adding expense: {str(e)}')
    
    # Get available funding for selection
    available_funding = Funding.objects.filter(
        sacco=request.user.sacco,
        status__in=['received', 'allocated']
    )
    
    # Get existing expenses grouped by allocation
    expenses_a = Expense.objects.filter(sacco=request.user.sacco, category__name__icontains='Allocation A')
    expenses_b = Expense.objects.filter(sacco=request.user.sacco, category__name__icontains='Allocation B')
    
    # Calculate totals
    total_a = sum(expense.amount for expense in expenses_a)
    total_b = sum(expense.amount for expense in expenses_b)
    
    context = {
        'available_funding': available_funding,
        'expenses_a': expenses_a,
        'expenses_b': expenses_b,
        'total_a': total_a,
        'total_b': total_b,
    }
    return render(request, 'expenses/enhanced_expenditure_logs.html', context)


@login_required
def expense_settings(request):
    categories = ExpenseCategory.objects.filter(sacco=request.user.sacco)
    return render(request, 'expenses/expense_settings.html', {'categories': categories})


@sacco_admin_required
def add_expense(request):
    """Add new expense"""
    if request.method == 'POST':
        try:
            amount = request.POST.get('amount')
            expense_date = request.POST.get('expense_date')
            receipt_number = request.POST.get('receipt_number')
            description = request.POST.get('description')
            category_id = request.POST.get('category')
            
            if not all([amount, expense_date, description]):
                messages.error(request, 'Please fill in all required fields.')
                return redirect('add_expense')
            
            category = get_object_or_404(ExpenseCategory, id=category_id, sacco=request.user.sacco)
            
            expense = Expense.objects.create(
                sacco=request.user.sacco,
                amount=amount,
                expense_date=expense_date,
                receipt_number=receipt_number,
                description=description,
                category=category,
                created_by=request.user
            )
            
            messages.success(request, f'Expense of UGX {float(amount):,.2f} added successfully!')
            return redirect('expenses_list')
            
        except Exception as e:
            messages.error(request, f'Error adding expense: {str(e)}')
    
    categories = ExpenseCategory.objects.filter(sacco=request.user.sacco)
    context = {
        'categories': categories,
        'breadcrumbs': [
            {'name': 'Expenses', 'url': 'expenses_list'},
            {'name': 'Add Expense', 'url': ''}
        ]
    }
    return render(request, 'expenses/add_expense.html', context)


@sacco_admin_required
def edit_expense(request, expense_id):
    """Edit existing expense"""
    expense = get_object_or_404(Expense, id=expense_id, sacco=request.user.sacco)
    
    if request.method == 'POST':
        try:
            expense.amount = request.POST.get('amount')
            expense.expense_date = request.POST.get('expense_date')
            expense.receipt_number = request.POST.get('receipt_number')
            expense.description = request.POST.get('description')
            category_id = request.POST.get('category')
            
            if category_id:
                expense.category = get_object_or_404(ExpenseCategory, id=category_id, sacco=request.user.sacco)
            
            expense.save()
            messages.success(request, 'Expense updated successfully!')
            return redirect('expenses_list')
            
        except Exception as e:
            messages.error(request, f'Error updating expense: {str(e)}')
    
    categories = ExpenseCategory.objects.filter(sacco=request.user.sacco)
    context = {
        'expense': expense,
        'categories': categories,
        'breadcrumbs': [
            {'name': 'Expenses', 'url': 'expenses_list'},
            {'name': 'Edit Expense', 'url': ''}
        ]
    }
    return render(request, 'expenses/edit_expense.html', context)


@sacco_admin_required
def delete_expense(request, expense_id):
    """Delete expense"""
    expense = get_object_or_404(Expense, id=expense_id, sacco=request.user.sacco)
    
    if request.method == 'POST':
        try:
            expense.delete()
            messages.success(request, 'Expense deleted successfully!')
        except Exception as e:
            messages.error(request, f'Error deleting expense: {str(e)}')
    
    return redirect('expenses_list')


# Category CRUD
@sacco_admin_required
def add_expense_category(request):
    """Add expense category"""
    if request.method == 'POST':
        try:
            name = request.POST.get('name')
            description = request.POST.get('description', '')
            if not name:
                messages.error(request, 'Category name is required.')
                return redirect('expense_settings')
            ExpenseCategory.objects.create(
                name=name,
                description=description,
                sacco=request.user.sacco
            )
            messages.success(request, 'Category created successfully!')
        except Exception as e:
            messages.error(request, f'Error creating category: {str(e)}')
    return redirect('expense_settings')


@sacco_admin_required
def edit_expense_category(request, category_id):
    """Edit expense category"""
    category = get_object_or_404(ExpenseCategory, id=category_id, sacco=request.user.sacco)
    if request.method == 'POST':
        try:
            category.name = request.POST.get('name')
            category.description = request.POST.get('description', '')
            category.save()
            messages.success(request, 'Category updated successfully!')
            return redirect('expense_settings')
        except Exception as e:
            messages.error(request, f'Error updating category: {str(e)}')
    context = {
        'category': category,
        'breadcrumbs': [
            {'name': 'Expense Settings', 'url': 'expense_settings'},
            {'name': 'Edit Category', 'url': ''}
        ]
    }
    return render(request, 'expenses/edit_expense_category.html', context)

# API Views for AJAX
@login_required
def api_categories(request):
    """API endpoint to get expense categories for AJAX"""
    categories = ExpenseCategory.objects.filter(
        sacco=request.user.sacco
    ).values('id', 'name')
    
    return JsonResponse({'categories': list(categories)})


@sacco_admin_required
def api_create_category(request):
    """API endpoint to create expense category via AJAX"""
    if request.method == 'POST':
        try:
            name = request.POST.get('name')
            description = request.POST.get('description', '')
            
            if not name:
                return JsonResponse({
                    'success': False,
                    'error': 'Name is required'
                })
            
            # Check if category with same name exists
            if ExpenseCategory.objects.filter(sacco=request.user.sacco, name__iexact=name).exists():
                return JsonResponse({
                    'success': False,
                    'error': 'A category with this name already exists'
                })
            
            category = ExpenseCategory.objects.create(
                name=name,
                description=description,
                sacco=request.user.sacco
            )
            
            return JsonResponse({
                'success': True,
                'id': category.id,
                'text': category.name
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})