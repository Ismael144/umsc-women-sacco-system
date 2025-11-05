from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count, Avg
from .models import Project
from accounts.decorators import sacco_admin_required
from accounts.permissions import filter_queryset_by_user_scope, get_accessible_saccos
from accounts.models import Sacco


@login_required
def add_project(request):
    if request.method == 'POST':
        try:
            # Get form data
            name = request.POST.get('name')
            description = request.POST.get('description')
            budget = request.POST.get('budget')
            start_date = request.POST.get('start_date')
            end_date = request.POST.get('end_date')
            status = request.POST.get('status')
            
            # Validate required fields
            if not all([name, description, budget, start_date, status]):
                messages.error(request, 'Please fill in all required fields.')
                return redirect('add_project')
            
            # Check if user has a sacco
            if not request.user.sacco:
                messages.error(request, 'You must be associated with a Sacco to add projects.')
                return redirect('add_project')
            
            # Create project
            project = Project.objects.create(
                sacco=request.user.sacco,
                name=name,
                description=description,
                budget=budget,
                start_date=start_date,
                end_date=end_date if end_date else None,
                status=status,
                created_by=request.user
            )
            
            messages.success(request, f'Project "{name}" added successfully!')
            return redirect('existing_projects')
            
        except Exception as e:
            messages.error(request, f'Error adding project: {str(e)}')
            return redirect('add_project')
    
    return render(request, 'projects/add_project.html')


@sacco_admin_required
def projects_overview(request):
    """Overview page showing project summary for all saccos (system admin) or regional saccos (regional admin)"""
    accessible_saccos = get_accessible_saccos(request.user)
    
    # Get selected sacco from query parameter
    selected_sacco_id = request.GET.get('sacco')
    
    # Get all projects for overview
    all_projects = filter_queryset_by_user_scope(
        Project.objects.select_related('sacco').all(),
        request.user,
        'project'
    )
    
    # Build summary by sacco
    sacco_summaries = []
    for sacco in accessible_saccos:
        sacco_projects = all_projects.filter(sacco=sacco)
        total_projects = sacco_projects.count()
        active_projects = sacco_projects.filter(status='active').count()
        planning_projects = sacco_projects.filter(status='planning').count()
        completed_projects = sacco_projects.filter(status='completed').count()
        on_hold_projects = sacco_projects.filter(status='on_hold').count()
        cancelled_projects = sacco_projects.filter(status='cancelled').count()
        
        total_budget = sacco_projects.aggregate(total=Sum('budget'))['total'] or 0
        avg_budget = sacco_projects.aggregate(avg=Avg('budget'))['avg'] or 0
        
        sacco_summaries.append({
            'sacco': sacco,
            'total_projects': total_projects,
            'active_projects': active_projects,
            'planning_projects': planning_projects,
            'completed_projects': completed_projects,
            'on_hold_projects': on_hold_projects,
            'cancelled_projects': cancelled_projects,
            'total_budget': total_budget,
            'avg_budget': avg_budget,
        })
    
    # Overall totals
    total_all_projects = all_projects.count()
    total_all_budget = all_projects.aggregate(total=Sum('budget'))['total'] or 0
    
    return render(request, 'projects/projects_overview.html', {
        'sacco_summaries': sacco_summaries,
        'accessible_saccos': accessible_saccos,
        'selected_sacco_id': selected_sacco_id,
        'total_all_projects': total_all_projects,
        'total_all_budget': total_all_budget,
    })


@login_required
def existing_projects(request):
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
    
    # Filter projects based on selected sacco
    projects = filter_queryset_by_user_scope(
        Project.objects.select_related('sacco').all(),
        request.user,
        'project'
    ).order_by('-created_at')
    
    # If system admin or regional admin selected a specific sacco, filter by it
    if selected_sacco_id and (request.user.is_system_admin or request.user.is_regional_admin):
        try:
            selected_sacco = Sacco.objects.get(id=selected_sacco_id)
            # Verify user has access to this sacco
            if selected_sacco in accessible_saccos:
                projects = projects.filter(sacco=selected_sacco)
        except Sacco.DoesNotExist:
            pass
    
    # CSV export
    if request.GET.get('export') == 'csv':
        import csv
        from django.http import HttpResponse
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="projects.csv"'
        writer = csv.writer(response)
        writer.writerow(['Project Name', 'Sacco', 'Description', 'Budget', 'Start Date', 'End Date', 'Status'])
        for proj in projects:
            writer.writerow([
                proj.name,
                proj.sacco.name if proj.sacco else 'N/A',
                proj.description,
                f"{proj.budget:.2f}",
                proj.start_date.strftime('%Y-%m-%d') if proj.start_date else '',
                proj.end_date.strftime('%Y-%m-%d') if proj.end_date else 'Ongoing',
                proj.get_status_display()
            ])
        return response
    
    return render(request, 'projects/existing_projects.html', {
        'projects': projects,
        'accessible_saccos': accessible_saccos,
        'selected_sacco_id': selected_sacco_id,
        'selected_sacco': selected_sacco,
    })


@sacco_admin_required
def edit_project(request, project_id):
    """Edit project"""
    project = get_object_or_404(Project, id=project_id, sacco=request.user.sacco)
    if request.method == 'POST':
        try:
            project.name = request.POST.get('name')
            project.description = request.POST.get('description')
            project.budget = request.POST.get('budget')
            project.start_date = request.POST.get('start_date')
            project.end_date = request.POST.get('end_date') or None
            project.status = request.POST.get('status')
            project.save()
            messages.success(request, 'Project updated successfully!')
            return redirect('existing_projects')
        except Exception as e:
            messages.error(request, f'Error updating project: {str(e)}')
    context = {
        'project': project,
        'breadcrumbs': [
            {'name': 'Projects', 'url': 'existing_projects'},
            {'name': 'Edit Project', 'url': ''}
        ]
    }
    return render(request, 'projects/edit_project.html', context)


@sacco_admin_required
def view_project(request, project_id):
    """View project details"""
    project = get_object_or_404(Project, id=project_id, sacco=request.user.sacco)
    context = {
        'project': project,
        'breadcrumbs': [
            {'name': 'Projects', 'url': 'existing_projects'},
            {'name': project.name, 'url': ''}
        ]
    }
    return render(request, 'projects/view_project.html', context)