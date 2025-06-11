from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Updates the pipeline_contacts table to support both people and churches'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting pipeline_contacts table update...'))
        
        # Check if the columns already exist
        with connection.cursor() as cursor:
            cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name='pipeline_contacts' AND column_name='person_id'")
            person_column_exists = cursor.fetchone() is not None
            
            cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name='pipeline_contacts' AND column_name='church_id'")
            church_column_exists = cursor.fetchone() is not None
            
            cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name='pipeline_contacts' AND column_name='contact_type'")
            contact_type_column_exists = cursor.fetchone() is not None
        
        # If the columns don't exist, create them
        with connection.cursor() as cursor:
            if not person_column_exists:
                self.stdout.write(self.style.SUCCESS('Adding person_id column...'))
                cursor.execute("ALTER TABLE pipeline_contacts ADD COLUMN person_id integer REFERENCES people(id) ON DELETE CASCADE")
            
            if not church_column_exists:
                self.stdout.write(self.style.SUCCESS('Adding church_id column...'))
                cursor.execute("ALTER TABLE pipeline_contacts ADD COLUMN church_id integer REFERENCES churches(id) ON DELETE CASCADE")
            
            if not contact_type_column_exists:
                self.stdout.write(self.style.SUCCESS('Adding contact_type column...'))
                cursor.execute("ALTER TABLE pipeline_contacts ADD COLUMN contact_type varchar(10) DEFAULT 'person' NOT NULL")
        
        # Migrate existing data from contact_id to person_id
        with connection.cursor() as cursor:
            # Check if contact_id column exists
            cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name='pipeline_contacts' AND column_name='contact_id'")
            contact_column_exists = cursor.fetchone() is not None
            
            if contact_column_exists:
                self.stdout.write(self.style.SUCCESS('Migrating data from contact_id to person_id...'))
                # Update person_id with contact_id values
                cursor.execute("""
                    UPDATE pipeline_contacts 
                    SET person_id = contact_id 
                    WHERE contact_id IN (SELECT id FROM contacts WHERE id IN (SELECT contact_ptr_id FROM people))
                """)
                
                # Update contact_type for any church contacts
                cursor.execute("""
                    UPDATE pipeline_contacts 
                    SET church_id = contact_id, contact_type = 'church' 
                    WHERE contact_id IN (SELECT id FROM contacts WHERE id IN (SELECT contact_ptr_id FROM churches))
                """)
                
                # Create indexes
                self.stdout.write(self.style.SUCCESS('Creating indexes...'))
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_pipeline_contacts_person ON pipeline_contacts(person_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_pipeline_contacts_church ON pipeline_contacts(church_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_pipeline_contacts_type ON pipeline_contacts(contact_type)")
                
                # Drop the contact_id column if it's safe to do so
                # Only drop if all data has been migrated
                cursor.execute("""
                    SELECT COUNT(*) FROM pipeline_contacts 
                    WHERE contact_id IS NOT NULL 
                    AND person_id IS NULL 
                    AND church_id IS NULL
                """)
                unmigrated_count = cursor.fetchone()[0]
                
                if unmigrated_count == 0:
                    self.stdout.write(self.style.SUCCESS('All data migrated. Dropping contact_id column...'))
                    cursor.execute("ALTER TABLE pipeline_contacts DROP COLUMN contact_id")
                else:
                    self.stdout.write(self.style.WARNING(f'Found {unmigrated_count} unmigrated contacts. Keeping contact_id column.'))
        
        self.stdout.write(self.style.SUCCESS('Pipeline contacts table update completed successfully!'))
