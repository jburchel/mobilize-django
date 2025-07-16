#!/usr/bin/env python
"""
Check communications in the new database to understand current state.
"""
import os
import django
from collections import defaultdict
from datetime import datetime
from django.db import models

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mobilize.settings')
django.setup()

from mobilize.communications.models import Communication
from mobilize.contacts.models import Person, Contact
from mobilize.churches.models import Church

def check_new_database_communications():
    """Check all communications in new database"""
    print("=" * 80)
    print("CHECKING NEW DATABASE COMMUNICATIONS")
    print("=" * 80)
    
    # Get all communication types and counts
    all_communications = Communication.objects.all()
    print(f"Total communications in database: {all_communications.count()}")
    
    # Group by type
    type_counts = defaultdict(int)
    for comm in all_communications:
        type_counts[comm.type or 'Unknown'] += 1
    
    print("\nCommunication Types and Counts:")
    print("-" * 50)
    for comm_type, count in sorted(type_counts.items()):
        print(f"{comm_type}: {count}")
    
    # Check non-email communications specifically
    non_email_types = ['text', 'Text Message', 'video', 'Video Call', 'phone', 'Phone Call', 'meeting', 'Meeting']
    non_email_comms = Communication.objects.filter(type__in=non_email_types)
    print(f"\nNon-email communications: {non_email_comms.count()}")
    
    # Check for communications without a type
    no_type_comms = Communication.objects.filter(type__isnull=True)
    print(f"Communications without type: {no_type_comms.count()}")
    
    # Check communications by contact (using person and church fields)
    comms_with_person = Communication.objects.exclude(person__isnull=True)
    comms_with_church = Communication.objects.exclude(church__isnull=True)
    comms_with_contact = Communication.objects.filter(
        models.Q(person__isnull=False) | models.Q(church__isnull=False)
    )
    comms_without_contact = Communication.objects.filter(
        person__isnull=True, church__isnull=True
    )
    
    print(f"\nCommunications with person: {comms_with_person.count()}")
    print(f"Communications with church: {comms_with_church.count()}")
    print(f"Communications with any contact: {comms_with_contact.count()}")
    print(f"Communications without any contact: {comms_without_contact.count()}")
    
    # Sample some communications
    print("\nSample communications:")
    print("-" * 50)
    
    sample_comms = Communication.objects.all()[:10]
    for comm in sample_comms:
        contact_name = "No Contact"
        if comm.person:
            contact_name = f"{comm.person.contact.first_name} {comm.person.contact.last_name}" if comm.person.contact.first_name and comm.person.contact.last_name else str(comm.person)
        elif comm.church:
            contact_name = comm.church.name or comm.church.contact.church_name or str(comm.church)
        
        print(f"ID: {comm.id}, Type: {comm.type}, Contact: {contact_name}, Date: {comm.date}, Subject: {comm.subject[:50] if comm.subject else 'No subject'}")
    
    # Check for recently created communications (potential migrations)
    from django.utils import timezone
    from datetime import timedelta
    
    recent_comms = Communication.objects.filter(
        created_at__gte=timezone.now() - timedelta(days=7)
    )
    print(f"\nCommunications created in last 7 days: {recent_comms.count()}")
    
    # Group recent communications by type
    recent_type_counts = defaultdict(int)
    for comm in recent_comms:
        recent_type_counts[comm.type or 'Unknown'] += 1
    
    if recent_type_counts:
        print("\nRecent communication types:")
        for comm_type, count in sorted(recent_type_counts.items()):
            print(f"  {comm_type}: {count}")
    
    # Check for any fields that might indicate migration source
    migration_indicators = []
    
    # Look for patterns in subjects or content that might indicate migration
    sample_large = Communication.objects.all()[:100]
    for comm in sample_large:
        if comm.subject and ('migrated' in comm.subject.lower() or 'import' in comm.subject.lower()):
            migration_indicators.append(comm)
    
    if migration_indicators:
        print(f"\nFound {len(migration_indicators)} communications with migration indicators")
    
    return type_counts, comms_with_contact.count(), comms_without_contact.count()

def check_contact_migration_status():
    """Check how many contacts we have and their sources"""
    print("\n" + "=" * 80)
    print("CHECKING CONTACT MIGRATION STATUS")
    print("=" * 80)
    
    # Check total contacts
    total_contacts = Contact.objects.count()
    person_contacts = Contact.objects.filter(type='person').count()
    church_contacts = Contact.objects.filter(type='church').count()
    
    print(f"Total contacts: {total_contacts}")
    print(f"Person contacts: {person_contacts}")
    print(f"Church contacts: {church_contacts}")
    
    # Check for recent contacts
    from django.utils import timezone
    from datetime import timedelta
    
    recent_contacts = Contact.objects.filter(
        created_at__gte=timezone.now() - timedelta(days=7)
    )
    
    print(f"\nContacts created in last 7 days: {recent_contacts.count()}")
    
    # Check people and churches
    total_people = Person.objects.count()
    total_churches = Church.objects.count()
    
    print(f"\nPeople records: {total_people}")
    print(f"Church records: {total_churches}")
    
    # Sample some contacts
    print("\nSample contacts:")
    print("-" * 50)
    
    sample_contacts = Contact.objects.all()[:10]
    for contact in sample_contacts:
        name = f"{contact.first_name} {contact.last_name}" if contact.first_name and contact.last_name else contact.church_name or f"Contact {contact.id}"
        print(f"ID: {contact.id}, Type: {contact.type}, Name: {name}, Email: {contact.email or 'No email'}, Created: {contact.created_at}")

def main():
    """Main verification function"""
    print("COMMUNICATIONS AND CONTACTS VERIFICATION")
    print("=" * 80)
    print(f"Verification started at: {datetime.now()}")
    print()
    
    try:
        # Check communications
        type_counts, with_contact, without_contact = check_new_database_communications()
        
        # Check contacts
        check_contact_migration_status()
        
        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)
        
        total_comms = sum(type_counts.values())
        print(f"Total communications: {total_comms}")
        print(f"Communications with contacts: {with_contact}")
        print(f"Communications without contacts: {without_contact}")
        
        non_email_types = ['text', 'Text Message', 'video', 'Video Call', 'phone', 'Phone Call', 'meeting', 'Meeting']
        non_email_count = sum(count for comm_type, count in type_counts.items() if comm_type in non_email_types)
        print(f"Non-email communications: {non_email_count}")
        
        print(f"\nVerification completed at: {datetime.now()}")
        
    except Exception as e:
        print(f"Error during verification: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()