"""
URL configuration for sacco_system project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from accounts import views as account_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', account_views.login_view, name='login'),
    path('dashboard/', account_views.dashboard, name='dashboard'),
    path('admin-dashboard/', account_views.admin_dashboard, name='admin_dashboard'),
    path('accounts/', include('accounts.urls')),
    path('members/', include('members.urls')),
    path('savings/', include('savings.urls')),
    path('loans/', include('loans.urls')),
    path('funding/', include('funding.urls')),
    path('projects/', include('projects.urls')),
    path('expenses/', include('expenses.urls')),
    path('reports/', include('reports.urls')),
    path('notifications/', include('notifications.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Custom error handlers
handler404 = 'accounts.views.custom_404'
handler500 = 'accounts.views.custom_500'
