#!/usr/bin/env python3
"""
Analyze assignment patterns in Render database to plan migration strategy
"""

import os
import psycopg2
from psycopg2.extras import DictCursor
import json
from collections import Counter

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

def analyze_render_assignments():
    """Analyze assignment patterns in Render database"""
    print("🔍 Analyzing assignment patterns in Render database...")
    
    conn = connect_to_db(RENDER_DB_CONFIG)
    cursor = conn.cursor(cursor_factory=DictCursor)
    
    # Get church assignments
    cursor.execute("""
        SELECT assigned_to, COUNT(*) as count
        FROM contacts_church 
        WHERE assigned_to IS NOT NULL AND assigned_to != ''
        GROUP BY assigned_to
        ORDER BY count DESC
    """)
    church_assignments = cursor.fetchall()
    
    # Get people assignments
    cursor.execute("""
        SELECT assigned_to, COUNT(*) as count
        FROM contacts_people 
        WHERE assigned_to IS NOT NULL AND assigned_to != ''
        GROUP BY assigned_to
        ORDER BY count DESC
    """)
    people_assignments = cursor.fetchall()
    
    # Get sample records with assignments
    cursor.execute("""
        SELECT 
            cc.church_name,
            ch.assigned_to,
            ch.priority,
            ch.church_pipeline,
            ch.info_given
        FROM contacts_contact cc
        JOIN contacts_church ch ON cc.id = ch.contact_ptr_id
        WHERE ch.assigned_to IS NOT NULL AND ch.assigned_to != ''
        ORDER BY ch.assigned_to, cc.church_name
        LIMIT 20
    """)
    church_samples = cursor.fetchall()
    
    cursor.execute("""
        SELECT 
            cc.first_name,
            cc.last_name,
            cp.assigned_to,
            cp.priority,
            cp.people_pipeline,
            cp.info_given
        FROM contacts_contact cc
        JOIN contacts_people cp ON cc.id = cp.contact_ptr_id
        WHERE cp.assigned_to IS NOT NULL AND cp.assigned_to != ''
        ORDER BY cp.assigned_to, cc.last_name
        LIMIT 20
    """)
    people_samples = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return {
        'church_assignments': [dict(row) for row in church_assignments],
        'people_assignments': [dict(row) for row in people_assignments],
        'church_samples': [dict(row) for row in church_samples],
        'people_samples': [dict(row) for row in people_samples]
    }

def get_supabase_users():
    """Get current users in Supabase database"""
    print("📋 Getting current users in Supabase...")
    
    conn = connect_to_db(SUPABASE_DB_CONFIG)
    cursor = conn.cursor(cursor_factory=DictCursor)
    
    cursor.execute("""
        SELECT 
            id,
            username,
            email,
            first_name,
            last_name,
            is_active
        FROM users
        WHERE is_active = true
        ORDER BY username
    """)
    
    users = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return [dict(user) for user in users]

def create_assignment_mapping(render_assignments, supabase_users):
    """Create mapping from Render assignment strings to Supabase users"""
    print("🔗 Creating assignment mapping...")
    
    # Get all unique assignment values
    all_assignments = set()
    for assignment in render_assignments['church_assignments']:
        all_assignments.add(assignment['assigned_to'])
    for assignment in render_assignments['people_assignments']:
        all_assignments.add(assignment['assigned_to'])
    
    # Known mappings based on your input
    known_mappings = {
        'Matthew Rule': 'm.rule@crossoverglobal.net',
        'Jim Burchel': 'j.burchel@crossoverglobal.net'
    }
    
    # Create user lookup by email and name
    user_lookup = {}
    for user in supabase_users:
        user_lookup[user['email']] = user
        if user['first_name'] and user['last_name']:
            full_name = f"{user['first_name']} {user['last_name']}"
            user_lookup[full_name] = user
    
    # Build mapping
    mapping = {}
    unmapped_assignments = []
    
    for assignment in all_assignments:
        mapped_user = None
        
        # Check known mappings first
        if assignment in known_mappings:
            email = known_mappings[assignment]
            if email in user_lookup:
                mapped_user = user_lookup[email]
        
        # Try direct name match
        if not mapped_user and assignment in user_lookup:
            mapped_user = user_lookup[assignment]
        
        # Try partial name matching
        if not mapped_user:
            assignment_lower = assignment.lower()
            for user in supabase_users:
                if user['first_name'] and user['last_name']:
                    full_name = f"{user['first_name']} {user['last_name']}"
                    if assignment_lower in full_name.lower() or full_name.lower() in assignment_lower:
                        mapped_user = user
                        break
        
        if mapped_user:
            mapping[assignment] = {
                'user_id': mapped_user['id'],
                'email': mapped_user['email'],
                'name': f"{mapped_user['first_name']} {mapped_user['last_name']}" if mapped_user['first_name'] else mapped_user['username']
            }
        else:
            unmapped_assignments.append(assignment)
    
    return mapping, unmapped_assignments

