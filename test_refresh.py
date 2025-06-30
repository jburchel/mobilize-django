#!/usr/bin/env python
import os
import django
import sys

# Add the project directory to Python path
sys.path.append('/Users/jimburchel/Developer-Playground/mobilize-django')

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mobilize.settings')
django.setup()

from django.conf import settings
from mobilize.authentication.models import GoogleToken
from django.contrib.auth import get_user_model
import requests

User = get_user_model()
user = User.objects.get(username='j.burchel')
token = GoogleToken.objects.get(user=user)

print('=== TESTING TOKEN REFRESH ===')
print(f'Refresh token exists: {bool(token.refresh_token)}')
print(f'Current Client ID: {settings.GOOGLE_CLIENT_ID}')
print(f'Client Secret exists: {bool(settings.GOOGLE_CLIENT_SECRET)}')
print()

# Try manual refresh
refresh_data = {
    'client_id': settings.GOOGLE_CLIENT_ID,
    'client_secret': settings.GOOGLE_CLIENT_SECRET,
    'refresh_token': token.refresh_token,
    'grant_type': 'refresh_token'
}

print('Attempting manual token refresh...')
response = requests.post('https://oauth2.googleapis.com/token', data=refresh_data)

print(f'Refresh response status: {response.status_code}')
print(f'Refresh response: {response.text}')

if response.status_code == 200:
    print('Manual refresh successful!')
    new_tokens = response.json()
    print(f'New access token received: {bool(new_tokens.get("access_token"))}')
else:
    print('Manual refresh failed - this confirms the issue is with OAuth configuration')