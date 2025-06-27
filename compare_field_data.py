#!/usr/bin/env python3
"""
Field Data Comparison Script - Render vs Supabase

This script compares field values between matching records in your Render and Supabase databases
to identify missing or incomplete data in the migration.

Usage: python compare_field_data.py
"""

import os
import psycopg2
from psycopg2.extras import DictCursor
import json
from datetime import datetime

# Render Database Configuration
RENDER_DB_CONFIG = {
    'host': 'dpg-cr6f1ei3esus73cnh1d0-a.oregon-postgres.render.com',
    'port': '5432',
    'database': 'mobilize',
    'user': 'jimburchel',
    'password': '1JmxPgDNQsk9UxDI7PdKXgF0PC4v1fiY'
}

# Supabase Database Configuration
SUPABASE_DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'port': os.getenv('DB_PORT', '5432'),
    'database': os.getenv('DB_NAME'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD')
}

def connect_to_db(config, db_name):
    """Create a database connection"""
    try:
        conn = psycopg2.connect(
            host=config['host'],
            port=config['port'],
            database=config['database'],
            user=config['user'],
            password=config['password']
        )
        print(f"✓ Connected to {db_name} database")
        return conn
    except Exception as e:
        print(f"✗ Failed to connect to {db_name} database: {e}")
        return None

def get_church_field_comparison(render_conn, supabase_conn):
    """Compare church field data between databases"""
    print("\n🏛️ Comparing Church Field Data...")
    
    render_cursor = render_conn.cursor(cursor_factory=DictCursor)
    supabase_cursor = supabase_conn.cursor(cursor_factory=DictCursor)
    
    try:
        # Get church data from Render
        render_cursor.execute("""
            SELECT 
                cc.id as contact_id,
                cc.church_name,
                cc.first_name,
                cc.last_name,
                cc.email,
                cc.phone,
                cc.street_address,
                cc.city,
                cc.state,
                cc.zip_code,
                ch.senior_pastor_first_name,
                ch.senior_pastor_last_name,
                ch.senior_pastor_phone,
                ch.senior_pastor_email,
                ch.missions_pastor_first_name,
                ch.missions_pastor_last_name,
                ch.mission_pastor_phone,
                ch.mission_pastor_email,
                ch.denomination,
                ch.website,
                ch.congregation_size,
                ch.weekly_attendance,
                ch.year_founded,
                ch.info_given,
                ch.church_pipeline,
                ch.priority
            FROM contacts_contact cc
            JOIN contacts_church ch ON cc.id = ch.contact_ptr_id
            WHERE cc.church_name IS NOT NULL AND cc.church_name != ''
            ORDER BY cc.church_name
        """)
        
        render_churches = render_cursor.fetchall()
        print(f"   Found {len(render_churches)} churches in Render")
        
        field_gaps = []
        matches_found = 0
        
        for render_church in render_churches:
            # Find matching church in Supabase by name
            supabase_cursor.execute("""
                SELECT 
                    c.id,
                    c.church_name,
                    c.first_name,
                    c.last_name,
                    c.email,
                    c.phone,
                    c.street_address,
                    c.city,
                    c.state,
                    c.zip_code,
                    ch.name as church_name_alt,
                    ch.denomination,
                    ch.website,
                    ch.congregation_size,
                    ch.weekly_attendance,
                    ch.year_founded,
                    ch.pastor_first_name,
                    ch.pastor_last_name,
                    ch.pastor_phone,
                    ch.pastor_email,
                    ch.info_given,
                    ch.church_pipeline,
                    c.priority
                FROM contacts c
                LEFT JOIN churches ch ON c.id = ch.contact_id
                WHERE (c.church_name ILIKE %s OR ch.name ILIKE %s)
                AND c.type = 'church'
                LIMIT 1
            """, (render_church['church_name'], render_church['church_name']))
            
            supabase_church = supabase_cursor.fetchone()
            
            if supabase_church:
                matches_found += 1
                
                # Compare fields and identify gaps
                missing_fields = []
                
                # Map Render fields to Supabase fields for comparison
                field_mappings = [
                    ('senior_pastor_first_name', 'pastor_first_name', 'Pastor First Name'),
                    ('senior_pastor_last_name', 'pastor_last_name', 'Pastor Last Name'),
                    ('senior_pastor_phone', 'pastor_phone', 'Pastor Phone'),
                    ('senior_pastor_email', 'pastor_email', 'Pastor Email'),
                    ('denomination', 'denomination', 'Denomination'),
                    ('website', 'website', 'Website'),
                    ('congregation_size', 'congregation_size', 'Congregation Size'),
                    ('weekly_attendance', 'weekly_attendance', 'Weekly Attendance'),
                    ('year_founded', 'year_founded', 'Year Founded'),
                    ('info_given', 'info_given', 'Info Given'),
                    ('church_pipeline', 'church_pipeline', 'Church Pipeline'),
                    ('priority', 'priority', 'Priority'),
                    ('street_address', 'street_address', 'Street Address'),
                    ('city', 'city', 'City'),
                    ('state', 'state', 'State'),
                    ('zip_code', 'zip_code', 'ZIP Code'),
                    ('phone', 'phone', 'Phone'),
                    ('email', 'email', 'Email')
                ]
                
                for render_field, supabase_field, display_name in field_mappings:
                    render_value = render_church.get(render_field)
                    supabase_value = supabase_church.get(supabase_field)
                    
                    # Check if Render has data but Supabase doesn't
                    if render_value and render_value.strip() and (not supabase_value or not supabase_value.strip()):
                        missing_fields.append({
                            'field': display_name,
                            'render_value': render_value,
                            'supabase_value': supabase_value
                        })
                
                if missing_fields:
                    field_gaps.append({
                        'church_name': render_church['church_name'],
                        'render_id': render_church['contact_id'],
                        'supabase_id': supabase_church['id'],
                        'missing_fields': missing_fields
                    })
        
        print(f"   Matched {matches_found} churches between databases")
        print(f"   Found {len(field_gaps)} churches with missing field data")
        
        return field_gaps
        
    except Exception as e:
        print(f"Error comparing church fields: {e}")
        return []
    finally:
        render_cursor.close()
        supabase_cursor.close()

