#!/usr/bin/env python
"""
Debug script to identify why queryset evaluation is failing
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mobilize.settings')
sys.path.append('/Users/jimburchel/Developer-Playground/mobilize-django')
django.setup()

from django.db import connection
from mobilize.contacts.models import Person, Contact
from mobilize.authentication.models import User
from mobilize.authentication.decorators import office_data_filter

print("🔍 Deep debugging queryset evaluation issue...")

try:
    # Get raw counts first
    with connection.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM people;")
        raw_people_count = cursor.fetchone()[0]
        print(f"📊 Raw people count: {raw_people_count}")
        
        cursor.execute("SELECT COUNT(*) FROM contacts WHERE type = 'person';")
        raw_contacts_count = cursor.fetchone()[0]
        print(f"📊 Raw person contacts count: {raw_contacts_count}")
        
        # Check for any broken foreign key relationships
        cursor.execute("""
            SELECT COUNT(*) FROM people p 
            LEFT JOIN contacts c ON p.contact_id = c.id 
            WHERE c.id IS NULL;
        """)
        broken_fk_count = cursor.fetchone()[0]
        print(f"📊 People with broken contact FK: {broken_fk_count}")
        
        # Check people table structure first
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'people'
            ORDER BY ordinal_position;
        """)
        people_columns = cursor.fetchall()
        print(f"📋 People table columns:")
        for col_name, col_type in people_columns:
            print(f"   {col_name}: {col_type}")
        
        # Check specific record examples with correct column names
        cursor.execute("""
            SELECT contact_id, title, profession, organization
            FROM people 
            LIMIT 5;
        """)
        raw_samples = cursor.fetchall()
        print(f"📋 Raw sample people records:")
        for contact_id, title, profession, organization in raw_samples:
            print(f"   contact_id={contact_id}, title={title}, profession={profession}, org={organization}")

    # Test Django ORM step by step
    print(f"\n🔧 Testing Django ORM step by step...")
    
    # Step 1: Basic Person queryset
    people_basic = Person.objects.all()
    print(f"1. Person.objects.all().count(): {people_basic.count()}")
    
    # Step 2: Add select_related
    people_related = Person.objects.select_related('contact')
    print(f"2. With select_related('contact').count(): {people_related.count()}")
    
    # Step 3: Add office select_related
    people_office = Person.objects.select_related('contact', 'contact__office')
    print(f"3. With contact__office.count(): {people_office.count()}")
    
    # Step 4: Test evaluation
    try:
        first_person = people_basic.first()
        if first_person:
            print(f"4. First person found!")
            print(f"   PK: {first_person.pk}")
            print(f"   Contact ID: {first_person.contact_id}")
            print(f"   Has ID attr: {hasattr(first_person, 'id')}")
            try:
                contact = first_person.contact
                print(f"   Contact name: {contact.first_name} {contact.last_name}")
            except Exception as e:
                print(f"   ❌ Error accessing contact: {e}")
        else:
            print(f"4. ❌ No first person found")
    except Exception as e:
        print(f"4. ❌ Error getting first person: {e}")
    
    # Step 5: Test with list conversion
    try:
        people_list = list(people_basic[:3])
        print(f"5. list(people_basic[:3]): {len(people_list)} items")
        for i, person in enumerate(people_list):
            print(f"   Person {i+1}: PK={person.pk}, Contact ID={person.contact_id}")
    except Exception as e:
        print(f"5. ❌ Error converting to list: {e}")
        import traceback
        print(f"   Full traceback: {traceback.format_exc()}")
    
    # Step 6: Test the exact API queryset
    print(f"\n🎯 Testing exact API queryset...")
    try:
        people = Person.objects.select_related(
            'contact', 
            'contact__office',
            'primary_church'
        ).prefetch_related(
            'contact__pipeline_entries__current_stage'
        )
        print(f"6. API queryset count: {people.count()}")
        
        people_ordered = people.order_by('-pk')
        print(f"7. With order_by('-pk'): {people_ordered.count()}")
        
        people_sliced = list(people_ordered[:3])
        print(f"8. Sliced and converted to list: {len(people_sliced)} items")
        
    except Exception as e:
        print(f"6-8. ❌ Error with API queryset: {e}")
        import traceback
        print(f"   Full traceback: {traceback.format_exc()}")

    # Step 7: Check if specific relationships are causing issues
    print(f"\n🔍 Testing individual relationship fields...")
    try:
        # Test without primary_church
        people_no_church = Person.objects.select_related('contact', 'contact__office')
        print(f"9. Without primary_church: {people_no_church.count()}")
        test_list = list(people_no_church[:3])
        print(f"   Converted to list: {len(test_list)} items")
        
    except Exception as e:
        print(f"9. ❌ Error without primary_church: {e}")
    
    try:
        # Test without prefetch_related
        people_no_prefetch = Person.objects.select_related('contact', 'contact__office', 'primary_church')
        print(f"10. Without prefetch_related: {people_no_prefetch.count()}")
        test_list = list(people_no_prefetch[:3])
        print(f"    Converted to list: {len(test_list)} items")
        
    except Exception as e:
        print(f"10. ❌ Error without prefetch_related: {e}")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()