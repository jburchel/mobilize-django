"""
Management command to find people showing as "No name listed" and check if they have names 
stored in the people table in Supabase that aren't synced to the contacts table.
"""

from django.core.management.base import BaseCommand
from django.db import connection, transaction
from django.db import models
from mobilize.contacts.models import Contact, Person


class Command(BaseCommand):
    help = 'Find people with "No name listed" and check for names in people table'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be changed without making actual changes',
        )
        parser.add_argument(
            '--fix',
            action='store_true',
            help='Actually fix the name mismatches',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== Finding and Fixing Supabase Name Mismatches ==='))
        
        cursor = connection.cursor()
        
        # First, let's see if the people table actually has first_name and last_name columns
        self.stdout.write('Checking if people table has name columns...')
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'people'
            AND column_name IN ('first_name', 'last_name')
            ORDER BY column_name;
        """)
        
        people_name_columns = [row[0] for row in cursor.fetchall()]
        
        if not people_name_columns:
            self.stdout.write('People table does not have first_name/last_name columns.')
            self.stdout.write('Let me check all columns with "name" in people table:')
            
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'people'
                AND column_name ILIKE '%name%'
                ORDER BY column_name;
            """)
            
            name_like_columns = [row[0] for row in cursor.fetchall()]
            self.stdout.write(f'Name-like columns in people table: {name_like_columns}')
            
            # Check for a different approach - maybe there are names in other fields
            self.stdout.write('\\nChecking for people with preferred_name that might solve the issue...')
            
            cursor.execute("""
                SELECT p.contact_id, p.preferred_name, c.first_name, c.last_name, c.email
                FROM people p
                JOIN contacts c ON p.contact_id = c.id
                WHERE c.type = 'person'
                AND (c.first_name IS NULL OR c.first_name = '')
                AND (c.last_name IS NULL OR c.last_name = '')
                AND p.preferred_name IS NOT NULL 
                AND p.preferred_name != ''
                ORDER BY p.contact_id;
            """)
            
            preferred_name_records = cursor.fetchall()
            if preferred_name_records:
                self.stdout.write(f'Found {len(preferred_name_records)} people with preferred_name but no contact names:')
                for record in preferred_name_records:
                    contact_id, preferred_name, c_first, c_last, email = record
                    self.stdout.write(f'  Contact {contact_id}: preferred_name="{preferred_name}", email="{email}"')
                    
                    if options['fix'] and not options['dry_run']:
                        # Use preferred_name as first_name
                        cursor.execute("""
                            UPDATE contacts 
                            SET first_name = %s
                            WHERE id = %s
                        """, [preferred_name, contact_id])
                        self.stdout.write(f'    → Fixed: Set first_name to "{preferred_name}"')
            else:
                self.stdout.write('No people found with preferred_name.')
        
        else:
            self.stdout.write(f'People table has these name columns: {people_name_columns}')
            
            # Now check for mismatches between people and contacts tables
            self.stdout.write('\\nLooking for name mismatches between people and contacts tables...')
            
            cursor.execute("""
                SELECT 
                    p.contact_id,
                    p.first_name as people_first_name,
                    p.last_name as people_last_name,
                    c.first_name as contact_first_name,
                    c.last_name as contact_last_name,
                    c.email
                FROM people p
                JOIN contacts c ON p.contact_id = c.id
                WHERE c.type = 'person'
                AND (
                    (p.first_name IS NOT NULL AND p.first_name != '' AND (c.first_name IS NULL OR c.first_name = ''))
                    OR 
                    (p.last_name IS NOT NULL AND p.last_name != '' AND (c.last_name IS NULL OR c.last_name = ''))
                    OR
                    (p.first_name != c.first_name)
                    OR
                    (p.last_name != c.last_name)
                )
                ORDER BY p.contact_id;
            """)
            
            mismatch_records = cursor.fetchall()
            
            if mismatch_records:
                self.stdout.write(f'Found {len(mismatch_records)} name mismatches:')
                
                for record in mismatch_records:
                    contact_id, p_first, p_last, c_first, c_last, email = record
                    
                    self.stdout.write(f'\\nContact {contact_id}:')
                    self.stdout.write(f'  People table: "{p_first or ""}" "{p_last or ""}"')
                    self.stdout.write(f'  Contact table: "{c_first or ""}" "{c_last or ""}"')
                    self.stdout.write(f'  Email: {email}')
                    
                    if options['fix']:
                        if options['dry_run']:
                            self.stdout.write(f'  → WOULD UPDATE contact table to: "{p_first or ""}" "{p_last or ""}"')
                        else:
                            cursor.execute("""
                                UPDATE contacts 
                                SET first_name = %s, last_name = %s
                                WHERE id = %s
                            """, [p_first, p_last, contact_id])
                            self.stdout.write(f'  → UPDATED contact table to: "{p_first or ""}" "{p_last or ""}"')
            else:
                self.stdout.write('No name mismatches found between people and contacts tables.')
        
        # Now let's specifically look for people showing as "Person ###" in the app
        self.stdout.write('\\n=== Checking Django models for people showing as "Person ###" ===')
        
        # Find people where the __str__ method would return "Person {id}"
        people_with_empty_names = Person.objects.filter(
            models.Q(contact__first_name__isnull=True) | models.Q(contact__first_name=''),
            models.Q(contact__last_name__isnull=True) | models.Q(contact__last_name='')
        )
        
        self.stdout.write(f'Found {people_with_empty_names.count()} people with empty names in Django:')
        
        for person in people_with_empty_names:
            self.stdout.write(f'  Person {person.contact.id}: "{str(person)}" (email: {person.contact.email})')
            
            # Check if this person has data in the database that we're missing
            cursor.execute("""
                SELECT preferred_name, spouse_first_name, spouse_last_name
                FROM people 
                WHERE contact_id = %s
            """, [person.contact.id])
            
            person_data = cursor.fetchone()
            if person_data:
                preferred_name, spouse_first, spouse_last = person_data
                if preferred_name:
                    self.stdout.write(f'    → Has preferred_name: "{preferred_name}"')
                    
                    if options['fix'] and not options['dry_run']:
                        person.contact.first_name = preferred_name
                        person.contact.save(update_fields=['first_name'])
                        self.stdout.write(f'    → FIXED: Set first_name to "{preferred_name}"')
                    elif options['fix']:
                        self.stdout.write(f'    → WOULD FIX: Set first_name to "{preferred_name}"')
        
        # Final summary
        self.stdout.write('\\n=== SUMMARY ===')
        if options['dry_run']:
            self.stdout.write('DRY RUN completed. Use --fix to apply changes.')
        elif options['fix']:
            self.stdout.write('Name fixes applied!')
        else:
            self.stdout.write('Investigation completed. Use --fix --dry-run to see proposed changes.')
        
        self.stdout.write(self.style.SUCCESS('\\nOperation complete!'))