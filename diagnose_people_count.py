#!/usr/bin/env python
"""
Diagnose the discrepancy between dashboard count (70) and list view count (61)
This script connects to Supabase to check production data
"""

import psycopg2
import os
from urllib.parse import urlparse
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_supabase_connection():
    """Get connection to Supabase database"""
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

def diagnose_counts():
    print("🔍 DIAGNOSING SUPABASE PEOPLE COUNT DISCREPANCY")
    print("=" * 60)
    
    conn = get_supabase_connection()
    cursor = conn.cursor()
    
    # 1. Check total counts in database
    print("\n📊 SUPABASE DATABASE COUNTS:")
    
    # Count contacts of type 'person'
    cursor.execute("SELECT COUNT(*) FROM contacts WHERE type = 'person'")
    person_contacts = cursor.fetchone()[0]
    print(f"   - Contacts with type='person': {person_contacts}")
    
    # Count Person model records
    cursor.execute("SELECT COUNT(*) FROM people")
    person_records = cursor.fetchone()[0]
    print(f"   - People table records: {person_records}")
    
    # Count valid person-contact joins
    cursor.execute("""
        SELECT COUNT(*) 
        FROM people p 
        INNER JOIN contacts c ON p.contact_id = c.id 
        WHERE c.type = 'person'
    """)
    valid_joins = cursor.fetchone()[0]
    print(f"   - Valid Person-Contact joins: {valid_joins}")
    
    # 2. Check for orphaned records
    print("\n🔍 CHECKING FOR DATA ISSUES:")
    
    # Contacts without Person records
    cursor.execute("""
        SELECT COUNT(*) 
        FROM contacts c
        LEFT JOIN people p ON c.id = p.contact_id
        WHERE c.type = 'person' AND p.contact_id IS NULL
    """)
    contacts_without_person = cursor.fetchone()[0]
    print(f"   - Person contacts without Person record: {contacts_without_person}")
    
    if contacts_without_person > 0:
        # Show some examples
        cursor.execute("""
            SELECT c.id, c.first_name, c.last_name, c.office_id
            FROM contacts c
            LEFT JOIN people p ON c.id = p.contact_id
            WHERE c.type = 'person' AND p.contact_id IS NULL
            LIMIT 5
        """)
        examples = cursor.fetchall()
        print("     Examples:")
        for contact_id, first_name, last_name, office_id in examples:
            print(f"     • Contact {contact_id}: {first_name} {last_name} (office_id: {office_id})")
    
    # Person records without valid contacts
    cursor.execute("""
        SELECT COUNT(*) 
        FROM people p 
        LEFT JOIN contacts c ON p.contact_id = c.id 
        WHERE c.id IS NULL
    """)
    orphaned_people = cursor.fetchone()[0]
    print(f"   - Person records without valid Contact: {orphaned_people}")
    
    # 3. Check office distribution
    print("\n🏢 OFFICE DISTRIBUTION:")
    
    # Count by office
    cursor.execute("""
        SELECT o.name, COUNT(c.id) as count
        FROM contacts c
        LEFT JOIN admin_panel_office o ON c.office_id = o.id
        WHERE c.type = 'person'
        GROUP BY o.name
        ORDER BY count DESC
    """)
    office_counts = cursor.fetchall()
    
    total_counted = 0
    for office_name, count in office_counts:
        office_name = office_name or 'No Office'
        total_counted += count
        print(f"   - {office_name}: {count}")
    
    # 4. Check what the dashboard vs list view would show
    print("\n📊 DASHBOARD VS LIST VIEW SIMULATION:")
    
    # Dashboard typically counts all person contacts
    cursor.execute("SELECT COUNT(*) FROM contacts WHERE type = 'person'")
    dashboard_count = cursor.fetchone()[0]
    print(f"   - Dashboard count (all person contacts): {dashboard_count}")
    
    # List view counts Person records with valid joins
    cursor.execute("""
        SELECT COUNT(DISTINCT p.contact_id) 
        FROM people p 
        INNER JOIN contacts c ON p.contact_id = c.id 
        WHERE c.type = 'person'
    """)
    list_view_count = cursor.fetchone()[0]
    print(f"   - List view count (valid Person-Contact joins): {list_view_count}")
    
    # Check if there are Person records with issues
    cursor.execute("""
        SELECT COUNT(*) 
        FROM people p 
        WHERE p.contact_id IS NULL OR p.contact_id = 0
    """)
    people_without_contact_id = cursor.fetchone()[0]
    print(f"   - Person records with NULL/0 contact_id: {people_without_contact_id}")
    
    # 5. Specific analysis for the 70 vs 61 discrepancy
    print("\n🎯 SPECIFIC ANALYSIS (70 vs 61):")
    
    # Check if specific office filtering could explain it
    cursor.execute("""
        SELECT office_id, COUNT(*) as count
        FROM contacts 
        WHERE type = 'person'
        GROUP BY office_id
        ORDER BY count DESC
    """)
    office_breakdown = cursor.fetchall()
    
    print("   Office ID breakdown:")
    for office_id, count in office_breakdown:
        print(f"   - Office {office_id}: {count} people")
    
    # Check if some contacts are missing Person records
    cursor.execute("""
        SELECT c.id, c.first_name, c.last_name, c.created_at
        FROM contacts c
        LEFT JOIN people p ON c.id = p.contact_id
        WHERE c.type = 'person' 
        AND p.contact_id IS NULL
        ORDER BY c.created_at DESC
        LIMIT 10
    """)
    missing_people = cursor.fetchall()
    
    if missing_people:
        print(f"\n   ⚠️  Found contacts without Person records (showing up to 10):")
        for contact_id, first_name, last_name, created_at in missing_people:
            print(f"      • Contact {contact_id}: {first_name} {last_name} (created: {created_at})")
        
        # Count total missing
        cursor.execute("""
            SELECT COUNT(*)
            FROM contacts c
            LEFT JOIN people p ON c.id = p.contact_id
            WHERE c.type = 'person' 
            AND p.contact_id IS NULL
        """)
        total_missing = cursor.fetchone()[0]
        print(f"\n   Total contacts missing Person records: {total_missing}")
        print(f"   This could explain the difference: {person_contacts} contacts - {total_missing} missing = {person_contacts - total_missing}")
    
    conn.close()

if __name__ == "__main__":
    diagnose_counts()