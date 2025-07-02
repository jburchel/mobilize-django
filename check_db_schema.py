#!/usr/bin/env python
import os
import sys
import django

# Add the project root to the path
sys.path.insert(0, os.path.abspath('.'))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mobilize.settings')
django.setup()

from django.db import connection

def check_user_offices_schema():
    with connection.cursor() as cursor:
        # Check the column type of user_id in user_offices table
        cursor.execute("""
            SELECT column_name, data_type, character_maximum_length
            FROM information_schema.columns
            WHERE table_name = 'user_offices'
            AND column_name = 'user_id';
        """)
        
        result = cursor.fetchone()
        if result:
            print(f"user_offices.user_id column:")
            print(f"  - Column name: {result[0]}")
            print(f"  - Data type: {result[1]}")
            print(f"  - Max length: {result[2]}")
        else:
            print("user_offices.user_id column not found!")
        
        # Check the data type of id in auth_user
        cursor.execute("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'auth_user'
            AND column_name = 'id';
        """)
        
        result = cursor.fetchone()
        if result:
            print(f"\nauth_user.id column:")
            print(f"  - Column name: {result[0]}")
            print(f"  - Data type: {result[1]}")
        
        # Check applied migrations
        cursor.execute("""
            SELECT app, name, applied
            FROM django_migrations
            WHERE app = 'admin_panel'
            ORDER BY id;
        """)
        
        print("\n\nApplied admin_panel migrations:")
        for row in cursor.fetchall():
            print(f"  - {row[0]}.{row[1]} (applied: {row[2]})")

if __name__ == "__main__":
    check_user_offices_schema()