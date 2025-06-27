#!/usr/bin/env python3
"""
Explore Render Database Schema and Data

This script explores what tables and data exist in your Render database.
"""

import os
import psycopg2
from psycopg2.extras import DictCursor

# Render Database Configuration
RENDER_DB_CONFIG = {
    'host': 'dpg-cr6f1ei3esus73cnh1d0-a.oregon-postgres.render.com',
    'port': '5432',
    'database': 'mobilize',
    'user': 'jimburchel',
    'password': '1JmxPgDNQsk9UxDI7PdKXgF0PC4v1fiY'
}

def connect_to_db():
    """Create a database connection"""
    try:
        conn = psycopg2.connect(
            host=RENDER_DB_CONFIG['host'],
            port=RENDER_DB_CONFIG['port'],
            database=RENDER_DB_CONFIG['database'],
            user=RENDER_DB_CONFIG['user'],
            password=RENDER_DB_CONFIG['password']
        )
        print("✓ Connected to Render database")
        return conn
    except Exception as e:
        print(f"✗ Failed to connect to Render database: {e}")
        return None

def get_all_tables(conn):
    """Get list of all tables in the database"""
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_type = 'BASE TABLE'
        ORDER BY table_name;
    """)
    
    tables = [row[0] for row in cursor.fetchall()]
    cursor.close()
    return tables

def get_table_info(conn, table_name):
    """Get column information for a table"""
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT column_name, data_type, is_nullable, column_default
        FROM information_schema.columns 
        WHERE table_name = %s 
        ORDER BY ordinal_position;
    """, (table_name,))
    
    columns = cursor.fetchall()
    cursor.close()
    return columns

def get_table_count(conn, table_name):
    """Get record count for a table"""
    cursor = conn.cursor()
    try:
        cursor.execute(f"SELECT COUNT(*) FROM \"{table_name}\"")
        count = cursor.fetchone()[0]
        cursor.close()
        return count
    except Exception as e:
        cursor.close()
        return f"Error: {e}"

def get_sample_data(conn, table_name, limit=3):
    """Get sample records from a table"""
    cursor = conn.cursor(cursor_factory=DictCursor)
    try:
        cursor.execute(f"SELECT * FROM \"{table_name}\" LIMIT {limit}")
        records = cursor.fetchall()
        cursor.close()
        return [dict(record) for record in records]
    except Exception as e:
        cursor.close()
        return f"Error: {e}"

def main():
    print("🔍 Exploring Render Database Structure and Data")
    print("=" * 60)
    
    # Connect to database
    conn = connect_to_db()
    if not conn:
        return
    
    # Get all tables
    print("\n📋 Finding all tables...")
    tables = get_all_tables(conn)
    print(f"Found {len(tables)} tables:")
    for table in tables:
        print(f"  - {table}")
    
    # Analyze each table
    print(f"\n📊 Analyzing each table...")
    print("-" * 80)
    
    for table in tables:
        print(f"\n🔸 Table: {table}")
        
        # Get record count
        count = get_table_count(conn, table)
        print(f"   Records: {count}")
        
        # Get column info
        columns = get_table_info(conn, table)
        print(f"   Columns ({len(columns)}):")
        for col_name, data_type, nullable, default in columns[:10]:  # Show first 10 columns
            nullable_str = "NULL" if nullable == "YES" else "NOT NULL"
            default_str = f" DEFAULT {default}" if default else ""
            print(f"     - {col_name}: {data_type} {nullable_str}{default_str}")
        
        if len(columns) > 10:
            print(f"     ... and {len(columns) - 10} more columns")
        
        # Get sample data
        if isinstance(count, int) and count > 0:
            print(f"   Sample data:")
            sample_data = get_sample_data(conn, table)
            if isinstance(sample_data, list) and sample_data:
                for i, record in enumerate(sample_data):
                    print(f"     Record {i+1}: {dict(list(record.items())[:5])}...")  # Show first 5 fields
            else:
                print(f"     {sample_data}")
        
        print("-" * 40)
    
    # Look for Django-specific tables that might contain your data
    django_tables = [t for t in tables if any(keyword in t.lower() for keyword in 
                    ['person', 'people', 'church', 'contact', 'user', 'communication', 'task'])]
    
    if django_tables:
        print(f"\n🎯 Django/CRM-related tables found:")
        for table in django_tables:
            count = get_table_count(conn, table)
            print(f"   - {table}: {count} records")
    
    conn.close()
    print(f"\n✅ Exploration complete!")

if __name__ == "__main__":
    main()