def get_people_field_comparison(render_conn, supabase_conn):
    """Compare people field data between databases"""
    print("\n👥 Comparing People Field Data...")
    
    render_cursor = render_conn.cursor(cursor_factory=DictCursor)
    supabase_cursor = supabase_conn.cursor(cursor_factory=DictCursor)
    
    try:
        # Get people data from Render
        render_cursor.execute("""
            SELECT 
                cc.id as contact_id,
                cc.first_name,
                cc.last_name,
                cc.email,
                cc.phone,
                cc.street_address,
                cc.city,
                cc.state,
                cc.zip_code,
                cp.home_country,
                cp.marital_status,
                cp.people_pipeline,
                cp.priority,
                cp.assigned_to,
                cp.source,
                cp.referred_by,
                cp.info_given,
                cp.spouse_first_name,
                cp.spouse_last_name,
                cp.birthday,
                cp.anniversary,
                cp.profession,
                cp.organization
            FROM contacts_contact cc
            JOIN contacts_people cp ON cc.id = cp.contact_ptr_id
            WHERE cc.first_name IS NOT NULL AND cc.first_name != ''
            ORDER BY cc.last_name, cc.first_name
        """)
        
        render_people = render_cursor.fetchall()
        print(f"   Found {len(render_people)} people in Render")
        
        field_gaps = []
        matches_found = 0
        
        for render_person in render_people:
            # Find matching person in Supabase by name and email
            supabase_cursor.execute("""
                SELECT 
                    c.id,
                    c.first_name,
                    c.last_name,
                    c.email,
                    c.phone,
                    c.street_address,
                    c.city,
                    c.state,
                    c.zip_code,
                    c.priority,
                    p.home_country,
                    p.marital_status,
                    p.spouse_first_name,
                    p.spouse_last_name,
                    p.birthday,
                    p.anniversary,
                    p.profession,
                    p.organization
                FROM contacts c
                LEFT JOIN people p ON c.id = p.contact_id
                WHERE c.type = 'person'
                AND (
                    (c.email = %s AND c.email IS NOT NULL) OR
                    (c.first_name ILIKE %s AND c.last_name ILIKE %s)
                )
                LIMIT 1
            """, (render_person['email'], render_person['first_name'], render_person['last_name']))
            
            supabase_person = supabase_cursor.fetchone()
            
            if supabase_person:
                matches_found += 1
                
                # Compare fields and identify gaps
                missing_fields = []
                
                # Map Render fields to Supabase fields for comparison
                field_mappings = [
                    ('home_country', 'home_country', 'Home Country'),
                    ('marital_status', 'marital_status', 'Marital Status'),
                    ('spouse_first_name', 'spouse_first_name', 'Spouse First Name'),
                    ('spouse_last_name', 'spouse_last_name', 'Spouse Last Name'),
                    ('birthday', 'birthday', 'Birthday'),
                    ('anniversary', 'anniversary', 'Anniversary'),
                    ('profession', 'profession', 'Profession'),
                    ('organization', 'organization', 'Organization'),
                    ('priority', 'priority', 'Priority'),
                    ('street_address', 'street_address', 'Street Address'),
                    ('city', 'city', 'City'),
                    ('state', 'state', 'State'),
                    ('zip_code', 'zip_code', 'ZIP Code'),
                    ('phone', 'phone', 'Phone'),
                    ('assigned_to', None, 'Assigned To'),  # This field structure changed
                    ('source', None, 'Source'),  # May not exist in new schema
                    ('referred_by', None, 'Referred By'),  # May not exist in new schema
                    ('info_given', None, 'Info Given'),  # May not exist in new schema
                    ('people_pipeline', None, 'People Pipeline')  # Pipeline system changed
                ]
                
                for render_field, supabase_field, display_name in field_mappings:
                    render_value = render_person.get(render_field)
                    supabase_value = supabase_person.get(supabase_field) if supabase_field else None
                    
                    # Check if Render has data but Supabase doesn't
                    if render_value and str(render_value).strip() and (not supabase_value or not str(supabase_value).strip()):
                        missing_fields.append({
                            'field': display_name,
                            'render_value': render_value,
                            'supabase_value': supabase_value
                        })
                
                if missing_fields:
                    field_gaps.append({
                        'person_name': f"{render_person['first_name']} {render_person['last_name']}",
                        'email': render_person['email'],
                        'render_id': render_person['contact_id'],
                        'supabase_id': supabase_person['id'],
                        'missing_fields': missing_fields
                    })
        
        print(f"   Matched {matches_found} people between databases")
        print(f"   Found {len(field_gaps)} people with missing field data")
        
        return field_gaps
        
    except Exception as e:
        print(f"Error comparing people fields: {e}")
        return []
    finally:
        render_cursor.close()
        supabase_cursor.close()

