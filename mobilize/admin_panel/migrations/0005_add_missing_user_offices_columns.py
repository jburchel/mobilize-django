# Generated manually to add missing columns to user_offices table

from django.db import migrations, models
import django.utils.timezone as django_timezone


class Migration(migrations.Migration):

    dependencies = [
        ('admin_panel', '0004_fix_user_id_column_type'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            -- Add missing columns to user_offices table if they don't exist
            DO $$ 
            BEGIN 
                -- Add is_primary column
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'user_offices' AND column_name = 'is_primary'
                ) THEN
                    ALTER TABLE user_offices ADD COLUMN is_primary BOOLEAN DEFAULT FALSE;
                END IF;
                
                -- Add permissions column (JSON)
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'user_offices' AND column_name = 'permissions'
                ) THEN
                    ALTER TABLE user_offices ADD COLUMN permissions JSONB;
                END IF;
                
                -- Add assigned_at column
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'user_offices' AND column_name = 'assigned_at'
                ) THEN
                    ALTER TABLE user_offices ADD COLUMN assigned_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();
                END IF;
                
                -- Add updated_at column
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'user_offices' AND column_name = 'updated_at'
                ) THEN
                    ALTER TABLE user_offices ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();
                END IF;
            END $$;
            """,
            reverse_sql="""
            -- Remove the columns if we reverse (optional)
            ALTER TABLE user_offices DROP COLUMN IF EXISTS is_primary;
            ALTER TABLE user_offices DROP COLUMN IF EXISTS permissions;
            ALTER TABLE user_offices DROP COLUMN IF EXISTS assigned_at;
            ALTER TABLE user_offices DROP COLUMN IF EXISTS updated_at;
            """
        ),
    ]