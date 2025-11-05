from django.urls import path
from . import views

urlpatterns = [
    path('overview/', views.savings_overview, name='savings_overview'),
    path('accounts/', views.savings_accounts, name='savings_accounts'),
    path('accounts/create/', views.create_savings_account, name='create_savings_account'),
    path('accounts/edit/<int:account_id>/', views.edit_savings_account, name='edit_savings_account'),
    path('transactions/add/', views.add_savings_transaction, name='add_savings_transaction'),
    path('statements/', views.savings_statements, name='savings_statements'),
    path('products/', views.saving_products, name='saving_products'),
    path('products/create/', views.create_saving_product, name='create_saving_product'),
    path('products/edit/<int:product_id>/', views.edit_saving_product, name='edit_saving_product'),
    # API endpoints
    path('api/members/', views.api_members, name='savings_api_members'),
    path('api/products/', views.api_products, name='savings_api_products'),
    path('api/create-account/', views.api_create_account, name='savings_api_create_account'),
]
