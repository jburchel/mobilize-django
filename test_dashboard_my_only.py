#!/usr/bin/env python
import os
import sys
import django

# Add the project root to the path
sys.path.insert(0, os.path.abspath('.'))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mobilize.settings')
django.setup()

from django.test import RequestFactory
from django.contrib.auth import get_user_model
from mobilize.core.views import dashboard
from mobilize.core.permissions import get_data_access_manager

User = get_user_model()

def test_dashboard_my_only():
    # Get a super admin user
    super_admin = User.objects.filter(role='super_admin').first()
    if not super_admin:
        print("No super admin found!")
        return
    
    print(f"Testing dashboard with super admin: {super_admin.email}")
    
    # Create a request factory
    factory = RequestFactory()
    
    # Test default view mode
    print("\n--- Testing DEFAULT view mode ---")
    request = factory.get('/?view_mode=default')
    request.user = super_admin
    
    try:
        # Get access manager to check what's happening
        access_manager = get_data_access_manager(request)
        print(f"View mode: {access_manager.view_mode}")
        print(f"Can view all data: {access_manager.can_view_all_data()}")
        
        # Try to get the people queryset
        people_qs = access_manager.get_people_queryset()
        print(f"People count: {people_qs.count()}")
        
        # Call the dashboard view
        response = dashboard(request)
        print(f"Response status: {response.status_code}")
    except Exception as e:
        print(f"Error in default mode: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
    
    # Test my_only view mode
    print("\n--- Testing MY_ONLY view mode ---")
    request = factory.get('/?view_mode=my_only')
    request.user = super_admin
    
    try:
        # Get access manager to check what's happening
        access_manager = get_data_access_manager(request)
        print(f"View mode: {access_manager.view_mode}")
        print(f"Can view all data: {access_manager.can_view_all_data()}")
        
        # Try each queryset method
        print("\nTesting querysets individually:")
        
        try:
            people_qs = access_manager.get_people_queryset()
            print(f"  - People queryset: OK ({people_qs.count()} records)")
        except Exception as e:
            print(f"  - People queryset: ERROR - {e}")
        
        try:
            churches_qs = access_manager.get_churches_queryset()
            print(f"  - Churches queryset: OK ({churches_qs.count()} records)")
        except Exception as e:
            print(f"  - Churches queryset: ERROR - {e}")
        
        try:
            tasks_qs = access_manager.get_tasks_queryset()
            print(f"  - Tasks queryset: OK ({tasks_qs.count()} records)")
        except Exception as e:
            print(f"  - Tasks queryset: ERROR - {e}")
        
        try:
            comms_qs = access_manager.get_communications_queryset()
            print(f"  - Communications queryset: OK ({comms_qs.count()} records)")
        except Exception as e:
            print(f"  - Communications queryset: ERROR - {e}")
        
        # Now try the full dashboard view
        print("\nCalling dashboard view...")
        response = dashboard(request)
        print(f"Response status: {response.status_code}")
        
    except Exception as e:
        print(f"Error in my_only mode: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_dashboard_my_only()