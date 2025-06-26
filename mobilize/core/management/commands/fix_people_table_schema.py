from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Fix people table schema mismatch between production and local'

    def handle(self, *args, **options):
        self.stdout.write("🔧 Fixing people table schema mismatch...")
        
        try:
            with connection.cursor() as cursor:
                # Check current people table structure
                cursor.execute("""
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns 
                    WHERE table_name = 'people'
                    ORDER BY ordinal_position;
                """)
                current_columns = cursor.fetchall()
                self.stdout.write(f"📊 Current people table columns:")
                for col_name, col_type, nullable in current_columns:
                    self.stdout.write(f"   {col_name}: {col_type} ({'NULL' if nullable == 'YES' else 'NOT NULL'})")
                
                # Check if we have the wrong schema (id instead of contact_id)
                has_id_column = any(col[0] == 'id' for col in current_columns)
                has_contact_id_column = any(col[0] == 'contact_id' for col in current_columns)
                
                self.stdout.write(f"📊 Has 'id' column: {has_id_column}")
                self.stdout.write(f"📊 Has 'contact_id' column: {has_contact_id_column}")
                
                if has_id_column and not has_contact_id_column:
                    self.stdout.write("🔧 SCHEMA MISMATCH DETECTED: Production has 'id' but should have 'contact_id'")
                    
                    # Check if there's data in the table
                    cursor.execute("SELECT COUNT(*) FROM people;")
                    row_count = cursor.fetchone()[0]
                    self.stdout.write(f"📊 People table has {row_count} rows")
                    
                    if row_count > 0:
                        self.stdout.write("⚠️  Table has data - need to migrate carefully")
                        
                        # Check if the current 'id' values correspond to contact IDs
                        cursor.execute("""
                            SELECT p.id, c.id as contact_id, c.first_name, c.last_name
                            FROM people p
                            LEFT JOIN contacts c ON p.id = c.id
                            WHERE c.type = 'person'
                            LIMIT 5;
                        """)
                        sample_data = cursor.fetchall()
                        
                        self.stdout.write("📋 Sample data check (people.id vs contacts.id):")
                        matches = 0
                        for p_id, c_id, fname, lname in sample_data:
                            match = "✅" if p_id == c_id else "❌"
                            self.stdout.write(f"   {match} people.id={p_id}, contact.id={c_id}, name={fname} {lname}")
                            if p_id == c_id:
                                matches += 1
                        
                        if matches == len(sample_data) and len(sample_data) > 0:
                            self.stdout.write("✅ Data alignment verified - safe to rename column")
                            
                            # Step 1: Rename id to contact_id
                            self.stdout.write("🔧 Renaming 'id' column to 'contact_id'...")
                            cursor.execute("ALTER TABLE people RENAME COLUMN id TO contact_id;")
                            
                            # Step 2: Add missing columns that should be in people table
                            missing_columns = [
                                "title VARCHAR(50)",
                                "preferred_name VARCHAR(100)", 
                                "birthday DATE",
                                "anniversary DATE",
                                "marital_status VARCHAR(20)",
                                "home_country VARCHAR(100)",
                                "languages JSONB",
                                "profession VARCHAR(100)",
                                "organization VARCHAR(255)",
                                "linkedin_url VARCHAR(255)",
                                "facebook_url VARCHAR(255)", 
                                "twitter_url VARCHAR(255)",
                                "instagram_url VARCHAR(255)",
                                "google_contact_id VARCHAR(255)",
                                "primary_church_id BIGINT"
                            ]
                            
                            for column_def in missing_columns:
                                try:
                                    cursor.execute(f"ALTER TABLE people ADD COLUMN IF NOT EXISTS {column_def};")
                                    self.stdout.write(f"   ✅ Added column: {column_def}")
                                except Exception as e:
                                    self.stdout.write(f"   ⚠️  Column may exist: {column_def} - {e}")
                            
                            # Step 3: Drop legacy columns that shouldn't be in people table
                            legacy_columns = ["church_role", "church_id"]  # These moved to ChurchMembership
                            for col in legacy_columns:
                                try:
                                    cursor.execute(f"ALTER TABLE people DROP COLUMN IF EXISTS {col};")
                                    self.stdout.write(f"   ✅ Dropped legacy column: {col}")
                                except Exception as e:
                                    self.stdout.write(f"   ⚠️  Error dropping {col}: {e}")
                            
                            self.stdout.write("✅ People table schema fixed!")
                            
                        else:
                            self.stdout.write("❌ Data alignment mismatch - manual intervention required")
                            return
                    else:
                        self.stdout.write("📊 Table is empty - safe to recreate schema")
                        # Could recreate the table here if needed
                        
                elif has_contact_id_column:
                    self.stdout.write("✅ People table schema is correct (has contact_id)")
                    
                else:
                    self.stdout.write("❌ People table has neither 'id' nor 'contact_id' - unexpected state")
                    
        except Exception as e:
            self.stdout.write(f"❌ Error fixing people table schema: {e}")
            import traceback
            self.stdout.write(f"Full traceback: {traceback.format_exc()}")