from django.urls import path
from . import views

urlpatterns = [
    path('overview/', views.loans_overview, name='loans_overview'),
    path('add/', views.add_loan, name='add_loan'),
    path('edit/<int:loan_id>/', views.edit_loan, name='edit_loan'),
    path('all/', views.view_all_loans, name='view_all_loans'),
    path('statistics/', views.loan_statistics, name='loan_statistics'),
    path('borrowers/', views.all_borrowers, name='all_borrowers'),
    path('pending-approval/', views.pending_approval, name='pending_approval'),
    path('pending-disbursement/', views.pending_disbursement, name='pending_disbursement'),
    path('declined/', views.loans_declined, name='loans_declined'),
    path('withdrawn/', views.loans_withdrawn, name='loans_withdrawn'),
    path('written-off/', views.loans_written_off, name='loans_written_off'),
    path('closed/', views.loans_closed, name='loans_closed'),
    path('approved/', views.loans_approved, name='loans_approved'),
    path('disbursed/', views.disbursed_loans, name='disbursed_loans'),
    path('repayments/', views.repayments, name='repayments'),
    path('profile/<int:loan_id>/', views.loan_profile, name='loan_profile'),
    path('approve/<int:loan_id>/', views.approve_loan, name='approve_loan'),
    path('reject/<int:loan_id>/', views.reject_loan, name='reject_loan'),
    path('disburse/<int:loan_id>/', views.disburse_loan, name='disburse_loan'),
    path('products/', views.manage_loan_products, name='manage_loan_products'),
    path('products/create/', views.create_loan_product, name='create_loan_product'),
    path('products/edit/<int:product_id>/', views.edit_loan_product, name='edit_loan_product'),
]
