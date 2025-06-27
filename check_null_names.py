#!/usr/bin/env python
"""
Check which people have NULL names in Supabase
"""

import psycopg2
import os
from urllib.parse import urlparse
from dotenv import load_dotenv

load_dotenv()

def get_supabase_connection():
    database_url = os.environ.get('SUPABASE_DATABASE_URL')
    if not database_url:
        raise ValueError("SUPABASE_DATABASE_URL not set")
    
    parsed = urlparse(database_url)
    conn = psycopg2.connect(
        host=parsed.hostname,
        port=parsed.port or 5432,
        database=parsed.path[1:],
        user=parsed.username,
        password=parsed.password,
        sslmode='require'
    )
    return conn

def check_null_names():
    print("🔍 CHECKING FOR NULL NAMES IN SUPABASE")
    print("=" * 60)
    
    conn = get_supabase_connection()
    cursor = conn.cursor()
    
    # Check all Person-Contact pairs
    cursor.execute("""
        SELECT p.contact_id, c.first_name, c.last_name, c.email
        FROM people p 
        INNER JOIN contacts c ON p.contact_id = c.id 
        WHERE c.type = 'person'
        ORDER BY p.contact_id DESC
    """)
    all_people = cursor.fetchall()
    
    print(f"\n📊 Total Person records: {len(all_people)}")
    
    # Find those with NULL or empty names
    no_names = []
    for person in all_people:
        contact_id, first_name, last_name, email = person
        if not first_name and not last_name:
            no_names.append(person)
    
    print(f"\n🔍 People with no names: {len(no_names)}")
    if no_names:
        print("\nShowing all people without names:")
        for contact_id, first_name, last_name, email in no_names:
            print(f"   • Contact {contact_id}: '{first_name}' '{last_name}' ({email})")
    
    # Check if these are the recently created ones
    cursor.execute("""
        SELECT p.contact_id, c.first_name, c.last_name, c.created_at
        FROM people p 
        INNER JOIN contacts c ON p.contact_id = c.id 
        WHERE c.type = 'person'
        AND (c.first_name IS NULL OR c.first_name = '')
        AND (c.last_name IS NULL OR c.last_name = '')
        ORDER BY c.created_at DESC
        LIMIT 10
    """)
    recent_no_names = cursor.fetchall()
    
    if recent_no_names:
        print(f"\n📅 Recently created contacts without names:")
        for contact_id, first_name, last_name, created_at in recent_no_names:
            print(f"   • Contact {contact_id}: created at {created_at}")
    
    # Check if we need to sync names again from people table
    cursor.execute("""
        SELECT p.contact_id, p.first_name, p.last_name, c.first_name, c.last_name
        FROM people p 
        INNER JOIN contacts c ON p.contact_id = c.id 
        WHERE c.type = 'person'
        AND p.first_name IS NOT NULL
        AND (c.first_name IS NULL OR c.first_name = '')
        LIMIT 10
    """)
    needs_sync = cursor.fetchall()
    
    if needs_sync:
        print(f"\n⚠️  Found people with names in people table but not in contacts:")
        for p_id, p_first, p_last, c_first, c_last in needs_sync:
            print(f"   • Contact {p_id}: people('{p_first}' '{p_last}') vs contacts('{c_first}' '{c_last}')")
    
    conn.close()

if __name__ == "__main__":
    check_null_names()