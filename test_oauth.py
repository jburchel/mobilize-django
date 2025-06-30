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

print('=== DEBUGGING GOOGLE OAUTH ===')
print(f'Current Client ID: {settings.GOOGLE_CLIENT_ID}')
print(f'Token was created: {token.created_at}')
print(f'Token expires: {token.expires_at}')
print()

# Test a simple Google API call
headers = {'Authorization': f'Bearer {token.access_token}'}
response = requests.get('https://www.googleapis.com/oauth2/v3/userinfo', headers=headers)

print(f'Google API test call status: {response.status_code}')
if response.status_code != 200:
    print(f'Error response: {response.text}')
else:
    print('Token is working for basic API calls')
    user_info = response.json()
    print(f'User email: {user_info.get("email")}')