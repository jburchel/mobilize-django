from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = "Fix data type mismatches between Supabase and Django expectations"

    def handle(self, *args, **options):
        self.stdout.write("🔧 Fixing data type mismatches in Supabase...")

        with connection.cursor() as cursor:
            # First, check the current data types
            self.stdout.write("\n📊 Checking current column data types...")

            tables_to_fix = {
                "communications": ["user_id"],
                "user_offices": ["user_id"],
                "tasks": ["created_by_id", "assigned_to_id"],
                "contacts": ["user_id"],
                "user_contact_sync_settings": ["user_id"],
                "google_tokens": ["user_id"],
                "email_signatures": ["user_id"],
                "dashboard_preferences": ["user_id"],
            }

            for table, columns in tables_to_fix.items():
                cursor.execute(
                    """
                    SELECT EXISTS (
                        SELECT 1 FROM information_schema.tables 
                        WHERE table_name = %s
                    );
                """,
                    [table],
                )

                if cursor.fetchone()[0]:
                    self.stdout.write(f"\n🔍 Checking {table}...")

                    for column in columns:
                        cursor.execute(
                            """
                            SELECT data_type 
                            FROM information_schema.columns 
                            WHERE table_name = %s AND column_name = %s;
                        """,
                            [table, column],
                        )

                        result = cursor.fetchone()
                        if result:
                            data_type = result[0]
                            if data_type == "character varying":
                                self.stdout.write(
                                    f"  ⚠️  {column} is VARCHAR, needs to be INTEGER"
                                )

                                try:
                                    # First, update any empty strings to NULL
                                    cursor.execute(
                                        f"""
                                        UPDATE {table} 
                                        SET {column} = NULL 
                                        WHERE {column} = '' OR {column} IS NULL;
                                    """
                                    )

                                    # Then convert the column to INTEGER
                                    cursor.execute(
                                        f"""
                                        ALTER TABLE {table} 
                                        ALTER COLUMN {column} TYPE INTEGER 
                                        USING {column}::INTEGER;
                                    """
                                    )

                                    self.stdout.write(
                                        f"  ✅ Converted {column} to INTEGER"
                                    )
                                except Exception as e:
                                    self.stdout.write(
                                        self.style.ERROR(
                                            f"  ❌ Failed to convert {column}: {e}"
                                        )
                                    )
                            else:
                                self.stdout.write(
                                    f"  ✅ {column} is already {data_type}"
                                )

            # Fix office_id columns as well
            self.stdout.write("\n🔍 Checking office_id columns...")
            office_tables = ["contacts", "tasks", "communications"]

            for table in office_tables:
                cursor.execute(
                    """
                    SELECT data_type 
                    FROM information_schema.columns 
                    WHERE table_name = %s AND column_name = 'office_id';
                """,
                    [table],
                )

                result = cursor.fetchone()
                if result and result[0] == "character varying":
                    self.stdout.write(
                        f"  ⚠️  {table}.office_id is VARCHAR, needs to be INTEGER"
                    )

                    try:
                        # Update empty strings to NULL
                        cursor.execute(
                            f"""
                            UPDATE {table} 
                            SET office_id = NULL 
                            WHERE office_id = '' OR office_id IS NULL;
                        """
                        )

                        # Convert to INTEGER
                        cursor.execute(
                            f"""
                            ALTER TABLE {table} 
                            ALTER COLUMN office_id TYPE INTEGER 
                            USING office_id::INTEGER;
                        """
                        )

                        self.stdout.write(
                            f"  ✅ Converted {table}.office_id to INTEGER"
                        )
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f"  ❌ Failed: {e}"))

            self.stdout.write("\n✅ Data type fixes complete!")
