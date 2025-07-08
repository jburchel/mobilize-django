from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import models
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.urls import reverse
from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
import requests
import json
import logging

from .models import User, UserContactSyncSettings
from mobilize.core.permissions import require_role

logger = logging.getLogger(__name__)


def google_auth_callback(request):
    """
    Handle the OAuth2 callback from Google.
    Create or update user account based on Google profile.
    """
    # Get authorization code from request
    code = request.GET.get('code')
    error = request.GET.get('error')
    
    if error:
        messages.error(request, f"Authentication error: {error}")
        return redirect('authentication:login')
    
    if not code:
        messages.error(request, "No authorization code received from Google")
        return redirect('authentication:login')
    
    try:
        # Exchange authorization code for access token
        from django.conf import settings
        token_url = 'https://oauth2.googleapis.com/token'
        client_id = getattr(settings, 'GOOGLE_CLIENT_ID', '')
        client_secret = getattr(settings, 'GOOGLE_CLIENT_SECRET', '')
        redirect_uri = request.build_absolute_uri('/auth/google/callback/')
        
        token_data = {
            'code': code,
            'client_id': client_id,
            'client_secret': client_secret,
            'redirect_uri': redirect_uri,
            'grant_type': 'authorization_code'
        }
        
        token_response = requests.post(token_url, data=token_data)
        
        if token_response.status_code != 200:
            logger.error(f"Token exchange failed: {token_response.status_code} - {token_response.text}")
            messages.error(request, "Failed to authenticate with Google. Please try again.")
            return redirect('authentication:login')
        
        tokens = token_response.json()
        access_token = tokens.get('access_token')
        refresh_token = tokens.get('refresh_token', '')
        
        # Get user info from Google
        user_info_url = 'https://www.googleapis.com/oauth2/v2/userinfo'
        headers = {'Authorization': f'Bearer {access_token}'}
        user_info_response = requests.get(user_info_url, headers=headers)
        
        if user_info_response.status_code != 200:
            logger.error(f"Failed to get user info: {user_info_response.status_code}")
            messages.error(request, "Failed to retrieve user information from Google.")
            return redirect('authentication:login')
        
        google_user = user_info_response.json()
        
        # Extract user information
        email = google_user.get('email', '').lower()
        first_name = google_user.get('given_name', '')
        last_name = google_user.get('family_name', '')
        google_id = google_user.get('id', '')
        
        if not email:
            messages.error(request, "No email address received from Google")
            return redirect('authentication:login')
        
        # Check if user exists by email
        try:
            user = User.objects.get(email=email)
            # Update existing user's Google tokens
            user.google_access_token = access_token
            user.google_refresh_token = refresh_token or user.google_refresh_token
            if not user.first_name and first_name:
                user.first_name = first_name
            if not user.last_name and last_name:
                user.last_name = last_name
            user.save()
            created = False
        except User.DoesNotExist:
            # Create new user
            username = email.split('@')[0]
            # Make username unique if needed
            base_username = username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1
            
            user = User.objects.create_user(
                username=username,
                email=email,
                first_name=first_name,
                last_name=last_name,
                google_access_token=access_token,
                google_refresh_token=refresh_token
            )
            user.set_unusable_password()  # Google auth users don't need passwords
            user.save()
            created = True
        
        # Log the user in
        user.backend = 'django.contrib.auth.backends.ModelBackend'
        login(request, user)
        
        if created:
            messages.success(request, "Welcome! Your account has been created successfully.")
        else:
            messages.success(request, "Welcome back!")
        
        # Check if user needs to set up contact sync preferences
        try:
            sync_settings = UserContactSyncSettings.objects.get(user=user)
        except UserContactSyncSettings.DoesNotExist:
            # Redirect to contact sync setup for first-time users
            return redirect('authentication:contact_sync_setup')
        
        # Redirect to dashboard
        return redirect('core:dashboard')
        
    except Exception as e:
        logger.exception(f"Unexpected error during Google auth callback: {str(e)}")
        messages.error(request, "An unexpected error occurred during authentication. Please try again.")
        return redirect('authentication:login')


