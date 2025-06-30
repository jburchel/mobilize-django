#!/usr/bin/env python
"""
Script to fix data integrity between contacts and people tables.
This script creates missing Person records for orphaned person-type contacts.
"""

import os
import sys
import django

# Add the project root to Python path
sys.path.append('/Users/jimburchel/Developer-Playground/mobilize-django')

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mobilize.settings')
django.setup()

from django.db import connection
from mobilize.contacts.models import Contact, Person

def fix_person_data_integrity():
    """Fix missing Person records for person-type contacts."""
    print("🔧 FIXING PERSON DATA INTEGRITY")
    print("=" * 50)
    
    # Find orphaned contacts
    orphaned_contacts = Contact.objects.filter(
        type='person'
    ).exclude(
        id__in=Person.objects.values_list('contact_id', flat=True)
    )
    
    print(f"📊 Found {orphaned_contacts.count()} orphaned person-type contacts")
    
    if orphaned_contacts.count() == 0:
        print("✅ No orphaned contacts found. Data integrity is good!")
        return
    
    # Show some examples
    print("\n📋 Examples of orphaned contacts:")
    for contact in orphaned_contacts[:5]:
        print(f"   • Contact {contact.id}: {contact.first_name} {contact.last_name} (Office: {contact.office})")
    
    # Use raw SQL to insert Person records since Django model doesn't match Supabase schema
    print(f"\n🛠️  Creating {orphaned_contacts.count()} Person records...")
    
    with connection.cursor() as cursor:
        # Get the list of orphaned contact IDs
        orphaned_ids = list(orphaned_contacts.values_list('id', flat=True))
        
        created_count = 0
        for contact_id in orphaned_ids:
            try:
                # Insert into people table with id=contact_id and contact_id=contact_id
                cursor.execute("""
                    INSERT INTO people (id, contact_id)
                    VALUES (%s, %s)
                """, [contact_id, contact_id])
                created_count += 1
                
                if created_count <= 5:  # Show first 5 as examples
                    contact = Contact.objects.get(id=contact_id)
                    print(f"   ✅ Created Person {contact_id} for Contact {contact_id}: {contact.first_name} {contact.last_name}")
                    
            except Exception as e:
                print(f"   ❌ Error creating Person for Contact {contact_id}: {e}")
    
    print(f"\n📈 RESULTS:")
    print(f"   • Created {created_count} Person records")
    print(f"   • Total Person records now: {Person.objects.count()}")
    print(f"   • Total person-type Contacts: {Contact.objects.filter(type='person').count()}")
    
    # Verify data integrity
    remaining_orphaned = Contact.objects.filter(
        type='person'
    ).exclude(
        id__in=Person.objects.values_list('contact_id', flat=True)
    ).count()
    
    if remaining_orphaned == 0:
        print("   ✅ Data integrity fixed! All person-type contacts now have Person records.")
    else:
        print(f"   ⚠️  Still have {remaining_orphaned} orphaned contacts")

if __name__ == '__main__':
    fix_person_data_integrity()