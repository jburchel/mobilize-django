"""
Management command to check which database Django is actually connecting to.
"""

from django.core.management.base import BaseCommand
from django.db import connection
from django.conf import settings


class Command(BaseCommand):
    help = 'Check which database Django is connecting to'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== Database Connection Info ==='))
        
        # Show Django settings
        db_config = settings.DATABASES['default']
        self.stdout.write(f'Django database config:')
        for key, value in db_config.items():
            if key == 'PASSWORD':
                self.stdout.write(f'  {key}: {"*" * len(str(value))}')
            else:
                self.stdout.write(f'  {key}: {value}')
        
        # Show actual connection info
        cursor = connection.cursor()
        
        try:
            # Get database name
            cursor.execute("SELECT current_database();")
            db_name = cursor.fetchone()[0]
            self.stdout.write(f'\nActual connected database: {db_name}')
            
            # Get user
            cursor.execute("SELECT current_user;")
            db_user = cursor.fetchone()[0]
            self.stdout.write(f'Connected as user: {db_user}')
            
            # Get host info if possible
            cursor.execute("SELECT inet_server_addr(), inet_server_port();")
            server_info = cursor.fetchone()
            if server_info[0]:
                self.stdout.write(f'Server: {server_info[0]}:{server_info[1]}')
            
            # Check if we can access the people table with the schema you described
            self.stdout.write(f'\n=== Testing People Table Access ===')
            
            # Try to find a table that matches your description
            cursor.execute("""
                SELECT schemaname, tablename 
                FROM pg_tables 
                WHERE tablename = 'people';
            """)
            
            people_tables = cursor.fetchall()
            
            if people_tables:
                self.stdout.write(f'Found people tables:')
                for schema, table in people_tables:
                    self.stdout.write(f'  - {schema}.{table}')
                    
                    # Check columns in each schema
                    cursor.execute("""
                        SELECT column_name 
                        FROM information_schema.columns 
                        WHERE table_schema = %s AND table_name = 'people'
                        AND column_name IN ('id', 'first_name', 'last_name', 'contact_id')
                        ORDER BY column_name;
                    """, [schema])
                    
                    key_columns = [row[0] for row in cursor.fetchall()]
                    self.stdout.write(f'    Key columns: {key_columns}')
            
            # Try to access different schemas explicitly
            schemas_to_try = ['public', 'mobilize', 'auth', 'storage']
            
            for schema in schemas_to_try:
                try:
                    cursor.execute(f"""
                        SELECT column_name 
                        FROM information_schema.columns 
                        WHERE table_schema = %s AND table_name = 'people'
                        AND column_name IN ('id', 'first_name', 'last_name')
                        ORDER BY column_name;
                    """, [schema])
                    
                    columns = [row[0] for row in cursor.fetchall()]
                    if columns:
                        self.stdout.write(f'\nSchema {schema}.people has name columns: {columns}')
                        
                        # Try to query this schema directly
                        try:
                            cursor.execute(f"""
                                SELECT id, first_name, last_name
                                FROM {schema}.people 
                                WHERE (first_name IS NOT NULL AND first_name != '') 
                                   OR (last_name IS NOT NULL AND last_name != '')
                                LIMIT 5;
                            """)
                            
                            results = cursor.fetchall()
                            if results:
                                self.stdout.write(f'  Found {len(results)} people with names:')
                                for row in results:
                                    self.stdout.write(f'    ID {row[0]}: "{row[1] or ""}" "{row[2] or ""}"')
                            else:
                                self.stdout.write(f'  No people with names found in {schema}.people')
                                
                        except Exception as e:
                            self.stdout.write(f'  Error querying {schema}.people: {e}')
                            
                except Exception as e:
                    # Schema doesn't exist or no access
                    pass
            
        except Exception as e:
            self.stdout.write(f'Error getting database info: {e}')
        
        self.stdout.write('\n' + self.style.SUCCESS('Database check complete!'))