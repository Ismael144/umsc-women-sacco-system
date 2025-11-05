from django.urls import path
from . import views

urlpatterns = [
    path('overview/', views.expenses_overview, name='expenses_overview'),
    path('', views.expenses_list, name='expenses_list'),
    path('statistics/', views.expense_statistics, name='expense_statistics'),
    path('add/', views.add_expense, name='add_expense'),
    path('edit/<int:expense_id>/', views.edit_expense, name='edit_expense'),
    path('delete/<int:expense_id>/', views.delete_expense, name='delete_expense'),
    path('enhanced-logs/', views.enhanced_expenditure_logs, name='enhanced_expenditure_logs'),
    path('settings/', views.expense_settings, name='expense_settings'),
    # Category CRUD
    path('category/add/', views.add_expense_category, name='add_expense_category'),
    path('category/edit/<int:category_id>/', views.edit_expense_category, name='edit_expense_category'),
    # API endpoints
    path('api/categories/', views.api_categories, name='expenses_api_categories'),
    path('api/create-category/', views.api_create_category, name='expenses_api_create_category'),
]