def main():
    print("🔍 Assignment Analysis Tool")
    print("=" * 50)
    
    # Analyze Render assignments
    render_data = analyze_render_assignments()
    
    # Get Supabase users
    supabase_users = get_supabase_users()
    
    # Create mapping
    mapping, unmapped = create_assignment_mapping(render_data, supabase_users)
    
    # Display results
    print(f"\n📊 Assignment Analysis Results:")
    print(f"   Church assignment patterns: {len(render_data['church_assignments'])}")
    print(f"   People assignment patterns: {len(render_data['people_assignments'])}")
    print(f"   Current Supabase users: {len(supabase_users)}")
    
    print(f"\n👥 Church Assignments in Render:")
    for assignment in render_data['church_assignments']:
        mapped = "✓" if assignment['assigned_to'] in mapping else "❌"
        print(f"   {mapped} {assignment['assigned_to']}: {assignment['count']} churches")
    
    print(f"\n👥 People Assignments in Render:")
    for assignment in render_data['people_assignments']:
        mapped = "✓" if assignment['assigned_to'] in mapping else "❌"
        print(f"   {mapped} {assignment['assigned_to']}: {assignment['count']} people")
    
    print(f"\n🔗 Successful Mappings ({len(mapping)}):")
    for render_name, user_info in mapping.items():
        print(f"   '{render_name}' → {user_info['name']} ({user_info['email']})")
    
    print(f"\n❌ Unmapped Assignments ({len(unmapped)}):")
    for assignment in unmapped:
        church_count = sum(1 for a in render_data['church_assignments'] if a['assigned_to'] == assignment)
        people_count = sum(1 for a in render_data['people_assignments'] if a['assigned_to'] == assignment)
        total_count = church_count + people_count
        print(f"   '{assignment}': {total_count} records ({church_count} churches, {people_count} people)")
    
    print(f"\n💡 Recommendations:")
    if unmapped:
        print(f"   1. For unmapped assignments, consider:")
        print(f"      a) Add them to 'notes' field for historical reference")
        print(f"      b) Create a 'legacy_assigned_to' field to preserve the data")
        print(f"      c) Manually create user accounts for active assignees")
        print(f"   2. Update the mapping in the migration script")
    else:
        print(f"   ✅ All assignments can be mapped to existing users!")
    
    # Save detailed analysis
    analysis_result = {
        'render_data': render_data,
        'supabase_users': supabase_users,
        'mapping': mapping,
        'unmapped_assignments': unmapped,
        'recommendations': {
            'mapped_count': len(mapping),
            'unmapped_count': len(unmapped),
            'total_unique_assignments': len(mapping) + len(unmapped)
        }
    }
    
    with open('assignment_analysis.json', 'w') as f:
        json.dump(analysis_result, f, indent=2, default=str)
    
    print(f"\n📄 Detailed analysis saved to: assignment_analysis.json")

if __name__ == "__main__":
    main()