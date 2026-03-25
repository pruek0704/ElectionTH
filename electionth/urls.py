# electionth/urls.py

from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect

urlpatterns = [
    path('django-admin/logout/', lambda r: redirect('/admin-panel/logout/')),
    path('django-admin/', admin.site.urls),
    path('admin/logout/', lambda r: redirect('/admin-panel/logout/')),
    path('accounts/login/', lambda r: redirect('citizen_login')),
    path('', lambda r: redirect('citizen_login'), name='home'),
    path('', include('voting.urls')),
]