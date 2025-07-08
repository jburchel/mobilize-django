#!/usr/bin/env python3

"""
Debug script to test Settings view components individually.
Run from the Django project root with: python debug_settings.py
"""

import os
import sys
import django

# Add the project directory to Python path
sys.path.append('/Users/jimburchel/Developer-Playground/mobilize-django')

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mobilize.settings')

# Setup Django
django.setup()

def test_imports():
    """Test if all required imports work."""
    print("Testing imports...")
    
    try:
        from mobilize.authentication.models import UserContactSyncSettings
        print("✓ UserContactSyncSettings import successful")
    except Exception as e:
        print(f"✗ UserContactSyncSettings import failed: {e}")
        return False
    
    try:
        from mobilize.authentication.forms import UserContactSyncSettingsForm, UserProfileForm
        print("✓ Forms import successful")
    except Exception as e:
        print(f"✗ Forms import failed: {e}")
        return False
    
    try:
        from mobilize.communications.gmail_service import GmailService
        print("✓ GmailService import successful")
    except Exception as e:
        print(f"✗ GmailService import failed: {e}")
        return False
    
    return True

def test_user_query():
    """Test querying a user and their sync settings."""
    print("\nTesting user queries...")
    
    try:
        from mobilize.authentication.models import User, UserContactSyncSettings
        
        # Get the first user
        user = User.objects.first()
        if not user:
            print("✗ No users found in database")
            return False
        
        print(f"✓ Found user: {user.email}")
        
        # Test sync settings query
        sync_settings, created = UserContactSyncSettings.objects.get_or_create(
            user=user,
            defaults={'sync_preference': 'crm_only'}
        )
        
        if created:
            print("✓ Created new sync settings")
        else:
            print("✓ Found existing sync settings")
        
        return True
        
    except Exception as e:
        print(f"✗ User query failed: {e}")
        return False

def test_forms():
    """Test form initialization."""
    print("\nTesting form initialization...")
    
    try:
        from mobilize.authentication.models import User, UserContactSyncSettings
        from mobilize.authentication.forms import UserContactSyncSettingsForm, UserProfileForm
        
        user = User.objects.first()
        sync_settings, _ = UserContactSyncSettings.objects.get_or_create(
            user=user,
            defaults={'sync_preference': 'crm_only'}
        )
        
        # Test sync form
        sync_form = UserContactSyncSettingsForm(instance=sync_settings, user=user)
        print("✓ UserContactSyncSettingsForm initialized")
        
        # Test profile form
        profile_form = UserProfileForm(instance=user)
        print("✓ UserProfileForm initialized")
        
        return True
        
    except Exception as e:
        print(f"✗ Form initialization failed: {e}")
        return False

def test_gmail_service():
    """Test Gmail service initialization."""
    print("\nTesting Gmail service...")
    
    try:
        from mobilize.authentication.models import User
        from mobilize.communications.gmail_service import GmailService
        
        user = User.objects.first()
        gmail_service = GmailService(user)
        print("✓ GmailService initialized")
        
        # Test authentication check
        gmail_connected = gmail_service.is_authenticated()
        print(f"✓ Gmail authentication check: {gmail_connected}")
        
        return True
        
    except Exception as e:
        print(f"✗ Gmail service failed: {e}")
        return False

if __name__ == "__main__":
    print("=== Settings Debug Test ===")
    
    success = True
    success &= test_imports()
    success &= test_user_query() 
    success &= test_forms()
    success &= test_gmail_service()
    
    if success:
        print("\n✓ All tests passed - Settings view should work")
    else:
        print("\n✗ Some tests failed - this explains the Settings error")