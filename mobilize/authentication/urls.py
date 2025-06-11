from django.urls import path
from . import views

app_name = 'authentication'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('google-auth/', views.google_auth, name='google_auth'),
    path('google-auth-callback/', views.google_auth_callback, name='google_auth_callback'),
]
