"""
Management command to find people with first_name/last_name in the people table
that might not be synced to contacts.
"""

from django.core.management.base import BaseCommand
from django.db import connection, transaction


class Command(BaseCommand):
    help = "Find people with names in people table and sync to contacts"

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
            self.style.SUCCESS("=== Finding People with Names in People Table ===")
        )

        cursor = connection.cursor()

        # Query the people table (with id as primary key) for people with names
        self.stdout.write("Searching for people with first_name or last_name...")

        try:
            cursor.execute(
                """
                SELECT id, first_name, last_name, contact_id
                FROM people 
                WHERE (first_name IS NOT NULL AND first_name != '') 
                   OR (last_name IS NOT NULL AND last_name != '')
                ORDER BY id
                LIMIT 50;
            """
            )

            people_with_names = cursor.fetchall()

            if people_with_names:
                self.stdout.write(
                    f"Found {len(people_with_names)} people with names in people table:"
                )

                mismatches = []

                for person_id, p_first, p_last, contact_id in people_with_names:
                    self.stdout.write(f"\nPeople ID {person_id}:")
                    self.stdout.write(f'  Names: "{p_first or ""}" "{p_last or ""}"')
                    self.stdout.write(f"  Contact ID: {contact_id}")

                    if contact_id:
                        # Check if this contact exists and what names it has
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
                            self.stdout.write(
                                f'  Contact: "{c_first or ""}" "{c_last or ""}" ({contact_type})'
                            )
                            self.stdout.write(f"  Email: {email}")

                            # Check for mismatch
                            if (p_first != c_first) or (p_last != c_last):
                                self.stdout.write(f"  ⚠️  MISMATCH!")
                                mismatches.append(
                                    (
                                        contact_id,
                                        p_first,
                                        p_last,
                                        c_first,
                                        c_last,
                                        email,
                                    )
                                )

                                # Check what this person shows as in Django
                                cursor.execute(
                                    """
                                    SELECT first_name, last_name
                                    FROM contacts 
                                    WHERE id = %s AND type = 'person'
                                """,
                                    [contact_id],
                                )

                                django_contact = cursor.fetchone()
                                if django_contact:
                                    dj_first, dj_last = django_contact
                                    if not dj_first and not dj_last:
                                        self.stdout.write(
                                            f'  → This would show as "No name listed" in Django!'
                                        )
                            else:
                                self.stdout.write(f"  ✓ Names match")
                        else:
                            self.stdout.write(f"  ✗ Contact {contact_id} not found")
                    else:
                        self.stdout.write(f"  ✗ No contact_id linked")

                # Show summary of mismatches
                if mismatches:
                    self.stdout.write(
                        f"\n=== SUMMARY: {len(mismatches)} mismatches found ==="
                    )

                    for (
                        contact_id,
                        p_first,
                        p_last,
                        c_first,
                        c_last,
                        email,
                    ) in mismatches:
                        self.stdout.write(f"\nContact {contact_id} ({email}):")
                        self.stdout.write(
                            f'  People table: "{p_first or ""}" "{p_last or ""}"'
                        )
                        self.stdout.write(
                            f'  Contact table: "{c_first or ""}" "{c_last or ""}"'
                        )

                        if options["fix"]:
                            if options["dry_run"]:
                                self.stdout.write(
                                    f'  → WOULD UPDATE contact to: "{p_first}" "{p_last}"'
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
                                    f'  → UPDATED contact to: "{p_first}" "{p_last}"'
                                )

                    if options["fix"] and not options["dry_run"]:
                        self.stdout.write(f"\n✓ Updated {len(mismatches)} contacts!")

                else:
                    self.stdout.write(
                        "\n✓ No mismatches found - all names are in sync!"
                    )

            else:
                self.stdout.write("No people found with names in people table.")

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error querying people table: {e}"))

        # Also check for people showing as "No name listed" who might have data in people table
        self.stdout.write('\n=== Checking for "No name listed" people ===')

        try:
            cursor.execute(
                """
                SELECT c.id, c.first_name, c.last_name, c.email, p.first_name, p.last_name
                FROM contacts c
                LEFT JOIN people p ON c.id = p.contact_id
                WHERE c.type = 'person'
                AND (c.first_name IS NULL OR c.first_name = '')
                AND (c.last_name IS NULL OR c.last_name = '')
                ORDER BY c.id;
            """
            )

            no_name_people = cursor.fetchall()

            if no_name_people:
                self.stdout.write(
                    f"Found {len(no_name_people)} people with no names in contacts:"
                )

                for (
                    contact_id,
                    c_first,
                    c_last,
                    email,
                    p_first,
                    p_last,
                ) in no_name_people:
                    self.stdout.write(f"\nContact {contact_id} ({email}):")
                    self.stdout.write(
                        f'  Contact names: "{c_first or ""}" "{c_last or ""}"'
                    )
                    self.stdout.write(
                        f'  People names: "{p_first or ""}" "{p_last or ""}"'
                    )

                    if p_first or p_last:
                        self.stdout.write(f"  → Could be fixed from people table!")
            else:
                self.stdout.write("No people found with empty names in contacts.")

        except Exception as e:
            self.stdout.write(f"Error checking no-name people: {e}")

        self.stdout.write("\n" + self.style.SUCCESS("Search complete!"))
