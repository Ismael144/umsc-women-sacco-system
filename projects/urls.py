from django.urls import path
from . import views

urlpatterns = [
    path('overview/', views.projects_overview, name='projects_overview'),
    path('add/', views.add_project, name='add_project'),
    path('all/', views.existing_projects, name='existing_projects'),
    path('edit/<int:project_id>/', views.edit_project, name='edit_project'),
    path('view/<int:project_id>/', views.view_project, name='view_project'),
]
