#!/usr/bin/env python
"""
Check why only 61 of 70 valid Person records show up in the list
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

def check_missing_nine():
    print("🔍 FINDING THE MISSING 9 PEOPLE (70 total - 61 shown = 9 missing)")
    print("=" * 60)
    
    conn = get_supabase_connection()
    cursor = conn.cursor()
    
    # Get all 70 valid Person-Contact pairs
    cursor.execute("""
        SELECT p.contact_id, c.first_name, c.last_name, c.office_id, c.status, c.email
        FROM people p 
        INNER JOIN contacts c ON p.contact_id = c.id 
        WHERE c.type = 'person'
        ORDER BY p.contact_id
    """)
    all_people = cursor.fetchall()
    print(f"\n📊 Total valid Person-Contact records: {len(all_people)}")
    
    # Check for any with NULL office_id
    null_office_count = sum(1 for p in all_people if p[3] is None)
    print(f"   - With NULL office_id: {null_office_count}")
    
    # Check for any inactive status
    statuses = {}
    for person in all_people:
        status = person[4] or 'NULL'
        statuses[status] = statuses.get(status, 0) + 1
    
    print(f"\n📊 Status breakdown:")
    for status, count in statuses.items():
        print(f"   - {status}: {count}")
    
    # Check if any have special conditions that might exclude them
    print(f"\n🔍 Checking for exclusion conditions:")
    
    # Check for test accounts
    test_accounts = [p for p in all_people if 
                     'test' in (p[1] or '').lower() or 
                     'test' in (p[2] or '').lower() or
                     'test' in (p[5] or '').lower()]
    print(f"   - Test accounts: {len(test_accounts)}")
    if test_accounts:
        for p in test_accounts[:5]:
            print(f"     • Contact {p[0]}: {p[1]} {p[2]} ({p[5]})")
    
    # Check office breakdown of the 70
    office_breakdown = {}
    for person in all_people:
        office_id = person[3] or 'NULL'
        office_breakdown[office_id] = office_breakdown.get(office_id, 0) + 1
    
    print(f"\n🏢 Office breakdown of the 70 valid records:")
    for office_id, count in sorted(office_breakdown.items()):
        print(f"   - Office {office_id}: {count}")
    
    # Simulate what the API query might be doing
    print(f"\n🔍 Simulating API query conditions:")
    
    # Check if ordering by pk might cause issues
    cursor.execute("""
        SELECT COUNT(*)
        FROM people p 
        INNER JOIN contacts c ON p.contact_id = c.id 
        WHERE c.type = 'person'
        AND c.office_id IS NULL
    """)
    null_office = cursor.fetchone()[0]
    print(f"   - People with NULL office_id: {null_office}")
    
    # The list view might be filtering by office_id IS NOT NULL
    cursor.execute("""
        SELECT COUNT(*)
        FROM people p 
        INNER JOIN contacts c ON p.contact_id = c.id 
        WHERE c.type = 'person'
        AND c.office_id IS NOT NULL
    """)
    with_office = cursor.fetchone()[0]
    print(f"   - People with valid office_id: {with_office}")
    
    # Check specific office_id = 1 (US Office)
    cursor.execute("""
        SELECT COUNT(*)
        FROM people p 
        INNER JOIN contacts c ON p.contact_id = c.id 
        WHERE c.type = 'person'
        AND c.office_id = 1
    """)
    office_1_count = cursor.fetchone()[0]
    print(f"   - People in office_id = 1: {office_1_count}")
    
    # Get the 9 people who might be excluded
    print(f"\n🎯 The 9 missing people are likely those with NULL office_id:")
    cursor.execute("""
        SELECT p.contact_id, c.first_name, c.last_name, c.email, c.status
        FROM people p 
        INNER JOIN contacts c ON p.contact_id = c.id 
        WHERE c.type = 'person'
        AND c.office_id IS NULL
        LIMIT 10
    """)
    missing = cursor.fetchall()
    for contact_id, first_name, last_name, email, status in missing:
        print(f"   • Contact {contact_id}: {first_name} {last_name} ({email}) - Status: {status}")
    
    conn.close()

if __name__ == "__main__":
    check_missing_nine()