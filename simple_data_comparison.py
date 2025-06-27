#!/usr/bin/env python3
"""
Simple Data Comparison - Check for key missing fields
"""

import os
import psycopg2
from psycopg2.extras import DictCursor
import json

# Database configurations
RENDER_DB_CONFIG = {
    'host': 'dpg-cr6f1ei3esus73cnh1d0-a.oregon-postgres.render.com',
    'port': '5432',
    'database': 'mobilize',
    'user': 'jimburchel',
    'password': '1JmxPgDNQsk9UxDI7PdKXgF0PC4v1fiY'
}

SUPABASE_DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'port': os.getenv('DB_PORT', '5432'),
    'database': os.getenv('DB_NAME'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD')
}

def connect_to_db(config):
    """Create a database connection"""
    return psycopg2.connect(
        host=config['host'],
        port=config['port'],
        database=config['database'],
        user=config['user'],
        password=config['password']
    )

def get_render_church_sample():
    """Get sample church data from Render with important fields"""
    conn = connect_to_db(RENDER_DB_CONFIG)
    cursor = conn.cursor(cursor_factory=DictCursor)
    
    cursor.execute("""
        SELECT 
            cc.church_name,
            cc.email,
            cc.phone,
            cc.initial_notes,
            ch.senior_pastor_first_name,
            ch.senior_pastor_last_name,
            ch.senior_pastor_email,
            ch.denomination,
            ch.website,
            ch.info_given,
            ch.church_pipeline,
            ch.priority,
            ch.assigned_to
        FROM contacts_contact cc
        JOIN contacts_church ch ON cc.id = ch.contact_ptr_id
        WHERE cc.church_name IS NOT NULL AND cc.church_name != ''
        ORDER BY cc.church_name
        LIMIT 10
    """)
    
    churches = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return [dict(church) for church in churches]

def get_render_people_sample():
    """Get sample people data from Render with important fields"""
    conn = connect_to_db(RENDER_DB_CONFIG)
    cursor = conn.cursor(cursor_factory=DictCursor)
    
    cursor.execute("""
        SELECT 
            cc.first_name,
            cc.last_name,
            cc.email,
            cc.phone,
            cc.initial_notes,
            cp.home_country,
            cp.marital_status,
            cp.spouse_first_name,
            cp.spouse_last_name,
            cp.people_pipeline,
            cp.priority,
            cp.assigned_to,
            cp.info_given
        FROM contacts_contact cc
        JOIN contacts_people cp ON cc.id = cp.contact_ptr_id
        WHERE cc.first_name IS NOT NULL AND cc.first_name != ''
        ORDER BY cc.last_name, cc.first_name
        LIMIT 10
    """)
    
    people = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return [dict(person) for person in people]

def get_supabase_church_sample():
    """Get sample church data from Supabase"""
    conn = connect_to_db(SUPABASE_DB_CONFIG)
    cursor = conn.cursor(cursor_factory=DictCursor)
    
    cursor.execute("""
        SELECT 
            c.church_name,
            c.email,
            c.phone,
            c.initial_notes,
            c.priority
        FROM contacts c
        WHERE c.type = 'church' AND c.church_name IS NOT NULL
        ORDER BY c.church_name
        LIMIT 10
    """)
    
    churches = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return [dict(church) for church in churches]

def get_supabase_people_sample():
    """Get sample people data from Supabase"""
    conn = connect_to_db(SUPABASE_DB_CONFIG)
    cursor = conn.cursor(cursor_factory=DictCursor)
    
    cursor.execute("""
        SELECT 
            c.first_name,
            c.last_name,
            c.email,
            c.phone,
            c.initial_notes,
            c.priority,
            p.home_country,
            p.marital_status,
            p.spouse_first_name,
            p.spouse_last_name
        FROM contacts c
        LEFT JOIN people p ON c.id = p.contact_id
        WHERE c.type = 'person' AND c.first_name IS NOT NULL
        ORDER BY c.last_name, c.first_name
        LIMIT 10
    """)
    
    people = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return [dict(person) for person in people]

