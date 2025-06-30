"""
Management command to investigate specific people showing as "No name listed" in the app.
"""

from django.core.management.base import BaseCommand
from django.db import connection
from mobilize.contacts.models import Contact, Person
from mobilize.core.permissions import DataAccessManager
from mobilize.authentication.models import User


class Command(BaseCommand):
    help = 'Investigate specific people showing name issues'

    def add_arguments(self, parser):
        parser.add_argument(
            '--person-ids',
            nargs='+',
            type=int,
            help='Specific person IDs to investigate (e.g., 699 728 685)',
            default=[699, 728, 685]
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== Investigating Specific People with Name Issues ==='))
        
        person_ids = options['person_ids']
        self.stdout.write(f'Investigating person IDs: {person_ids}')
        
        cursor = connection.cursor()
        
        # Get a super admin user to test permissions
        super_admin = User.objects.filter(role='super_admin').first()
        if super_admin:
            self.stdout.write(f'Testing with super admin: {super_admin.username}')
            access_manager = DataAccessManager(super_admin, 'default')
            people_queryset = access_manager.get_people_queryset()
        else:
            self.stdout.write('No super admin found, using all people')
            people_queryset = Person.objects.all()
        
        for person_id in person_ids:
            self.stdout.write(f'\\n=== INVESTIGATING PERSON {person_id} ===')
            
            # Check if person exists in Django
            try:
                person = Person.objects.get(contact_id=person_id)
                contact = person.contact
                
                self.stdout.write(f'✓ Person {person_id} exists in Django')
                self.stdout.write(f'  Contact ID: {contact.id}')
                self.stdout.write(f'  Contact type: {contact.type}')
                self.stdout.write(f'  Contact first_name: "{contact.first_name or "EMPTY"}"')
                self.stdout.write(f'  Contact last_name: "{contact.last_name or "EMPTY"}"')
                self.stdout.write(f'  Contact email: "{contact.email or "EMPTY"}"')
                self.stdout.write(f'  Person preferred_name: "{person.preferred_name or "EMPTY"}"')
                self.stdout.write(f'  Person title: "{person.title or "EMPTY"}"')
                
                # Test the name property
                person_name = person.name
                person_str = str(person)
                self.stdout.write(f'  Person.name property: "{person_name}"')
                self.stdout.write(f'  Person.__str__(): "{person_str}"')
                
                # Test what the API would return
                first_name = (contact.first_name or "").strip()
                last_name = (contact.last_name or "").strip()
                full_name = f"{first_name} {last_name}".strip()
                api_result = full_name if full_name else "No name listed"
                self.stdout.write(f'  API would show: "{api_result}"')
                
                # Check permissions
                is_accessible = people_queryset.filter(contact_id=person_id).exists()
                self.stdout.write(f'  Accessible to super admin: {"Yes" if is_accessible else "No"}')
                
                if not is_accessible:
                    self.stdout.write(f'  Contact user_id: {contact.user_id}')
                    self.stdout.write(f'  Contact office_id: {contact.office_id}')
                
                # Check in Supabase people table directly for any name data
                self.stdout.write('\\n  Checking Supabase people table...')
                cursor.execute("""
                    SELECT contact_id, preferred_name, title, spouse_first_name, spouse_last_name
                    FROM people 
                    WHERE contact_id = %s
                """, [person_id])
                
                supabase_data = cursor.fetchone()
                if supabase_data:
                    sb_contact_id, sb_preferred, sb_title, sb_spouse_first, sb_spouse_last = supabase_data
                    self.stdout.write(f'  Supabase preferred_name: "{sb_preferred or "EMPTY"}"')
                    self.stdout.write(f'  Supabase title: "{sb_title or "EMPTY"}"')
                    self.stdout.write(f'  Supabase spouse names: "{sb_spouse_first or ""}" "{sb_spouse_last or ""}"')
                else:
                    self.stdout.write('  No data found in Supabase people table')
                
                # Check in Supabase contacts table
                self.stdout.write('\\n  Checking Supabase contacts table...')
                cursor.execute("""
                    SELECT id, type, first_name, last_name, email, user_id, office_id
                    FROM contacts 
                    WHERE id = %s
                """, [person_id])
                
                supabase_contact = cursor.fetchone()
                if supabase_contact:
                    sb_id, sb_type, sb_first, sb_last, sb_email, sb_user, sb_office = supabase_contact
                    self.stdout.write(f'  Supabase contact first_name: "{sb_first or "EMPTY"}"')
                    self.stdout.write(f'  Supabase contact last_name: "{sb_last or "EMPTY"}"')
                    self.stdout.write(f'  Supabase contact email: "{sb_email or "EMPTY"}"')
                    self.stdout.write(f'  Supabase contact user_id: {sb_user}')
                    self.stdout.write(f'  Supabase contact office_id: {sb_office}')
                    
                    # Compare Django vs Supabase
                    if sb_first != contact.first_name or sb_last != contact.last_name:
                        self.stdout.write('  ⚠️  MISMATCH between Django and Supabase contact data!')
                else:
                    self.stdout.write('  No data found in Supabase contacts table')
                
            except Person.DoesNotExist:
                self.stdout.write(f'✗ Person {person_id} does not exist in Django')
                
                # Check if contact exists without person
                try:
                    contact = Contact.objects.get(id=person_id)
                    self.stdout.write(f'  But Contact {person_id} exists: type={contact.type}')
                    if contact.type != 'person':
                        self.stdout.write(f'  This is a {contact.type}, not a person!')
                except Contact.DoesNotExist:
                    self.stdout.write(f'  Contact {person_id} also does not exist in Django')
                    
                    # Check Supabase directly
                    cursor.execute("SELECT id, type FROM contacts WHERE id = %s", [person_id])
                    supabase_contact = cursor.fetchone()
                    if supabase_contact:
                        sb_id, sb_type = supabase_contact
                        self.stdout.write(f'  But exists in Supabase: id={sb_id}, type={sb_type}')
        
        # Also check for ALL people currently showing name issues
        self.stdout.write(f'\\n=== CHECKING ALL PEOPLE WITH NAME ISSUES ===')
        
        people_with_issues = []
        
        # Get all people accessible to super admin
        all_people = people_queryset[:50]  # Check first 50
        
        for person in all_people:
            # Check if this person would show name issues
            first_name = (person.contact.first_name or "").strip()
            last_name = (person.contact.last_name or "").strip()
            full_name = f"{first_name} {last_name}".strip()
            
            if not full_name:  # Would show "No name listed"
                people_with_issues.append(person)
        
        self.stdout.write(f'Found {len(people_with_issues)} people with name issues in first 50:')
        for person in people_with_issues[:10]:  # Show first 10
            self.stdout.write(f'  Person {person.contact.id}: email={person.contact.email}')
        
        if len(people_with_issues) > 10:
            self.stdout.write(f'  ... and {len(people_with_issues) - 10} more')
        
        self.stdout.write('\\n' + self.style.SUCCESS('Investigation complete!'))