#!/usr/bin/env python
"""
Debug script to test contact filtering logic
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mobilize.settings')
sys.path.append('/Users/jimburchel/Developer-Playground/mobilize-django')
django.setup()

from mobilize.authentication.models import User
from mobilize.contacts.models import Person
from mobilize.authentication.decorators import office_data_filter

print("🔍 Debugging contact filtering...")

try:
    # Get your super admin user
    user = User.objects.get(email='j.burchel@crossoverglobal.net')
    print(f"\n✅ Found user: {user.email} (Role: {user.role})")
    
    # Get initial queryset
    people = Person.objects.select_related('contact', 'contact__office').all()
    print(f"\n📊 Total people in database: {people.count()}")
    
    # Test the office_data_filter function
    filtered_people = office_data_filter(people, user, 'contact__office')
    print(f"📊 After office_data_filter: {filtered_people.count()}")
    
    # Check a few sample records
    print(f"\n📋 Sample people (first 5):")
    for person in people[:5]:
        print(f"   - {person.contact.first_name} {person.contact.last_name}")
        print(f"     Contact ID: {person.contact.id}")
        print(f"     Office ID: {person.contact.office_id}")
        print(f"     User ID: {person.contact.user_id}")
    
    # Check if there are people without office assignments
    people_no_office = people.filter(contact__office_id__isnull=True)
    print(f"\n📊 People without office assignments: {people_no_office.count()}")
    
    # Check if there are people with office assignments
    people_with_office = people.filter(contact__office_id__isnull=False)
    print(f"📊 People with office assignments: {people_with_office.count()}")
    
    # Simulate the exact filtering from the API
    print(f"\n🔧 Simulating API filtering logic...")
    
    # This is the exact logic from person_list_api
    if user.role != 'super_admin':
        print("   User is NOT super_admin - applying office filter")
        filtered_people = office_data_filter(people, user, 'contact__office')
    else:
        print("   User IS super_admin - should see all people")
        filtered_people = people
    
    print(f"   Final count after filtering: {filtered_people.count()}")
    
    if filtered_people.count() > 0:
        print(f"   ✅ People should be visible!")
        for person in filtered_people[:3]:
            print(f"     - {person.contact.first_name} {person.contact.last_name}")
    else:
        print(f"   ❌ No people visible - this is the problem!")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()