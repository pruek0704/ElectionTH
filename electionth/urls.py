# electionth/urls.py

from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', lambda r: redirect('citizen_login'), name='home'),
    path('', include('voting.urls')),
    path('accounts/', include('django.contrib.auth.urls')),  # สำหรับ Admin login
]