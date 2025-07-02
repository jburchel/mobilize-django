# Generated manually to fix user_id column type mismatch

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('admin_panel', '0003_remove_useroffice_role'),
    ]

    operations = [
        migrations.RunSQL(
            # Fix the user_id column type in user_offices table
            sql="ALTER TABLE user_offices ALTER COLUMN user_id TYPE integer USING user_id::integer;",
            reverse_sql="ALTER TABLE user_offices ALTER COLUMN user_id TYPE varchar(255);"
        ),
    ]