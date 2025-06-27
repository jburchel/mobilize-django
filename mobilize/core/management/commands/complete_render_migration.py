"""
Complete migration of all contacts and data from Render database to Supabase

This management command performs a comprehensive migration:
1. Transfers missing contacts (people and churches) from Render to Supabase
2. Updates existing contacts with missing field data
3. Migrates newly discovered fields: people.info_given, people.desired_service
4. Includes robust duplicate detection to prevent conflicts
5. Preserves assignment history using Enhanced Notes approach
"""

import os
import psycopg2
from psycopg2.extras import DictCursor
from django.core.management.base import BaseCommand
from django.db import transaction
from django.conf import settings
from mobilize.contacts.models import Contact, Person
from mobilize.churches.models import Church
from mobilize.authentication.models import User
from mobilize.admin_panel.models import Office
from mobilize.pipeline.models import PipelineStage, PipelineContact, Pipeline


class Command(BaseCommand):
    help = 'Complete migration of all contacts and data from Render database to Supabase'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be migrated without making changes',
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='Limit number of records to process (for testing)',
        )
        parser.add_argument(
            '--only-missing',
            action='store_true',
            help='Only migrate missing contacts, skip updating existing ones',
        )

    def handle(self, *args, **options):
        self.dry_run = options['dry_run']
        self.limit = options['limit']
        self.only_missing = options['only_missing']
        
        if self.dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))
        
        # Render Database Configuration
        render_config = {
            'host': 'dpg-cr6f1ei3esus73cnh1d0-a.oregon-postgres.render.com',
            'port': '5432',
            'database': 'mobilize',
            'user': 'jimburchel',
            'password': '1JmxPgDNQsk9UxDI7PdKXgF0PC4v1fiY'
        }
        
        try:
            # Connect to Render database
            self.stdout.write('Connecting to Render database...')
            render_conn = psycopg2.connect(**render_config)
            
            # Create assignment mapping and get default user
            assignment_mapping, default_church_user, default_office = self.create_assignment_mapping()
            
            # Migrate missing people first
            people_stats = self.migrate_missing_people(render_conn, assignment_mapping, default_office)
            
            # Migrate missing churches
            church_stats = self.migrate_missing_churches(render_conn, assignment_mapping, default_church_user, default_office)
            
            # Update existing contacts with missing data (unless --only-missing)
            if not self.only_missing:
                existing_people_stats = self.update_existing_people(render_conn, assignment_mapping)
                existing_church_stats = self.update_existing_churches(render_conn, assignment_mapping, default_church_user)
            else:
                existing_people_stats = {'processed': 0, 'updated': 0}
                existing_church_stats = {'processed': 0, 'updated': 0, 'assigned_to_mrule': 0}
            
            # Summary
            self.stdout.write(self.style.SUCCESS('\\n' + '='*80))
            self.stdout.write(self.style.SUCCESS('COMPLETE MIGRATION SUMMARY:'))
            self.stdout.write('\\n--- NEW CONTACTS CREATED ---')
            self.stdout.write(f"New people created: {people_stats['created']}")
            self.stdout.write(f"New churches created: {church_stats['created']}")
            self.stdout.write(f"Churches assigned to m.rule: {church_stats['assigned_to_mrule']}")
            
            if not self.only_missing:
                self.stdout.write('\\n--- EXISTING CONTACTS UPDATED ---')
                self.stdout.write(f"Existing people updated: {existing_people_stats['updated']}")
                self.stdout.write(f"Existing churches updated: {existing_church_stats['updated']}")
            
            self.stdout.write(f"\\nTotal people in Supabase: {people_stats['total_in_supabase']}")
            self.stdout.write(f"Total churches in Supabase: {church_stats['total_in_supabase']}")
            
            if self.dry_run:
                self.stdout.write(self.style.WARNING('\\nDRY RUN - No actual changes made'))
            else:
                self.stdout.write(self.style.SUCCESS('\\nComplete migration finished successfully!'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Migration failed: {e}'))
            raise
        finally:
            if 'render_conn' in locals():
                render_conn.close()

    def create_assignment_mapping(self):
        """Create mapping from Render assignment strings to Supabase users"""
        self.stdout.write('Creating assignment mapping...')
        
        # Known mappings based on analysis
        mapping = {}
        default_church_user = None
        default_office = None
        
        try:
            # Map Jim Burchel variants
            jim_user = User.objects.get(email='j.burchel@crossoverglobal.net')
            mapping.update({
                'JIM BURCHEL': jim_user,
                'Jim Burchel': jim_user,
            })
            
            # Try to find Matthew Rule user (multiple possible emails)
            matthew_user = None
            possible_emails = ['m.rule@crossoverglobal.net', 'matthew.rule@crossoverglobal.net', 'mrule@crossoverglobal.net']
            
            for email in possible_emails:
                try:
                    matthew_user = User.objects.get(email=email)
                    self.stdout.write(f'   Found Matthew Rule at: {email}')
                    break
                except User.DoesNotExist:
                    continue
            
            if matthew_user:
                mapping.update({
                    'MATTHEW RULE': matthew_user,
                    'Matthew Rule': matthew_user,
                })
                default_church_user = matthew_user
                self.stdout.write(f'   Using Matthew Rule as default church user: {matthew_user.email}')
            else:
                # If Matthew Rule doesn't exist, use Jim Burchel as default
                self.stdout.write(self.style.WARNING('   Matthew Rule user not found, using Jim Burchel as default for churches'))
                default_church_user = jim_user
            
            # Get default office
            default_office = Office.objects.first()
            if default_office:
                self.stdout.write(f'   Using default office: {default_office.name}')
            
            self.stdout.write(f'   Mapped {len(mapping)} assignment patterns to users')
            
        except User.DoesNotExist as e:
            self.stdout.write(self.style.ERROR(f'   Could not find required user j.burchel@crossoverglobal.net: {e}'))
            raise
        
        return mapping, default_church_user, default_office

    def check_duplicate_person(self, render_person):
        """Check if person already exists in Supabase"""
        # Try email match first (most reliable)
        if render_person['email']:
            existing = Contact.objects.filter(
                type='person',
                email=render_person['email']
            ).first()
            if existing:
                return existing, 'email'
        
        # Try name match 
        if render_person['first_name'] and render_person['last_name']:
            existing = Contact.objects.filter(
                type='person',
                first_name__iexact=render_person['first_name'],
                last_name__iexact=render_person['last_name']
            ).first()
            if existing:
                return existing, 'name'
        
        return None, None

    def check_duplicate_church(self, render_church):
        """Check if church already exists in Supabase"""
        # Try church name match
        if render_church['church_name']:
            # Try exact match first
            existing = Contact.objects.filter(
                type='church',
                church_name__iexact=render_church['church_name']
            ).first()
            if existing:
                return existing, 'exact_name'
            
            # Try contains match
            existing = Contact.objects.filter(
                type='church',
                church_name__icontains=render_church['church_name']
            ).first()
            if existing:
                return existing, 'similar_name'
        
        # Try email match if available
        if render_church['email']:
            existing = Contact.objects.filter(
                type='church',
                email=render_church['email']
            ).first()
            if existing:
                return existing, 'email'
        
        return None, None

    def create_assignment_note(self, original_assignee, contact_type="contact"):
        """Create a standardized note for original assignment"""
        return f"Originally assigned to: {original_assignee}"

    def append_to_notes(self, existing_notes, new_note):
        """Append new note to existing notes in a clean format"""
        if not existing_notes or existing_notes.strip() == "":
            return new_note
        
        # Check if the assignment note already exists
        if "Originally assigned to:" in existing_notes:
            return existing_notes
        
        # Add separator and new note
        return f"{existing_notes.strip()}\\n\\n{new_note}"

    def migrate_missing_people(self, render_conn, assignment_mapping, default_office):
        """Migrate people that don't exist in Supabase"""
        self.stdout.write('\\nMigrating missing people from Render...')
        
        cursor = render_conn.cursor(cursor_factory=DictCursor)
        
        # Get all people from Render
        limit_clause = f"LIMIT {self.limit}" if self.limit else ""
        cursor.execute(f"""
            SELECT 
                cc.id as render_id,
                cc.first_name,
                cc.last_name,
                cc.email,
                cc.phone,
                cc.street_address,
                cc.city,
                cc.state,
                cc.zip_code,
                cc.initial_notes,
                cp.home_country,
                cp.marital_status,
                cp.spouse_first_name,
                cp.spouse_last_name,
                cp.info_given,
                cp.desired_service,
                cp.people_pipeline,
                cp.priority,
                cp.assigned_to
            FROM contacts_contact cc
            JOIN contacts_people cp ON cc.id = cp.contact_ptr_id
            WHERE cc.first_name IS NOT NULL AND cc.first_name != ''
            ORDER BY cc.last_name, cc.first_name
            {limit_clause}
        """)
        
        render_people = cursor.fetchall()
        created = 0
        skipped = 0
        total_in_supabase = Contact.objects.filter(type='person').count()
        
        for render_person in render_people:
            try:
                # Check for duplicates
                existing_contact, match_type = self.check_duplicate_person(render_person)
                
                if existing_contact:
                    skipped += 1
                    if self.dry_run:
                        self.stdout.write(f"   Would skip {render_person['first_name']} {render_person['last_name']} (exists: {match_type})")
                    continue
                
                # Create new person
                if not self.dry_run:
                    with transaction.atomic():
                        # Create Contact
                        contact = Contact.objects.create(
                            type='person',
                            first_name=render_person['first_name'],
                            last_name=render_person['last_name'],
                            email=render_person['email'],
                            phone=render_person['phone'],
                            street_address=render_person['street_address'],
                            city=render_person['city'],
                            state=render_person['state'],
                            zip_code=render_person['zip_code'],
                            initial_notes=render_person['initial_notes'],
                            priority=render_person['priority'] or 'medium',
                            office=default_office,
                        )
                        
                        # Handle assignment
                        if render_person['assigned_to'] and render_person['assigned_to'].strip() and render_person['assigned_to'] != 'Unassigned':
                            assigned_to = render_person['assigned_to'].strip()
                            if assigned_to in assignment_mapping:
                                contact.user = assignment_mapping[assigned_to]
                            else:
                                # Add assignment note
                                assignment_note = self.create_assignment_note(assigned_to, "person")
                                contact.notes = self.append_to_notes(contact.notes, assignment_note)
                        
                        contact.save()
                        
                        # Create Person
                        person = Person.objects.create(
                            contact=contact,
                            home_country=render_person['home_country'],
                            marital_status=render_person['marital_status'],
                            spouse_first_name=render_person['spouse_first_name'],
                            spouse_last_name=render_person['spouse_last_name'],
                            info_given=render_person['info_given'],
                            desired_service=render_person['desired_service'],
                        )
                        
                        # Handle pipeline
                        if render_person['people_pipeline'] and render_person['people_pipeline'] not in ['None', '', 'null']:
                            self.migrate_pipeline_stage(contact, render_person['people_pipeline'], 'person')
                
                created += 1
                if created % 10 == 0 or self.dry_run:
                    action = "Would create" if self.dry_run else "Created"
                    self.stdout.write(f"   {action} {render_person['first_name']} {render_person['last_name']}")
                
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"   Error processing {render_person['first_name']} {render_person['last_name']}: {e}"))
        
        cursor.close()
        
        if not self.dry_run:
            total_in_supabase = Contact.objects.filter(type='person').count()
        
        return {
            'created': created, 
            'skipped': skipped, 
            'total_in_supabase': total_in_supabase
        }

    def migrate_missing_churches(self, render_conn, assignment_mapping, default_church_user, default_office):
        """Migrate churches that don't exist in Supabase"""
        self.stdout.write('\\nMigrating missing churches from Render...')
        
        cursor = render_conn.cursor(cursor_factory=DictCursor)
        
        # Get all churches from Render
        limit_clause = f"LIMIT {self.limit}" if self.limit else ""
        cursor.execute(f"""
            SELECT 
                cc.id as render_id,
                cc.church_name,
                cc.email,
                cc.phone,
                cc.street_address,
                cc.city,
                cc.state,
                cc.zip_code,
                cc.initial_notes,
                ch.senior_pastor_first_name,
                ch.senior_pastor_last_name,
                ch.senior_pastor_phone,
                ch.senior_pastor_email,
                ch.denomination,
                ch.website,
                ch.congregation_size,
                ch.year_founded,
                ch.info_given,
                ch.church_pipeline,
                ch.priority,
                ch.assigned_to
            FROM contacts_contact cc
            JOIN contacts_church ch ON cc.id = ch.contact_ptr_id
            WHERE cc.church_name IS NOT NULL AND cc.church_name != ''
            ORDER BY cc.church_name
            {limit_clause}
        """)
        
        render_churches = cursor.fetchall()
        created = 0
        skipped = 0
        assigned_to_mrule = 0
        total_in_supabase = Contact.objects.filter(type='church').count()
        
        for render_church in render_churches:
            try:
                # Check for duplicates
                existing_contact, match_type = self.check_duplicate_church(render_church)
                
                if existing_contact:
                    skipped += 1
                    if self.dry_run:
                        self.stdout.write(f"   Would skip {render_church['church_name']} (exists: {match_type})")
                    continue
                
                # Create new church
                if not self.dry_run:
                    with transaction.atomic():
                        # Create Contact
                        contact = Contact.objects.create(
                            type='church',
                            church_name=render_church['church_name'],
                            email=render_church['email'],
                            phone=render_church['phone'],
                            street_address=render_church['street_address'],
                            city=render_church['city'],
                            state=render_church['state'],
                            zip_code=render_church['zip_code'],
                            initial_notes=render_church['initial_notes'],
                            priority=render_church['priority'] or 'medium',
                            office=default_office,
                        )
                        
                        # Handle assignment with Enhanced Notes approach
                        if render_church['assigned_to'] and render_church['assigned_to'].strip() and render_church['assigned_to'] != 'Unassigned':
                            assigned_to = render_church['assigned_to'].strip()
                            if assigned_to in assignment_mapping:
                                contact.user = assignment_mapping[assigned_to]
                            else:
                                # Assign to m.rule by default and add note
                                contact.user = default_church_user
                                assigned_to_mrule += 1
                                assignment_note = self.create_assignment_note(assigned_to, "church")
                                contact.notes = self.append_to_notes(contact.notes, assignment_note)
                        
                        contact.save()
                        
                        # Create Church
                        church = Church.objects.create(
                            contact=contact,
                            name=render_church['church_name'],
                            denomination=render_church['denomination'],
                            website=render_church['website'],
                            congregation_size=render_church['congregation_size'],
                            year_founded=render_church['year_founded'],
                            info_given=render_church['info_given'],
                            senior_pastor_first_name=render_church['senior_pastor_first_name'],
                            senior_pastor_last_name=render_church['senior_pastor_last_name'],
                            pastor_phone=render_church['senior_pastor_phone'],
                            pastor_email=render_church['senior_pastor_email'],
                        )
                        
                        # Handle pipeline
                        if render_church['church_pipeline'] and render_church['church_pipeline'] not in ['None', '', 'null']:
                            self.migrate_pipeline_stage(contact, render_church['church_pipeline'], 'church')
                
                created += 1
                if created % 10 == 0 or self.dry_run:
                    action = "Would create" if self.dry_run else "Created"
                    self.stdout.write(f"   {action} {render_church['church_name']}")
                
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"   Error processing {render_church['church_name']}: {e}"))
        
        cursor.close()
        
        if not self.dry_run:
            total_in_supabase = Contact.objects.filter(type='church').count()
        
        return {
            'created': created, 
            'skipped': skipped, 
            'assigned_to_mrule': assigned_to_mrule,
            'total_in_supabase': total_in_supabase
        }

    def update_existing_people(self, render_conn, assignment_mapping):
        """Update existing people with missing field data"""
        self.stdout.write('\\nUpdating existing people with missing data...')
        
        cursor = render_conn.cursor(cursor_factory=DictCursor)
        
        # Get people data from Render for updating existing records
        limit_clause = f"LIMIT {self.limit}" if self.limit else ""
        cursor.execute(f"""
            SELECT 
                cc.id as render_id,
                cc.first_name,
                cc.last_name,
                cc.email,
                cc.initial_notes,
                cp.home_country,
                cp.marital_status,
                cp.spouse_first_name,
                cp.spouse_last_name,
                cp.info_given,
                cp.desired_service,
                cp.people_pipeline,
                cp.priority,
                cp.assigned_to
            FROM contacts_contact cc
            JOIN contacts_people cp ON cc.id = cp.contact_ptr_id
            WHERE cc.first_name IS NOT NULL AND cc.first_name != ''
            ORDER BY cc.last_name, cc.first_name
            {limit_clause}
        """)
        
        render_people = cursor.fetchall()
        processed = 0
        updated = 0
        
        for render_person in render_people:
            processed += 1
            
            # Find matching person in Supabase
            try:
                existing_contact, match_type = self.check_duplicate_person(render_person)
                
                if existing_contact:
                    updates_made = False
                    field_updates = {}
                    
                    # Update missing contact fields
                    if render_person['initial_notes'] and not existing_contact.initial_notes:
                        field_updates['initial_notes'] = render_person['initial_notes']
                        updates_made = True
                    
                    # Handle assignment with Enhanced Notes approach
                    if render_person['assigned_to'] and render_person['assigned_to'].strip() and render_person['assigned_to'] != 'Unassigned':
                        assigned_to = render_person['assigned_to'].strip()
                        if assigned_to in assignment_mapping and not existing_contact.user:
                            field_updates['user'] = assignment_mapping[assigned_to]
                            updates_made = True
                        elif assigned_to not in assignment_mapping:
                            # Add assignment note
                            assignment_note = self.create_assignment_note(assigned_to, "person")
                            field_updates['notes'] = self.append_to_notes(existing_contact.notes, assignment_note)
                            updates_made = True
                    
                    # Person-specific fields
                    try:
                        person_obj = existing_contact.person_details
                        person_updates = {}
                        
                        if render_person['home_country'] and not person_obj.home_country:
                            person_updates['home_country'] = render_person['home_country']
                        
                        if render_person['marital_status'] and not person_obj.marital_status:
                            person_updates['marital_status'] = render_person['marital_status']
                        
                        if render_person['spouse_first_name'] and not person_obj.spouse_first_name:
                            person_updates['spouse_first_name'] = render_person['spouse_first_name']
                        
                        if render_person['spouse_last_name'] and not person_obj.spouse_last_name:
                            person_updates['spouse_last_name'] = render_person['spouse_last_name']
                        
                        # NEW FIELDS
                        if render_person['info_given'] and not person_obj.info_given:
                            person_updates['info_given'] = render_person['info_given']
                        
                        if render_person['desired_service'] and not person_obj.desired_service:
                            person_updates['desired_service'] = render_person['desired_service']
                        
                        if person_updates and not self.dry_run:
                            for field, value in person_updates.items():
                                setattr(person_obj, field, value)
                            person_obj.save(update_fields=list(person_updates.keys()))
                            updates_made = True
                    
                    except Exception as e:
                        # Person details might not exist, that's okay
                        pass
                    
                    # Handle pipeline migration
                    if render_person['people_pipeline'] and render_person['people_pipeline'] not in ['None', '', 'null']:
                        self.migrate_pipeline_stage(existing_contact, render_person['people_pipeline'], 'person')
                        updates_made = True
                    
                    # Apply contact updates
                    if field_updates and not self.dry_run:
                        for field, value in field_updates.items():
                            setattr(existing_contact, field, value)
                        existing_contact.save(update_fields=list(field_updates.keys()))
                    
                    if updates_made:
                        updated += 1
                        if processed % 20 == 0 or self.dry_run:
                            action = "Would update" if self.dry_run else "Updated"
                            self.stdout.write(f"   {action} {render_person['first_name']} {render_person['last_name']}")
                
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"   Error processing {render_person['first_name']} {render_person['last_name']}: {e}"))
        
        cursor.close()
        return {'processed': processed, 'updated': updated}

    def update_existing_churches(self, render_conn, assignment_mapping, default_church_user):
        """Update existing churches with missing field data"""
        self.stdout.write('\\nUpdating existing churches with missing data...')
        
        cursor = render_conn.cursor(cursor_factory=DictCursor)
        
        # Get church data from Render for updating existing records
        limit_clause = f"LIMIT {self.limit}" if self.limit else ""
        cursor.execute(f"""
            SELECT 
                cc.id as render_id,
                cc.church_name,
                cc.email,
                cc.phone,
                cc.initial_notes,
                ch.senior_pastor_first_name,
                ch.senior_pastor_last_name,
                ch.senior_pastor_phone,
                ch.senior_pastor_email,
                ch.denomination,
                ch.website,
                ch.congregation_size,
                ch.year_founded,
                ch.info_given,
                ch.church_pipeline,
                ch.priority,
                ch.assigned_to
            FROM contacts_contact cc
            JOIN contacts_church ch ON cc.id = ch.contact_ptr_id
            WHERE cc.church_name IS NOT NULL AND cc.church_name != ''
            ORDER BY cc.church_name
            {limit_clause}
        """)
        
        render_churches = cursor.fetchall()
        processed = 0
        updated = 0
        assigned_to_mrule = 0
        
        for render_church in render_churches:
            processed += 1
            
            # Find matching church in Supabase
            try:
                existing_contact, match_type = self.check_duplicate_church(render_church)
                
                if existing_contact:
                    updates_made = False
                    field_updates = {}
                    
                    # Handle assignment with Enhanced Notes approach
                    if render_church['assigned_to'] and render_church['assigned_to'].strip() and render_church['assigned_to'] != 'Unassigned':
                        assigned_to = render_church['assigned_to'].strip()
                        
                        if assigned_to in assignment_mapping and not existing_contact.user:
                            field_updates['user'] = assignment_mapping[assigned_to]
                            updates_made = True
                        elif assigned_to not in assignment_mapping and not existing_contact.user:
                            # Assign to m.rule and add note
                            field_updates['user'] = default_church_user
                            assigned_to_mrule += 1
                            assignment_note = self.create_assignment_note(assigned_to, "church")
                            field_updates['notes'] = self.append_to_notes(existing_contact.notes, assignment_note)
                            updates_made = True
                    
                    # Update other missing contact fields
                    if render_church['initial_notes'] and not existing_contact.initial_notes:
                        field_updates['initial_notes'] = render_church['initial_notes']
                        updates_made = True
                    
                    # Church-specific fields
                    try:
                        church_obj = Church.objects.get(contact=existing_contact)
                        church_updates = {}
                        
                        if render_church['denomination'] and not church_obj.denomination:
                            church_updates['denomination'] = render_church['denomination']
                        
                        if render_church['website'] and not church_obj.website:
                            church_updates['website'] = render_church['website']
                        
                        if render_church['congregation_size'] and not church_obj.congregation_size:
                            church_updates['congregation_size'] = render_church['congregation_size']
                        
                        if render_church['year_founded'] and not church_obj.year_founded:
                            church_updates['year_founded'] = render_church['year_founded']
                        
                        if render_church['info_given'] and not church_obj.info_given:
                            church_updates['info_given'] = render_church['info_given']
                        
                        # Pastor information
                        if render_church['senior_pastor_first_name'] and not church_obj.senior_pastor_first_name:
                            church_updates['senior_pastor_first_name'] = render_church['senior_pastor_first_name']
                        
                        if render_church['senior_pastor_last_name'] and not church_obj.senior_pastor_last_name:
                            church_updates['senior_pastor_last_name'] = render_church['senior_pastor_last_name']
                        
                        if render_church['senior_pastor_phone'] and not church_obj.pastor_phone:
                            church_updates['pastor_phone'] = render_church['senior_pastor_phone']
                        
                        if render_church['senior_pastor_email'] and not church_obj.pastor_email:
                            church_updates['pastor_email'] = render_church['senior_pastor_email']
                        
                        if church_updates and not self.dry_run:
                            for field, value in church_updates.items():
                                setattr(church_obj, field, value)
                            church_obj.save(update_fields=list(church_updates.keys()))
                            updates_made = True
                    
                    except Church.DoesNotExist:
                        pass
                    
                    # Handle pipeline migration
                    if render_church['church_pipeline'] and render_church['church_pipeline'] not in ['None', '', 'null']:
                        self.migrate_pipeline_stage(existing_contact, render_church['church_pipeline'], 'church')
                        updates_made = True
                    
                    # Apply contact updates
                    if field_updates and not self.dry_run:
                        safe_updates = {k: v for k, v in field_updates.items() if k not in ['first_name', 'last_name', 'church_name']}
                        if safe_updates:
                            for field, value in safe_updates.items():
                                setattr(existing_contact, field, value)
                            existing_contact.save(update_fields=list(safe_updates.keys()))
                    
                    if updates_made:
                        updated += 1
                        if processed % 10 == 0 or self.dry_run:
                            action = "Would update" if self.dry_run else "Updated"
                            self.stdout.write(f"   {action} {existing_contact.church_name}")
                
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"   Error processing {render_church['church_name']}: {e}"))
        
        cursor.close()
        return {'processed': processed, 'updated': updated, 'assigned_to_mrule': assigned_to_mrule}

    def migrate_pipeline_stage(self, contact, pipeline_stage, contact_type):
        """Migrate pipeline stage from Render to Supabase pipeline system"""
        if self.dry_run:
            return
            
        try:
            # Map Render pipeline stages to Supabase stages
            stage_mapping = {
                'PROMOTION': 'Promotion',
                'INFORMATION': 'Information', 
                'INVITATION': 'Invitation',
                'CONFIRMATION': 'Confirmation',
                'AUTOMATION': 'Automation',
                'EN42': 'EN42',
            }
            
            mapped_stage = stage_mapping.get(pipeline_stage.upper(), pipeline_stage.title())
            
            # Get the main pipeline for this contact type
            main_pipeline = contact.get_main_pipeline()
            if not main_pipeline:
                return
            
            # Find the stage
            try:
                stage = main_pipeline.stages.get(name=mapped_stage)
                contact.set_pipeline_stage(stage.name)
                
            except PipelineStage.DoesNotExist:
                # Stage doesn't exist, could log this or create it
                self.stdout.write(self.style.WARNING(f"   Pipeline stage '{mapped_stage}' not found for {contact_type}"))
                
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"   Error setting pipeline stage for {contact}: {e}"))