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
from django.db import connection

print('=== FIXING ORPHANED CONTACTS WITH SQL ===')

# Find orphaned person contacts
orphaned_contacts = Contact.objects.filter(type='person').exclude(id__in=Person.objects.values_list('contact_id', flat=True))

print(f'Found {orphaned_contacts.count()} orphaned person contacts')

created_count = 0
with connection.cursor() as cursor:
    for contact in orphaned_contacts:
        try:
            # Insert person record using raw SQL to handle auto-increment ID
            cursor.execute("""
                INSERT INTO people (contact_id) 
                VALUES (%s)
            """, [contact.id])
            
            print(f'Created Person for Contact {contact.id}: {contact.first_name} {contact.last_name}')
            created_count += 1
        except Exception as e:
            print(f'Error creating Person for Contact {contact.id}: {e}')

print(f'\n✅ Created {created_count} Person records')

# Verify the fix
remaining_orphaned = Contact.objects.filter(type='person').exclude(id__in=Person.objects.values_list('contact_id', flat=True))
print(f'Remaining orphaned contacts: {remaining_orphaned.count()}')