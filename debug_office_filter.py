#!/usr/bin/env python

import os
import sys
import django

# Add the project root to Python path
sys.path.append('/Users/jimburchel/Developer-Playground/mobilize-django')

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mobilize.settings')
os.environ['LOG_LEVEL'] = 'INFO'
django.setup()

from mobilize.authentication.models import User
from mobilize.authentication.decorators import office_data_filter
from mobilize.contacts.models import Person, Contact

print('=== OFFICE DATA FILTER TESTING ===')

# Test with a non-super_admin user
office_admin = User.objects.filter(role='office_admin').first()
if office_admin:
    print(f'Testing with office_admin: {office_admin.email}')
    print(f'User offices: {[uo.office.name for uo in office_admin.useroffice_set.all()]}')
    
    # Test with Person queryset
    all_people = Person.objects.all()
    print(f'Total people before filtering: {all_people.count()}')
    
    filtered_people = office_data_filter(all_people, office_admin, 'contact__office')
    print(f'People after office filtering: {filtered_people.count()}')

# Test with super_admin
super_admin = User.objects.filter(role='super_admin').first()
if super_admin:
    print(f'\nTesting with super_admin: {super_admin.email}')
    print(f'User offices: {[uo.office.name for uo in super_admin.useroffice_set.all()]}')
    
    all_people = Person.objects.all()
    print(f'Total people before filtering: {all_people.count()}')
    
    filtered_people = office_data_filter(all_people, super_admin, 'contact__office')
    print(f'People after office filtering: {filtered_people.count()}')

print()
print('=== CHECKING ISSUE WITH person_list VIEW ===')
# Simulate the exact logic from person_list view
print('Simulating person_list view logic...')

# Get a user that's not super_admin
test_user = User.objects.filter(role='office_admin').first()
print(f'Test user: {test_user.email} (Role: {test_user.role})')

# This is the exact code from line 93-97 in person_list view
people = Person.objects.select_related('contact', 'contact__office').all()
print(f'Initial queryset count: {people.count()}')

# Apply office-level filtering only for non-super admins
if test_user.role != 'super_admin':
    people = office_data_filter(people, test_user, 'contact__office')
    print(f'After office_data_filter: {people.count()}')

# Check what the Paginator would see
from django.core.paginator import Paginator
paginator = Paginator(people, 25)
print(f'Paginator count: {paginator.count}')
print(f'Paginator num_pages: {paginator.num_pages}')

# Get first page
page_obj = paginator.get_page(1)
print(f'Page 1 object count: {len(page_obj.object_list)}')
print(f'Page 1 start_index: {page_obj.start_index}')
print(f'Page 1 end_index: {page_obj.end_index}')

print()
print('=== TESTING LAZY LOADING API ===')
# Test the person_list_api function similar to the view
print('Testing person_list_api behavior...')

# Simulate the API call
people_api = Person.objects.all()
print(f'API: Initial people count: {people_api.count()}')

# Apply office filtering based on user role
if test_user.role != 'super_admin':
    people_api = office_data_filter(people_api, test_user, 'contact__office')
    print(f'API: After office filtering: {people_api.count()}')

# Test pagination slice
per_page = 25
page = 1
start_idx = (page - 1) * per_page
end_idx = start_idx + per_page

people_slice = list(people_api[start_idx:end_idx])
print(f'API: Page slice count: {len(people_slice)}')
print(f'API: Total count for pagination: {people_api.count()}')