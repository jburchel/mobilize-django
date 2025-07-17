"""
Management command to sync names from production Supabase people table to contacts table.
"""

import os
import psycopg2
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Sync names from production Supabase people table to contacts table"

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
            self.style.SUCCESS("=== Syncing Production Supabase Names ===")
        )

        # Get production database URL
        production_db_url = os.environ.get("SUPABASE_DATABASE_URL")

        if not production_db_url:
            self.stdout.write(
                self.style.ERROR("SUPABASE_DATABASE_URL not found in environment")
            )
            return

        self.stdout.write(f"Connecting to production database...")

        try:
            # Connect directly to production Supabase
            conn = psycopg2.connect(production_db_url)
            cursor = conn.cursor()

            self.stdout.write("✓ Connected to production Supabase")

            # First, check the schema of the people table
            cursor.execute(
                """
                SELECT column_name, data_type
                FROM information_schema.columns 
                WHERE table_name = 'people' AND table_schema = 'public'
                AND column_name IN ('id', 'first_name', 'last_name', 'contact_id')
                ORDER BY column_name;
            """
            )

            key_columns = cursor.fetchall()
            column_names = [col[0] for col in key_columns]
            self.stdout.write(f"Production people table key columns: {column_names}")

            # Check if the production people table has the structure you described
            if "first_name" in column_names:
                self.stdout.write(
                    "✓ Production people table has first_name/last_name columns!"
                )

                # Find people with names that might be missing from contacts
                cursor.execute(
                    """
                    SELECT p.id, p.first_name, p.last_name, p.contact_id,
                           c.first_name as contact_first, c.last_name as contact_last, c.email
                    FROM people p
                    LEFT JOIN contacts c ON p.contact_id = c.id
                    WHERE (p.first_name IS NOT NULL AND p.first_name != '') 
                       OR (p.last_name IS NOT NULL AND p.last_name != '')
                    ORDER BY p.id
                    LIMIT 20;
                """
                )

                people_with_names = cursor.fetchall()

                if people_with_names:
                    self.stdout.write(
                        f"Found {len(people_with_names)} people with names in production:"
                    )

                    mismatches = []

                    for row in people_with_names:
                        p_id, p_first, p_last, contact_id, c_first, c_last, email = row

                        # Format names safely
                        p_first_display = p_first or ""
                        p_last_display = p_last or ""
                        c_first_display = c_first or ""
                        c_last_display = c_last or ""

                        self.stdout.write(f"\nPeople ID {p_id}:")
                        self.stdout.write(
                            f'  Names: "{p_first_display}" "{p_last_display}"'
                        )
                        self.stdout.write(f"  Contact ID: {contact_id}")

                        if contact_id and email:
                            self.stdout.write(
                                f'  Contact names: "{c_first_display}" "{c_last_display}"'
                            )
                            self.stdout.write(f"  Email: {email}")

                            # Check for mismatch
                            if (p_first != c_first) or (p_last != c_last):
                                self.stdout.write(f"  ⚠️  MISMATCH!")

                                # Check if contact has empty names (would show "No name listed")
                                if not c_first and not c_last:
                                    self.stdout.write(
                                        f'  → This shows as "No name listed" in the app!'
                                    )

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
                            else:
                                self.stdout.write(f"  ✓ Names match")
                        else:
                            self.stdout.write(
                                f"  ✗ No linked contact or contact not found"
                            )

                    # Apply fixes if requested
                    if mismatches:
                        self.stdout.write(
                            f"\n=== {len(mismatches)} MISMATCHES FOUND ==="
                        )

                        if options["fix"]:
                            if options["dry_run"]:
                                self.stdout.write("DRY RUN - Would apply these fixes:")
                                for (
                                    contact_id,
                                    p_first,
                                    p_last,
                                    c_first,
                                    c_last,
                                    email,
                                ) in mismatches:
                                    p_first_safe = p_first or ""
                                    p_last_safe = p_last or ""
                                    self.stdout.write(
                                        f'  Contact {contact_id}: Update to "{p_first_safe}" "{p_last_safe}"'
                                    )
                            else:
                                confirm = input(
                                    f"Apply {len(mismatches)} name fixes to production? (y/N): "
                                )
                                if confirm.lower() == "y":
                                    self.stdout.write("Applying fixes...")

                                    for (
                                        contact_id,
                                        p_first,
                                        p_last,
                                        c_first,
                                        c_last,
                                        email,
                                    ) in mismatches:
                                        cursor.execute(
                                            """
                                            UPDATE contacts 
                                            SET first_name = %s, last_name = %s
                                            WHERE id = %s
                                        """,
                                            [p_first, p_last, contact_id],
                                        )

                                        p_first_safe = p_first or ""
                                        p_last_safe = p_last or ""
                                        self.stdout.write(
                                            f'✓ Updated Contact {contact_id}: "{p_first_safe}" "{p_last_safe}"'
                                        )

                                    conn.commit()
                                    self.stdout.write(
                                        self.style.SUCCESS(
                                            f"✓ Successfully updated {len(mismatches)} contacts!"
                                        )
                                    )
                                else:
                                    self.stdout.write("Fixes cancelled.")
                        else:
                            self.stdout.write(
                                "Use --fix to apply changes, or --fix --dry-run to preview."
                            )
                    else:
                        self.stdout.write(
                            "\n✓ No mismatches found - all names are synced!"
                        )

                else:
                    self.stdout.write(
                        "No people with names found in production people table."
                    )

            else:
                self.stdout.write(
                    "✗ Production people table does not have first_name/last_name columns"
                )
                self.stdout.write("Available columns: " + ", ".join(column_names))

            cursor.close()
            conn.close()

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Error connecting to production database: {e}")
            )

        self.stdout.write("\n" + self.style.SUCCESS("Production sync complete!"))
