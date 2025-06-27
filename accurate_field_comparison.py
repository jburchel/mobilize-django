#!/usr/bin/env python3
"""
Accurate Field Data Comparison Script - Render vs Supabase

This script compares field values between matching records using the correct column names.
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

def compare_church_data(render_conn, supabase_conn):
    """Compare church field data between databases"""
    print("\n🏛️ Comparing Church Field Data...")
    
    render_cursor = render_conn.cursor(cursor_factory=DictCursor)
    supabase_cursor = supabase_conn.cursor(cursor_factory=DictCursor)
    
    try:
        # Get church data from Render with correct column names
        render_cursor.execute("""
            SELECT 
                cc.id as contact_id,
                cc.church_name,
                cc.email,
                cc.phone,
                cc.street_address,
                cc.city,
                cc.state,
                cc.zip_code,
                cc.initial_notes,
                ch.senior_pastor_first_name,
                ch.senior_pastor_last_name,
                ch.senior_pastor_phone,
                ch.senior_pastor_email,
                ch.missions_pastor_first_name,
                ch.missions_pastor_last_name,
                ch.mission_pastor_phone,
                ch.mission_pastor_email,
                ch.primary_contact_first_name,
                ch.primary_contact_last_name,
                ch.primary_contact_phone,
                ch.primary_contact_email,
                ch.denomination,
                ch.website,
                ch.congregation_size,
                ch.year_founded,
                ch.info_given,
                ch.church_pipeline,
                ch.priority,
                ch.assigned_to,
                ch.source,
                ch.referred_by
            FROM contacts_contact cc
            JOIN contacts_church ch ON cc.id = ch.contact_ptr_id
            WHERE cc.church_name IS NOT NULL AND cc.church_name != ''
            ORDER BY cc.church_name
        """)
        
        render_churches = render_cursor.fetchall()
        print(f"   Found {len(render_churches)} churches in Render")
        
        field_gaps = []
        matches_found = 0
        detailed_comparisons = []
        
        for render_church in render_churches:
            # Find matching church in Supabase by name
            church_name = render_church['church_name']
            
            supabase_cursor.execute("""
                SELECT 
                    c.id,
                    c.church_name,
                    c.email,
                    c.phone,
                    c.street_address,
                    c.city,
                    c.state,
                    c.zip_code,
                    c.initial_notes,
                    c.priority,
                    ch.name as church_name_alt,
                    ch.denomination,
                    ch.website,
                    ch.congregation_size,
                    ch.year_founded,
                    ch.pastor_first_name,
                    ch.pastor_last_name,
                    ch.pastor_phone,
                    ch.pastor_email,
                    ch.info_given,
                    ch.church_pipeline
                FROM contacts c
                LEFT JOIN churches ch ON c.id = ch.contact_id
                WHERE (c.church_name ILIKE %s OR ch.name ILIKE %s)
                AND c.type = 'church'
                LIMIT 1
            """, (f"%{church_name}%", f"%{church_name}%"))
            
            supabase_church = supabase_cursor.fetchone()
            
            if supabase_church:
                matches_found += 1
                
                # Compare fields and identify gaps
                missing_fields = []
                
                # Field mappings: (render_field, supabase_field, display_name, importance)
                field_mappings = [
                    ('senior_pastor_first_name', 'pastor_first_name', 'Senior Pastor First Name', 'high'),
                    ('senior_pastor_last_name', 'pastor_last_name', 'Senior Pastor Last Name', 'high'),
                    ('senior_pastor_phone', 'pastor_phone', 'Senior Pastor Phone', 'high'),
                    ('senior_pastor_email', 'pastor_email', 'Senior Pastor Email', 'high'),
                    ('denomination', 'denomination', 'Denomination', 'medium'),
                    ('website', 'website', 'Website', 'medium'),
                    ('congregation_size', 'congregation_size', 'Congregation Size', 'medium'),
                    ('year_founded', 'year_founded', 'Year Founded', 'low'),
                    ('info_given', 'info_given', 'Info Given', 'high'),
                    ('church_pipeline', 'church_pipeline', 'Church Pipeline', 'high'),
                    ('priority', 'priority', 'Priority', 'high'),
                    ('street_address', 'street_address', 'Street Address', 'medium'),
                    ('city', 'city', 'City', 'medium'),
                    ('state', 'state', 'State', 'medium'),
                    ('zip_code', 'zip_code', 'ZIP Code', 'low'),
                    ('phone', 'phone', 'Phone', 'medium'),
                    ('email', 'email', 'Email', 'high'),
                    ('initial_notes', 'initial_notes', 'Initial Notes', 'medium'),
                    ('missions_pastor_first_name', None, 'Missions Pastor First Name', 'medium'),
                    ('missions_pastor_last_name', None, 'Missions Pastor Last Name', 'medium'),
                    ('mission_pastor_phone', None, 'Missions Pastor Phone', 'medium'),
                    ('mission_pastor_email', None, 'Missions Pastor Email', 'medium'),
                    ('primary_contact_first_name', None, 'Primary Contact First Name', 'medium'),
                    ('primary_contact_last_name', None, 'Primary Contact Last Name', 'medium'),
                    ('primary_contact_phone', None, 'Primary Contact Phone', 'medium'),
                    ('primary_contact_email', None, 'Primary Contact Email', 'medium'),
                    ('assigned_to', None, 'Assigned To', 'high'),
                    ('source', None, 'Source', 'medium'),
                    ('referred_by', None, 'Referred By', 'medium')
                ]
                
                for render_field, supabase_field, display_name, importance in field_mappings:
                    render_value = render_church.get(render_field)
                    supabase_value = supabase_church.get(supabase_field) if supabase_field else None
                    
                    # Check if Render has data but Supabase doesn't
                    if render_value and str(render_value).strip() and (not supabase_value or not str(supabase_value).strip()):
                        missing_fields.append({
                            'field': display_name,
                            'render_value': str(render_value)[:100],  # Limit length for display
                            'supabase_value': str(supabase_value) if supabase_value else None,
                            'importance': importance
                        })
                
                if missing_fields:
                    field_gaps.append({
                        'church_name': church_name,
                        'render_id': render_church['contact_id'],
                        'supabase_id': supabase_church['id'],
                        'missing_fields': missing_fields,
                        'high_priority_missing': len([f for f in missing_fields if f['importance'] == 'high'])
                    })
                
                # Store detailed comparison for analysis
                detailed_comparisons.append({
                    'church_name': church_name,
                    'render_data': dict(render_church),
                    'supabase_data': dict(supabase_church),
                    'missing_count': len(missing_fields)
                })
        
        print(f"   Matched {matches_found} churches between databases")
        print(f"   Found {len(field_gaps)} churches with missing field data")
        
        # Show summary of high-priority gaps
        high_priority_gaps = [gap for gap in field_gaps if gap['high_priority_missing'] > 0]
        if high_priority_gaps:
            print(f"   ⚠️  {len(high_priority_gaps)} churches missing HIGH PRIORITY data:")
            for gap in high_priority_gaps[:5]:
                high_fields = [f['field'] for f in gap['missing_fields'] if f['importance'] == 'high']
                print(f"      - {gap['church_name']}: {', '.join(high_fields)}")
        
        return {
            'gaps': field_gaps,
            'detailed': detailed_comparisons[:10],  # Store first 10 for analysis
            'summary': {
                'total_render': len(render_churches),
                'matched': matches_found,
                'with_gaps': len(field_gaps),
                'high_priority_gaps': len(high_priority_gaps)
            }
        }
        
    except Exception as e:
        print(f"Error comparing church fields: {e}")
        import traceback
        traceback.print_exc()
        return {}
    finally:
        render_cursor.close()
        supabase_cursor.close()

def compare_people_data(render_conn, supabase_conn):
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
                cc.initial_notes,
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
                cp.title,
                cp.desired_service
            FROM contacts_contact cc
            JOIN contacts_people cp ON cc.id = cp.contact_ptr_id
            WHERE cc.first_name IS NOT NULL AND cc.first_name != ''
            ORDER BY cc.last_name, cc.first_name
            LIMIT 50
        """)
        
        render_people = render_cursor.fetchall()
        print(f"   Found {len(render_people)} people in Render (sampling first 50)")
        
        field_gaps = []
        matches_found = 0
        
        for render_person in render_people:
            # Find matching person in Supabase by email first, then by name
            email = render_person['email']
            first_name = render_person['first_name']
            last_name = render_person['last_name']
            
            # Try email match first
            if email and email.strip():
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
                        c.initial_notes,
                        c.priority,
                        p.home_country,
                        p.marital_status,
                        p.spouse_first_name,
                        p.spouse_last_name,
                        p.title
                    FROM contacts c
                    LEFT JOIN people p ON c.id = p.contact_id
                    WHERE c.type = 'person' AND c.email = %s
                    LIMIT 1
                """, (email,))
                
                supabase_person = supabase_cursor.fetchone()
            else:
                supabase_person = None
            
            # If no email match, try name match
            if not supabase_person and first_name and last_name:
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
                        c.initial_notes,
                        c.priority,
                        p.home_country,
                        p.marital_status,
                        p.spouse_first_name,
                        p.spouse_last_name,
                        p.title
                    FROM contacts c
                    LEFT JOIN people p ON c.id = p.contact_id
                    WHERE c.type = 'person' 
                    AND c.first_name ILIKE %s 
                    AND c.last_name ILIKE %s
                    LIMIT 1
                """, (first_name, last_name))
                
                supabase_person = supabase_cursor.fetchone()
            
            if supabase_person:
                matches_found += 1
                
                # Compare fields
                missing_fields = []
                
                field_mappings = [
                    ('home_country', 'home_country', 'Home Country', 'medium'),
                    ('marital_status', 'marital_status', 'Marital Status', 'medium'),
                    ('spouse_first_name', 'spouse_first_name', 'Spouse First Name', 'medium'),
                    ('spouse_last_name', 'spouse_last_name', 'Spouse Last Name', 'medium'),
                    ('title', 'title', 'Title', 'low'),
                    ('priority', 'priority', 'Priority', 'high'),
                    ('street_address', 'street_address', 'Street Address', 'medium'),
                    ('city', 'city', 'City', 'medium'),
                    ('state', 'state', 'State', 'medium'),
                    ('zip_code', 'zip_code', 'ZIP Code', 'low'),
                    ('phone', 'phone', 'Phone', 'medium'),
                    ('initial_notes', 'initial_notes', 'Initial Notes', 'medium'),
                    ('assigned_to', None, 'Assigned To', 'high'),
                    ('source', None, 'Source', 'medium'),
                    ('referred_by', None, 'Referred By', 'medium'),
                    ('info_given', None, 'Info Given', 'high'),
                    ('people_pipeline', None, 'People Pipeline', 'high'),
                    ('desired_service', None, 'Desired Service', 'medium')
                ]
                
                for render_field, supabase_field, display_name, importance in field_mappings:
                    render_value = render_person.get(render_field)
                    supabase_value = supabase_person.get(supabase_field) if supabase_field else None
                    
                    if render_value and str(render_value).strip() and (not supabase_value or not str(supabase_value).strip()):
                        missing_fields.append({
                            'field': display_name,
                            'render_value': str(render_value)[:100],
                            'supabase_value': str(supabase_value) if supabase_value else None,
                            'importance': importance
                        })
                
                if missing_fields:
                    field_gaps.append({
                        'person_name': f"{first_name} {last_name}",
                        'email': email,
                        'render_id': render_person['contact_id'],
                        'supabase_id': supabase_person['id'],
                        'missing_fields': missing_fields,
                        'high_priority_missing': len([f for f in missing_fields if f['importance'] == 'high'])
                    })
        
        print(f"   Matched {matches_found} people between databases")
        print(f"   Found {len(field_gaps)} people with missing field data")
        
        # Show high-priority gaps
        high_priority_gaps = [gap for gap in field_gaps if gap['high_priority_missing'] > 0]
        if high_priority_gaps:
            print(f"   ⚠️  {len(high_priority_gaps)} people missing HIGH PRIORITY data:")
            for gap in high_priority_gaps[:5]:
                high_fields = [f['field'] for f in gap['missing_fields'] if f['importance'] == 'high']
                print(f"      - {gap['person_name']}: {', '.join(high_fields)}")
        
        return {
            'gaps': field_gaps,
            'summary': {
                'total_checked': len(render_people),
                'matched': matches_found,
                'with_gaps': len(field_gaps),
                'high_priority_gaps': len(high_priority_gaps)
            }
        }
        
    except Exception as e:
        print(f"Error comparing people fields: {e}")
        import traceback
        traceback.print_exc()
        return {}
    finally:
        render_cursor.close()
        supabase_cursor.close()

