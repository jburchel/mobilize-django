#!/usr/bin/env python
"""
Debug script to check user office assignments and data types
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mobilize.settings')
sys.path.append('/Users/jimburchel/Developer-Playground/mobilize-django')
django.setup()

from django.db import connection
from mobilize.authentication.models import User

print("🔍 Debugging user office assignments...")

# Check your super admin user
try:
    user = User.objects.get(email='j.burchel@crossoverglobal.net')
    print(f"\n✅ Found user: {user.email}")
    print(f"   Role: {user.role}")
    print(f"   ID: {user.id}")
    print(f"   Type of ID: {type(user.id)}")
    
    # Check office assignments
    print(f"\n🏢 Office assignments:")
    office_assignments = user.useroffice_set.all()
    print(f"   Count: {office_assignments.count()}")
    
    for assignment in office_assignments:
        print(f"   - Office ID: {assignment.office_id} (Type: {type(assignment.office_id)})")
        print(f"     Is Primary: {assignment.is_primary}")
        print(f"     Office Name: {assignment.office.name}")
    
    # Check raw database data
    with connection.cursor() as cursor:
        print(f"\n📊 Raw database check:")
        
        # Check user_offices table structure
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'user_offices';
        """)
        columns = cursor.fetchall()
        print(f"   user_offices table columns:")
        for col_name, col_type in columns:
            print(f"     {col_name}: {col_type}")
        
        # Check actual data in user_offices for this user
        cursor.execute("""
            SELECT user_id, office_id, is_primary 
            FROM user_offices 
            WHERE user_id = %s;
        """, [str(user.id)])
        
        raw_assignments = cursor.fetchall()
        print(f"\n   Raw user_offices data for user {user.id}:")
        for user_id, office_id, is_primary in raw_assignments:
            print(f"     user_id: {user_id} (type: {type(user_id)})")
            print(f"     office_id: {office_id} (type: {type(office_id)})")
            print(f"     is_primary: {is_primary}")

except User.DoesNotExist:
    print("❌ User j.burchel@crossoverglobal.net not found")
except Exception as e:
    print(f"❌ Error: {e}")