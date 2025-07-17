"""
Management command to directly query the Supabase people table for first_name/last_name
and sync them to the contacts table.
"""

from django.core.management.base import BaseCommand
from django.db import connection, transaction


class Command(BaseCommand):
    help = (
        "Direct sync from Supabase people table first_name/last_name to contacts table"
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be changed without making actual changes",
        )
        parser.add_argument(
            "--fix",
            action="store_true",
            help="Actually apply the fixes",
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS("=== Direct Supabase People Table Sync ===")
        )

        cursor = connection.cursor()

        # Direct query attempt - assume the columns exist as you stated
        self.stdout.write(
            "Attempting direct query of people table with first_name/last_name..."
        )

        try:
            # Try to query the people table for names as you described
            cursor.execute(
                """
                SELECT contact_id, first_name, last_name
                FROM people 
                WHERE contact_id IN (699, 728, 685)
                ORDER BY contact_id;
            """
            )

            people_data = cursor.fetchall()

            if people_data:
                self.stdout.write(f"SUCCESS! Found data in people table:")
                for contact_id, first_name, last_name in people_data:
                    self.stdout.write(
                        f'  Person {contact_id}: "{first_name or ""}" "{last_name or ""}"'
                    )

                # Now check what's in contacts table for these same IDs
                self.stdout.write("\nChecking contacts table for these IDs:")

                for contact_id, p_first, p_last in people_data:
                    cursor.execute(
                        """
                        SELECT first_name, last_name, email, type
                        FROM contacts 
                        WHERE id = %s
                    """,
                        [contact_id],
                    )

                    contact_data = cursor.fetchone()
                    if contact_data:
                        c_first, c_last, email, contact_type = contact_data
                        self.stdout.write(f"\n  Contact {contact_id}:")
                        self.stdout.write(
                            f'    People table: "{p_first or ""}" "{p_last or ""}"'
                        )
                        self.stdout.write(
                            f'    Contact table: "{c_first or ""}" "{c_last or ""}"'
                        )
                        self.stdout.write(f"    Email: {email}")
                        self.stdout.write(f"    Type: {contact_type}")

                        # Check if update is needed
                        if (p_first != c_first) or (p_last != c_last):
                            self.stdout.write(f"    → MISMATCH DETECTED!")

                            if options["fix"]:
                                if options["dry_run"]:
                                    self.stdout.write(
                                        f'    → WOULD UPDATE to: "{p_first}" "{p_last}"'
                                    )
                                else:
                                    cursor.execute(
                                        """
                                        UPDATE contacts 
                                        SET first_name = %s, last_name = %s
                                        WHERE id = %s
                                    """,
                                        [p_first, p_last, contact_id],
                                    )
                                    self.stdout.write(
                                        f'    → UPDATED to: "{p_first}" "{p_last}"'
                                    )
                        else:
                            self.stdout.write(f"    → Names match, no update needed")
                    else:
                        self.stdout.write(
                            f"\n  Contact {contact_id}: NOT FOUND in contacts table"
                        )

                # Now do a broader search for ALL mismatches
                if options["fix"]:
                    self.stdout.write("\n=== Searching for ALL name mismatches ===")

                    cursor.execute(
                        """
                        SELECT p.contact_id, p.first_name, p.last_name, c.first_name, c.last_name, c.email
                        FROM people p
                        JOIN contacts c ON p.contact_id = c.id
                        WHERE c.type = 'person'
                        AND (
                            (p.first_name IS NOT NULL AND p.first_name != '' AND (c.first_name IS NULL OR c.first_name = ''))
                            OR (p.last_name IS NOT NULL AND p.last_name != '' AND (c.last_name IS NULL OR c.last_name = ''))
                            OR (p.first_name != c.first_name)
                            OR (p.last_name != c.last_name)
                        )
                        ORDER BY p.contact_id
                        LIMIT 20;
                    """
                    )

                    all_mismatches = cursor.fetchall()

                    if all_mismatches:
                        self.stdout.write(
                            f"Found {len(all_mismatches)} total mismatches:"
                        )

                        with transaction.atomic():
                            for (
                                contact_id,
                                p_first,
                                p_last,
                                c_first,
                                c_last,
                                email,
                            ) in all_mismatches:
                                self.stdout.write(f"\nContact {contact_id}:")
                                self.stdout.write(
                                    f'  People: "{p_first or ""}" "{p_last or ""}"'
                                )
                                self.stdout.write(
                                    f'  Contact: "{c_first or ""}" "{c_last or ""}"'
                                )
                                self.stdout.write(f"  Email: {email}")

                                if options["dry_run"]:
                                    self.stdout.write(
                                        f'  → WOULD UPDATE to: "{p_first}" "{p_last}"'
                                    )
                                else:
                                    cursor.execute(
                                        """
                                        UPDATE contacts 
                                        SET first_name = %s, last_name = %s
                                        WHERE id = %s
                                    """,
                                        [p_first, p_last, contact_id],
                                    )
                                    self.stdout.write(
                                        f'  → UPDATED to: "{p_first}" "{p_last}"'
                                    )
                    else:
                        self.stdout.write("No additional mismatches found!")
            else:
                self.stdout.write(
                    "No data found for those specific contact IDs in people table"
                )

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error querying people table: {e}"))

            # Show what columns actually exist
            self.stdout.write("\nChecking actual table structure:")

            try:
                cursor.execute(
                    """
                    SELECT column_name, data_type
                    FROM information_schema.columns 
                    WHERE table_name = 'people'
                    ORDER BY ordinal_position;
                """
                )

                columns = cursor.fetchall()
                self.stdout.write("People table columns:")
                for col_name, data_type in columns:
                    self.stdout.write(f"  - {col_name} ({data_type})")

            except Exception as schema_error:
                self.stdout.write(f"Error checking schema: {schema_error}")

        self.stdout.write("\n" + self.style.SUCCESS("Direct sync complete!"))
