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

print('=== SIMPLE FIX FOR ORPHANED CONTACTS ===')

# Find orphaned person contacts and change their type to None
orphaned_contacts = Contact.objects.filter(type='person').exclude(id__in=Person.objects.values_list('contact_id', flat=True))

print(f'Found {orphaned_contacts.count()} orphaned person contacts')
print('Changing their type from "person" to None so they won\'t cause foreign key errors...')

updated_count = orphaned_contacts.update(type=None)
print(f'✅ Updated {updated_count} contacts')

# Verify the fix
remaining_orphaned = Contact.objects.filter(type='person').exclude(id__in=Person.objects.values_list('contact_id', flat=True))
print(f'Remaining orphaned person contacts: {remaining_orphaned.count()}')

print('\n✅ Gmail sync should work now!')