"""
Management command to test what the production API would return for specific people.
"""

import os
import psycopg2
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Test what the production API would return for specific people'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== Testing Production API Results ==='))
        
        # Get production database URL
        production_db_url = os.environ.get('SUPABASE_DATABASE_URL')
        
        if not production_db_url:
            self.stdout.write(self.style.ERROR('SUPABASE_DATABASE_URL not found in environment'))
            return
        
        try:
            # Connect directly to production Supabase
            conn = psycopg2.connect(production_db_url)
            cursor = conn.cursor()
            
            self.stdout.write('✓ Connected to production Supabase')
            
            # Test the exact API logic for person list
            self.stdout.write(f'\n=== Simulating Person List API ===')
            
            # Get all person contacts and simulate the API response
            cursor.execute("""
                SELECT c.id, c.first_name, c.last_name, c.email, c.user_id
                FROM contacts c
                WHERE c.type = 'person'
                ORDER BY c.id
                LIMIT 20
            """)
            
            person_contacts = cursor.fetchall()
            
            self.stdout.write(f'Found {len(person_contacts)} person contacts:')
            
            for contact_id, first_name, last_name, email, user_id in person_contacts:
                # Simulate the exact API logic
                first_name_clean = (first_name or "").strip()
                last_name_clean = (last_name or "").strip()
                full_name = f"{first_name_clean} {last_name_clean}".strip()
                
                api_result = full_name if full_name else "No name listed"
                
                self.stdout.write(f'\n  Contact {contact_id}:')
                self.stdout.write(f'    API shows: "{api_result}"')
                self.stdout.write(f'    Raw names: "{first_name or ""}" "{last_name or ""}"')
                self.stdout.write(f'    Email: {email or "None"}')
                self.stdout.write(f'    User ID: {user_id or "None"}')
                
                if api_result == "No name listed":
                    self.stdout.write(f'    ⚠️  This would show as "No name listed"!')
            
            # Look specifically for the IDs mentioned in the conversation
            test_contact_ids = [699, 728, 685, 788, 810]
            
            self.stdout.write(f'\n=== Testing Specific Contact IDs ===')
            
            for contact_id in test_contact_ids:
                cursor.execute("""
                    SELECT id, first_name, last_name, email, type, user_id
                    FROM contacts
                    WHERE id = %s
                """, [contact_id])
                
                result = cursor.fetchone()
                
                if result:
                    c_id, first_name, last_name, email, contact_type, user_id = result
                    
                    # Simulate API logic
                    first_name_clean = (first_name or "").strip()
                    last_name_clean = (last_name or "").strip()
                    full_name = f"{first_name_clean} {last_name_clean}".strip()
                    api_result = full_name if full_name else "No name listed"
                    
                    self.stdout.write(f'\n  Contact {contact_id}: FOUND')
                    self.stdout.write(f'    Type: {contact_type}')
                    self.stdout.write(f'    API result: "{api_result}"')
                    self.stdout.write(f'    Raw names: "{first_name or ""}" "{last_name or ""}"')
                    self.stdout.write(f'    Email: {email or "None"}')
                    self.stdout.write(f'    User ID: {user_id}')
                    
                    if api_result == "No name listed":
                        self.stdout.write(f'    ⚠️  Shows as "No name listed"')
                    
                    # Check if there's a corresponding person record
                    if contact_type == 'person':
                        cursor.execute("""
                            SELECT id, first_name, last_name
                            FROM people
                            WHERE contact_id = %s
                        """, [contact_id])
                        
                        person_result = cursor.fetchone()
                        if person_result:
                            p_id, p_first, p_last = person_result
                            self.stdout.write(f'    People record: ID {p_id}, names "{p_first or ""}" "{p_last or ""}"')
                        else:
                            self.stdout.write(f'    No people record found')
                else:
                    self.stdout.write(f'\n  Contact {contact_id}: NOT FOUND')
            
            # Check for any contacts that would truly show "No name listed"
            self.stdout.write(f'\n=== Contacts That Would Show "No name listed" ===')
            
            cursor.execute("""
                SELECT id, first_name, last_name, email, user_id
                FROM contacts
                WHERE type = 'person'
                AND (first_name IS NULL OR first_name = '')
                AND (last_name IS NULL OR last_name = '')
            """)
            
            no_name_contacts = cursor.fetchall()
            
            if no_name_contacts:
                self.stdout.write(f'Found {len(no_name_contacts)} contacts with no names:')
                for contact_id, first_name, last_name, email, user_id in no_name_contacts:
                    self.stdout.write(f'  Contact {contact_id}: email={email}, user_id={user_id}')
            else:
                self.stdout.write('✓ No contacts found that would show "No name listed"')
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {e}'))
        
        self.stdout.write('\n' + self.style.SUCCESS('Production API test complete!'))