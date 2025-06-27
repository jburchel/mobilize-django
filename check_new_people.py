#!/usr/bin/env python
"""
Check for recently added Person records that might not have been synced
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

def check_new_people():
    print("🔍 CHECKING FOR NEW PERSON RECORDS")
    print("=" * 60)
    
    conn = get_supabase_connection()
    cursor = conn.cursor()
    
    # Count current totals
    cursor.execute("SELECT COUNT(*) FROM people")
    total_people = cursor.fetchone()[0]
    
    cursor.execute("""
        SELECT COUNT(*) 
        FROM people p 
        INNER JOIN contacts c ON p.contact_id = c.id 
        WHERE c.type = 'person'
    """)
    valid_people = cursor.fetchone()[0]
    
    print(f"\n📊 Current counts:")
    print(f"   - Total people records: {total_people}")
    print(f"   - Valid Person-Contact joins: {valid_people}")
    
    # Check for any Person records created after our sync
    cursor.execute("""
        SELECT p.contact_id, c.first_name, c.last_name, p.id
        FROM people p
        INNER JOIN contacts c ON p.contact_id = c.id
        WHERE c.type = 'person'
        ORDER BY p.contact_id DESC
        LIMIT 15
    """)
    recent_people = cursor.fetchall()
    
    print(f"\n📋 Last 15 Person records (newest first):")
    for contact_id, first_name, last_name, person_id in recent_people:
        name = f"{first_name or ''} {last_name or ''}".strip() or "NO NAME"
        print(f"   • Person ID {person_id}, Contact {contact_id}: {name}")
    
    # Check if comprehensive_schema_sync created new Person records
    cursor.execute("""
        SELECT COUNT(*)
        FROM people p
        WHERE p.contact_id NOT IN (
            SELECT contact_id FROM people WHERE contact_id < 863
        )
    """)
    new_people = cursor.fetchone()[0]
    
    if new_people > 0:
        print(f"\n⚠️  Found {new_people} Person records with contact_id >= 863")
        cursor.execute("""
            SELECT p.contact_id, c.first_name, c.last_name
            FROM people p
            INNER JOIN contacts c ON p.contact_id = c.id
            WHERE p.contact_id >= 863
            ORDER BY p.contact_id
        """)
        new_records = cursor.fetchall()
        for contact_id, first_name, last_name in new_records:
            name = f"{first_name or ''} {last_name or ''}".strip() or "NO NAME"
            print(f"   • Contact {contact_id}: {name}")
    
    conn.close()

if __name__ == "__main__":
    check_new_people()