def main():
    print("🔍 Accurate Field Data Comparison - Render vs Supabase")
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
    all_results = {}
    
    # Church field comparison
    church_results = compare_church_data(render_conn, supabase_conn)
    if church_results:
        all_results['churches'] = church_results
    
    # People field comparison
    people_results = compare_people_data(render_conn, supabase_conn)
    if people_results:
        all_results['people'] = people_results
    
    # Generate report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"accurate_field_gaps_report_{timestamp}.json"
    
    with open(report_file, 'w') as f:
        json.dump(all_results, f, indent=2, default=str)
    
    print(f"\n📄 Detailed report saved to: {report_file}")
    
    # Final summary
    church_gaps = len(church_results.get('gaps', [])) if church_results else 0
    people_gaps = len(people_results.get('gaps', [])) if people_results else 0
    
    church_high = church_results.get('summary', {}).get('high_priority_gaps', 0) if church_results else 0
    people_high = people_results.get('summary', {}).get('high_priority_gaps', 0) if people_results else 0
    
    print(f"\n📊 FINAL SUMMARY:")
    print(f"   Churches with missing data: {church_gaps}")
    print(f"   People with missing data: {people_gaps}")
    print(f"   HIGH PRIORITY gaps: {church_high + people_high}")
    
    if church_gaps > 0 or people_gaps > 0:
        print(f"\n💡 Consider creating a data migration script to fill these gaps")
        print(f"    Focus on HIGH PRIORITY fields first (pipeline, priority, assignments)")
    else:
        print(f"\n✅ No significant field data gaps found!")
    
    # Cleanup
    render_conn.close()
    supabase_conn.close()

if __name__ == "__main__":
    main()