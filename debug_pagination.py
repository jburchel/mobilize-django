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

from django.test import RequestFactory
from mobilize.authentication.models import User
from mobilize.contacts.views import person_list

def test_pagination_issue():
    """Test both lazy and traditional pagination"""
    print('=== TESTING PAGINATION ISSUE ===')
    
    # Get a non-super_admin user
    office_admin = User.objects.filter(role='office_admin').first()
    print(f'Test user: {office_admin.email} (Role: {office_admin.role})')
    print(f'User offices: {[uo.office.name for uo in office_admin.useroffice_set.all()]}')
    
    factory = RequestFactory()
    
    # Test 1: Traditional pagination (lazy=false)
    print('\n--- Test 1: Traditional Pagination (lazy=false) ---')
    request = factory.get('/contacts/person_list/?lazy=false')
    request.user = office_admin
    
    response = person_list(request)
    print(f'Response status: {response.status_code}')
    
    # Get the rendered content to check what template was used
    rendered_content = response.render().content.decode('utf-8')
    
    # Check if it's using lazy loading template
    if 'person_list_lazy.html' in str(response.template_name) if hasattr(response, 'template_name') else False:
        print('Template: person_list_lazy.html (LAZY LOADING)')
        # Look for the count display in lazy template
        if 'id="current-count">0<' in rendered_content and 'id="total-count">0<' in rendered_content:
            print('❌ Found "0 of 0" in lazy template - this is the issue!')
    else:
        print('Template: person_list.html (TRADITIONAL PAGINATION)')
        # Look for pagination info in traditional template
        if 'Showing' in rendered_content and 'of' in rendered_content:
            # Extract the pagination text
            import re
            pagination_match = re.search(r'Showing (\d+) - (\d+) of (\d+) items', rendered_content)
            if pagination_match:
                start, end, total = pagination_match.groups()
                print(f'✅ Traditional pagination shows: "{start} - {end} of {total} items"')
            else:
                print('❓ Traditional pagination format not found')
    
    # Test 2: Lazy loading (default)
    print('\n--- Test 2: Lazy Loading (default) ---')
    request = factory.get('/contacts/person_list/')  # Default is lazy=true
    request.user = office_admin
    
    response = person_list(request)
    print(f'Response status: {response.status_code}')
    
    rendered_content = response.render().content.decode('utf-8')
    
    if 'id="current-count">0<' in rendered_content and 'id="total-count">0<' in rendered_content:
        print('❌ Lazy template shows "0 of 0" initially (this is expected, should be updated by JS)')
    
    # Check if JavaScript lazy loading is properly set up
    if 'lazy-loading.js' in rendered_content:
        print('✅ lazy-loading.js script is included')
    else:
        print('❌ lazy-loading.js script is missing!')
    
    # Test 3: Super admin user
    print('\n--- Test 3: Super Admin User ---')
    super_admin = User.objects.filter(role='super_admin').first()
    print(f'Super admin: {super_admin.email}')
    
    request = factory.get('/contacts/person_list/?lazy=false')
    request.user = super_admin
    
    response = person_list(request)
    rendered_content = response.render().content.decode('utf-8')
    
    # Extract pagination info for super admin
    import re
    pagination_match = re.search(r'Showing (\d+) - (\d+) of (\d+) items', rendered_content)
    if pagination_match:
        start, end, total = pagination_match.groups()
        print(f'✅ Super admin sees: "{start} - {end} of {total} items"')
    else:
        print('❓ Super admin pagination format not found')

if __name__ == '__main__':
    test_pagination_issue()