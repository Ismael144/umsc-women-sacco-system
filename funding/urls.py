from django.urls import path
from . import views

urlpatterns = [
    path('overview/', views.funding_overview, name='funding_overview'),
    path('', views.funding_list, name='funding_list'),
    path('add/', views.funding_list, name='add_funding'),  # Redirect to main page
    path('allocation/', views.funds_allocation, name='funds_allocation'),
    path('enhanced-allocation/', views.enhanced_funds_allocation, name='enhanced_funds_allocation'),
    path('expenditure/', views.expenditure_logs, name='expenditure_logs'),
    path('sources/', views.funding_sources, name='funding_sources'),
    path('sources/add/', views.add_funding_source, name='add_funding_source'),
    path('sources/edit/<int:source_id>/', views.edit_funding_source, name='edit_funding_source'),
]
