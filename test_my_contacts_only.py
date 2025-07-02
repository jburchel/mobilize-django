#!/usr/bin/env python
import os
import sys
import django

# Add the project root to the path
sys.path.insert(0, os.path.abspath('.'))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mobilize.settings')
django.setup()

from django.contrib.auth import get_user_model
from mobilize.core.permissions import DataAccessManager
from mobilize.contacts.models import Person, Contact

User = get_user_model()

def test_my_contacts_only():
    # Get a super admin user
    super_admin = User.objects.filter(role='super_admin').first()
    if not super_admin:
        print("No super admin found!")
        return
    
    print(f"Testing with super admin: {super_admin.email}")
    print(f"User ID: {super_admin.id}")
    print(f"User role: {super_admin.role}")
    
    # Test default view mode
    print("\n--- Testing DEFAULT view mode ---")
    access_manager = DataAccessManager(super_admin, 'default')
    try:
        people_queryset = access_manager.get_people_queryset()
        count = people_queryset.count()
        print(f"People visible in default mode: {count}")
        
        # Show a sample
        sample = people_queryset[:3]
        for person in sample:
            print(f"  - {person.contact.first_name} {person.contact.last_name} (user_id: {person.contact.user_id})")
    except Exception as e:
        print(f"Error in default mode: {type(e).__name__}: {e}")
    
    # Test my_only view mode
    print("\n--- Testing MY_ONLY view mode ---")
    access_manager = DataAccessManager(super_admin, 'my_only')
    try:
        people_queryset = access_manager.get_people_queryset()
        count = people_queryset.count()
        print(f"People visible in my_only mode: {count}")
        
        # Show the actual query
        print(f"\nGenerated SQL query:")
        print(str(people_queryset.query))
        
        # Show a sample
        sample = people_queryset[:3]
        for person in sample:
            print(f"  - {person.contact.first_name} {person.contact.last_name} (user_id: {person.contact.user_id})")
    except Exception as e:
        print(f"Error in my_only mode: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
    
    # Check if there are any contacts directly assigned to the super admin
    print(f"\n--- Checking contacts assigned to user {super_admin.id} ---")
    contacts_count = Contact.objects.filter(user_id=super_admin.id).count()
    print(f"Contacts directly assigned to this user: {contacts_count}")
    
    # Show sample contacts
    sample_contacts = Contact.objects.filter(user_id=super_admin.id)[:5]
    for contact in sample_contacts:
        print(f"  - {contact.first_name} {contact.last_name} (type: {contact.type}, id: {contact.id})")

if __name__ == "__main__":
    test_my_contacts_only()