"""
Management command to migrate name data from people table to contacts table.

This addresses the issue where Supabase has first_name and last_name columns
in the people table, but Django models expect them in the contacts table.
"""

from django.core.management.base import BaseCommand
from django.db import connection, transaction


class Command(BaseCommand):
    help = 'Migrate name data from people table to contacts table'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be changed without making actual changes',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== Migrating Names from People Table to Contacts Table ==='))
        
        cursor = connection.cursor()
        
        # First, let's check what columns actually exist in the people table
        self.stdout.write('Checking people table structure...')
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'people'
            AND column_name IN ('first_name', 'last_name', 'contact_id')
            ORDER BY column_name;
        """)
        
        people_columns = [row[0] for row in cursor.fetchall()]
        self.stdout.write(f'People table columns found: {people_columns}')
        
        if 'first_name' not in people_columns or 'last_name' not in people_columns:
            self.stdout.write(self.style.ERROR('People table does not have first_name and last_name columns!'))
            return
        
        # Check contacts table structure  
        self.stdout.write('Checking contacts table structure...')
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'contacts'
            AND column_name IN ('first_name', 'last_name', 'id')
            ORDER BY column_name;
        """)
        
        contacts_columns = [row[0] for row in cursor.fetchall()]
        self.stdout.write(f'Contacts table columns found: {contacts_columns}')
        
        # Find people with names in people table but empty names in contacts table
        self.stdout.write('\\nFinding mismatched name data...')
        cursor.execute("""
            SELECT 
                p.contact_id,
                p.first_name as people_first_name,
                p.last_name as people_last_name,
                c.first_name as contact_first_name,
                c.last_name as contact_last_name
            FROM people p
            JOIN contacts c ON p.contact_id = c.id
            WHERE 
                (p.first_name IS NOT NULL AND p.first_name != '') 
                OR (p.last_name IS NOT NULL AND p.last_name != '')
            AND (
                (c.first_name IS NULL OR c.first_name = '') 
                OR (c.last_name IS NULL OR c.last_name = '')
            )
            ORDER BY p.contact_id;
        """)
        
        mismatched_records = cursor.fetchall()
        total_mismatched = len(mismatched_records)
        
        self.stdout.write(f'Found {total_mismatched} people with names in people table but missing in contacts table:')
        
        if total_mismatched == 0:
            self.stdout.write(self.style.SUCCESS('No mismatched records found!'))
            return
        
        # Show the records that will be updated
        self.stdout.write('\\n=== RECORDS TO UPDATE ===')
        for record in mismatched_records:
            contact_id, p_first, p_last, c_first, c_last = record
            self.stdout.write(f'\\nContact ID {contact_id}:')
            self.stdout.write(f'  People table: "{p_first or ""}" "{p_last or ""}"')
            self.stdout.write(f'  Contact table: "{c_first or ""}" "{c_last or ""}"')
            self.stdout.write(f'  → Will update contact table to: "{p_first or ""}" "{p_last or ""}"')
        
        if options['dry_run']:
            self.stdout.write(f'\\n{self.style.WARNING("DRY RUN MODE - No changes made")}')
            self.stdout.write(f'Run without --dry-run to apply {total_mismatched} updates')
            return
        
        # Confirm before making changes
        confirm = input(f'\\nUpdate {total_mismatched} contact records? (y/N): ')
        if confirm.lower() != 'y':
            self.stdout.write('Operation cancelled.')
            return
        
        # Perform the migration
        self.stdout.write('\\nMigrating name data...')
        updated_count = 0
        
        with transaction.atomic():
            for record in mismatched_records:
                contact_id, p_first, p_last, c_first, c_last = record
                
                try:
                    cursor.execute("""
                        UPDATE contacts 
                        SET 
                            first_name = %s,
                            last_name = %s
                        WHERE id = %s
                    """, [p_first, p_last, contact_id])
                    
                    updated_count += 1
                    self.stdout.write(f'✓ Updated Contact {contact_id}: "{p_first or ""}" "{p_last or ""}"')
                    
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'✗ Failed to update Contact {contact_id}: {e}'))
        
        self.stdout.write(f'\\n=== MIGRATION COMPLETE ===')
        self.stdout.write(f'Successfully updated: {updated_count} contacts')
        self.stdout.write(f'Failed updates: {total_mismatched - updated_count}')
        
        if updated_count > 0:
            self.stdout.write(self.style.SUCCESS('\\nName migration completed! People should now display proper names.'))
        
        # Verify the results
        self.stdout.write('\\nVerifying results...')
        cursor.execute("""
            SELECT COUNT(*)
            FROM people p
            JOIN contacts c ON p.contact_id = c.id
            WHERE 
                (p.first_name IS NOT NULL AND p.first_name != '') 
                OR (p.last_name IS NOT NULL AND p.last_name != '')
            AND (
                (c.first_name IS NULL OR c.first_name = '') 
                AND (c.last_name IS NULL OR c.last_name = '')
            )
        """)
        
        remaining_issues = cursor.fetchone()[0]
        if remaining_issues == 0:
            self.stdout.write(self.style.SUCCESS('✓ All name data successfully migrated!'))
        else:
            self.stdout.write(self.style.WARNING(f'⚠ {remaining_issues} records still have name issues'))