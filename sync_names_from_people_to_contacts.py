#!/usr/bin/env python
"""
Script to sync real names from people table to contacts table.
This fixes the "No name listed" issue by copying real names from people to contacts.
"""

import os
import sys
import django

# Setup Django
sys.path.append('/Users/jimburchel/Developer-Playground/mobilize-django')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mobilize.settings')
django.setup()

from django.db import connection
from mobilize.contacts.models import Contact, Person

def sync_names_from_people_to_contacts():
    """Sync real names from people table to contacts table."""
    print("🔄 SYNCING NAMES FROM PEOPLE TO CONTACTS")
    print("=" * 50)
    
    # Find contacts with placeholder names that have real names in people table
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT 
                c.id,
                c.first_name as contact_first_name,
                c.last_name as contact_last_name,
                p.first_name as people_first_name,
                p.last_name as people_last_name
            FROM people p 
            JOIN contacts c ON p.contact_id = c.id 
            WHERE (c.first_name ~ '^Person [0-9]+$' OR c.first_name IS NULL OR c.first_name = '')
            AND (p.first_name IS NOT NULL AND p.first_name != '' AND p.first_name !~ '^Person [0-9]+$')
        """)
        
        records_to_update = cursor.fetchall()
    
    print(f"📊 Found {len(records_to_update)} contacts with placeholder names but real names in people table")
    
    if len(records_to_update) == 0:
        print("✅ No contacts need name updates!")
        return
    
    # Show some examples
    print("\n📋 Examples of contacts to update:")
    for i, record in enumerate(records_to_update[:5]):
        contact_id, contact_first, contact_last, people_first, people_last = record
        print(f"   • Contact {contact_id}: '{contact_first}' → '{people_first} {people_last}'")
    
    # Update contacts with real names from people table
    updated_count = 0
    print(f"\n🛠️  Updating {len(records_to_update)} contact names...")
    
    with connection.cursor() as cursor:
        for record in records_to_update:
            contact_id, contact_first, contact_last, people_first, people_last = record
            
            try:
                # Update the contact with real names from people table
                cursor.execute("""
                    UPDATE contacts 
                    SET first_name = %s, last_name = %s
                    WHERE id = %s
                """, [people_first or contact_first, people_last or contact_last, contact_id])
                
                updated_count += 1
                
                if updated_count <= 5:  # Show first 5 as examples
                    print(f"   ✅ Updated Contact {contact_id}: {people_first} {people_last}")
                    
            except Exception as e:
                print(f"   ❌ Error updating Contact {contact_id}: {e}")
    
    print(f"\n📈 RESULTS:")
    print(f"   • Updated {updated_count} contact records")
    print(f"   • Contacts with real names now: {Contact.objects.exclude(first_name__regex=r'^Person [0-9]+$').count()}")
    
    # Verify the fix
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT COUNT(*) 
            FROM people p 
            JOIN contacts c ON p.contact_id = c.id 
            WHERE c.first_name ~ '^Person [0-9]+$'
        """)
        remaining_placeholders = cursor.fetchone()[0]
    
    if remaining_placeholders == 0:
        print("   ✅ All placeholder names fixed! The 'No name listed' issue should be resolved.")
    else:
        print(f"   ⚠️  Still have {remaining_placeholders} contacts with placeholder names")
    
    print("\n🔄 After this fix:")
    print("   • Person list should show real names instead of 'No name listed'")
    print("   • Dashboard and person list counts should be consistent")

if __name__ == '__main__':
    sync_names_from_people_to_contacts()