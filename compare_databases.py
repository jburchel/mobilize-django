#!/usr/bin/env python3
"""
Database Comparison Script - Render vs Supabase

This script compares data between your old Render database and current Supabase database
to identify missing records or data discrepancies.

Usage:
1. Update the RENDER_DB_CONFIG with your Render database credentials
2. Run: python compare_databases.py
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

# Supabase Database Configuration - FROM ENVIRONMENT
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

def get_table_counts(conn, tables):
    """Get record counts for specified tables"""
    cursor = conn.cursor()
    counts = {}
    
    for table in tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            counts[table] = count
            print(f"  {table}: {count} records")
        except Exception as e:
            counts[table] = f"Error: {e}"
            print(f"  {table}: Error - {e}")
    
    cursor.close()
    return counts

def get_sample_records(conn, table, limit=5):
    """Get sample records from a table"""
    cursor = conn.cursor(cursor_factory=DictCursor)
    
    try:
        cursor.execute(f"SELECT * FROM {table} LIMIT {limit}")
        records = cursor.fetchall()
        return [dict(record) for record in records]
    except Exception as e:
        print(f"Error getting sample records from {table}: {e}")
        return []
    finally:
        cursor.close()

def compare_key_fields(render_conn, supabase_conn, table, key_fields):
    """Compare key fields between databases to find missing records"""
    render_cursor = render_conn.cursor(cursor_factory=DictCursor)
    supabase_cursor = supabase_conn.cursor(cursor_factory=DictCursor)
    
    missing_in_supabase = []
    
    try:
        # Get key data from Render
        fields_str = ', '.join(key_fields)
        render_cursor.execute(f"SELECT {fields_str} FROM {table}")
        render_records = render_cursor.fetchall()
        
        print(f"\nChecking {len(render_records)} records from Render {table}...")
        
        for record in render_records:
            # Build WHERE clause to find matching record in Supabase
            where_conditions = []
            params = []
            
            for field in key_fields:
                if record[field] is not None:
                    where_conditions.append(f"{field} = %s")
                    params.append(record[field])
                else:
                    where_conditions.append(f"{field} IS NULL")
            
            where_clause = " AND ".join(where_conditions)
            
            # Check if record exists in Supabase
            supabase_cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE {where_clause}", params)
            count = supabase_cursor.fetchone()[0]
            
            if count == 0:
                missing_in_supabase.append(dict(record))
        
        return missing_in_supabase
        
    except Exception as e:
        print(f"Error comparing {table}: {e}")
        return []
    finally:
        render_cursor.close()
        supabase_cursor.close()

def main():
    print("🔍 Database Comparison Tool - Render vs Supabase")
    print("=" * 60)
    
    # Check if Render config is updated
    if RENDER_DB_CONFIG['host'] == 'YOUR_RENDER_HOST':
        print("❌ Please update RENDER_DB_CONFIG with your actual database credentials")
        print("   Update the values at the top of this script and run again.")
        return
    
    # Connect to databases
    print("\n📡 Connecting to databases...")
    render_conn = connect_to_db(RENDER_DB_CONFIG, "Render")
    supabase_conn = connect_to_db(SUPABASE_DB_CONFIG, "Supabase")
    
    if not render_conn or not supabase_conn:
        print("❌ Could not connect to both databases. Please check your configuration.")
        return
    
    # Define tables to compare
    tables_to_compare = [
        'contacts',
        'people', 
        'churches',
        'communications',
        'tasks',
        'users',
        'user_offices'
    ]
    
    print(f"\n📊 Comparing record counts...")
    print("\nRender Database:")
    render_counts = get_table_counts(render_conn, tables_to_compare)
    
    print("\nSupabase Database:")
    supabase_counts = get_table_counts(supabase_conn, tables_to_compare)
    
    # Compare counts
    print(f"\n📈 Count Comparison:")
    print("-" * 50)
    discrepancies = []
    
    for table in tables_to_compare:
        render_count = render_counts.get(table, 0) if isinstance(render_counts.get(table), int) else 0
        supabase_count = supabase_counts.get(table, 0) if isinstance(supabase_counts.get(table), int) else 0
        difference = render_count - supabase_count
        
        status = "✓" if difference == 0 else "⚠️" if difference > 0 else "❓"
        print(f"{status} {table:15} | Render: {render_count:4} | Supabase: {supabase_count:4} | Diff: {difference:+4}")
        
        if difference != 0:
            discrepancies.append({
                'table': table,
                'render_count': render_count,
                'supabase_count': supabase_count,
                'difference': difference
            })
    
    # Detailed comparison for tables with discrepancies
    if discrepancies:
        print(f"\n🔍 Detailed Analysis of Discrepancies:")
        print("-" * 60)
        
        # Define key fields for each table to identify unique records
        key_fields_map = {
            'contacts': ['email', 'first_name', 'last_name'],
            'people': ['id'],  # Primary key
            'churches': ['name', 'location'],
            'communications': ['id'],  # Primary key
            'tasks': ['id'],  # Primary key
            'users': ['email', 'username'],
            'user_offices': ['user_id', 'office_id']
        }
        
        missing_records_summary = {}
        
        for discrepancy in discrepancies:
            table = discrepancy['table']
            if discrepancy['difference'] > 0:  # More records in Render than Supabase
                print(f"\n🔎 Analyzing missing records in {table}...")
                key_fields = key_fields_map.get(table, ['id'])
                missing_records = compare_key_fields(render_conn, supabase_conn, table, key_fields)
                
                if missing_records:
                    missing_records_summary[table] = missing_records
                    print(f"   Found {len(missing_records)} records missing in Supabase")
                    
                    # Show first few missing records
                    print(f"   Sample missing records:")
                    for i, record in enumerate(missing_records[:3]):
                        print(f"     {i+1}. {record}")
                    
                    if len(missing_records) > 3:
                        print(f"     ... and {len(missing_records) - 3} more")
                else:
                    print(f"   No missing records found (may be data differences)")
    
    # Generate summary report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"database_comparison_report_{timestamp}.json"
    
    report = {
        'timestamp': timestamp,
        'render_counts': render_counts,
        'supabase_counts': supabase_counts,
        'discrepancies': discrepancies,
        'missing_records': missing_records_summary if 'missing_records_summary' in locals() else {}
    }
    
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f"\n📄 Detailed report saved to: {report_file}")
    
    # Cleanup
    render_conn.close()
    supabase_conn.close()
    
    if discrepancies:
        print(f"\n⚠️  Found {len(discrepancies)} tables with count discrepancies")
        print("   Review the detailed report for missing records analysis")
    else:
        print(f"\n✅ All table counts match between databases!")

if __name__ == "__main__":
    main()