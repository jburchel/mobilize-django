import requests
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from django.contrib import messages
from datetime import timedelta

from .models import GoogleToken


def login_view(request):
    """
    Render the login page with Google OAuth configuration.
    """
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            return redirect('core:dashboard')
        else:
            messages.error(request, 'Invalid username or password')
    
    return render(request, 'authentication/login.html', {
        'google_client_id': settings.GOOGLE_CLIENT_ID,
    })


@login_required
def logout_view(request):
    """
    Log out the user and redirect to login page.
    """
    logout(request)
    return redirect('authentication:login')


def google_auth(request):
    """
    Initiate Google OAuth2 flow for authentication and API access.
    """
    # Google OAuth2 authorization URL
    auth_url = "https://accounts.google.com/o/oauth2/auth"
    
    # Parameters for Google OAuth2
    params = {
        'client_id': settings.GOOGLE_CLIENT_ID,
        'redirect_uri': request.build_absolute_uri(reverse('authentication:google_auth_callback')),
        'response_type': 'code',
        'scope': ' '.join([
            'https://www.googleapis.com/auth/userinfo.email',
            'https://www.googleapis.com/auth/userinfo.profile',
            'https://www.googleapis.com/auth/gmail.readonly',
            'https://www.googleapis.com/auth/gmail.send',
            'https://www.googleapis.com/auth/calendar',
            'https://www.googleapis.com/auth/contacts.readonly'
        ]),
        'access_type': 'offline',
        'prompt': 'consent',
        'include_granted_scopes': 'true',
    }
    
    # Build the authorization URL
    auth_url = f"{auth_url}?{'&'.join([f'{k}={v}' for k, v in params.items()])}"
    
    return redirect(auth_url)


def google_auth_callback(request):
    """
    Handle Google OAuth2 callback and store tokens.
    Also creates or authenticates the user based on Google account info.
    """
    code = request.GET.get('code')
    error = request.GET.get('error')
    
    if error:
        return render(request, 'authentication/google_auth_error.html', {'error': error})
    
    if not code:
        return render(request, 'authentication/google_auth_error.html', 
                     {'error': 'No authorization code received'})
    
    # Exchange code for tokens
    token_url = "https://oauth2.googleapis.com/token"
    data = {
        'code': code,
        'client_id': settings.GOOGLE_CLIENT_ID,
        'client_secret': settings.GOOGLE_CLIENT_SECRET,
        'redirect_uri': request.build_absolute_uri(reverse('authentication:google_auth_callback')),
        'grant_type': 'authorization_code',
    }
    
    response = requests.post(token_url, data=data)
    
    if response.status_code != 200:
        return render(request, 'authentication/google_auth_error.html', 
                     {'error': f'Token exchange failed: {response.text}'})
    
    tokens = response.json()
    
    # Get user info from Google
    user_info_response = requests.get(
        'https://www.googleapis.com/oauth2/v3/userinfo',
        headers={'Authorization': f"Bearer {tokens.get('access_token')}"}
    )
    
    if user_info_response.status_code != 200:
        return render(request, 'authentication/google_auth_error.html',
                     {'error': f'Failed to get user info: {user_info_response.text}'})
    
    user_info = user_info_response.json()
    email = user_info.get('email')
    
    if not email:
        return render(request, 'authentication/google_auth_error.html',
                     {'error': 'Email not provided by Google'})
    
    # Get or create user based on email
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    try:
        # Try to find existing user by email
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        # Create new user
        username = email.split('@')[0]
        # Ensure username is unique
        base_username = username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1
        
        # Create the user
        user = User.objects.create_user(
            username=username,
            email=email,
            is_active=True
        )
        
        # Set name if provided
        if user_info.get('name'):
            name_parts = user_info.get('name').split(' ', 1)
            user.first_name = name_parts[0]
            if len(name_parts) > 1:
                user.last_name = name_parts[1]
            user.save()
    
    # Log the user in
    login(request, user)
    
    # Calculate token expiration
    expires_in = tokens.get('expires_in', 3600)
    expires_at = timezone.now() + timedelta(seconds=expires_in)
    
    # Store tokens in database
    GoogleToken.objects.update_or_create(
        user=user,
        defaults={
            'access_token': tokens.get('access_token'),
            'refresh_token': tokens.get('refresh_token', ''),
            'token_type': tokens.get('token_type'),
            'expires_at': expires_at,
            'scopes': tokens.get('scope', '').split(' '),
        }
    )
    
    return redirect('core:dashboard')
