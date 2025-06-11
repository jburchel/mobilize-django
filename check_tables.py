#!/usr/bin/env python
"""
Script to check database tables in both Django and Supabase.
"""
import os
import sys
import django
from django.db import connection

# Set up Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mobilize.settings')
django.setup()

# Check Django tables
with connection.cursor() as cursor:
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        ORDER BY table_name;
    """)
    tables = cursor.fetchall()
    
    print("=== Django Database Tables ===")
    for table in tables:
        print(table[0])

# Check if a specific table exists
def check_table_exists(table_name):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = %s
            );
        """, [table_name])
        exists = cursor.fetchone()[0]
        print(f"Table '{table_name}' exists: {exists}")

# Check specific tables
print("\n=== Checking Specific Tables ===")
check_table_exists('contacts')
check_table_exists('people')
check_table_exists('churches')

# Check table structure if it exists
def describe_table(table_name):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = %s
            );
        """, [table_name])
        exists = cursor.fetchone()[0]
        
        if not exists:
            print(f"Table '{table_name}' does not exist")
            return
            
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_schema = 'public'
            AND table_name = %s
            ORDER BY ordinal_position;
        """, [table_name])
        columns = cursor.fetchall()
        
        print(f"\n=== Structure of '{table_name}' table ===")
        for column in columns:
            print(f"{column[0]} ({column[1]}) {'NULL' if column[2] == 'YES' else 'NOT NULL'}")

# Describe tables
describe_table('contacts')
describe_table('people')
describe_table('churches')

# Try to get Supabase connection info
from mobilize.utils.supabase_client import supabase

print("\n=== Supabase Connection Info ===")
if supabase.client:
    print("Supabase client is initialized")
    print(f"URL: {supabase.supabase_url}")
    # Don't print the key for security reasons
    
    # Try to query Supabase tables
    try:
        print("\n=== Attempting to query Supabase tables ===")
        for table_name in ['contacts', 'people', 'churches']:
            try:
                response = supabase.client.table(table_name).select('count').limit(1).execute()
                print(f"Table '{table_name}' query succeeded")
            except Exception as e:
                print(f"Table '{table_name}' query failed: {str(e)}")
    except Exception as e:
        print(f"Error querying Supabase: {str(e)}")
else:
    print("Supabase client is not initialized")
