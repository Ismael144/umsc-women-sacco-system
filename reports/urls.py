from django.urls import path
from . import views

urlpatterns = [
    path('', views.reports_index, name='reports_index'),
    path('loan/', views.loan_report, name='loan_report'),
    path('member/', views.member_report, name='member_report'),
    path('funding/', views.funding_report, name='funding_report'),
    # Performance (KRAs & KPIs)
    path('performance/', views.performance_overview, name='reports_performance'),
    path('performance/kras/', views.manage_kras, name='reports_performance_kras'),
    path('performance/kpis/<int:kra_id>/', views.manage_kpis, name='reports_performance_kpis'),
    path('performance/periods/', views.manage_periods, name='reports_performance_periods'),
    path('performance/results/', views.enter_results, name='reports_performance_results'),
]