def login_view(request):
    """
    Handle user login with Google OAuth2.
    """
    if request.user.is_authenticated:
        return redirect('core:dashboard')
    
    # Generate Google OAuth URL
    from django.conf import settings
    client_id = getattr(settings, 'GOOGLE_CLIENT_ID', '')
    redirect_uri = request.build_absolute_uri('/auth/google/callback/')
    scope = ' '.join([
        'openid',
        'email',
        'profile',
        'https://www.googleapis.com/auth/gmail.compose',
        'https://www.googleapis.com/auth/gmail.send',
        'https://www.googleapis.com/auth/gmail.readonly',
        'https://www.googleapis.com/auth/contacts',
        'https://www.googleapis.com/auth/calendar'
    ])
    
    google_auth_url = (
        f"https://accounts.google.com/o/oauth2/v2/auth?"
        f"client_id={client_id}&"
        f"redirect_uri={redirect_uri}&"
        f"response_type=code&"
        f"scope={scope}&"
        f"access_type=offline&"
        f"prompt=consent"
    )
    
    context = {
        'google_auth_url': google_auth_url,
    }
    
    return render(request, 'authentication/login.html', context)


@login_required
def logout_view(request):
    """Handle user logout."""
    logout(request)
    messages.info(request, "You have been logged out successfully.")
    return redirect('authentication:login')


@login_required
def contact_sync_setup(request):
    """Handle contact sync preference setup for new users."""
    from .forms import ContactSyncPreferenceForm
    
    if request.method == 'POST':
        form = ContactSyncPreferenceForm(request.POST)
        if form.is_valid():
            sync_preference = form.cleaned_data['sync_preference']
            
            # Get the actual User instance (middleware gives us a wrapper)
            actual_user = User.objects.get(id=request.user.id)
            
            # Create or update user's sync settings
            UserContactSyncSettings.objects.update_or_create(
                user=actual_user,
                defaults={'sync_preference': sync_preference}
            )
            
            messages.success(request, "Contact sync preferences saved successfully!")
            return redirect('core:dashboard')
    else:
        form = ContactSyncPreferenceForm()
    
    context = {
        'form': form,
    }
    return render(request, 'authentication/contact_sync_setup.html', context)


def google_auth_error(request):
    """Handle Google OAuth errors."""
    error = request.GET.get('error', 'Unknown error')
    error_description = request.GET.get('error_description', 'An error occurred during authentication')
    
    context = {
        'error': error,
        'error_description': error_description,
    }
    return render(request, 'authentication/google_auth_error.html', context)


class UserListView(LoginRequiredMixin, ListView):
    """
    List all users in the system - for super admins only.
    """
    model = User
    template_name = 'authentication/user_list.html'
    context_object_name = 'users'
    paginate_by = 25
    
    def dispatch(self, request, *args, **kwargs):
        """Check if user has super_admin role."""
        if not hasattr(request.user, 'role') or request.user.role != 'super_admin':
            from django.http import HttpResponseForbidden
            return HttpResponseForbidden("Access denied: Super admin privileges required")
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        queryset = User.objects.all().select_related().prefetch_related(
            'useroffice_set__office'
        ).annotate(
            office_count=Count('useroffice', distinct=True)
        )
        
        # Search functionality
        search = self.request.GET.get('search', '')
        if search:
            queryset = queryset.filter(
                Q(email__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(username__icontains=search)
            )
        
        # Role filter
        role_filter = self.request.GET.get('role', '')
        if role_filter:
            queryset = queryset.filter(role=role_filter)
        
        # Office filter
        office_filter = self.request.GET.get('office', '')
        if office_filter:
            queryset = queryset.filter(useroffice__office_id=office_filter).distinct()
        
        # Active status filter
        status_filter = self.request.GET.get('status', '')
        if status_filter == 'active':
            queryset = queryset.filter(is_active=True)
        elif status_filter == 'inactive':
            queryset = queryset.filter(is_active=False)
        
        # Sorting
        sort_by = self.request.GET.get('sort', '-date_joined')
        if sort_by in ['email', '-email', 'first_name', '-first_name', 'last_name', '-last_name', 
                        'role', '-role', 'date_joined', '-date_joined', 'last_login', '-last_login']:
            queryset = queryset.order_by(sort_by)
        else:
            queryset = queryset.order_by('-date_joined')
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add filter options
        from mobilize.admin_panel.models import Office
        context['offices'] = Office.objects.all().order_by('name')
        context['roles'] = User.ROLE_CHOICES
        
        # Add current filters
        context['current_search'] = self.request.GET.get('search', '')
        context['current_role'] = self.request.GET.get('role', '')
        context['current_office'] = self.request.GET.get('office', '')
        context['current_status'] = self.request.GET.get('status', '')
        context['current_sort'] = self.request.GET.get('sort', '-date_joined')
        
        # Add statistics
        context['total_users'] = User.objects.count()
        context['active_users'] = User.objects.filter(is_active=True).count()
        context['admin_users'] = User.objects.filter(
            models.Q(role='super_admin') | models.Q(role='office_admin')
        ).count()
        
        return context