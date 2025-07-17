"""
Management command to explore different people table structures and find the right one.
"""

from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = "Explore people table structures to find the right schema"

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS("=== Exploring People Table Structures ===")
        )

        cursor = connection.cursor()

        # First, let's see what tables exist with "people" in the name
        self.stdout.write('Checking for tables with "people" in the name...')

        try:
            cursor.execute(
                """
                SELECT table_name, table_schema
                FROM information_schema.tables 
                WHERE table_name ILIKE '%people%'
                ORDER BY table_schema, table_name;
            """
            )

            tables = cursor.fetchall()

            if tables:
                self.stdout.write("Found these people-related tables:")
                for table_name, schema in tables:
                    self.stdout.write(f"  - {schema}.{table_name}")
            else:
                self.stdout.write('No tables found with "people" in the name')

        except Exception as e:
            self.stdout.write(f"Error checking tables: {e}")

        # Now let's try to access the people table with different approaches
        self.stdout.write("\n=== Testing Different People Table Schemas ===")

        # Test 1: Try the schema you showed (with id, first_name, last_name)
        self.stdout.write("\nTest 1: Querying with id, first_name, last_name...")
        try:
            cursor.execute(
                """
                SELECT id, first_name, last_name, contact_id
                FROM public.people 
                WHERE (first_name IS NOT NULL AND first_name != '') 
                   OR (last_name IS NOT NULL AND last_name != '')
                LIMIT 5;
            """
            )

            results = cursor.fetchall()
            if results:
                self.stdout.write("SUCCESS! Found data:")
                for row in results:
                    self.stdout.write(
                        f'  ID {row[0]}: "{row[1] or ""}" "{row[2] or ""}" (contact_id: {row[3]})'
                    )
            else:
                self.stdout.write("No data found with this schema")

        except Exception as e:
            self.stdout.write(f"Failed: {e}")

        # Test 2: Try Django's expected schema (contact_id as primary key)
        self.stdout.write("\nTest 2: Querying with contact_id, preferred_name...")
        try:
            cursor.execute(
                """
                SELECT contact_id, preferred_name, title
                FROM public.people 
                LIMIT 5;
            """
            )

            results = cursor.fetchall()
            if results:
                self.stdout.write("SUCCESS! Found data:")
                for row in results:
                    self.stdout.write(
                        f'  Contact ID {row[0]}: preferred="{row[1] or ""}" title="{row[2] or ""}"'
                    )
            else:
                self.stdout.write("No data found with this schema")

        except Exception as e:
            self.stdout.write(f"Failed: {e}")

        # Test 3: Check all columns in the people table
        self.stdout.write("\nTest 3: Getting ALL columns from people table...")
        try:
            cursor.execute(
                """
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns 
                WHERE table_name = 'people' AND table_schema = 'public'
                ORDER BY ordinal_position;
            """
            )

            columns = cursor.fetchall()
            if columns:
                self.stdout.write("People table columns:")
                for col_name, data_type, nullable in columns:
                    self.stdout.write(
                        f"  - {col_name} ({data_type}, nullable: {nullable})"
                    )
            else:
                self.stdout.write("No columns found")

        except Exception as e:
            self.stdout.write(f"Failed: {e}")

        # Test 4: Try to find people with names who might be showing as "No name listed"
        self.stdout.write(
            "\nTest 4: Looking for specific contacts that might have name data..."
        )

        # Let's check contacts that show as "No name listed" but might have data elsewhere
        try:
            cursor.execute(
                """
                SELECT c.id, c.first_name, c.last_name, c.email
                FROM contacts c
                WHERE c.type = 'person'
                AND (c.first_name IS NULL OR c.first_name = '')
                AND (c.last_name IS NULL OR c.last_name = '')
                ORDER BY c.id;
            """
            )

            empty_contacts = cursor.fetchall()

            if empty_contacts:
                self.stdout.write(
                    f"Found {len(empty_contacts)} contacts with empty names:"
                )

                for contact_id, first_name, last_name, email in empty_contacts[:10]:
                    self.stdout.write(f"\n  Contact {contact_id} ({email}):")

                    # Try to find this contact in people table using different approaches

                    # Approach 1: Look by contact_id
                    try:
                        cursor.execute(
                            "SELECT preferred_name FROM people WHERE contact_id = %s",
                            [contact_id],
                        )
                        pref_result = cursor.fetchone()
                        if pref_result and pref_result[0]:
                            self.stdout.write(
                                f'    Has preferred_name: "{pref_result[0]}"'
                            )
                    except:
                        pass

                    # Approach 2: Look by id (assuming contact_id maps to id)
                    try:
                        cursor.execute(
                            "SELECT first_name, last_name FROM people WHERE id = %s",
                            [contact_id],
                        )
                        name_result = cursor.fetchone()
                        if name_result and (name_result[0] or name_result[1]):
                            self.stdout.write(
                                f'    Has names in people table: "{name_result[0] or ""}" "{name_result[1] or ""}"'
                            )
                    except:
                        pass

            else:
                self.stdout.write("No contacts found with empty names")

        except Exception as e:
            self.stdout.write(f"Failed: {e}")

        self.stdout.write("\n" + self.style.SUCCESS("Exploration complete!"))
