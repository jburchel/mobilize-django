#!/usr/bin/env python
import os
import sys
import django

# Add the project root to the path
sys.path.insert(0, os.path.abspath('.'))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mobilize.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.auth.middleware import AuthenticationMiddleware
from django.test import RequestFactory

User = get_user_model()

def test_dashboard_500_error():
    # Get a super admin user
    super_admin = User.objects.filter(role='super_admin').first()
    if not super_admin:
        print("No super admin found!")
        return
    
    print(f"Testing with super admin: {super_admin.email}")
    
    # Create a test client
    client = Client()
    
    # Login as super admin
    client.force_login(super_admin)
    
    # Test default view
    print("\n--- Testing DEFAULT view via Client ---")
    response = client.get('/', {'view_mode': 'default'})
    print(f"Response status: {response.status_code}")
    if response.status_code != 200:
        print(f"Response content: {response.content[:500]}")
    
    # Test my_only view
    print("\n--- Testing MY_ONLY view via Client ---")
    response = client.get('/', {'view_mode': 'my_only'})
    print(f"Response status: {response.status_code}")
    if response.status_code != 200:
        print(f"Response content: {response.content[:500]}")
        if hasattr(response, 'context') and response.context:
            if 'exception' in response.context:
                print(f"Exception: {response.context['exception']}")
    
    # Check for office admin
    office_admin = User.objects.filter(role='office_admin').first()
    if office_admin:
        print(f"\n--- Testing with office admin: {office_admin.email} ---")
        client.force_login(office_admin)
        
        # Check office assignments
        office_count = office_admin.useroffice_set.count()
        print(f"Office assignments: {office_count}")
        
        response = client.get('/', {'view_mode': 'my_only'})
        print(f"Response status: {response.status_code}")
        if response.status_code != 200:
            print(f"Response content: {response.content[:500]}")

if __name__ == "__main__":
    test_dashboard_500_error()