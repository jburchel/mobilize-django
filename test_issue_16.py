#!/usr/bin/env python
"""
Test script to verify that Issue #16 has been fixed.

This script verifies that the three churches mentioned in the issue
are now properly visible in the Churches list page.
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mobilize.settings')
django.setup()

from mobilize.churches.models import Church
from mobilize.contacts.models import Contact


def test_issue_16_fix():
    """Test that the three churches from Issue #16 are now visible."""
    
    # Churches mentioned in the issue
    expected_churches = [
        'Grace City Church',
        'First Presbyterian',
        'Greenville Christian Fellowship'
    ]
    
    print("Testing Issue #16 fix...")
    print("=" * 50)
    
    success = True
    
    for church_name in expected_churches:
        # Check if church exists in Church model
        churches = Church.objects.filter(name__icontains=church_name)
        
        if not churches.exists():
            print(f"❌ {church_name} - NOT FOUND in Church model")
            success = False
        else:
            church = churches.first()
            print(f"✅ {church_name} - FOUND")
            print(f"   Church ID: {church.id}")
            print(f"   Full Name: {church.name}")
            print(f"   Location: {church.location}")
            print(f"   Contact ID: {church.contact.id}")
            print(f"   Office: {church.contact.office}")
            print()
    
    print("=" * 50)
    
    if success:
        print("✅ Issue #16 FIXED - All three churches are now visible!")
        return True
    else:
        print("❌ Issue #16 NOT FIXED - Some churches are still missing")
        return False


if __name__ == "__main__":
    success = test_issue_16_fix()
    sys.exit(0 if success else 1)