def get_communication_comparison(render_conn, supabase_conn):
    """Compare communication data between databases"""
    print("\n💬 Comparing Communication Data...")
    
    render_cursor = render_conn.cursor(cursor_factory=DictCursor)
    supabase_cursor = supabase_conn.cursor(cursor_factory=DictCursor)
    
    try:
        # Get communication data from Render
        render_cursor.execute("""
            SELECT 
                id,
                object_id,
                date,
                communication_type,
                notes,
                direction,
                interaction_type,
                subject,
                user_id
            FROM com_log_comlog
            ORDER BY date DESC
            LIMIT 50
        """)
        
        render_comms = render_cursor.fetchall()
        print(f"   Found {len(render_comms)} recent communications in Render")
        
        # Get sample of communications from Supabase
        supabase_cursor.execute("""
            SELECT COUNT(*) FROM communications
        """)
        supabase_count = supabase_cursor.fetchone()[0]
        print(f"   Found {supabase_count} communications in Supabase")
        
        # Sample some communications to check structure
        supabase_cursor.execute("""
            SELECT 
                id,
                contact_id,
                created_at,
                type,
                message,
                subject,
                direction,
                user_id
            FROM communications
            ORDER BY created_at DESC
            LIMIT 10
        """)
        
        supabase_comms = supabase_cursor.fetchall()
        
        return {
            'render_sample': [dict(comm) for comm in render_comms[:5]],
            'supabase_sample': [dict(comm) for comm in supabase_comms[:5]],
            'render_count': len(render_comms),
            'supabase_count': supabase_count
        }
        
    except Exception as e:
        print(f"Error comparing communications: {e}")
        return {}
    finally:
        render_cursor.close()
        supabase_cursor.close()

def main():
    print("🔍 Field Data Comparison Tool - Render vs Supabase")
    print("=" * 70)
    print("Checking for missing or incomplete field data in existing records...")
    
    # Connect to databases
    print("\n📡 Connecting to databases...")
    render_conn = connect_to_db(RENDER_DB_CONFIG, "Render")
    supabase_conn = connect_to_db(SUPABASE_DB_CONFIG, "Supabase")
    
    if not render_conn or not supabase_conn:
        print("❌ Could not connect to both databases. Please check your configuration.")
        return
    
    # Compare field data
    all_gaps = {}
    
    # Church field comparison
    church_gaps = get_church_field_comparison(render_conn, supabase_conn)
    if church_gaps:
        all_gaps['churches'] = church_gaps
        print(f"\n   📊 Church Field Gaps Summary:")
        for gap in church_gaps[:5]:  # Show first 5
            print(f"      - {gap['church_name']}: {len(gap['missing_fields'])} missing fields")
            for field in gap['missing_fields'][:3]:  # Show first 3 fields
                print(f"        • {field['field']}: '{field['render_value']}'")
    
    # People field comparison
    people_gaps = get_people_field_comparison(render_conn, supabase_conn)
    if people_gaps:
        all_gaps['people'] = people_gaps
        print(f"\n   📊 People Field Gaps Summary:")
        for gap in people_gaps[:5]:  # Show first 5
            print(f"      - {gap['person_name']}: {len(gap['missing_fields'])} missing fields")
            for field in gap['missing_fields'][:3]:  # Show first 3 fields
                print(f"        • {field['field']}: '{field['render_value']}'")
    
    # Communication comparison
    comm_comparison = get_communication_comparison(render_conn, supabase_conn)
    if comm_comparison:
        all_gaps['communications'] = comm_comparison
    
    # Generate detailed report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"field_data_gaps_report_{timestamp}.json"
    
    with open(report_file, 'w') as f:
        json.dump(all_gaps, f, indent=2, default=str)
    
    print(f"\n📄 Detailed field gaps report saved to: {report_file}")
    
    # Summary
    church_count = len(church_gaps) if church_gaps else 0
    people_count = len(people_gaps) if people_gaps else 0
    
    if church_count > 0 or people_count > 0:
        print(f"\n⚠️  Found field data gaps:")
        print(f"   - {church_count} churches with incomplete field data")
        print(f"   - {people_count} people with incomplete field data")
        print(f"\n💡 Consider creating a data update script to fill these gaps")
    else:
        print(f"\n✅ No significant field data gaps found!")
    
    # Cleanup
    render_conn.close()
    supabase_conn.close()

if __name__ == "__main__":
    main()