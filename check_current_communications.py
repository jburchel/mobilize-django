#!/usr/bin/env python

import os
import sys
import django

# Add the project root to the Python path
sys.path.insert(0, '/Users/jimburchel/Developer-Playground/mobilize-django')

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mobilize.settings')
django.setup()

from mobilize.communications.models import Communication
from mobilize.contacts.models import Person
from mobilize.churches.models import Church
from django.db import models

def check_current_communications():
    print("CURRENT COMMUNICATIONS IN NEW DATABASE")
    print("=" * 50)
    
    # Total count
    total_count = Communication.objects.count()
    print(f"Total communications: {total_count}")
    print()
    
    # By type
    print("Communications by type:")
    type_counts = Communication.objects.values('type').annotate(count=models.Count('type')).order_by('type')
    for item in type_counts:
        print(f"  {item['type']}: {item['count']}")
    print()
    
    # By direction
    print("Communications by direction:")
    direction_counts = Communication.objects.values('direction').annotate(count=models.Count('direction')).order_by('direction')
    for item in direction_counts:
        print(f"  {item['direction']}: {item['count']}")
    print()
    
    # Recent communications
    print("Recent communications (last 10):")
    recent = Communication.objects.filter(type__isnull=False).order_by('-created_at')[:10]
    for comm in recent:
        print(f"  ID: {comm.id}, Type: {comm.type}, Message: '{comm.message[:50] if comm.message else 'N/A'}...', Date: {comm.date}")
    print()
    
    # Check for non-null types
    non_null_types = Communication.objects.exclude(type__isnull=True).exclude(type='').count()
    print(f"Communications with non-null types: {non_null_types}")
    
    # Check for Gmail synced communications
    gmail_synced = Communication.objects.exclude(gmail_message_id__isnull=True).exclude(gmail_message_id='').count()
    print(f"Gmail synced communications: {gmail_synced}")
    
    # Check contact relationships
    with_person = Communication.objects.exclude(person__isnull=True).count()
    with_church = Communication.objects.exclude(church__isnull=True).count()
    print(f"Communications with person: {with_person}")
    print(f"Communications with church: {with_church}")
    
    # Check for orphaned communications
    orphaned = Communication.objects.filter(person__isnull=True, church__isnull=True).count()
    print(f"Orphaned communications (no person or church): {orphaned}")

if __name__ == "__main__":
    check_current_communications()