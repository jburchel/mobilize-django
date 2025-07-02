#!/usr/bin/env python
import os
import django
import sys

# Add the project directory to Python path
sys.path.append('/Users/jimburchel/Developer-Playground/mobilize-django')

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mobilize.settings')
django.setup()

from mobilize.contacts.models import Person, Contact

print('=== DEBUGGING CONTACT REFERENCES ===')

# Check total counts
total_contacts = Contact.objects.count()
total_people = Person.objects.count()
print(f'Total contacts: {total_contacts}')
print(f'Total people: {total_people}')

# Check for orphaned references
try:
    # Find contacts that claim to have person details but the person doesn't exist
    orphaned_contacts = Contact.objects.filter(type='person').exclude(id__in=Person.objects.values_list('contact_id', flat=True))
    print(f'Orphaned person contacts: {orphaned_contacts.count()}')
    
    for contact in orphaned_contacts[:5]:
        print(f'  Contact {contact.id}: {contact.first_name} {contact.last_name} <{contact.email}>')
        
except Exception as e:
    print(f'Error checking orphaned contacts: {e}')

# Check specific person 822 that's causing the error
try:
    person_822 = Person.objects.filter(id=822).first()
    if person_822:
        print(f'Person 822 exists: {person_822}')
    else:
        print('Person 822 does NOT exist')
        
    # Check if any contact references person 822
    contact_ref_822 = Contact.objects.filter(person_details_id=822).first()
    if contact_ref_822:
        print(f'Contact {contact_ref_822.id} references missing person 822')
    
except Exception as e:
    print(f'Error checking person 822: {e}')

print('\n=== CONTACTS WITH EMAIL ADDRESSES ===')
contacts_with_email = Contact.objects.filter(email__isnull=False).exclude(email='')
print(f'Contacts with email addresses: {contacts_with_email.count()}')

for contact in contacts_with_email[:3]:
    print(f'  {contact.id}: {contact.first_name} {contact.last_name} <{contact.email}> (type: {contact.type})')