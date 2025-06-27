from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Debug pipeline database schema issues'

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            # Check what pipeline-related tables exist
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name LIKE '%pipeline%'
                ORDER BY table_name;
            """)
            tables = cursor.fetchall()
            
            self.stdout.write('\n=== Pipeline Tables ===')
            for table in tables:
                self.stdout.write(f"- {table[0]}")
            
            # Check foreign key constraints on pipeline contact tables
            cursor.execute("""
                SELECT 
                    conname AS constraint_name,
                    conrelid::regclass AS table_name,
                    confrelid::regclass AS foreign_table
                FROM pg_constraint 
                WHERE conrelid::regclass::text LIKE '%pipeline%contact%'
                AND contype = 'f';
            """)
            constraints = cursor.fetchall()
            
            self.stdout.write('\n=== Foreign Key Constraints ===')
            for constraint in constraints:
                self.stdout.write(f"- {constraint[0]}: {constraint[1]} -> {constraint[2]}")
            
            # Check pipeline stages
            cursor.execute("""
                SELECT id, name, pipeline_id, "order" 
                FROM pipeline_pipelinestage 
                ORDER BY pipeline_id, "order";
            """)
            stages = cursor.fetchall()
            
            self.stdout.write('\n=== Pipeline Stages ===')
            for stage in stages:
                self.stdout.write(f"- ID {stage[0]}: {stage[1]} (Pipeline {stage[2]}, Order {stage[3]})")
            
            # Check if pipeline_contacts table exists (wrong name)
            cursor.execute("""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'pipeline_contacts';
            """)
            wrong_table_exists = cursor.fetchone()[0] > 0
            
            if wrong_table_exists:
                self.stdout.write(self.style.ERROR('\n=== PROBLEM FOUND ==='))
                self.stdout.write(self.style.ERROR('Table "pipeline_contacts" exists but Django expects "pipeline_pipelinecontact"'))
                self.stdout.write('This is likely causing the foreign key constraint error.')
                
                # Check if the correct table also exists
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'pipeline_pipelinecontact';
                """)
                correct_table_exists = cursor.fetchone()[0] > 0
                
                if correct_table_exists:
                    self.stdout.write('Both tables exist. You may need to consolidate data.')
                else:
                    self.stdout.write('Only the wrong table name exists. You may need to rename it.')
            
            self.stdout.write(self.style.SUCCESS('\nDone!'))