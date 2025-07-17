from django.urls import path
from . import views

app_name = "authentication"

urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("google/callback/", views.google_auth_callback, name="google_auth_callback"),
    path("contact-sync-setup/", views.contact_sync_setup, name="contact_sync_setup"),
    path("google-auth-error/", views.google_auth_error, name="google_auth_error"),
    path("users/", views.UserListView.as_view(), name="user_list"),
    path("debug-oauth/", views.debug_oauth_config, name="debug_oauth_config"),
]
