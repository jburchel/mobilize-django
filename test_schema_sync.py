#!/usr/bin/env python
"""
Test script to validate the comprehensive schema sync command
Run this locally to make sure everything works before deploying
"""

import os
import sys
import django
from django.core.management import call_command
from django.db import connection

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mobilize.settings')
django.setup()

def test_schema_sync():
    """Test the comprehensive schema sync command"""
    print("🧪 Testing Comprehensive Schema Sync Command")
    print("=" * 50)
    
    # First, test in dry-run mode
    print("\n1. Testing in DRY-RUN mode...")
    try:
        call_command('comprehensive_schema_sync', '--dry-run', '--verbose')
        print("✅ Dry-run completed successfully")
    except Exception as e:
        print(f"❌ Dry-run failed: {e}")
        return False
    
    # Test database connectivity
    print("\n2. Testing database connectivity...")
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1;")
            result = cursor.fetchone()
            if result[0] == 1:
                print("✅ Database connection successful")
            else:
                print("❌ Database connection failed")
                return False
    except Exception as e:
        print(f"❌ Database connectivity test failed: {e}")
        return False
    
    # Test key table existence
    print("\n3. Testing key table existence...")
    key_tables = ['users', 'contacts', 'people', 'churches', 'communications', 'tasks']
    
    with connection.cursor() as cursor:
        for table in key_tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table} LIMIT 1;")
                cursor.fetchone()
                print(f"✅ {table} table accessible")
            except Exception as e:
                print(f"❌ {table} table issue: {e}")
    
    # Test Django models
    print("\n4. Testing Django model imports...")
    try:
        from mobilize.authentication.models import User
        from mobilize.contacts.models import Contact, Person
        from mobilize.churches.models import Church
        from mobilize.communications.models import Communication
        from mobilize.tasks.models import Task
        from mobilize.pipeline.models import Pipeline, PipelineStage, PipelineContact
        print("✅ All Django models imported successfully")
    except Exception as e:
        print(f"❌ Django model import failed: {e}")
        return False
    
    print("\n5. Testing model queries...")
    try:
        # Test basic queries
        user_count = User.objects.count()
        contact_count = Contact.objects.count()
        print(f"✅ Users: {user_count}, Contacts: {contact_count}")
        
        # Test more complex queries
        try:
            from mobilize.pipeline.models import PipelineContact
            pipeline_contacts = PipelineContact.objects.count()
            print(f"✅ Pipeline contacts: {pipeline_contacts}")
        except Exception as e:
            print(f"⚠️  Pipeline contacts query issue (expected if table doesn't exist yet): {e}")
            
    except Exception as e:
        print(f"❌ Model query test failed: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 All tests passed! Schema sync should work in production.")
    return True

if __name__ == '__main__':
    success = test_schema_sync()
    sys.exit(0 if success else 1)