# Generated manually to fix user_id column type mismatch

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('admin_panel', '0003_remove_useroffice_role'),
    ]

    operations = [
        # Since we can't alter the column type due to RLS policies, we'll work with the existing VARCHAR type
        # and ensure the application code handles the conversion properly
        migrations.RunSQL(
            sql="""
            -- Ensure user_offices table has proper indexes for VARCHAR user_id
            CREATE INDEX IF NOT EXISTS user_offices_user_id_varchar_idx ON user_offices(user_id);
            
            -- Add a comment to document the column type
            COMMENT ON COLUMN user_offices.user_id IS 'VARCHAR column storing user IDs as strings for RLS compatibility';
            """,
            reverse_sql="""
            -- Remove the index if we reverse
            DROP INDEX IF EXISTS user_offices_user_id_varchar_idx;
            """
        ),
    ]