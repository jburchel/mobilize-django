#!/usr/bin/env python3
"""
Check exact column names in Render database tables
"""

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

def get_table_columns(conn, table_name):
    """Get all column names for a table"""
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns 
        WHERE table_name = %s 
        ORDER BY ordinal_position;
    """, (table_name,))
    
    columns = cursor.fetchall()
    cursor.close()
    return columns

def main():
    print("🔍 Checking Render Database Column Names")
    print("=" * 50)
    
    conn = psycopg2.connect(
        host=RENDER_DB_CONFIG['host'],
        port=RENDER_DB_CONFIG['port'],
        database=RENDER_DB_CONFIG['database'],
        user=RENDER_DB_CONFIG['user'],
        password=RENDER_DB_CONFIG['password']
    )
    
    tables_to_check = ['contacts_church', 'contacts_people', 'contacts_contact', 'com_log_comlog']
    
    for table in tables_to_check:
        print(f"\n📋 Table: {table}")
        columns = get_table_columns(conn, table)
        for col_name, data_type, nullable in columns:
            print(f"   - {col_name}: {data_type} ({'NULL' if nullable == 'YES' else 'NOT NULL'})")
    
    conn.close()

if __name__ == "__main__":
    main()