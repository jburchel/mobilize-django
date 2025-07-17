"""
Management command to sync names from Supabase people table to contacts table.

This directly queries the actual Supabase database structure, ignoring Django's model assumptions.
"""

from django.core.management.base import BaseCommand
from django.db import connection, transaction


class Command(BaseCommand):
    help = "Sync names from Supabase people table to contacts table"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be changed without making actual changes",
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS("=== Syncing Names from Supabase People Table ===")
        )

        cursor = connection.cursor()

        # Query the actual Supabase people table directly - assume first_name and last_name exist
        self.stdout.write("Querying Supabase people table for name data...")

        try:
            # Try to query the people table with first_name and last_name columns
            cursor.execute(
                """
                SELECT contact_id, first_name, last_name
                FROM people 
                WHERE (first_name IS NOT NULL AND first_name != '') 
                   OR (last_name IS NOT NULL AND last_name != '')
                ORDER BY contact_id
                LIMIT 20;
            """
            )

            people_with_names = cursor.fetchall()

            if people_with_names:
                self.stdout.write(
                    f"Found {len(people_with_names)} people with names in Supabase people table:"
                )

                for contact_id, first_name, last_name in people_with_names:
                    self.stdout.write(
                        f'  Person {contact_id}: "{first_name or ""}" "{last_name or ""}"'
                    )

                # Now check what's in the contacts table for these same people
                self.stdout.write("\\nChecking corresponding contacts table entries...")

                updates_needed = []

                for contact_id, p_first, p_last in people_with_names:
                    # Check contacts table
                    cursor.execute(
                        """
                        SELECT first_name, last_name, email
                        FROM contacts 
                        WHERE id = %s AND type = 'person'
                    """,
                        [contact_id],
                    )

                    contact_data = cursor.fetchone()
                    if contact_data:
                        c_first, c_last, email = contact_data

                        # Check if names are different
                        if (p_first != c_first) or (p_last != c_last):
                            updates_needed.append(
                                (contact_id, p_first, p_last, c_first, c_last, email)
                            )

                            self.stdout.write(f"\\nContact {contact_id} MISMATCH:")
                            self.stdout.write(
                                f'  People table: "{p_first or ""}" "{p_last or ""}"'
                            )
                            self.stdout.write(
                                f'  Contact table: "{c_first or ""}" "{c_last or ""}"'
                            )
                            self.stdout.write(f"  Email: {email}")
                    else:
                        self.stdout.write(
                            f"  Contact {contact_id}: No corresponding contact record found"
                        )

                # Apply updates
                if updates_needed:
                    self.stdout.write(
                        f"\\n=== {len(updates_needed)} UPDATES NEEDED ==="
                    )

                    if options["dry_run"]:
                        self.stdout.write("DRY RUN - Would make these updates:")
                        for (
                            contact_id,
                            p_first,
                            p_last,
                            c_first,
                            c_last,
                            email,
                        ) in updates_needed:
                            self.stdout.write(
                                f'  Contact {contact_id}: Update to "{p_first or ""}" "{p_last or ""}"'
                            )
                    else:
                        confirm = input(
                            f"Update {len(updates_needed)} contact records? (y/N): "
                        )
                        if confirm.lower() == "y":
                            with transaction.atomic():
                                for (
                                    contact_id,
                                    p_first,
                                    p_last,
                                    c_first,
                                    c_last,
                                    email,
                                ) in updates_needed:
                                    cursor.execute(
                                        """
                                        UPDATE contacts 
                                        SET first_name = %s, last_name = %s
                                        WHERE id = %s
                                    """,
                                        [p_first, p_last, contact_id],
                                    )

                                    self.stdout.write(
                                        f'✓ Updated Contact {contact_id}: "{p_first or ""}" "{p_last or ""}"'
                                    )

                                self.stdout.write(
                                    self.style.SUCCESS(
                                        f"\\nSuccessfully updated {len(updates_needed)} contacts!"
                                    )
                                )
                        else:
                            self.stdout.write("Update cancelled.")
                else:
                    self.stdout.write(
                        "\\nNo updates needed - all names are already in sync!"
                    )

            else:
                self.stdout.write("No people found with names in people table.")

        except Exception as e:
            if 'column "first_name" does not exist' in str(
                e
            ) or 'column "last_name" does not exist' in str(e):
                self.stdout.write(
                    self.style.ERROR(
                        "The people table does not have first_name/last_name columns."
                    )
                )
                self.stdout.write("\\nLet me check what columns actually exist:")

                cursor.execute(
                    """
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'people'
                    ORDER BY ordinal_position;
                """
                )

                columns = [row[0] for row in cursor.fetchall()]
                self.stdout.write(f"Actual people table columns: {columns}")

                # Check if there are any people showing as "Person ###" due to missing contact names
                self.stdout.write("\\nChecking for people with empty contact names...")

                cursor.execute(
                    """
                    SELECT p.contact_id, c.first_name, c.last_name, c.email
                    FROM people p
                    JOIN contacts c ON p.contact_id = c.id
                    WHERE c.type = 'person'
                    AND (c.first_name IS NULL OR c.first_name = '')
                    AND (c.last_name IS NULL OR c.last_name = '')
                    ORDER BY p.contact_id;
                """
                )

                empty_name_people = cursor.fetchall()
                self.stdout.write(
                    f"Found {len(empty_name_people)} people with empty names in contacts:"
                )

                for contact_id, first_name, last_name, email in empty_name_people:
                    self.stdout.write(
                        f'  Contact {contact_id}: "{first_name or ""}" "{last_name or ""}" ({email})'
                    )

            else:
                self.stdout.write(self.style.ERROR(f"Database error: {e}"))

        self.stdout.write("\\n" + self.style.SUCCESS("Supabase name sync complete!"))
