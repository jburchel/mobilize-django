from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = "Safely sync Supabase database schema to match local Django models"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be changed without making changes",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]

        if dry_run:
            self.stdout.write("DRY RUN MODE - No changes will be made")

        with connection.cursor() as cursor:
            # First, let's inspect what tables exist
            self.stdout.write("=== Current Supabase Tables ===")
            cursor.execute(
                """
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                ORDER BY table_name;
            """
            )
            tables = [row[0] for row in cursor.fetchall()]
            for table in tables:
                self.stdout.write(f"✓ {table}")

            # Check people table structure
            self.stdout.write("\n=== People Table Structure ===")
            cursor.execute(
                """
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns 
                WHERE table_name = 'people'
                ORDER BY ordinal_position;
            """
            )
            people_columns = cursor.fetchall()
            for col in people_columns:
                self.stdout.write(
                    f"  {col[0]} ({col[1]}) {'NULL' if col[2] == 'YES' else 'NOT NULL'}"
                )

            # Check if contact_id column exists
            has_contact_id = any(col[0] == "contact_id" for col in people_columns)

            if not has_contact_id:
                self.stdout.write("\n=== Missing contact_id column in people table ===")

                # Check if we have a contact table
                cursor.execute(
                    """
                    SELECT column_name
                    FROM information_schema.columns 
                    WHERE table_name = 'contacts'
                    ORDER BY ordinal_position;
                """
                )
                contact_columns = [row[0] for row in cursor.fetchall()]

                if contact_columns:
                    self.stdout.write("✓ contacts table exists")
                    for col in contact_columns:
                        self.stdout.write(f"  - {col}")

                    if not dry_run:
                        # Add contact_id column to people table
                        self.stdout.write("\n=== Adding contact_id to people table ===")
                        cursor.execute(
                            """
                            ALTER TABLE people 
                            ADD COLUMN IF NOT EXISTS contact_id BIGINT;
                        """
                        )

                        # Create foreign key constraint
                        cursor.execute(
                            """
                            ALTER TABLE people 
                            ADD CONSTRAINT IF NOT EXISTS people_contact_id_fkey 
                            FOREIGN KEY (contact_id) REFERENCES contacts(id);
                        """
                        )

                        self.stdout.write("✓ Added contact_id column and foreign key")
                    else:
                        self.stdout.write(
                            "WOULD ADD: contact_id column to people table"
                        )
                else:
                    self.stdout.write("⚠ contacts table not found")
            else:
                self.stdout.write("✓ contact_id column already exists in people table")

            # Check other critical tables and columns
            critical_checks = [
                ("users", ["password", "username", "email", "first_name", "last_name"]),
                ("django_session", ["session_key", "session_data", "expire_date"]),
                ("contacts", ["id", "first_name", "last_name", "email"]),
            ]

            for table_name, required_columns in critical_checks:
                self.stdout.write(f"\n=== Checking {table_name} table ===")
                cursor.execute(
                    """
                    SELECT column_name
                    FROM information_schema.columns 
                    WHERE table_name = %s;
                """,
                    [table_name],
                )
                existing_columns = [row[0] for row in cursor.fetchall()]

                if existing_columns:
                    missing_columns = [
                        col for col in required_columns if col not in existing_columns
                    ]
                    if missing_columns:
                        self.stdout.write(
                            f"⚠ Missing columns in {table_name}: {missing_columns}"
                        )
                    else:
                        self.stdout.write(f"✓ {table_name} has all required columns")
                else:
                    self.stdout.write(f"⚠ {table_name} table does not exist")

        if dry_run:
            self.stdout.write("\n=== DRY RUN COMPLETE ===")
            self.stdout.write("Run without --dry-run to apply changes")
        else:
            self.stdout.write("\n=== SCHEMA SYNC COMPLETE ===")
