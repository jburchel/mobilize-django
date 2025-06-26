from django.core.management.base import BaseCommand
from django.db import connection
from django.core.management import call_command
import json

class Command(BaseCommand):
    help = 'Comprehensive schema synchronization between local Django models and Supabase'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be changed without making changes',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed information about changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        verbose = options['verbose']
        
        if dry_run:
            self.stdout.write(self.style.WARNING("🔍 DRY RUN MODE - No changes will be made"))
        
        self.stdout.write(self.style.SUCCESS("🚀 Starting Comprehensive Schema Synchronization"))
        self.stdout.write("=" * 80)
        
        # Step 1: Analyze current database state
        self.analyze_current_state(verbose)
        
        # Step 2: Create missing tables
        self.create_missing_tables(dry_run, verbose)
        
        # Step 3: Add missing columns to existing tables
        self.add_missing_columns(dry_run, verbose)
        
        # Step 4: Fix table naming mismatches
        self.fix_table_naming_mismatches(dry_run, verbose)
        
        # Step 5: Create missing indexes
        self.create_missing_indexes(dry_run, verbose)
        
        # Step 6: Fix Person data integrity issues
        self.fix_person_data_integrity(dry_run, verbose)
        
        # Step 7: Verify schema integrity
        self.verify_schema_integrity(verbose)
        
        if dry_run:
            self.stdout.write(self.style.WARNING("\n🔍 DRY RUN COMPLETE - Run without --dry-run to apply changes"))
        else:
            self.stdout.write(self.style.SUCCESS("\n✅ COMPREHENSIVE SCHEMA SYNC COMPLETE"))

    def analyze_current_state(self, verbose):
        """Analyze current database state and identify what needs to be fixed"""
        self.stdout.write(self.style.HTTP_INFO("\n📊 ANALYZING CURRENT DATABASE STATE"))
        
        with connection.cursor() as cursor:
            # Get all existing tables
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_type = 'BASE TABLE'
                ORDER BY table_name;
            """)
            existing_tables = {row[0] for row in cursor.fetchall()}
            
            # Expected Django tables based on model analysis
            expected_tables = {
                # Auth and User management
                'users', 'google_tokens', 'user_contact_sync_settings',
                'roles', 'permissions', 'role_permissions', 'user_offices',
                
                # Core contact management
                'contacts', 'people', 'churches', 'church_memberships',
                
                # Communication
                'communications', 'email_templates', 'email_signatures',
                
                # Pipeline management
                'pipeline_pipeline', 'pipeline_pipelinestage', 
                'pipeline_pipelinecontact', 'pipeline_pipelinestagehistory',
                
                # Task management
                'tasks', 'recurring_task_templates',
                
                # Admin and multi-tenancy
                'admin_panel_office', 'activity_logs', 'dashboard_preferences',
                
                # Django system tables
                'django_session', 'django_content_type', 'django_migrations',
                'django_admin_log', 'auth_group', 'auth_group_permissions',
                'auth_permission', 'django_celery_beat_clockedschedule',
                'django_celery_beat_crontabschedule', 'django_celery_beat_intervalschedule',
                'django_celery_beat_periodictask', 'django_celery_beat_solarschedule',
                'django_celery_results_chordcounter', 'django_celery_results_groupresult',
                'django_celery_results_taskresult'
            }
            
            # Check for legacy table names that might exist in Supabase
            legacy_table_mappings = {
                'pipeline_contacts': 'pipeline_pipelinecontact',
                'offices': 'admin_panel_office',
            }
            
            missing_tables = expected_tables - existing_tables
            extra_tables = existing_tables - expected_tables
            
            if verbose:
                self.stdout.write(f"📋 Found {len(existing_tables)} existing tables")
                self.stdout.write(f"📋 Expected {len(expected_tables)} Django tables")
                self.stdout.write(f"⚠️  Missing {len(missing_tables)} tables")
                self.stdout.write(f"ℹ️  Extra {len(extra_tables)} tables (may be legacy)")
                
                if missing_tables:
                    self.stdout.write(f"\n🔍 Missing tables: {', '.join(sorted(missing_tables))}")
                if extra_tables:
                    self.stdout.write(f"\n🔍 Extra tables: {', '.join(sorted(extra_tables))}")
            
            # Store analysis results
            self.missing_tables = missing_tables
            self.existing_tables = existing_tables
            self.legacy_mappings = legacy_table_mappings

    def create_missing_tables(self, dry_run, verbose):
        """Create tables that are completely missing"""
        self.stdout.write(self.style.HTTP_INFO("\n🔨 CREATING MISSING TABLES"))
        
        if not self.missing_tables:
            self.stdout.write("✅ All required tables already exist")
            return
        
        critical_tables = {
            'django_session': """
                CREATE TABLE django_session (
                    session_key VARCHAR(40) PRIMARY KEY,
                    session_data TEXT NOT NULL,
                    expire_date TIMESTAMP WITH TIME ZONE NOT NULL
                );
                CREATE INDEX django_session_expire_date_idx ON django_session(expire_date);
            """,
            
            'google_tokens': """
                CREATE TABLE google_tokens (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                    access_token TEXT NOT NULL,
                    refresh_token TEXT,
                    token_type VARCHAR(50),
                    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
                    scopes JSONB,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
                CREATE INDEX google_tokens_user_id_idx ON google_tokens(user_id);
                CREATE INDEX google_tokens_expires_at_idx ON google_tokens(expires_at);
            """,
            
            'user_contact_sync_settings': """
                CREATE TABLE user_contact_sync_settings (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER UNIQUE REFERENCES users(id) ON DELETE CASCADE,
                    sync_preference VARCHAR(20) DEFAULT 'crm_only',
                    auto_sync_enabled BOOLEAN DEFAULT TRUE,
                    sync_frequency_hours INTEGER DEFAULT 24,
                    last_sync_at TIMESTAMP WITH TIME ZONE,
                    sync_errors JSONB,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
            """,
            
            'email_templates': """
                CREATE TABLE email_templates (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    subject VARCHAR(255) NOT NULL,
                    body TEXT NOT NULL,
                    is_html BOOLEAN DEFAULT TRUE,
                    created_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    category VARCHAR(50),
                    is_active BOOLEAN DEFAULT TRUE
                );
                CREATE INDEX email_templates_name_idx ON email_templates(name);
                CREATE INDEX email_templates_category_idx ON email_templates(category);
            """,
            
            'email_signatures': """
                CREATE TABLE email_signatures (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                    name VARCHAR(50) NOT NULL,
                    content TEXT NOT NULL,
                    logo_url VARCHAR(255),
                    is_default BOOLEAN DEFAULT FALSE,
                    is_html BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
                CREATE INDEX email_signatures_user_default_idx ON email_signatures(user_id, is_default);
            """,
            
            'pipeline_pipeline': """
                CREATE TABLE pipeline_pipeline (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    description TEXT,
                    pipeline_type VARCHAR(50) DEFAULT 'custom',
                    office_id INTEGER REFERENCES admin_panel_office(id) ON DELETE CASCADE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    is_main_pipeline BOOLEAN DEFAULT FALSE,
                    parent_pipeline_stage VARCHAR(100)
                );
                CREATE INDEX pipeline_pipeline_name_idx ON pipeline_pipeline(name);
                CREATE INDEX pipeline_pipeline_type_idx ON pipeline_pipeline(pipeline_type);
                CREATE INDEX pipeline_pipeline_office_idx ON pipeline_pipeline(office_id);
            """,
            
            'pipeline_pipelinestage': """
                CREATE TABLE pipeline_pipelinestage (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    description TEXT,
                    "order" INTEGER NOT NULL,
                    color VARCHAR(20),
                    pipeline_id INTEGER REFERENCES pipeline_pipeline(id) ON DELETE CASCADE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    auto_move_days INTEGER,
                    auto_reminder BOOLEAN DEFAULT FALSE,
                    auto_task_template TEXT
                );
                CREATE INDEX pipeline_pipelinestage_name_idx ON pipeline_pipelinestage(name);
                CREATE INDEX pipeline_pipelinestage_pipeline_order_idx ON pipeline_pipelinestage(pipeline_id, "order");
            """,
            
            'pipeline_pipelinecontact': """
                CREATE TABLE pipeline_pipelinecontact (
                    id SERIAL PRIMARY KEY,
                    contact_id INTEGER REFERENCES contacts(id) ON DELETE CASCADE,
                    person_id INTEGER,
                    church_id INTEGER,
                    contact_type VARCHAR(10) DEFAULT 'person',
                    pipeline_id INTEGER REFERENCES pipeline_pipeline(id) ON DELETE CASCADE,
                    current_stage_id INTEGER REFERENCES pipeline_pipelinestage(id) ON DELETE CASCADE,
                    entered_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
                CREATE INDEX pipeline_pipelinecontact_contact_idx ON pipeline_pipelinecontact(contact_id);
                CREATE INDEX pipeline_pipelinecontact_pipeline_idx ON pipeline_pipelinecontact(pipeline_id);
                CREATE INDEX pipeline_pipelinecontact_stage_idx ON pipeline_pipelinecontact(current_stage_id);
            """,
            
            'pipeline_pipelinestagehistory': """
                CREATE TABLE pipeline_pipelinestagehistory (
                    id SERIAL PRIMARY KEY,
                    pipeline_contact_id INTEGER REFERENCES pipeline_pipelinecontact(id) ON DELETE CASCADE,
                    from_stage_id INTEGER REFERENCES pipeline_pipelinestage(id) ON DELETE CASCADE,
                    to_stage_id INTEGER REFERENCES pipeline_pipelinestage(id) ON DELETE CASCADE,
                    notes TEXT,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    created_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL
                );
                CREATE INDEX pipeline_pipelinestagehistory_contact_idx ON pipeline_pipelinestagehistory(pipeline_contact_id);
                CREATE INDEX pipeline_pipelinestagehistory_created_idx ON pipeline_pipelinestagehistory(created_at);
            """,
            
            'recurring_task_templates': """
                CREATE TABLE recurring_task_templates (
                    id SERIAL PRIMARY KEY,
                    title VARCHAR(255) NOT NULL,
                    description TEXT,
                    priority VARCHAR(50) DEFAULT 'medium',
                    category VARCHAR(255),
                    type VARCHAR(50) DEFAULT 'general',
                    default_assignee_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
                    default_contact_id INTEGER REFERENCES contacts(id) ON DELETE SET NULL,
                    recurrence_pattern JSONB NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE,
                    last_created TIMESTAMP WITH TIME ZONE,
                    send_notifications BOOLEAN DEFAULT TRUE,
                    created_by_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                    office_id INTEGER REFERENCES admin_panel_office(id) ON DELETE SET NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
                CREATE INDEX recurring_task_templates_active_idx ON recurring_task_templates(is_active);
                CREATE INDEX recurring_task_templates_created_by_idx ON recurring_task_templates(created_by_id);
            """,
            
            'church_memberships': """
                CREATE TABLE church_memberships (
                    id SERIAL PRIMARY KEY,
                    person_id INTEGER NOT NULL,
                    church_id INTEGER NOT NULL,
                    role VARCHAR(50) DEFAULT 'member',
                    is_primary_contact BOOLEAN DEFAULT FALSE,
                    start_date DATE DEFAULT CURRENT_DATE,
                    end_date DATE,
                    status VARCHAR(20) DEFAULT 'active',
                    notes TEXT,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    UNIQUE(person_id, church_id)
                );
                CREATE INDEX church_memberships_person_idx ON church_memberships(person_id);
                CREATE INDEX church_memberships_church_idx ON church_memberships(church_id);
                CREATE INDEX church_memberships_primary_idx ON church_memberships(is_primary_contact);
            """,
            
            'activity_logs': """
                CREATE TABLE activity_logs (
                    id SERIAL PRIMARY KEY,
                    action_type VARCHAR(50) DEFAULT 'other',
                    ip_address INET,
                    user_agent TEXT,
                    entity_type VARCHAR(50),
                    entity_id INTEGER,
                    details JSONB,
                    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
                    office_id INTEGER REFERENCES admin_panel_office(id) ON DELETE SET NULL,
                    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
                CREATE INDEX activity_logs_action_type_idx ON activity_logs(action_type);
                CREATE INDEX activity_logs_timestamp_idx ON activity_logs(timestamp);
                CREATE INDEX activity_logs_user_idx ON activity_logs(user_id);
                CREATE INDEX activity_logs_entity_idx ON activity_logs(entity_type, entity_id);
            """,
            
            'dashboard_preferences': """
                CREATE TABLE dashboard_preferences (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER UNIQUE REFERENCES users(id) ON DELETE CASCADE,
                    widget_config JSONB DEFAULT '{}',
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
            """,
            
            'user_offices': """
                CREATE TABLE user_offices (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                    office_id INTEGER REFERENCES admin_panel_office(id) ON DELETE CASCADE,
                    is_primary BOOLEAN DEFAULT FALSE,
                    permissions JSONB,
                    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    UNIQUE(user_id, office_id)
                );
                CREATE INDEX user_offices_user_idx ON user_offices(user_id);
                CREATE INDEX user_offices_office_idx ON user_offices(office_id);
            """,
        }
        
        with connection.cursor() as cursor:
            for table_name in self.missing_tables:
                if table_name in critical_tables:
                    if verbose:
                        self.stdout.write(f"🔨 Creating table: {table_name}")
                    
                    if not dry_run:
                        try:
                            cursor.execute(critical_tables[table_name])
                            self.stdout.write(f"✅ Created table: {table_name}")
                        except Exception as e:
                            self.stdout.write(self.style.ERROR(f"❌ Failed to create {table_name}: {e}"))
                    else:
                        self.stdout.write(f"WOULD CREATE: {table_name}")
                elif verbose:
                    self.stdout.write(f"⚠️  Skipping {table_name} (no schema definition)")

    def add_missing_columns(self, dry_run, verbose):
        """Add missing columns to existing tables"""
        self.stdout.write(self.style.HTTP_INFO("\n🔧 ADDING MISSING COLUMNS"))
        
        # Define required columns for each table
        required_columns = {
            'users': {
                'password': 'VARCHAR(128)',
                'username': 'VARCHAR(150) UNIQUE',
                'first_name': 'VARCHAR(150)',
                'last_name': 'VARCHAR(150)',
                'is_staff': 'BOOLEAN DEFAULT FALSE',
                'is_active': 'BOOLEAN DEFAULT TRUE',
                'date_joined': 'TIMESTAMP WITH TIME ZONE DEFAULT NOW()',
                'role': 'VARCHAR(20) DEFAULT \'standard_user\'',
                'preferences': 'JSONB',
                'email_signature': 'TEXT',
                'notification_settings': 'JSONB',
                'theme_preferences': 'JSONB',
                'google_refresh_token': 'TEXT',
                'profile_picture_url': 'VARCHAR(255)',
                'person_id': 'INTEGER',
            },
            'contacts': {
                'type': 'VARCHAR(20)',
                'first_name': 'VARCHAR(255)',
                'last_name': 'VARCHAR(255)',
                'church_name': 'VARCHAR(255)',
                'phone': 'VARCHAR(20)',
                'image': 'VARCHAR(255)',
                'preferred_contact_method': 'VARCHAR(255)',
                'street_address': 'VARCHAR(255)',
                'city': 'VARCHAR(255)',
                'state': 'VARCHAR(255)',
                'zip_code': 'VARCHAR(255)',
                'address': 'TEXT',
                'country': 'VARCHAR(100)',
                'notes': 'TEXT',
                'initial_notes': 'TEXT',
                'google_resource_name': 'VARCHAR(255)',
                'google_contact_id': 'VARCHAR(255)',
                'created_at': 'TIMESTAMP WITH TIME ZONE DEFAULT NOW()',
                'updated_at': 'TIMESTAMP WITH TIME ZONE DEFAULT NOW()',
                'date_created': 'DATE',
                'date_modified': 'DATE',
                'last_synced_at': 'TIMESTAMP WITH TIME ZONE',
                'office_id': 'INTEGER',
                'user_id': 'INTEGER',
                'conflict_data': 'JSONB',
                'has_conflict': 'BOOLEAN',
                'priority': 'VARCHAR(20)',
                'status': 'VARCHAR(20) DEFAULT \'active\'',
                'last_contact_date': 'TIMESTAMP WITH TIME ZONE',
                'next_contact_date': 'TIMESTAMP WITH TIME ZONE',
                'tags': 'JSONB',
                'custom_fields': 'JSONB',
            },
            'people': {
                'contact_id': 'INTEGER',
                'title': 'VARCHAR(50)',
                'preferred_name': 'VARCHAR(100)',
                'birthday': 'DATE',
                'anniversary': 'DATE',
                'marital_status': 'VARCHAR(20)',
                'spouse_first_name': 'VARCHAR(255)',
                'spouse_last_name': 'VARCHAR(255)',
                'home_country': 'VARCHAR(100)',
                'languages': 'JSONB',
                'profession': 'VARCHAR(100)',
                'organization': 'VARCHAR(255)',
                'primary_church_id': 'INTEGER',
                'church_role': 'VARCHAR(100)',
                'linkedin_url': 'VARCHAR(255)',
                'facebook_url': 'VARCHAR(255)',
                'twitter_url': 'VARCHAR(255)',
                'instagram_url': 'VARCHAR(255)',
                'google_contact_id': 'VARCHAR(255)',
            },
            'churches': {
                'contact_id': 'INTEGER',
                'name': 'VARCHAR(255)',
                'location': 'VARCHAR(255)',
                'denomination': 'VARCHAR(100)',
                'website': 'VARCHAR(255)',
                'year_founded': 'INTEGER',
                'congregation_size': 'INTEGER',
                'weekly_attendance': 'INTEGER',
                'service_times': 'JSONB',
                'facilities': 'JSONB',
                'ministries': 'JSONB',
                'primary_language': 'VARCHAR(50)',
                'secondary_languages': 'JSONB',
                'pastor_name': 'VARCHAR(200)',
                'senior_pastor_first_name': 'VARCHAR(255)',
                'senior_pastor_last_name': 'VARCHAR(255)',
                'pastor_phone': 'VARCHAR(20)',
                'pastor_email': 'VARCHAR(255)',
                'missions_pastor_first_name': 'VARCHAR(255)',
                'missions_pastor_last_name': 'VARCHAR(255)',
                'mission_pastor_phone': 'VARCHAR(255)',
                'mission_pastor_email': 'VARCHAR(255)',
                'primary_contact_first_name': 'VARCHAR(255)',
                'primary_contact_last_name': 'VARCHAR(255)',
                'primary_contact_phone': 'VARCHAR(255)',
                'primary_contact_email': 'VARCHAR(255)',
                'main_contact_id': 'INTEGER',
                'church_pipeline': 'VARCHAR(255)',
                'virtuous': 'BOOLEAN',
                'info_given': 'TEXT',
            },
            'communications': {
                'type': 'VARCHAR(255)',
                'message': 'VARCHAR(255)',
                'subject': 'VARCHAR(255)',
                'direction': 'VARCHAR(255)',
                'date': 'DATE',
                'date_sent': 'TIMESTAMP WITH TIME ZONE',
                'person_id': 'INTEGER',
                'church_id': 'INTEGER',
                'gmail_message_id': 'VARCHAR(255)',
                'gmail_thread_id': 'VARCHAR(255)',
                'email_status': 'VARCHAR(255)',
                'attachments': 'VARCHAR(255)',
                'sender': 'VARCHAR(255)',
                'user_id': 'INTEGER',
                'owner_id': 'INTEGER',
                'office_id': 'INTEGER',
                'content': 'TEXT',
                'status': 'VARCHAR(50) DEFAULT \'pending\'',
                'external_id': 'VARCHAR(255)',
                'error_message': 'TEXT',
                'template_used_id': 'INTEGER',
                'cc_recipients': 'TEXT',
                'bcc_recipients': 'TEXT',
                'is_notification': 'BOOLEAN DEFAULT FALSE',
                'archived': 'BOOLEAN DEFAULT FALSE',
                'google_calendar_event_id': 'VARCHAR(255)',
                'google_meet_link': 'VARCHAR(255)',
                'last_synced_at': 'TIMESTAMP WITH TIME ZONE',
                'created_at': 'DATE DEFAULT CURRENT_DATE',
                'updated_at': 'DATE DEFAULT CURRENT_DATE',
            },
            'tasks': {
                'title': 'VARCHAR(255)',
                'description': 'VARCHAR(255)',
                'due_date': 'DATE',
                'due_time': 'VARCHAR(255)',
                'due_time_details': 'TEXT',
                'reminder_time': 'VARCHAR(255)',
                'reminder_option': 'VARCHAR(255) DEFAULT \'none\'',
                'reminder_sent': 'BOOLEAN DEFAULT FALSE',
                'priority': 'VARCHAR(50) DEFAULT \'medium\'',
                'status': 'VARCHAR(50) DEFAULT \'pending\'',
                'category': 'VARCHAR(255)',
                'type': 'VARCHAR(50) DEFAULT \'general\'',
                'person_id': 'INTEGER',
                'church_id': 'INTEGER',
                'contact_id': 'INTEGER',
                'created_by_id': 'INTEGER',
                'assigned_to_id': 'INTEGER',
                'office_id': 'INTEGER',
                'completed_at': 'TIMESTAMP WITH TIME ZONE',
                'completed_date': 'TIMESTAMP WITH TIME ZONE',
                'completion_notes': 'TEXT',
                'google_calendar_event_id': 'VARCHAR(255)',
                'google_calendar_sync_enabled': 'BOOLEAN',
                'last_synced_at': 'TIMESTAMP WITH TIME ZONE',
                'recurring_pattern': 'JSONB',
                'is_recurring_template': 'BOOLEAN DEFAULT FALSE',
                'recurrence_end_date': 'DATE',
                'parent_task_id': 'INTEGER',
                'next_occurrence_date': 'TIMESTAMP WITH TIME ZONE',
                'recurring_template_id': 'INTEGER',
                'notification_sent': 'BOOLEAN DEFAULT FALSE',
                'overdue_notification_sent': 'BOOLEAN DEFAULT FALSE',
                'created_at': 'TIMESTAMP WITH TIME ZONE DEFAULT NOW()',
                'updated_at': 'TIMESTAMP WITH TIME ZONE DEFAULT NOW()',
            },
            'admin_panel_office': {
                'name': 'VARCHAR(100)',
                'code': 'VARCHAR(20) UNIQUE',
                'address': 'TEXT',
                'city': 'VARCHAR(100)',
                'state': 'VARCHAR(50)',
                'country': 'VARCHAR(100)',
                'postal_code': 'VARCHAR(20)',
                'phone': 'VARCHAR(30)',
                'email': 'VARCHAR(255)',
                'is_active': 'BOOLEAN DEFAULT TRUE',
                'timezone_name': 'VARCHAR(50) DEFAULT \'UTC\'',
                'settings': 'JSONB',
                'created_at': 'TIMESTAMP WITH TIME ZONE DEFAULT NOW()',
                'updated_at': 'TIMESTAMP WITH TIME ZONE DEFAULT NOW()',
            },
        }
        
        with connection.cursor() as cursor:
            for table_name, columns in required_columns.items():
                if table_name in self.existing_tables:
                    # Get existing columns
                    cursor.execute("""
                        SELECT column_name, data_type, is_nullable, column_default
                        FROM information_schema.columns 
                        WHERE table_name = %s
                        ORDER BY ordinal_position;
                    """, [table_name])
                    existing_columns = {row[0]: row for row in cursor.fetchall()}
                    
                    # Check for missing columns
                    missing_columns = set(columns.keys()) - set(existing_columns.keys())
                    
                    if missing_columns:
                        if verbose:
                            self.stdout.write(f"🔧 Table {table_name} missing columns: {', '.join(missing_columns)}")
                        
                        for column_name in missing_columns:
                            column_def = columns[column_name]
                            if verbose:
                                self.stdout.write(f"  + Adding {column_name} {column_def}")
                            
                            if not dry_run:
                                try:
                                    cursor.execute(f"""
                                        ALTER TABLE {table_name} 
                                        ADD COLUMN IF NOT EXISTS {column_name} {column_def};
                                    """)
                                    self.stdout.write(f"✅ Added {table_name}.{column_name}")
                                except Exception as e:
                                    self.stdout.write(self.style.ERROR(f"❌ Failed to add {table_name}.{column_name}: {e}"))
                            else:
                                self.stdout.write(f"WOULD ADD: {table_name}.{column_name}")
                    elif verbose:
                        self.stdout.write(f"✅ Table {table_name} has all required columns")

    def fix_people_table_schema(self, dry_run, verbose):
        """Fix critical people table schema mismatch (id vs contact_id)"""
        if verbose:
            self.stdout.write("🔧 Checking people table schema...")
        
        with connection.cursor() as cursor:
            # Check current people table structure
            cursor.execute("""
                SELECT column_name, data_type
                FROM information_schema.columns 
                WHERE table_name = 'people'
                ORDER BY ordinal_position;
            """)
            current_columns = cursor.fetchall()
            column_names = [col[0] for col in current_columns]
            
            has_id_column = 'id' in column_names
            has_contact_id_column = 'contact_id' in column_names
            
            if has_id_column and not has_contact_id_column:
                if verbose:
                    self.stdout.write("🔧 CRITICAL: People table has 'id' but needs 'contact_id'")
                
                if not dry_run:
                    try:
                        # Check if data alignment is correct (people.id should match contacts.id)
                        cursor.execute("""
                            SELECT COUNT(*) FROM people p 
                            INNER JOIN contacts c ON p.id = c.id 
                            WHERE c.type = 'person';
                        """)
                        aligned_count = cursor.fetchone()[0]
                        
                        cursor.execute("SELECT COUNT(*) FROM people;")
                        total_count = cursor.fetchone()[0]
                        
                        if aligned_count == total_count and total_count > 0:
                            if verbose:
                                self.stdout.write(f"✅ Data alignment verified ({aligned_count}/{total_count})")
                            
                            # Rename the column
                            cursor.execute("ALTER TABLE people RENAME COLUMN id TO contact_id;")
                            if verbose:
                                self.stdout.write("✅ Renamed 'id' to 'contact_id' in people table")
                            
                            # Drop legacy columns that don't belong in people table
                            legacy_columns = ['church_role', 'church_id']
                            for col in legacy_columns:
                                if col in column_names:
                                    cursor.execute(f"ALTER TABLE people DROP COLUMN IF EXISTS {col};")
                                    if verbose:
                                        self.stdout.write(f"✅ Dropped legacy column: {col}")
                        else:
                            self.stdout.write(self.style.ERROR(f"❌ Data alignment mismatch: {aligned_count}/{total_count}"))
                            
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f"❌ Failed to fix people table schema: {e}"))
                else:
                    self.stdout.write("WOULD FIX: Rename people.id to people.contact_id")
                    
            elif has_contact_id_column:
                if verbose:
                    self.stdout.write("✅ People table schema is correct")
                    # Test a quick Django ORM query to verify it works
                    try:
                        from mobilize.contacts.models import Person
                        test_count = Person.objects.count()
                        self.stdout.write(f"✅ Django Person.objects.count() = {test_count}")
                        
                        # Test queryset evaluation 
                        test_people = list(Person.objects.all()[:3])
                        self.stdout.write(f"✅ Django queryset evaluation works - got {len(test_people)} people")
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f"❌ Django ORM test failed: {e}"))
            else:
                if verbose:
                    self.stdout.write("⚠️  People table structure is unexpected")

    def fix_table_naming_mismatches(self, dry_run, verbose):
        """Fix table naming mismatches between Supabase and Django expectations"""
        self.stdout.write(self.style.HTTP_INFO("\n🔄 FIXING TABLE NAMING MISMATCHES"))
        
        # First, fix the critical people table schema mismatch
        self.fix_people_table_schema(dry_run, verbose)
        
        # Check if we have legacy tables that need to be renamed or have data migrated
        table_mappings = {
            'pipeline_contacts': 'pipeline_pipelinecontact',
            'offices': 'admin_panel_office',
        }
        
        with connection.cursor() as cursor:
            for old_name, new_name in table_mappings.items():
                # Check if old table exists
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT 1 FROM information_schema.tables 
                        WHERE table_name = %s AND table_schema = 'public'
                    );
                """, [old_name])
                old_exists = cursor.fetchone()[0]
                
                # Check if new table exists
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT 1 FROM information_schema.tables 
                        WHERE table_name = %s AND table_schema = 'public'
                    );
                """, [new_name])
                new_exists = cursor.fetchone()[0]
                
                if old_exists and not new_exists:
                    if verbose:
                        self.stdout.write(f"🔄 Renaming {old_name} to {new_name}")
                    
                    if not dry_run:
                        try:
                            cursor.execute(f"ALTER TABLE {old_name} RENAME TO {new_name};")
                            self.stdout.write(f"✅ Renamed {old_name} to {new_name}")
                        except Exception as e:
                            self.stdout.write(self.style.ERROR(f"❌ Failed to rename {old_name}: {e}"))
                    else:
                        self.stdout.write(f"WOULD RENAME: {old_name} to {new_name}")
                        
                elif old_exists and new_exists:
                    # Both exist - need to migrate data
                    if verbose:
                        self.stdout.write(f"⚠️  Both {old_name} and {new_name} exist - data migration needed")
                    
                    if not dry_run:
                        # Count records in both tables
                        cursor.execute(f"SELECT COUNT(*) FROM {old_name};")
                        old_count = cursor.fetchone()[0]
                        cursor.execute(f"SELECT COUNT(*) FROM {new_name};")
                        new_count = cursor.fetchone()[0]
                        
                        if old_count > 0 and new_count == 0:
                            self.stdout.write(f"📊 Migrating {old_count} records from {old_name} to {new_name}")
                            # Would need specific migration logic here for each table
                        elif old_count == 0:
                            self.stdout.write(f"🗑️  Dropping empty {old_name} table")
                            cursor.execute(f"DROP TABLE {old_name};")
                        else:
                            self.stdout.write(f"⚠️  Manual review needed for {old_name} ({old_count} records) vs {new_name} ({new_count} records)")

    def create_missing_indexes(self, dry_run, verbose):
        """Create missing indexes for performance"""
        self.stdout.write(self.style.HTTP_INFO("\n🏗️  CREATING MISSING INDEXES"))
        
        # Define critical indexes
        indexes = {
            'users': [
                'CREATE INDEX IF NOT EXISTS users_email_idx ON users(email);',
                'CREATE INDEX IF NOT EXISTS users_role_idx ON users(role);',
                'CREATE INDEX IF NOT EXISTS users_active_role_idx ON users(is_active, role);',
            ],
            'contacts': [
                'CREATE INDEX IF NOT EXISTS contacts_type_idx ON contacts(type);',
                'CREATE INDEX IF NOT EXISTS contacts_office_idx ON contacts(office_id);',
                'CREATE INDEX IF NOT EXISTS contacts_email_idx ON contacts(email);',
                'CREATE INDEX IF NOT EXISTS contacts_first_name_idx ON contacts(first_name);',
                'CREATE INDEX IF NOT EXISTS contacts_last_name_idx ON contacts(last_name);',
                'CREATE INDEX IF NOT EXISTS contacts_priority_idx ON contacts(priority);',
                'CREATE INDEX IF NOT EXISTS contacts_status_idx ON contacts(status);',
                'CREATE INDEX IF NOT EXISTS contacts_created_at_idx ON contacts(created_at);',
            ],
            'communications': [
                'CREATE INDEX IF NOT EXISTS communications_date_idx ON communications(date);',
                'CREATE INDEX IF NOT EXISTS communications_type_idx ON communications(type);',
                'CREATE INDEX IF NOT EXISTS communications_user_idx ON communications(user_id);',
                'CREATE INDEX IF NOT EXISTS communications_status_idx ON communications(status);',
                'CREATE INDEX IF NOT EXISTS communications_gmail_message_idx ON communications(gmail_message_id);',
            ],
            'tasks': [
                'CREATE INDEX IF NOT EXISTS tasks_due_date_idx ON tasks(due_date);',
                'CREATE INDEX IF NOT EXISTS tasks_status_idx ON tasks(status);',
                'CREATE INDEX IF NOT EXISTS tasks_priority_idx ON tasks(priority);',
                'CREATE INDEX IF NOT EXISTS tasks_assigned_to_idx ON tasks(assigned_to_id);',
                'CREATE INDEX IF NOT EXISTS tasks_created_by_idx ON tasks(created_by_id);',
                'CREATE INDEX IF NOT EXISTS tasks_status_due_idx ON tasks(status, due_date);',
            ],
        }
        
        with connection.cursor() as cursor:
            for table_name, table_indexes in indexes.items():
                if table_name in self.existing_tables:
                    for index_sql in table_indexes:
                        if verbose:
                            index_name = index_sql.split('IF NOT EXISTS')[1].split('ON')[0].strip()
                            self.stdout.write(f"🏗️  Creating index: {index_name}")
                        
                        if not dry_run:
                            try:
                                cursor.execute(index_sql)
                                if verbose:
                                    self.stdout.write(f"✅ Created index")
                            except Exception as e:
                                self.stdout.write(self.style.ERROR(f"❌ Failed to create index: {e}"))
                        else:
                            self.stdout.write(f"WOULD CREATE INDEX: {index_sql}")

    def verify_schema_integrity(self, verbose):
        """Verify that the schema is now properly synchronized"""
        self.stdout.write(self.style.HTTP_INFO("\n🔍 VERIFYING SCHEMA INTEGRITY"))
        
        with connection.cursor() as cursor:
            # Check key relationships
            critical_checks = [
                ("users table exists", "SELECT COUNT(*) FROM users LIMIT 1;"),
                ("contacts table exists", "SELECT COUNT(*) FROM contacts LIMIT 1;"),
                ("people table has contact_id", "SELECT contact_id FROM people LIMIT 1;"),
                ("churches table has contact_id", "SELECT contact_id FROM churches LIMIT 1;"),
                ("pipeline_pipelinecontact exists", "SELECT COUNT(*) FROM pipeline_pipelinecontact LIMIT 1;"),
                ("django_session table exists", "SELECT COUNT(*) FROM django_session LIMIT 1;"),
            ]
            
            for check_name, check_sql in critical_checks:
                try:
                    cursor.execute(check_sql)
                    cursor.fetchone()
                    self.stdout.write(f"✅ {check_name}")
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"❌ {check_name}: {e}"))
            
            # Final table count
            cursor.execute("""
                SELECT COUNT(*) FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_type = 'BASE TABLE';
            """)
            table_count = cursor.fetchone()[0]
            self.stdout.write(f"📊 Total tables in database: {table_count}")

    def fix_person_data_integrity(self, dry_run, verbose):
        """Fix Person data integrity issues - NULL PKs and broken FK relationships"""
        self.stdout.write(self.style.HTTP_INFO("\n🔧 FIXING PERSON DATA INTEGRITY ISSUES"))
        
        with connection.cursor() as cursor:
            # Determine the actual primary key column for people table
            cursor.execute("""
                SELECT column_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu 
                    ON tc.constraint_name = kcu.constraint_name
                WHERE tc.table_name = 'people' 
                AND tc.constraint_type = 'PRIMARY KEY'
            """)
            pk_result = cursor.fetchone()
            pk_column = pk_result[0] if pk_result else 'id'
            
            if verbose:
                self.stdout.write(f"   People table primary key: {pk_column}")
            
            # Check for NULL primary keys
            cursor.execute(f"SELECT COUNT(*) FROM people WHERE {pk_column} IS NULL")
            null_pk_count = cursor.fetchone()[0]
            
            if null_pk_count > 0:
                self.stdout.write(f"   🚨 CRITICAL: Found {null_pk_count} Person records with NULL {pk_column}")
                
                if not dry_run:
                    try:
                        # Fix NULL primary keys by setting them to sequential values
                        if pk_column == 'contact_id':
                            # For contact_id PK, set them to match the contact's ID
                            cursor.execute("""
                                UPDATE people 
                                SET contact_id = (
                                    SELECT c.id FROM contacts c 
                                    WHERE c.type = 'person' 
                                    AND NOT EXISTS (
                                        SELECT 1 FROM people p2 
                                        WHERE p2.contact_id = c.id
                                    )
                                    LIMIT 1
                                )
                                WHERE contact_id IS NULL;
                            """)
                        else:
                            # For id PK, use nextval from sequence
                            cursor.execute(f"""
                                UPDATE people 
                                SET {pk_column} = nextval('people_id_seq')
                                WHERE {pk_column} IS NULL;
                            """)
                        
                        # Check how many were fixed
                        cursor.execute(f"SELECT COUNT(*) FROM people WHERE {pk_column} IS NULL")
                        remaining_nulls = cursor.fetchone()[0]
                        fixed_count = null_pk_count - remaining_nulls
                        
                        if fixed_count > 0:
                            self.stdout.write(f"   ✅ Fixed {fixed_count} NULL {pk_column} values")
                        if remaining_nulls > 0:
                            self.stdout.write(f"   ⚠️  {remaining_nulls} NULL {pk_column} values remain")
                            
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f"   ❌ Failed to fix NULL primary keys: {e}"))
                else:
                    self.stdout.write(f"   WOULD FIX: {null_pk_count} NULL {pk_column} values")
            else:
                if verbose:
                    self.stdout.write(f"   ✅ No NULL {pk_column} values found")
            
            # Check for broken Person-Contact relationships
            cursor.execute(f"""
                SELECT COUNT(*) FROM people p
                LEFT JOIN contacts c ON p.contact_id = c.id
                WHERE c.id IS NULL AND p.{pk_column} IS NOT NULL
            """)
            broken_fk_count = cursor.fetchone()[0]
            
            if broken_fk_count > 0:
                self.stdout.write(f"   🚨 Found {broken_fk_count} Person records with invalid contact_id")
                
                if not dry_run:
                    try:
                        # Create basic contact records for orphaned Person records
                        cursor.execute(f"""
                            SELECT p.{pk_column}, p.contact_id, p.title, p.profession 
                            FROM people p
                            LEFT JOIN contacts c ON p.contact_id = c.id
                            WHERE c.id IS NULL AND p.{pk_column} IS NOT NULL
                            LIMIT 20
                        """)
                        orphaned_people = cursor.fetchall()
                        
                        for person_pk, contact_id, title, profession in orphaned_people:
                            # Create a basic contact record
                            cursor.execute("""
                                INSERT INTO contacts (type, first_name, last_name, created_at, updated_at)
                                VALUES ('person', %s, '', NOW(), NOW())
                                RETURNING id
                            """, [title or f'Person {person_pk}'])
                            new_contact_id = cursor.fetchone()[0]
                            
                            # Update Person record with new contact_id
                            cursor.execute(f"""
                                UPDATE people SET contact_id = %s WHERE {pk_column} = %s
                            """, [new_contact_id, person_pk])
                            
                            if verbose:
                                self.stdout.write(f"   ✅ Created Contact {new_contact_id} for Person {person_pk}")
                        
                        self.stdout.write(f"   ✅ Fixed {len(orphaned_people)} broken Person-Contact relationships")
                        
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f"   ❌ Failed to fix broken relationships: {e}"))
                else:
                    self.stdout.write(f"   WOULD FIX: {broken_fk_count} broken Person-Contact relationships")
            else:
                if verbose:
                    self.stdout.write("   ✅ All Person-Contact relationships are valid")
            
            # Verify Django ORM functionality
            try:
                from mobilize.contacts.models import Person
                django_count = Person.objects.count()
                self.stdout.write(f"   📊 Django Person.objects.count() = {django_count}")
                
                # Test queryset evaluation
                test_people = list(Person.objects.all()[:3])
                self.stdout.write(f"   ✅ Django queryset evaluation works - got {len(test_people)} people")
                
                # Test foreign key access
                success_count = 0
                for person in test_people:
                    try:
                        contact = person.contact
                        success_count += 1
                        if verbose:
                            self.stdout.write(f"   ✅ Person {person.pk}: contact={contact.id}")
                    except Exception:
                        pass
                
                if success_count == len(test_people) and len(test_people) > 0:
                    self.stdout.write(f"   ✅ All {success_count} Person-Contact FK relationships work correctly")
                elif success_count > 0:
                    self.stdout.write(f"   ⚠️  {success_count}/{len(test_people)} Person-Contact FK relationships work")
                else:
                    self.stdout.write(f"   ❌ No Person-Contact FK relationships work")
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"   ❌ Django ORM verification failed: {e}"))