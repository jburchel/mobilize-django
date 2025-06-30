"""
Management command to check contact ID mapping between people and contacts tables.
"""

import os
import psycopg2
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Check contact ID mapping between people and contacts tables'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== Checking Contact ID Mapping ==='))
        
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
            
            # Check a few specific people mentioned in the conversation
            test_people = ['Olivia Tanchak', 'Nate White']
            
            for name_to_find in test_people:
                first_name = name_to_find.split()[0]
                last_name = name_to_find.split()[1] if len(name_to_find.split()) > 1 else ''
                
                self.stdout.write(f'\n=== Searching for {name_to_find} ===')
                
                # Look in people table
                cursor.execute("""
                    SELECT id, first_name, last_name, contact_id
                    FROM people 
                    WHERE first_name ILIKE %s AND last_name ILIKE %s
                """, [first_name, last_name])
                
                people_results = cursor.fetchall()
                
                if people_results:
                    for p_id, p_first, p_last, contact_id in people_results:
                        self.stdout.write(f'  People table: ID {p_id}, contact_id {contact_id}')
                        
                        # Check if this contact_id exists in contacts table
                        cursor.execute("""
                            SELECT id, first_name, last_name, email, type
                            FROM contacts 
                            WHERE id = %s
                        """, [contact_id])
                        
                        contact_result = cursor.fetchone()
                        if contact_result:
                            c_id, c_first, c_last, email, c_type = contact_result
                            self.stdout.write(f'    → Contact {c_id}: "{c_first or ""}" "{c_last or ""}" ({c_type}) {email}')
                        else:
                            self.stdout.write(f'    → Contact {contact_id}: NOT FOUND in contacts table')
                            
                            # Look for this name in contacts table directly
                            cursor.execute("""
                                SELECT id, first_name, last_name, email, type
                                FROM contacts 
                                WHERE first_name ILIKE %s AND last_name ILIKE %s
                            """, [first_name, last_name])
                            
                            contacts_matches = cursor.fetchall()
                            if contacts_matches:
                                self.stdout.write(f'    → Found in contacts with different IDs:')
                                for c_id, c_first, c_last, email, c_type in contacts_matches:
                                    self.stdout.write(f'       Contact {c_id}: "{c_first or ""}" "{c_last or ""}" ({c_type}) {email}')
                else:
                    self.stdout.write(f'  Not found in people table')
                    
                    # Look directly in contacts table
                    cursor.execute("""
                        SELECT id, first_name, last_name, email, type
                        FROM contacts 
                        WHERE first_name ILIKE %s AND last_name ILIKE %s
                    """, [first_name, last_name])
                    
                    contacts_matches = cursor.fetchall()
                    if contacts_matches:
                        self.stdout.write(f'  Found only in contacts table:')
                        for c_id, c_first, c_last, email, c_type in contacts_matches:
                            self.stdout.write(f'    Contact {c_id}: "{c_first or ""}" "{c_last or ""}" ({c_type}) {email}')
            
            # Check overall statistics
            self.stdout.write(f'\n=== Database Statistics ===')
            
            # Count people with names
            cursor.execute("""
                SELECT COUNT(*) FROM people 
                WHERE (first_name IS NOT NULL AND first_name != '') 
                   OR (last_name IS NOT NULL AND last_name != '')
            """)
            people_with_names = cursor.fetchone()[0]
            
            # Count total people
            cursor.execute("SELECT COUNT(*) FROM people")
            total_people = cursor.fetchone()[0]
            
            # Count contacts of type person
            cursor.execute("SELECT COUNT(*) FROM contacts WHERE type = 'person'")
            person_contacts = cursor.fetchone()[0]
            
            # Count contacts with empty names
            cursor.execute("""
                SELECT COUNT(*) FROM contacts 
                WHERE type = 'person'
                AND (first_name IS NULL OR first_name = '')
                AND (last_name IS NULL OR last_name = '')
            """)
            empty_name_contacts = cursor.fetchone()[0]
            
            self.stdout.write(f'  People table: {total_people} total, {people_with_names} with names')
            self.stdout.write(f'  Contacts table: {person_contacts} persons, {empty_name_contacts} with empty names')
            
            # Check for broken links
            cursor.execute("""
                SELECT COUNT(*) FROM people p
                LEFT JOIN contacts c ON p.contact_id = c.id
                WHERE c.id IS NULL
            """)
            broken_links = cursor.fetchone()[0]
            
            self.stdout.write(f'  Broken links (people with no matching contact): {broken_links}')
            
            # Show some examples of broken links
            if broken_links > 0:
                self.stdout.write(f'\n=== Examples of Broken Links ===')
                cursor.execute("""
                    SELECT p.id, p.first_name, p.last_name, p.contact_id
                    FROM people p
                    LEFT JOIN contacts c ON p.contact_id = c.id
                    WHERE c.id IS NULL
                    AND ((p.first_name IS NOT NULL AND p.first_name != '') 
                         OR (p.last_name IS NOT NULL AND p.last_name != ''))
                    LIMIT 5
                """)
                
                broken_examples = cursor.fetchall()
                for p_id, p_first, p_last, contact_id in broken_examples:
                    self.stdout.write(f'  People {p_id}: "{p_first or ""}" "{p_last or ""}" → Contact {contact_id} (missing)')
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {e}'))
        
        self.stdout.write('\n' + self.style.SUCCESS('Contact mapping check complete!'))