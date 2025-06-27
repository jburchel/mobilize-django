#!/usr/bin/env python3
"""
Create comprehensive migration script using Enhanced Notes approach
"""

import os

def create_migration_script():
    """Create the Django management command for data migration using Enhanced Notes approach"""
    
    migration_script = '''"""
Migrate missing CRM data from Render database to Supabase using Enhanced Notes approach

This management command restores valuable field data that was lost during the initial migration.
Uses notes field to preserve original assignment information and assigns unmapped church 
assignments to m.rule as default user.
"""

import os
import psycopg2
from psycopg2.extras import DictCursor
from django.core.management.base import BaseCommand
from django.db import transaction
from mobilize.contacts.models import Contact
from mobilize.churches.models import Church
from mobilize.authentication.models import User
from mobilize.pipeline.models import PipelineStage, PipelineContact, Pipeline


class Command(BaseCommand):
    help = 'Migrate missing CRM data from Render database using Enhanced Notes approach'

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

    def handle(self, *args, **options):
        self.dry_run = options['dry_run']
        self.limit = options['limit']
        
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
            assignment_mapping, default_church_user = self.create_assignment_mapping()
            
            # Migrate church data
            church_stats = self.migrate_church_data(render_conn, assignment_mapping, default_church_user)
            
            # Migrate people data
            people_stats = self.migrate_people_data(render_conn, assignment_mapping)
            
            # Summary
            self.stdout.write(self.style.SUCCESS('\\n' + '='*60))
            self.stdout.write(self.style.SUCCESS('MIGRATION SUMMARY:'))
            self.stdout.write(f"Churches processed: {church_stats['processed']}")
            self.stdout.write(f"Churches updated: {church_stats['updated']}")
            self.stdout.write(f"Churches assigned to m.rule: {church_stats['assigned_to_mrule']}")
            self.stdout.write(f"People processed: {people_stats['processed']}")
            self.stdout.write(f"People updated: {people_stats['updated']}")
            
            if self.dry_run:
                self.stdout.write(self.style.WARNING('DRY RUN - No actual changes made'))
            else:
                self.stdout.write(self.style.SUCCESS('Migration completed successfully!'))
                
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
        
        try:
            # Map Jim Burchel variants
            jim_user = User.objects.get(email='j.burchel@crossoverglobal.net')
            mapping.update({
                'JIM BURCHEL': jim_user,
                'Jim Burchel': jim_user,
            })
            
            # Map Matthew Rule variants and set as default for churches
            matthew_user = User.objects.get(email='m.rule@crossoverglobal.net')
            mapping.update({
                'MATTHEW RULE': matthew_user,
                'Matthew Rule': matthew_user,
            })
            default_church_user = matthew_user
            
            self.stdout.write(f'   Mapped {len(mapping)} assignment patterns to users')
            self.stdout.write(f'   Default church user: {default_church_user.get_full_name()} ({default_church_user.email})')
            
        except User.DoesNotExist as e:
            self.stdout.write(self.style.ERROR(f'   Could not find required user: {e}'))
            self.stdout.write(self.style.ERROR('   Please ensure m.rule@crossoverglobal.net and j.burchel@crossoverglobal.net users exist'))
            raise
        
        return mapping, default_church_user

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

    def migrate_church_data(self, render_conn, assignment_mapping, default_church_user):
        """Migrate church field data from Render to Supabase"""
        self.stdout.write('\\nMigrating church data...')
        
        cursor = render_conn.cursor(cursor_factory=DictCursor)
        
        # Get church data from Render
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
                supabase_contact = Contact.objects.filter(
                    type='church',
                    church_name__icontains=render_church['church_name']
                ).first()
                
                if not supabase_contact:
                    # Try alternative matching through Church model
                    church_obj = Church.objects.filter(
                        name__icontains=render_church['church_name']
                    ).first()
                    if church_obj:
                        supabase_contact = church_obj.contact
                
                if supabase_contact:
                    updates_made = False
                    field_updates = {}
                    
                    # Handle assignment with Enhanced Notes approach
                    if render_church['assigned_to'] and render_church['assigned_to'].strip():
                        assigned_to = render_church['assigned_to'].strip()
                        
                        if assigned_to != 'Unassigned':
                            # Create assignment note
                            assignment_note = self.create_assignment_note(assigned_to, "church")
                            
                            # Check if user can be mapped directly
                            if assigned_to in assignment_mapping:
                                # Direct mapping available
                                mapped_user = assignment_mapping[assigned_to]
                                if not supabase_contact.user:
                                    field_updates['user'] = mapped_user
                                    updates_made = True
                                    self.stdout.write(f"   Mapped {assigned_to} → {mapped_user.get_full_name()}")
                            else:
                                # No direct mapping - assign to m.rule and add note
                                if not supabase_contact.user:
                                    field_updates['user'] = default_church_user
                                    assigned_to_mrule += 1
                                    updates_made = True
                                
                                # Add assignment note to contact notes
                                field_updates['notes'] = self.append_to_notes(
                                    supabase_contact.notes, 
                                    assignment_note
                                )
                                updates_made = True
                                
                                if self.dry_run:
                                    self.stdout.write(f"   Would assign {render_church['church_name']} to m.rule (was: {assigned_to})")
                    
                    # Update other missing contact fields
                    if render_church['initial_notes'] and not supabase_contact.initial_notes:
                        field_updates['initial_notes'] = render_church['initial_notes']
                        updates_made = True
                    
                    # Handle info_given data
                    if render_church['info_given'] and render_church['info_given'].strip():
                        info_note = f"Legacy Info: {render_church['info_given']}"
                        field_updates['notes'] = self.append_to_notes(
                            field_updates.get('notes', supabase_contact.notes), 
                            info_note
                        )
                        updates_made = True
                    
                    # Church-specific fields
                    church_obj = None
                    try:
                        church_obj = Church.objects.get(contact=supabase_contact)
                    except Church.DoesNotExist:
                        pass
                    
                    if church_obj:
                        church_updates = {}
                        
                        if render_church['denomination'] and not church_obj.denomination:
                            church_updates['denomination'] = render_church['denomination']
                        
                        if render_church['website'] and not church_obj.website:
                            church_updates['website'] = render_church['website']
                        
                        if render_church['congregation_size'] and not church_obj.congregation_size:
                            church_updates['congregation_size'] = render_church['congregation_size']
                        
                        if render_church['year_founded'] and not church_obj.year_founded:
                            church_updates['year_founded'] = render_church['year_founded']
                        
                        # Pastor information - store in church info_given field
                        pastor_info = []
                        if render_church['senior_pastor_first_name'] or render_church['senior_pastor_last_name']:
                            pastor_name = f"{render_church['senior_pastor_first_name'] or ''} {render_church['senior_pastor_last_name'] or ''}".strip()
                            if pastor_name:
                                pastor_info.append(f"Senior Pastor: {pastor_name}")
                        
                        if render_church['senior_pastor_phone']:
                            pastor_info.append(f"Pastor Phone: {render_church['senior_pastor_phone']}")
                        
                        if render_church['senior_pastor_email']:
                            pastor_info.append(f"Pastor Email: {render_church['senior_pastor_email']}")
                        
                        if pastor_info:
                            pastor_text = "; ".join(pastor_info)
                            if not church_obj.info_given:
                                church_updates['info_given'] = pastor_text
                            elif pastor_text not in church_obj.info_given:
                                church_updates['info_given'] = f"{church_obj.info_given}; {pastor_text}"
                        
                        if church_updates and not self.dry_run:
                            for field, value in church_updates.items():
                                setattr(church_obj, field, value)
                            church_obj.save()
                            updates_made = True
                    
                    # Handle pipeline migration
                    if render_church['church_pipeline'] and render_church['church_pipeline'] not in ['None', '', 'null']:
                        self.migrate_pipeline_stage(supabase_contact, render_church['church_pipeline'], 'church')
                        updates_made = True
                    
                    # Apply contact updates
                    if field_updates and not self.dry_run:
                        for field, value in field_updates.items():
                            setattr(supabase_contact, field, value)
                        supabase_contact.save()
                    
                    if updates_made:
                        updated += 1
                        if processed % 10 == 0 or self.dry_run:
                            action = "Would update" if self.dry_run else "Updated"
                            update_info = []
                            if 'user' in field_updates:
                                update_info.append(f"assigned to {field_updates['user'].get_full_name()}")
                            if 'notes' in field_updates:
                                update_info.append("added notes")
                            if 'initial_notes' in field_updates:
                                update_info.append("added initial notes")
                            
                            self.stdout.write(f"   {action} {supabase_contact.church_name}: {', '.join(update_info)}")
                
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"   Error processing {render_church['church_name']}: {e}"))
        
        cursor.close()
        return {'processed': processed, 'updated': updated, 'assigned_to_mrule': assigned_to_mrule}

    def migrate_people_data(self, render_conn, assignment_mapping):
        """Migrate people field data from Render to Supabase"""
        self.stdout.write('\\nMigrating people data...')
        
        cursor = render_conn.cursor(cursor_factory=DictCursor)
        
        # Get people data from Render
        limit_clause = f"LIMIT {self.limit}" if self.limit else ""
        cursor.execute(f"""
            SELECT 
                cc.id as render_id,
                cc.first_name,
                cc.last_name,
                cc.email,
                cc.phone,
                cc.initial_notes,
                cp.home_country,
                cp.marital_status,
                cp.spouse_first_name,
                cp.spouse_last_name,
                cp.people_pipeline,
                cp.priority,
                cp.assigned_to,
                cp.info_given
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
                supabase_contact = None
                
                # Try email match first
                if render_person['email']:
                    supabase_contact = Contact.objects.filter(
                        type='person',
                        email=render_person['email']
                    ).first()
                
                # Try name match if no email match
                if not supabase_contact:
                    supabase_contact = Contact.objects.filter(
                        type='person',
                        first_name__iexact=render_person['first_name'],
                        last_name__iexact=render_person['last_name']
                    ).first()
                
                if supabase_contact:
                    updates_made = False
                    field_updates = {}
                    
                    # Handle assignment with Enhanced Notes approach (for people, just preserve in notes)
                    if render_person['assigned_to'] and render_person['assigned_to'].strip():
                        assigned_to = render_person['assigned_to'].strip()
                        
                        if assigned_to != 'Unassigned':
                            # Check if user can be mapped directly
                            if assigned_to in assignment_mapping:
                                # Direct mapping available
                                mapped_user = assignment_mapping[assigned_to]
                                if not supabase_contact.user:
                                    field_updates['user'] = mapped_user
                                    updates_made = True
                            else:
                                # No direct mapping - just preserve in notes for people
                                assignment_note = self.create_assignment_note(assigned_to, "person")
                                field_updates['notes'] = self.append_to_notes(
                                    supabase_contact.notes, 
                                    assignment_note
                                )
                                updates_made = True
                    
                    # Update missing contact fields
                    if render_person['initial_notes'] and not supabase_contact.initial_notes:
                        field_updates['initial_notes'] = render_person['initial_notes']
                        updates_made = True
                    
                    # Handle additional info_given data
                    if render_person['info_given'] and render_person['info_given'].strip():
                        info_note = f"Legacy Info: {render_person['info_given']}"
                        field_updates['notes'] = self.append_to_notes(
                            field_updates.get('notes', supabase_contact.notes), 
                            info_note
                        )
                        updates_made = True
                    
                    # Person-specific fields
                    try:
                        person_obj = supabase_contact.person_details
                        person_updates = {}
                        
                        if render_person['home_country'] and not person_obj.home_country:
                            person_updates['home_country'] = render_person['home_country']
                        
                        if render_person['marital_status'] and not person_obj.marital_status:
                            person_updates['marital_status'] = render_person['marital_status']
                        
                        if render_person['spouse_first_name'] and not person_obj.spouse_first_name:
                            person_updates['spouse_first_name'] = render_person['spouse_first_name']
                        
                        if render_person['spouse_last_name'] and not person_obj.spouse_last_name:
                            person_updates['spouse_last_name'] = render_person['spouse_last_name']
                        
                        if person_updates and not self.dry_run:
                            for field, value in person_updates.items():
                                setattr(person_obj, field, value)
                            person_obj.save()
                            updates_made = True
                            
                    except Exception as e:
                        # Person details might not exist, that's okay
                        pass
                    
                    # Handle pipeline migration
                    if render_person['people_pipeline'] and render_person['people_pipeline'] not in ['None', '', 'null']:
                        self.migrate_pipeline_stage(supabase_contact, render_person['people_pipeline'], 'person')
                        updates_made = True
                    
                    # Apply contact updates
                    if field_updates and not self.dry_run:
                        for field, value in field_updates.items():
                            setattr(supabase_contact, field, value)
                        supabase_contact.save()
                    
                    if updates_made:
                        updated += 1
                        if processed % 20 == 0 or self.dry_run:
                            action = "Would update" if self.dry_run else "Updated"
                            self.stdout.write(f"   {action} {render_person['first_name']} {render_person['last_name']}")
                
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"   Error processing {render_person['first_name']} {render_person['last_name']}: {e}"))
        
        cursor.close()
        return {'processed': processed, 'updated': updated}

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
                # Add other mappings as needed
            }
            
            mapped_stage = stage_mapping.get(pipeline_stage.upper(), pipeline_stage.title())
            
            # Get the main pipeline for this contact type
            main_pipeline = contact.get_main_pipeline()
            if not main_pipeline:
                return
            
            # Find the stage
            try:
                stage = main_pipeline.stages.get(name=mapped_stage)
                
                # Set the pipeline stage
                contact.set_pipeline_stage(stage.name)
                
            except PipelineStage.DoesNotExist:
                # Stage doesn't exist, could log this or create it
                self.stdout.write(self.style.WARNING(f"   Pipeline stage '{mapped_stage}' not found for {contact_type}"))
                
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"   Error setting pipeline stage for {contact}: {e}"))
'''

    # Write the migration script
    script_path = '/Users/jimburchel/Developer-Playground/mobilize-django/mobilize/core/management/commands/migrate_render_data.py'
    
    # Create directories if they don't exist
    os.makedirs(os.path.dirname(script_path), exist_ok=True)
    
    with open(script_path, 'w') as f:
        f.write(migration_script)
    
    print(f"✅ Enhanced Notes migration script created at: {script_path}")
    print("\n🔧 Migration Strategy:")
    print("   • Churches: Unmapped assignments → assigned to m.rule + note in notes field")
    print("   • People: Unmapped assignments → preserved in notes field only")
    print("   • All: Pipeline stages, pastor info, and other missing data migrated")
    print("\nTo run the migration:")
    print("1. Dry run first: python manage.py migrate_render_data --dry-run")
    print("2. Test with limit: python manage.py migrate_render_data --dry-run --limit=10")
    print("3. Full migration: python manage.py migrate_render_data")

if __name__ == "__main__":
    create_migration_script()