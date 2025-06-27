#!/usr/bin/env python
"""
Check why pagination isn't working and all 71 people are showing at once
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

def check_pagination_issue():
    print("🔍 CHECKING PAGINATION ISSUE (71 people all showing at once)")
    print("=" * 60)
    
    conn = get_supabase_connection()
    cursor = conn.cursor()
    
    # Get current counts
    cursor.execute("""
        SELECT COUNT(*) 
        FROM people p 
        INNER JOIN contacts c ON p.contact_id = c.id 
        WHERE c.type = 'person'
    """)
    total_people = cursor.fetchone()[0]
    print(f"\n📊 Total valid Person-Contact records: {total_people}")
    
    # Check if there are any without office_id (which might affect filtering)
    cursor.execute("""
        SELECT COUNT(*) 
        FROM people p 
        INNER JOIN contacts c ON p.contact_id = c.id 
        WHERE c.type = 'person' AND c.office_id IS NULL
    """)
    null_office = cursor.fetchone()[0]
    print(f"   - With NULL office_id: {null_office}")
    
    # Simulate pagination query
    print(f"\n📄 Simulating pagination (25 per page):")
    
    # Page 1
    cursor.execute("""
        SELECT p.contact_id, c.first_name, c.last_name
        FROM people p 
        INNER JOIN contacts c ON p.contact_id = c.id 
        WHERE c.type = 'person'
        ORDER BY p.id
        LIMIT 25 OFFSET 0
    """)
    page1 = cursor.fetchall()
    print(f"   - Page 1 would have: {len(page1)} items")
    if page1:
        print(f"     First: Contact {page1[0][0]} - {page1[0][1]} {page1[0][2]}")
        print(f"     Last:  Contact {page1[-1][0]} - {page1[-1][1]} {page1[-1][2]}")
    
    # Page 2
    cursor.execute("""
        SELECT p.contact_id, c.first_name, c.last_name
        FROM people p 
        INNER JOIN contacts c ON p.contact_id = c.id 
        WHERE c.type = 'person'
        ORDER BY p.id
        LIMIT 25 OFFSET 25
    """)
    page2 = cursor.fetchall()
    print(f"   - Page 2 would have: {len(page2)} items")
    if page2:
        print(f"     First: Contact {page2[0][0]} - {page2[0][1]} {page2[0][2]}")
        print(f"     Last:  Contact {page2[-1][0]} - {page2[-1][1]} {page2[-1][2]}")
    
    # Page 3
    cursor.execute("""
        SELECT p.contact_id, c.first_name, c.last_name
        FROM people p 
        INNER JOIN contacts c ON p.contact_id = c.id 
        WHERE c.type = 'person'
        ORDER BY p.id
        LIMIT 25 OFFSET 50
    """)
    page3 = cursor.fetchall()
    print(f"   - Page 3 would have: {len(page3)} items")
    if page3:
        print(f"     First: Contact {page3[0][0]} - {page3[0][1]} {page3[0][2]}")
        if len(page3) > 0:
            print(f"     Last:  Contact {page3[-1][0]} - {page3[-1][1]} {page3[-1][2]}")
    
    # Check if ordering by pk vs id matters
    print(f"\n🔍 Checking ordering difference (pk vs id):")
    
    cursor.execute("""
        SELECT p.id, p.contact_id
        FROM people p 
        INNER JOIN contacts c ON p.contact_id = c.id 
        WHERE c.type = 'person'
        ORDER BY p.id
        LIMIT 5
    """)
    by_id = cursor.fetchall()
    print(f"   Order by p.id:")
    for pid, cid in by_id:
        print(f"     Person.id={pid}, contact_id={cid}")
    
    cursor.execute("""
        SELECT p.id, p.contact_id
        FROM people p 
        INNER JOIN contacts c ON p.contact_id = c.id 
        WHERE c.type = 'person'
        ORDER BY p.contact_id
        LIMIT 5
    """)
    by_contact_id = cursor.fetchall()
    print(f"   Order by p.contact_id:")
    for pid, cid in by_contact_id:
        print(f"     Person.id={pid}, contact_id={cid}")
    
    # Check for any recent names that still show "No name listed"
    cursor.execute("""
        SELECT p.contact_id, c.first_name, c.last_name
        FROM people p 
        INNER JOIN contacts c ON p.contact_id = c.id 
        WHERE c.type = 'person'
        AND (c.first_name IS NULL OR c.first_name = '' OR 
             c.last_name IS NULL OR c.last_name = '')
        ORDER BY p.contact_id DESC
        LIMIT 10
    """)
    no_names = cursor.fetchall()
    
    if no_names:
        print(f"\n⚠️  Still have {len(no_names)} people with no names:")
        for cid, first, last in no_names:
            print(f"     Contact {cid}: '{first}' '{last}'")
    else:
        print(f"\n✅ All people have names now!")
    
    conn.close()

if __name__ == "__main__":
    check_pagination_issue()