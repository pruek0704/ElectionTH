# voting/urls.py

from django.urls import path
from . import views

urlpatterns = [
    # Citizen Auth
    path('login/', views.citizen_login, name='citizen_login'),
    path('logout/', views.citizen_logout, name='citizen_logout'),

    # Citizen Voting
    path('dashboard/', views.citizen_dashboard, name='citizen_dashboard'),
    path('vote/constituency/', views.vote_constituency, name='vote_constituency'),
    path('vote/constituency/submit/', views.submit_constituency_vote, name='submit_constituency'),
    path('vote/party/', views.vote_party, name='vote_party'),
    path('vote/party/submit/', views.submit_party_vote, name='submit_party'),

    # Admin
    path('admin-panel/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-panel/constituency/', views.admin_constituency_results, name='admin_constituency_results'),
    path('admin-panel/party/', views.admin_party_results, name='admin_party_results'),
    path('api/results/', views.api_results, name='api_results'),
]