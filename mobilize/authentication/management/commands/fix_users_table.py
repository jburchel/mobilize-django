from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = "Fix users table schema to match Django User model"

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            # First create django_session table
            self.stdout.write("Creating django_session table...")
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS django_session (
                    session_key VARCHAR(40) PRIMARY KEY,
                    session_data TEXT NOT NULL,
                    expire_date TIMESTAMP WITH TIME ZONE NOT NULL
                );
            """
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS django_session_expire_date_idx ON django_session (expire_date);"
            )
            self.stdout.write("✓ Django session table created")
            # Check if password column exists
            cursor.execute(
                """
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='users' AND column_name='password';
            """
            )

            if not cursor.fetchone():
                self.stdout.write("Adding missing columns to users table...")

                # Add missing Django User fields
                missing_columns = [
                    "ALTER TABLE users ADD COLUMN IF NOT EXISTS password VARCHAR(128) DEFAULT '';",
                    "ALTER TABLE users ADD COLUMN IF NOT EXISTS last_login TIMESTAMP WITH TIME ZONE;",
                    "ALTER TABLE users ADD COLUMN IF NOT EXISTS is_superuser BOOLEAN DEFAULT FALSE;",
                    "ALTER TABLE users ADD COLUMN IF NOT EXISTS username VARCHAR(150) UNIQUE;",
                    "ALTER TABLE users ADD COLUMN IF NOT EXISTS first_name VARCHAR(150) DEFAULT '';",
                    "ALTER TABLE users ADD COLUMN IF NOT EXISTS last_name VARCHAR(150) DEFAULT '';",
                    "ALTER TABLE users ADD COLUMN IF NOT EXISTS is_staff BOOLEAN DEFAULT FALSE;",
                    "ALTER TABLE users ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;",
                    "ALTER TABLE users ADD COLUMN IF NOT EXISTS date_joined TIMESTAMP WITH TIME ZONE DEFAULT NOW();",
                ]

                for sql in missing_columns:
                    try:
                        cursor.execute(sql)
                        self.stdout.write(f"✓ {sql}")
                    except Exception as e:
                        self.stdout.write(f"⚠ {sql} - {e}")

                # Update existing users to have valid usernames if missing
                cursor.execute(
                    """
                    UPDATE users 
                    SET username = COALESCE(email, 'user_' || id::text)
                    WHERE username IS NULL OR username = '';
                """
                )

                self.stdout.write(
                    self.style.SUCCESS("Users table schema updated successfully!")
                )
            else:
                self.stdout.write("Users table already has required schema.")

            # Also create django_session table if it doesn't exist
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS django_session (
                    session_key VARCHAR(40) PRIMARY KEY,
                    session_data TEXT NOT NULL,
                    expire_date TIMESTAMP WITH TIME ZONE NOT NULL
                );
            """
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS django_session_expire_date_idx ON django_session (expire_date);"
            )

            self.stdout.write("Django session table ensured.")
