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

print('=== FIXING ORPHANED CONTACTS ===')

# Find orphaned person contacts
orphaned_contacts = Contact.objects.filter(type='person').exclude(id__in=Person.objects.values_list('contact_id', flat=True))

print(f'Found {orphaned_contacts.count()} orphaned person contacts')

created_count = 0
for contact in orphaned_contacts:
    try:
        # Create the missing Person record
        person = Person.objects.create(
            contact=contact,
            # Add any default fields if needed
        )
        print(f'Created Person for Contact {contact.id}: {contact.first_name} {contact.last_name}')
        created_count += 1
    except Exception as e:
        print(f'Error creating Person for Contact {contact.id}: {e}')

print(f'\n✅ Created {created_count} Person records')
print('Orphaned contacts have been fixed!')

# Verify the fix
remaining_orphaned = Contact.objects.filter(type='person').exclude(id__in=Person.objects.values_list('contact_id', flat=True))
print(f'Remaining orphaned contacts: {remaining_orphaned.count()}')