"""
Management command to fix migration state when columns already exist in production.
This handles the case where schema sync commands have already added columns
but Django migrations haven't been marked as applied.
"""

from django.core.management.base import BaseCommand
from django.db import connection
from django.core.management import call_command


class Command(BaseCommand):
    help = 'Fix migration state when columns already exist in production database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        self.stdout.write(self.style.SUCCESS('🔧 Fixing Migration State'))
        self.stdout.write('=' * 60)
        
        # Check if the problematic columns exist
        with connection.cursor() as cursor:
            # Check if desired_service column exists
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'people' 
                AND column_name IN ('desired_service', 'info_given')
            """)
            existing_columns = [row[0] for row in cursor.fetchall()]
            
            self.stdout.write(f"📊 Found existing columns in people table: {existing_columns}")
            
            if 'desired_service' in existing_columns and 'info_given' in existing_columns:
                self.stdout.write(self.style.WARNING(
                    "⚠️  Both mission fields already exist in database"
                ))
                
                if not dry_run:
                    # Mark the migration as applied without actually running it
                    self.stdout.write("🔄 Marking migration 0008_add_person_mission_fields as fake applied...")
                    
                    try:
                        call_command(
                            'migrate', 
                            'contacts', 
                            '0008_add_person_mission_fields',
                            '--fake'
                        )
                        self.stdout.write(self.style.SUCCESS(
                            "✅ Successfully marked migration as applied"
                        ))
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(
                            f"❌ Error marking migration as applied: {e}"
                        ))
                        return
                else:
                    self.stdout.write(self.style.WARNING(
                        "🔍 DRY RUN: Would mark migration 0008_add_person_mission_fields as fake applied"
                    ))
            
            elif len(existing_columns) == 1:
                self.stdout.write(self.style.WARNING(
                    f"⚠️  Only {existing_columns[0]} exists. This is unexpected."
                ))
            else:
                self.stdout.write(self.style.SUCCESS(
                    "✅ No problematic columns found. Migration should run normally."
                ))
                return
        
        # Check migration status
        if not dry_run:
            self.stdout.write("\n📋 Current migration status:")
            call_command('showmigrations', 'contacts')
        
        self.stdout.write(self.style.SUCCESS('\n✅ Migration state fix complete!'))