#!/usr/bin/env python
"""
Direct Supabase Database Name Sync Script

This script connects directly to your Supabase database to:
1. Analyze the current state of people and contacts tables
2. Sync first_name and last_name from people table to contacts table
3. Ensure data consistency for your Django production app

Run with: python fix_supabase_names.py --analyze
Run with: python fix_supabase_names.py --sync
"""

import psycopg2
import argparse
import os
from urllib.parse import urlparse
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def get_supabase_connection():
    """Get connection to Supabase database using DATABASE_URL from Render"""
    
    # Get from environment or .env file
    database_url = os.environ.get('SUPABASE_DATABASE_URL')
    
    if not database_url:
        raise ValueError("SUPABASE_DATABASE_URL not provided")
    
    # Parse the URL
    parsed = urlparse(database_url)
    
    try:
        conn = psycopg2.connect(
            host=parsed.hostname,
            port=parsed.port or 5432,
            database=parsed.path[1:],  # Remove leading slash
            user=parsed.username,
            password=parsed.password,
            sslmode='require'
        )
        print(f"✅ Connected to Supabase database: {parsed.hostname}")
        return conn
    except Exception as e:
        print(f"❌ Failed to connect to Supabase: {e}")
        raise

def analyze_database(conn):
    """Analyze the current state of people and contacts tables"""
    print("\n🔍 ANALYZING SUPABASE DATABASE")
    print("=" * 60)
    
    with conn.cursor() as cursor:
        # Check if tables exist
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('people', 'contacts')
            ORDER BY table_name;
        """)
        tables = [row[0] for row in cursor.fetchall()]
        print(f"📋 Found tables: {tables}")
        
        if 'people' not in tables or 'contacts' not in tables:
            print("❌ Missing required tables!")
            return False
        
        # Analyze people table structure
        print(f"\n📊 PEOPLE TABLE STRUCTURE:")
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'people' 
            ORDER BY ordinal_position;
        """)
        people_columns = cursor.fetchall()
        for col in people_columns:
            nullable = "NULL" if col[2] == 'YES' else "NOT NULL"
            print(f"   - {col[0]} ({col[1]}) {nullable}")
        
        # Check for name columns in people table
        name_columns = [col[0] for col in people_columns if 'name' in col[0].lower()]
        print(f"📝 Name-related columns in people: {name_columns}")
        
        # Analyze contacts table structure
        print(f"\n📊 CONTACTS TABLE STRUCTURE:")
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'contacts' 
            ORDER BY ordinal_position;
        """)
        contacts_columns = cursor.fetchall()
        for col in contacts_columns:
            nullable = "NULL" if col[2] == 'YES' else "NOT NULL"
            print(f"   - {col[0]} ({col[1]}) {nullable}")
        
        # Check data counts
        cursor.execute("SELECT COUNT(*) FROM people;")
        people_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM contacts WHERE type = 'person';")
        person_contacts_count = cursor.fetchone()[0]
        
        print(f"\n📊 DATA COUNTS:")
        print(f"   - People records: {people_count}")
        print(f"   - Person contacts: {person_contacts_count}")
        
        # Check if people table has first_name and last_name
        people_has_first_name = any(col[0] == 'first_name' for col in people_columns)
        people_has_last_name = any(col[0] == 'last_name' for col in people_columns)
        
        print(f"\n🔍 NAME FIELD ANALYSIS:")
        print(f"   - People table has first_name: {people_has_first_name}")
        print(f"   - People table has last_name: {people_has_last_name}")
        
        if people_has_first_name and people_has_last_name:
            # Sample the data
            cursor.execute("""
                SELECT first_name, last_name, contact_id
                FROM people 
                WHERE first_name IS NOT NULL OR last_name IS NOT NULL
                LIMIT 5;
            """)
            people_samples = cursor.fetchall()
            print(f"📝 Sample people with names:")
            for sample in people_samples:
                print(f"   - '{sample[0]}' '{sample[1]}' (contact_id: {sample[2]})")
            
            # Check corresponding contacts
            print(f"\n📝 Corresponding contacts:")
            for sample in people_samples:
                cursor.execute("""
                    SELECT id, first_name, last_name, type
                    FROM contacts 
                    WHERE id = %s;
                """, [sample[2]])
                contact = cursor.fetchone()
                if contact:
                    print(f"   - Contact {contact[0]}: '{contact[1]}' '{contact[2]}' ({contact[3]})")
                else:
                    print(f"   - Contact {sample[2]}: NOT FOUND")
        
        return True

def sync_names(conn, dry_run=True):
    """Sync names from people table to contacts table"""
    print(f"\n🔄 SYNCING NAMES FROM PEOPLE TO CONTACTS")
    if dry_run:
        print("🔍 DRY RUN MODE - No changes will be made")
    print("=" * 60)
    
    updated_count = 0
    error_count = 0
    no_change_count = 0
    
    with conn.cursor() as cursor:
        # Check if people table has name fields
        cursor.execute("""
            SELECT column_name
            FROM information_schema.columns 
            WHERE table_name = 'people' 
            AND column_name IN ('first_name', 'last_name');
        """)
        people_name_fields = [row[0] for row in cursor.fetchall()]
        
        if not people_name_fields:
            print("❌ People table doesn't have first_name or last_name fields")
            return
        
        print(f"✅ People table has name fields: {people_name_fields}")
        
        # Get all people with names and their contact relationships
        cursor.execute("""
            SELECT p.contact_id, p.first_name, p.last_name,
                   c.first_name as contact_first, c.last_name as contact_last
            FROM people p
            JOIN contacts c ON p.contact_id = c.id
            WHERE c.type = 'person'
            ORDER BY p.contact_id;
        """)
        
        records = cursor.fetchall()
        total_records = len(records)
        print(f"📊 Processing {total_records} people-contact pairs...")
        
        for i, (contact_id, people_first, people_last, contact_first, contact_last) in enumerate(records, 1):
            try:
                # Clean up names
                people_first = people_first.strip() if people_first else None
                people_last = people_last.strip() if people_last else None
                
                # Check if we need to update
                needs_update = False
                changes = []
                new_first = contact_first
                new_last = contact_last
                
                # Only update if people table has better data
                if people_first and (not contact_first or contact_first != people_first):
                    needs_update = True
                    changes.append(f"first_name: '{contact_first}' → '{people_first}'")
                    new_first = people_first
                
                if people_last and (not contact_last or contact_last != people_last):
                    needs_update = True
                    changes.append(f"last_name: '{contact_last}' → '{people_last}'")
                    new_last = people_last
                
                if needs_update:
                    print(f"📝 Record {i}: Contact {contact_id} - {', '.join(changes)}")
                    
                    if not dry_run:
                        cursor.execute("""
                            UPDATE contacts 
                            SET first_name = %s, last_name = %s
                            WHERE id = %s;
                        """, [new_first, new_last, contact_id])
                    
                    updated_count += 1
                else:
                    no_change_count += 1
                    if i <= 5:  # Show first few no-change records
                        print(f"✅ Record {i}: Contact {contact_id} - No changes needed")
            
            except Exception as e:
                error_count += 1
                print(f"❌ Record {i}: Contact {contact_id} - Error: {e}")
        
        if not dry_run:
            conn.commit()
            print(f"\n💾 Changes committed to database")
        
        print(f"\n📊 SYNC SUMMARY:")
        print(f"   • Total records processed: {total_records}")
        print(f"   • Records updated: {updated_count}")
        print(f"   • No changes needed: {no_change_count}")
        print(f"   • Errors: {error_count}")

def main():
    parser = argparse.ArgumentParser(description='Fix Supabase name data')
    parser.add_argument('--analyze', action='store_true', help='Analyze database structure and data')
    parser.add_argument('--sync', action='store_true', help='Sync names from people to contacts')
    parser.add_argument('--dry-run', action='store_true', help='Show what would change without making changes')
    
    args = parser.parse_args()
    
    if not args.analyze and not args.sync:
        print("Please specify --analyze or --sync")
        return
    
    try:
        conn = get_supabase_connection()
        
        if args.analyze:
            analyze_database(conn)
        
        if args.sync:
            sync_names(conn, dry_run=args.dry_run)
        
        conn.close()
        print(f"\n✅ Script completed successfully")
        
    except Exception as e:
        print(f"❌ Script failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()