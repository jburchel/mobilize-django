#!/usr/bin/env python

import psycopg2
from psycopg2.extras import RealDictCursor

# Old Render database connection info
OLD_DB_CONFIG = {
    'host': 'dpg-cr6f1ei3esus73cnh1d0-a.oregon-postgres.render.com',
    'port': '5432',
    'database': 'mobilize',
    'user': 'jimburchel',
    'password': '1JmxPgDNQsk9UxDI7PdKXgF0PC4v1fiY'
}

def connect_to_old_database():
    """Connect to the old Render database"""
    try:
        conn = psycopg2.connect(**OLD_DB_CONFIG, cursor_factory=RealDictCursor)
        return conn
    except Exception as e:
        print(f"Error connecting to old database: {e}")
        return None

def check_communications_table():
    """Check the structure of the communications table"""
    conn = connect_to_old_database()
    if not conn:
        return
    
    try:
        cursor = conn.cursor()
        
        # Check if com_log_comlog table exists
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name LIKE '%comm%' OR table_name LIKE '%log%'
            ORDER BY table_name;
        """)
        
        tables = cursor.fetchall()
        print("Tables with 'comm' or 'log' in name:")
        for table in tables:
            print(f"  - {table['table_name']}")
        
        # Check columns in com_log_comlog table
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'com_log_comlog'
            ORDER BY ordinal_position;
        """)
        
        columns = cursor.fetchall()
        print("\nColumns in com_log_comlog table:")
        for col in columns:
            print(f"  - {col['column_name']}: {col['data_type']} ({'nullable' if col['is_nullable'] == 'YES' else 'not null'})")
        
        # Get sample data
        cursor.execute("SELECT * FROM com_log_comlog LIMIT 5")
        sample_data = cursor.fetchall()
        print("\nSample data from com_log_comlog:")
        for i, row in enumerate(sample_data):
            print(f"Row {i+1}:")
            for key, value in row.items():
                print(f"  {key}: {value}")
            print()
        
        # Get counts by type
        cursor.execute("""
            SELECT 
                communication_type,
                COUNT(*) as count
            FROM com_log_comlog 
            WHERE communication_type IS NOT NULL
            GROUP BY communication_type
            ORDER BY count DESC;
        """)
        
        type_counts = cursor.fetchall()
        print("Communication types and counts:")
        for type_count in type_counts:
            print(f"  - {type_count['communication_type']}: {type_count['count']}")
        
        conn.close()
        
    except Exception as e:
        print(f"Error checking database: {e}")
        if conn:
            conn.close()

if __name__ == "__main__":
    check_communications_table()