# Generated migration to fix user_id column type mismatch

from django.db import migrations, connection


def fix_user_id_column_type(apps, schema_editor):
    """
    Fix the communications.user_id column type from varchar to integer.

    This was needed because imported communications had user_id stored as
    varchar which prevented proper foreign key joins with the users table
    where id is integer.
    """
    with connection.cursor() as cursor:
        # Check current column type
        cursor.execute(
            """
            SELECT data_type 
            FROM information_schema.columns 
            WHERE table_name = 'communications' AND column_name = 'user_id'
        """
        )
        result = cursor.fetchone()

        if result and result[0] == "character varying":
            # Update invalid user_id values to NULL first
            cursor.execute(
                """
                UPDATE communications 
                SET user_id = NULL 
                WHERE user_id IS NOT NULL 
                AND user_id NOT IN (SELECT CAST(id AS VARCHAR) FROM users)
            """
            )

            # Convert the column type from varchar to integer
            cursor.execute(
                """
                ALTER TABLE communications 
                ALTER COLUMN user_id TYPE INTEGER 
                USING CASE 
                    WHEN user_id IS NULL THEN NULL
                    WHEN user_id ~ '^[0-9]+$' THEN CAST(user_id AS INTEGER)
                    ELSE NULL
                END
            """
            )


def reverse_user_id_column_type(apps, schema_editor):
    """
    Reverse the fix by converting back to varchar.
    Note: This should rarely be needed.
    """
    with connection.cursor() as cursor:
        cursor.execute(
            """
            ALTER TABLE communications 
            ALTER COLUMN user_id TYPE VARCHAR(255) 
            USING CAST(user_id AS VARCHAR)
        """
        )


class Migration(migrations.Migration):

    dependencies = [
        ("communications", "0007_alter_communication_direction_and_more"),
    ]

    operations = [
        migrations.RunPython(
            fix_user_id_column_type,
            reverse_user_id_column_type,
        ),
    ]