def analyze_field_richness(render_data, supabase_data, data_type):
    """Analyze which database has richer field data"""
    print(f"\n📊 {data_type} Data Richness Analysis:")
    
    # Count non-empty fields in each dataset
    render_field_counts = {}
    supabase_field_counts = {}
    
    # Analyze Render data
    for record in render_data:
        for field, value in record.items():
            if field not in render_field_counts:
                render_field_counts[field] = 0
            if value and str(value).strip():
                render_field_counts[field] += 1
    
    # Analyze Supabase data
    for record in supabase_data:
        for field, value in record.items():
            if field not in supabase_field_counts:
                supabase_field_counts[field] = 0
            if value and str(value).strip():
                supabase_field_counts[field] += 1
    
    # Compare common fields
    common_fields = set(render_field_counts.keys()) & set(supabase_field_counts.keys())
    render_only_fields = set(render_field_counts.keys()) - set(supabase_field_counts.keys())
    
    print(f"   Render records: {len(render_data)}")
    print(f"   Supabase records: {len(supabase_data)}")
    print(f"   Common fields: {len(common_fields)}")
    print(f"   Render-only fields: {len(render_only_fields)}")
    
    if render_only_fields:
        print(f"   Fields only in Render: {', '.join(render_only_fields)}")
    
    print(f"\n   Field Population Comparison:")
    for field in sorted(common_fields):
        render_pop = render_field_counts.get(field, 0)
        supabase_pop = supabase_field_counts.get(field, 0)
        render_pct = (render_pop / len(render_data)) * 100 if render_data else 0
        supabase_pct = (supabase_pop / len(supabase_data)) * 100 if supabase_data else 0
        
        if render_pop > supabase_pop:
            status = "⚠️"
        elif render_pop == supabase_pop:
            status = "✓"
        else:
            status = "📈"
        
        print(f"   {status} {field:20} | Render: {render_pop:2}/{len(render_data)} ({render_pct:5.1f}%) | Supabase: {supabase_pop:2}/{len(supabase_data)} ({supabase_pct:5.1f}%)")
    
    return {
        'render_counts': render_field_counts,
        'supabase_counts': supabase_field_counts,
        'render_only_fields': list(render_only_fields),
        'common_fields': list(common_fields)
    }

def main():
    print("🔍 Simple Data Comparison - Render vs Supabase")
    print("=" * 60)
    print("Comparing field richness between databases...")
    
    try:
        # Get sample data from both databases
        print("\n📡 Fetching sample data...")
        
        render_churches = get_render_church_sample()
        supabase_churches = get_supabase_church_sample()
        
        render_people = get_render_people_sample()
        supabase_people = get_supabase_people_sample()
        
        # Analyze field richness
        church_analysis = analyze_field_richness(render_churches, supabase_churches, "Church")
        people_analysis = analyze_field_richness(render_people, supabase_people, "People")
        
        # Show sample records for comparison
        print(f"\n🔍 Sample Render Church Record:")
        if render_churches:
            sample_church = render_churches[0]
            for field, value in sample_church.items():
                if value and str(value).strip():
                    print(f"   {field}: {str(value)[:50]}...")
        
        print(f"\n🔍 Sample Supabase Church Record:")
        if supabase_churches:
            sample_church = supabase_churches[0]
            for field, value in sample_church.items():
                if value and str(value).strip():
                    print(f"   {field}: {str(value)[:50]}...")
        
        # Save detailed analysis
        analysis_results = {
            'church_analysis': church_analysis,
            'people_analysis': people_analysis,
            'sample_data': {
                'render_churches': render_churches,
                'supabase_churches': supabase_churches,
                'render_people': render_people,
                'supabase_people': supabase_people
            }
        }
        
        with open('data_richness_analysis.json', 'w') as f:
            json.dump(analysis_results, f, indent=2, default=str)
        
        print(f"\n📄 Detailed analysis saved to: data_richness_analysis.json")
        
        # Summary
        render_only_church_fields = len(church_analysis['render_only_fields'])
        render_only_people_fields = len(people_analysis['render_only_fields'])
        
        if render_only_church_fields > 0 or render_only_people_fields > 0:
            print(f"\n⚠️  Found {render_only_church_fields + render_only_people_fields} fields that exist only in Render")
            print("   These fields may contain valuable data not migrated to Supabase")
        else:
            print(f"\n✅ All Render fields appear to be represented in Supabase")
            
    except Exception as e:
        print(f"Error during comparison: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()