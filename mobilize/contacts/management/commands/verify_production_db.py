"""
Management command to verify production database connection and deployment settings.
"""

import os
import psycopg2
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = 'Verify production database connection and deployment settings'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== Production Database Verification ==='))
        
        # Check environment variables
        self.stdout.write('\n=== Environment Variables ===')
        
        database_url = os.environ.get('DATABASE_URL')
        supabase_database_url = os.environ.get('SUPABASE_DATABASE_URL')
        supabase_url = os.environ.get('SUPABASE_URL')
        
        self.stdout.write(f'DATABASE_URL: {"SET" if database_url else "NOT SET"}')
        self.stdout.write(f'SUPABASE_DATABASE_URL: {"SET" if supabase_database_url else "NOT SET"}')
        self.stdout.write(f'SUPABASE_URL: {"SET" if supabase_url else "NOT SET"}')
        
        if database_url:
            # Mask password in URL for display
            masked_url = database_url
            if '@' in masked_url:
                parts = masked_url.split('@')
                if ':' in parts[0]:
                    auth_parts = parts[0].split(':')
                    if len(auth_parts) >= 3:
                        auth_parts[2] = '****'
                        parts[0] = ':'.join(auth_parts)
                masked_url = '@'.join(parts)
            self.stdout.write(f'DATABASE_URL value: {masked_url}')
        
        # Check Django database configuration
        self.stdout.write(f'\n=== Django Database Configuration ===')
        db_config = settings.DATABASES['default']
        
        for key, value in db_config.items():
            if key == 'PASSWORD':
                self.stdout.write(f'  {key}: {"*" * len(str(value)) if value else "NOT SET"}')
            elif key in ['HOST', 'NAME', 'USER', 'PORT']:
                self.stdout.write(f'  {key}: {value}')
        
        # Test actual database connection
        self.stdout.write(f'\n=== Testing Database Connection ===')
        
        try:
            from django.db import connection
            cursor = connection.cursor()
            
            # Get connection details
            cursor.execute("SELECT current_database(), current_user, inet_server_addr(), inet_server_port();")
            db_name, db_user, server_addr, server_port = cursor.fetchone()
            
            self.stdout.write(f'✓ Successfully connected to Django database')
            self.stdout.write(f'  Database: {db_name}')
            self.stdout.write(f'  User: {db_user}')
            self.stdout.write(f'  Server: {server_addr}:{server_port}')
            
            # Check if this matches Supabase
            is_supabase = 'supabase' in str(server_addr).lower() or 'supabase' in db_name.lower()
            self.stdout.write(f'  Appears to be Supabase: {"YES" if is_supabase else "NO"}')
            
            # Test a simple query to verify we can read data
            cursor.execute("SELECT COUNT(*) FROM contacts WHERE type = 'person'")
            person_count = cursor.fetchone()[0]
            self.stdout.write(f'  Person contacts found: {person_count}')
            
            # Check for specific test data
            cursor.execute("""
                SELECT id, first_name, last_name, email 
                FROM contacts 
                WHERE first_name = 'Olivia' AND last_name = 'Tanchak'
                LIMIT 1
            """)
            olivia_result = cursor.fetchone()
            
            if olivia_result:
                contact_id, first_name, last_name, email = olivia_result
                self.stdout.write(f'  Found Olivia Tanchak: Contact {contact_id} ({email})')
            else:
                self.stdout.write(f'  Olivia Tanchak: NOT FOUND')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Database connection failed: {e}'))
        
        # Test direct Supabase connection
        if supabase_database_url:
            self.stdout.write(f'\n=== Testing Direct Supabase Connection ===')
            
            try:
                conn = psycopg2.connect(supabase_database_url)
                cursor = conn.cursor()
                
                cursor.execute("SELECT current_database(), current_user, inet_server_addr(), inet_server_port();")
                sb_db_name, sb_user, sb_addr, sb_port = cursor.fetchone()
                
                self.stdout.write(f'✓ Successfully connected to Supabase directly')
                self.stdout.write(f'  Database: {sb_db_name}')
                self.stdout.write(f'  User: {sb_user}')
                self.stdout.write(f'  Server: {sb_addr}:{sb_port}')
                
                # Compare with Django connection
                if 'db_name' in locals() and 'server_addr' in locals():
                    same_db = (db_name == sb_db_name and str(server_addr) == str(sb_addr))
                    self.stdout.write(f'  Same as Django connection: {"YES" if same_db else "NO"}')
                    
                    if not same_db:
                        self.stdout.write(self.style.WARNING('  ⚠️  Django and Supabase connections differ!'))
                
                cursor.close()
                conn.close()
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'✗ Direct Supabase connection failed: {e}'))
        
        # Check for common deployment issues
        self.stdout.write(f'\n=== Deployment Configuration Check ===')
        
        # Check if running in production environment
        debug_mode = settings.DEBUG
        self.stdout.write(f'DEBUG mode: {debug_mode}')
        
        if debug_mode:
            self.stdout.write(self.style.WARNING('  ⚠️  DEBUG is True - this may not be production'))
        
        # Check allowed hosts
        allowed_hosts = settings.ALLOWED_HOSTS
        self.stdout.write(f'ALLOWED_HOSTS: {allowed_hosts}')
        
        # Render-specific checks
        render_service_name = os.environ.get('RENDER_SERVICE_NAME')
        render_service_id = os.environ.get('RENDER_SERVICE_ID')
        
        if render_service_name or render_service_id:
            self.stdout.write(f'\n=== Render Deployment Info ===')
            self.stdout.write(f'Service Name: {render_service_name or "Not set"}')
            self.stdout.write(f'Service ID: {render_service_id or "Not set"}')
            
            # Check if DATABASE_URL is being used (Render sets this)
            if database_url:
                self.stdout.write(f'✓ DATABASE_URL is set (Render configuration)')
                
                # Check if it's a Supabase URL
                if 'supabase.co' in database_url:
                    self.stdout.write(f'✓ DATABASE_URL points to Supabase')
                else:
                    self.stdout.write(self.style.WARNING(f'⚠️  DATABASE_URL does not appear to be Supabase'))
            else:
                self.stdout.write(self.style.ERROR(f'✗ DATABASE_URL not set in Render'))
        else:
            self.stdout.write(f'\n⚠️  No Render environment variables detected')
        
        # Final recommendation
        self.stdout.write(f'\n=== Recommendations ===')
        
        if database_url and 'supabase.co' in database_url:
            self.stdout.write(f'✓ Configuration appears correct for Supabase')
        else:
            self.stdout.write(f'❌ Database configuration issue detected')
            self.stdout.write(f'   - Ensure DATABASE_URL points to your Supabase database')
            self.stdout.write(f'   - Check Render environment variables')
        
        self.stdout.write('\n' + self.style.SUCCESS('Verification complete!'))