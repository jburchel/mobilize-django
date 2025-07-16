#!/usr/bin/env python3
"""
Test script to verify that the notes search functionality works correctly.
"""

import os
import sys
import django
from django.conf import settings

# Add the project directory to the Python path
sys.path.insert(0, '/Users/jimburchel/Developer-Playground/mobilize-django')

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mobilize.settings')
django.setup()

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from mobilize.contacts.models import Contact, Person
from mobilize.admin_panel.models import Office

User = get_user_model()

def test_notes_search():
    """Test that notes search functionality works correctly."""
    print("Testing notes search functionality...")
    
    # Create a test user and office
    office = Office.objects.create(name="Test Office")
    user = User.objects.create_user(
        username='testuser',
        email='test@example.com',
        first_name='Test',
        last_name='User',
        role='super_admin'
    )
    
    # Create a test contact with notes
    contact = Contact.objects.create(
        first_name='John',
        last_name='Doe',
        email='john@example.com',
        type='person',
        notes='This person is interested in missions work',
        initial_notes='Met at conference, very enthusiastic',
        office=office,
        user=user
    )
    
    # Create a Person record
    person = Person.objects.create(contact=contact)
    
    # Create another contact without relevant notes
    contact2 = Contact.objects.create(
        first_name='Jane',
        last_name='Smith',
        email='jane@example.com',
        type='person',
        notes='Regular supporter',
        office=office,
        user=user
    )
    person2 = Person.objects.create(contact=contact2)
    
    # Test the search functionality
    client = Client()
    client.force_login(user)
    
    # Test 1: Search for "missions" should find John
    response = client.get('/contacts/api/list/?q=missions')
    assert response.status_code == 200
    data = response.json()
    print(f"Search for 'missions': Found {data['total']} results")
    assert data['total'] == 1
    assert data['results'][0]['name'] == 'John Doe'
    
    # Test 2: Search for "conference" should find John
    response = client.get('/contacts/api/list/?q=conference')
    assert response.status_code == 200
    data = response.json()
    print(f"Search for 'conference': Found {data['total']} results")
    assert data['total'] == 1
    assert data['results'][0]['name'] == 'John Doe'
    
    # Test 3: Search for "enthusiastic" should find John
    response = client.get('/contacts/api/list/?q=enthusiastic')
    assert response.status_code == 200
    data = response.json()
    print(f"Search for 'enthusiastic': Found {data['total']} results")
    assert data['total'] == 1
    assert data['results'][0]['name'] == 'John Doe'
    
    # Test 4: Search for "supporter" should find Jane
    response = client.get('/contacts/api/list/?q=supporter')
    assert response.status_code == 200
    data = response.json()
    print(f"Search for 'supporter': Found {data['total']} results")
    assert data['total'] == 1
    assert data['results'][0]['name'] == 'Jane Smith'
    
    # Test 5: Search for "nonexistent" should find no results
    response = client.get('/contacts/api/list/?q=nonexistent')
    assert response.status_code == 200
    data = response.json()
    print(f"Search for 'nonexistent': Found {data['total']} results")
    assert data['total'] == 0
    
    # Test 6: Search for name should still work
    response = client.get('/contacts/api/list/?q=John')
    assert response.status_code == 200
    data = response.json()
    print(f"Search for 'John': Found {data['total']} results")
    assert data['total'] == 1
    assert data['results'][0]['name'] == 'John Doe'
    
    print("✅ All tests passed! Notes search is working correctly.")
    
    # Clean up
    Person.objects.all().delete()
    Contact.objects.all().delete()
    User.objects.all().delete()
    Office.objects.all().delete()

if __name__ == "__main__":
    test_notes_search()