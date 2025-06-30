"""
Management command to debug why Django ORM isn't finding names that exist in the database.
"""

from django.core.management.base import BaseCommand
from django.db import models
from mobilize.contacts.models import Contact, Person


class Command(BaseCommand):
    help = 'Debug Django ORM queries for name data'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== Debugging Django ORM Name Queries ==='))
        
        # Test specific contact IDs that we know have names
        test_ids = [685, 699, 728]
        
        for contact_id in test_ids:
            self.stdout.write(f'\\n--- Testing Contact ID {contact_id} ---')
            
            try:
                # Try to get the contact directly
                contact = Contact.objects.get(id=contact_id)
                self.stdout.write(f'Contact found: {contact}')
                self.stdout.write(f'  Type: {contact.type}')
                self.stdout.write(f'  first_name: "{contact.first_name}"')
                self.stdout.write(f'  last_name: "{contact.last_name}"')
                self.stdout.write(f'  email: "{contact.email}"')
                
                # Check if there's a corresponding Person
                try:
                    person = Person.objects.get(contact=contact)
                    self.stdout.write(f'Person found: {person}')
                    self.stdout.write(f'  Person.name property: "{person.name}"')
                    self.stdout.write(f'  Person.__str__(): "{str(person)}"')
                    
                    # Test the name property logic step by step
                    first_name = (person.contact.first_name or "").strip()
                    last_name = (person.contact.last_name or "").strip()
                    self.stdout.write(f'  Name property breakdown:')
                    self.stdout.write(f'    - first_name stripped: "{first_name}"')
                    self.stdout.write(f'    - last_name stripped: "{last_name}"')
                    
                    if first_name and last_name:
                        computed_name = f"{first_name} {last_name}"
                        self.stdout.write(f'    - Result: "{computed_name}" (both names)')
                    elif first_name:
                        computed_name = first_name
                        self.stdout.write(f'    - Result: "{computed_name}" (first only)')
                    elif last_name:
                        computed_name = last_name
                        self.stdout.write(f'    - Result: "{computed_name}" (last only)')
                    else:
                        computed_name = "Unknown Person"
                        self.stdout.write(f'    - Result: "{computed_name}" (fallback)')
                        
                except Person.DoesNotExist:
                    self.stdout.write('  No corresponding Person record found')
                    
            except Contact.DoesNotExist:
                self.stdout.write(f'Contact {contact_id} not found')
        
        # Now test our problematic query from the investigation
        self.stdout.write('\\n=== Testing Our Empty Name Query ===')
        
        empty_names = Contact.objects.filter(
            models.Q(first_name__isnull=True) | models.Q(first_name='') | 
            models.Q(last_name__isnull=True) | models.Q(last_name='')
        ).filter(type='person')
        
        self.stdout.write(f'Query returned {empty_names.count()} contacts with empty names')
        
        for contact in empty_names:
            self.stdout.write(f'  Contact {contact.id}: first="{contact.first_name}", last="{contact.last_name}"')
        
        # Test a more precise query - contacts where BOTH names are empty
        self.stdout.write('\\n=== Testing Both Names Empty Query ===')
        
        both_empty = Contact.objects.filter(
            (models.Q(first_name__isnull=True) | models.Q(first_name='')) &
            (models.Q(last_name__isnull=True) | models.Q(last_name=''))
        ).filter(type='person')
        
        self.stdout.write(f'Query returned {both_empty.count()} contacts with both names empty')
        
        for contact in both_empty:
            self.stdout.write(f'  Contact {contact.id}: first="{contact.first_name}", last="{contact.last_name}"')
        
        # Test the API logic that was causing "No name listed"
        self.stdout.write('\\n=== Testing API Name Logic ===')
        
        for contact_id in test_ids:
            try:
                person = Person.objects.get(contact_id=contact_id)
                
                # Replicate the API logic
                first_name = person.contact.first_name or ""
                last_name = person.contact.last_name or ""
                
                # Clean up names
                first_name = first_name.strip()
                last_name = last_name.strip()
                
                # Build full name
                full_name = f"{first_name} {last_name}".strip()
                
                # Check for "No name listed" condition
                if not full_name:
                    api_result = "No name listed"
                else:
                    api_result = full_name
                
                self.stdout.write(f'Person {contact_id} API result: "{api_result}"')
                self.stdout.write(f'  - Raw first: "{person.contact.first_name}"')
                self.stdout.write(f'  - Raw last: "{person.contact.last_name}"')
                self.stdout.write(f'  - Processed: "{first_name}" + "{last_name}" = "{full_name}"')
                
            except Person.DoesNotExist:
                self.stdout.write(f'Person {contact_id} not found')
        
        self.stdout.write('\\n' + self.style.SUCCESS('Debug complete!'))