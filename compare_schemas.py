#!/usr/bin/env python
"""
Comprehensive schema comparison between local PostgreSQL and Supabase
Compares tables, columns, data types, constraints, indexes, foreign keys, and Django compatibility
"""
import os
import sys
import django
import psycopg2

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mobilize.settings')
sys.path.append('/Users/jimburchel/Developer-Playground/mobilize-django')
django.setup()

from django.db import connection
from django.conf import settings

def get_database_info():
    """Get database connection info"""
    db_settings = settings.DATABASES['default']
    return {
        'local': {
            'host': 'localhost',
            'port': 5432,
            'name': 'mobilize',
            'user': 'jimburchel',
            'password': ''
        },
        'supabase': {
            'host': db_settings['HOST'],
            'port': db_settings['PORT'],
            'name': db_settings['NAME'],
            'user': db_settings['USER'],
            'password': db_settings['PASSWORD']
        }
    }

def connect_to_db(db_config):
    """Create database connection"""
    try:
        conn = psycopg2.connect(
            host=db_config['host'],
            port=db_config['port'],
            database=db_config['name'],
            user=db_config['user'],
            password=db_config['password']
        )
        return conn
    except Exception as e:
        print(f"❌ Failed to connect to database: {e}")
        return None

def get_tables(cursor):
    """Get all tables in the database"""
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_type = 'BASE TABLE'
        ORDER BY table_name;
    """)
    return [row[0] for row in cursor.fetchall()]

def get_table_columns(cursor, table_name):
    """Get detailed column information for a table"""
    cursor.execute("""
        SELECT 
            column_name,
            data_type,
            character_maximum_length,
            is_nullable,
            column_default,
            ordinal_position
        FROM information_schema.columns 
        WHERE table_name = %s 
        ORDER BY ordinal_position;
    """, [table_name])
    
    columns = {}
    for row in cursor.fetchall():
        col_name, data_type, max_length, nullable, default, position = row
        columns[col_name] = {
            'data_type': data_type,
            'max_length': max_length,
            'nullable': nullable,
            'default': default,
            'position': position
        }
    return columns

def get_primary_keys(cursor, table_name):
    """Get primary key constraints for a table"""
    cursor.execute("""
        SELECT 
            kcu.column_name,
            tc.constraint_name
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu 
            ON tc.constraint_name = kcu.constraint_name
        WHERE tc.table_name = %s 
        AND tc.constraint_type = 'PRIMARY KEY'
        ORDER BY kcu.ordinal_position;
    """, [table_name])
    return cursor.fetchall()

def get_foreign_keys(cursor, table_name):
    """Get foreign key constraints for a table"""
    cursor.execute("""
        SELECT 
            kcu.column_name,
            ccu.table_name AS foreign_table_name,
            ccu.column_name AS foreign_column_name,
            tc.constraint_name
        FROM information_schema.table_constraints AS tc 
        JOIN information_schema.key_column_usage AS kcu
            ON tc.constraint_name = kcu.constraint_name
        JOIN information_schema.constraint_column_usage AS ccu
            ON ccu.constraint_name = tc.constraint_name
        WHERE tc.constraint_type = 'FOREIGN KEY' 
        AND tc.table_name = %s;
    """, [table_name])
    return cursor.fetchall()

def get_indexes(cursor, table_name):
    """Get indexes for a table"""
    cursor.execute("""
        SELECT 
            indexname,
            indexdef
        FROM pg_indexes 
        WHERE tablename = %s
        ORDER BY indexname;
    """, [table_name])
    return cursor.fetchall()

def get_constraints(cursor, table_name):
    """Get check constraints for a table"""
    cursor.execute("""
        SELECT 
            constraint_name,
            check_clause
        FROM information_schema.check_constraints cc
        JOIN information_schema.table_constraints tc
            ON cc.constraint_name = tc.constraint_name
        WHERE tc.table_name = %s;
    """, [table_name])
    return cursor.fetchall()

def compare_schemas():
    """Main comparison function"""
    print("🔍 COMPREHENSIVE SCHEMA COMPARISON: LOCAL vs SUPABASE")
    print("=" * 80)
    
    db_info = get_database_info()
    
    # Connect to both databases
    local_conn = connect_to_db(db_info['local'])
    supabase_conn = connect_to_db(db_info['supabase'])
    
    if not local_conn:
        print("❌ Cannot connect to local database")
        return
    
    if not supabase_conn:
        print("❌ Cannot connect to Supabase database")
        return
    
    local_cursor = local_conn.cursor()
    supabase_cursor = supabase_conn.cursor()
    
    try:
        # Get tables from both databases
        local_tables = set(get_tables(local_cursor))
        supabase_tables = set(get_tables(supabase_cursor))
        
        print(f"📊 LOCAL TABLES: {len(local_tables)}")
        print(f"📊 SUPABASE TABLES: {len(supabase_tables)}")
        
        # Tables only in local
        local_only = local_tables - supabase_tables
        if local_only:
            print(f"\n⚠️  TABLES ONLY IN LOCAL ({len(local_only)}):")
            for table in sorted(local_only):
                print(f"   - {table}")
        
        # Tables only in Supabase
        supabase_only = supabase_tables - local_tables
        if supabase_only:
            print(f"\n⚠️  TABLES ONLY IN SUPABASE ({len(supabase_only)}):")
            for table in sorted(supabase_only):
                print(f"   - {table}")
        
        # Common tables - do detailed comparison
        common_tables = local_tables & supabase_tables
        print(f"\n✅ COMMON TABLES ({len(common_tables)}):")
        
        differences_found = False
        
        for table_name in sorted(common_tables):
            print(f"\n🔍 ANALYZING TABLE: {table_name}")
            
            # Compare columns
            local_columns = get_table_columns(local_cursor, table_name)
            supabase_columns = get_table_columns(supabase_cursor, table_name)
            
            # Column differences
            local_col_names = set(local_columns.keys())
            supabase_col_names = set(supabase_columns.keys())
            
            missing_in_supabase = local_col_names - supabase_col_names
            missing_in_local = supabase_col_names - local_col_names
            
            if missing_in_supabase:
                differences_found = True
                print(f"   ❌ COLUMNS MISSING IN SUPABASE: {missing_in_supabase}")
            
            if missing_in_local:
                differences_found = True
                print(f"   ❌ COLUMNS MISSING IN LOCAL: {missing_in_local}")
            
            # Compare column details for common columns
            common_columns = local_col_names & supabase_col_names
            column_diffs = []
            
            for col_name in common_columns:
                local_col = local_columns[col_name]
                supabase_col = supabase_columns[col_name]
                
                diffs = []
                if local_col['data_type'] != supabase_col['data_type']:
                    diffs.append(f"type: {local_col['data_type']} vs {supabase_col['data_type']}")
                
                if local_col['nullable'] != supabase_col['nullable']:
                    diffs.append(f"nullable: {local_col['nullable']} vs {supabase_col['nullable']}")
                
                if str(local_col['default']) != str(supabase_col['default']):
                    diffs.append(f"default: {local_col['default']} vs {supabase_col['default']}")
                
                if diffs:
                    differences_found = True
                    column_diffs.append([col_name, ' | '.join(diffs)])
            
            if column_diffs:
                print(f"   ❌ COLUMN DIFFERENCES:")
                for col_name, diffs in column_diffs:
                    print(f"      {col_name}: {diffs}")
            
            # Compare primary keys
            local_pks = get_primary_keys(local_cursor, table_name)
            supabase_pks = get_primary_keys(supabase_cursor, table_name)
            
            if local_pks != supabase_pks:
                differences_found = True
                print(f"   ❌ PRIMARY KEY DIFFERENCES:")
                print(f"      LOCAL: {local_pks}")
                print(f"      SUPABASE: {supabase_pks}")
            
            # Compare foreign keys
            local_fks = get_foreign_keys(local_cursor, table_name)
            supabase_fks = get_foreign_keys(supabase_cursor, table_name)
            
            if set(local_fks) != set(supabase_fks):
                differences_found = True
                print(f"   ❌ FOREIGN KEY DIFFERENCES:")
                print(f"      LOCAL: {local_fks}")
                print(f"      SUPABASE: {supabase_fks}")
            
            # Compare indexes (basic comparison)
            local_indexes = get_indexes(local_cursor, table_name)
            supabase_indexes = get_indexes(supabase_cursor, table_name)
            
            local_index_names = {idx[0] for idx in local_indexes}
            supabase_index_names = {idx[0] for idx in supabase_indexes}
            
            missing_indexes = local_index_names - supabase_index_names
            extra_indexes = supabase_index_names - local_index_names
            
            if missing_indexes or extra_indexes:
                differences_found = True
                if missing_indexes:
                    print(f"   ⚠️  INDEXES MISSING IN SUPABASE: {missing_indexes}")
                if extra_indexes:
                    print(f"   ⚠️  EXTRA INDEXES IN SUPABASE: {extra_indexes}")
            
            if not any([missing_in_supabase, missing_in_local, column_diffs, 
                       local_pks != supabase_pks, set(local_fks) != set(supabase_fks),
                       missing_indexes, extra_indexes]):
                print(f"   ✅ {table_name} schemas match perfectly")
        
        # Test Django model compatibility
        print(f"\n🔧 TESTING DJANGO MODEL COMPATIBILITY WITH SUPABASE:")
        
        try:
            from mobilize.contacts.models import Person, Contact
            from mobilize.churches.models import Church
            
            # Test basic model operations
            contact_count = Contact.objects.count()
            person_count = Person.objects.count()
            church_count = Church.objects.count()
            
            print(f"   ✅ Contact.objects.count() = {contact_count}")
            print(f"   ✅ Person.objects.count() = {person_count}")
            print(f"   ✅ Church.objects.count() = {church_count}")
            
            # Test queryset evaluation
            try:
                test_contacts = list(Contact.objects.all()[:3])
                print(f"   ✅ Contact queryset evaluation works - got {len(test_contacts)} contacts")
            except Exception as e:
                print(f"   ❌ Contact queryset evaluation failed: {e}")
            
            try:
                test_people = list(Person.objects.all()[:3])
                print(f"   ✅ Person queryset evaluation works - got {len(test_people)} people")
            except Exception as e:
                print(f"   ❌ Person queryset evaluation failed: {e}")
            
            try:
                test_churches = list(Church.objects.all()[:3])
                print(f"   ✅ Church queryset evaluation works - got {len(test_churches)} churches")
            except Exception as e:
                print(f"   ❌ Church queryset evaluation failed: {e}")
                
        except Exception as e:
            print(f"   ❌ Django model compatibility test failed: {e}")
        
        # Summary
        print(f"\n" + "=" * 80)
        if differences_found:
            print(f"❌ SCHEMA DIFFERENCES FOUND - Review the details above")
        else:
            print(f"✅ ALL SCHEMAS MATCH PERFECTLY")
        
        print(f"📊 COMPARISON COMPLETE")
        
    except Exception as e:
        print(f"❌ Error during comparison: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        local_cursor.close()
        local_conn.close()
        supabase_cursor.close()
        supabase_conn.close()

if __name__ == "__main__":
    compare_schemas()