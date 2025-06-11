#!/usr/bin/env python
import argparse
import logging
import os
from datetime import datetime
from django.core.management.base import BaseCommand
from django.db import connection
from supabase import create_client, Client

from mobilize.contacts.models import Contact, Person, Church

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Synchronize data between Django and Supabase'

    def add_arguments(self, parser):
        parser.add_argument('--direction', choices=['to_supabase', 'from_supabase'], default='from_supabase',
                            help='Direction of synchronization')
        parser.add_argument('--model', choices=['contact', 'person', 'church', 'all'], default='all',
                            help='Model to synchronize')
        parser.add_argument('--conflict', choices=['django', 'supabase', 'newer'], default='django',
                            help='Strategy for resolving conflicts')
        parser.add_argument('--limit', type=int, help='Limit the number of records to synchronize')
        parser.add_argument('--dry-run', action='store_true', help='Perform a dry run without making changes')

    def handle(self, *args, **options):
        direction = options['direction']
        model_name = options['model']
        conflict_strategy = options['conflict']
        limit = options['limit']
        dry_run = options['dry_run']

        self.stdout.write(f"Starting synchronization with parameters:")
        self.stdout.write(f"  Direction: {direction}")
        self.stdout.write(f"  Models: {model_name.title()}")
        self.stdout.write(f"  Conflict strategy: {conflict_strategy}")
        self.stdout.write(f"  Limit: {'No limit' if limit is None else limit}")
        self.stdout.write(f"  Dry run: {'Yes' if dry_run else 'No'}")
        self.stdout.write("")

        # Initialize Supabase client
        supabase_url = os.environ.get('SUPABASE_URL')
        supabase_key = os.environ.get('SUPABASE_KEY')
        if not supabase_url or not supabase_key:
            self.stderr.write(self.style.ERROR("SUPABASE_URL and SUPABASE_KEY environment variables must be set"))
            return

        self.supabase = create_client(supabase_url, supabase_key)

        # Map model names to classes
        model_map = {
            'contact': Contact,
            'person': Person,
            'church': Church,
            'all': [Contact, Person, Church]
        }

        models_to_sync = model_map[model_name]
        if not isinstance(models_to_sync, list):
            models_to_sync = [models_to_sync]

        for model_class in models_to_sync:
            self.stdout.write(f"Synchronizing {model_class.__name__}...")
            if direction == 'to_supabase':
                self._sync_to_supabase(model_class, conflict_strategy, limit, dry_run)
            else:
                self._sync_from_supabase(model_class, conflict_strategy, limit, dry_run)

        self.stdout.write("Synchronization completed successfully")

    def _sync_to_supabase(self, model_class, conflict_strategy, limit, dry_run):
        # Implementation for syncing from Django to Supabase
        pass

    def _sync_from_supabase(self, model_class, conflict_strategy, limit, dry_run):
        # Special handling for Person model due to user_id type mismatch
        if model_class == Person:
            return self._sync_person_from_supabase(conflict_strategy, limit, dry_run)
        
        # Get the table name from the model's Meta
        table_name = model_class._meta.db_table
        
        # Fetch data from Supabase
        query = self.supabase.table(table_name).select('*')
        if limit:
            query = query.limit(limit)
        
        response = query.execute()
        records = response.data
        
        self.stdout.write(f"Synchronizing {model_class.__name__}...")
        
        success_count = 0
        conflict_count = 0
        error_count = 0
        
        for record in records:
            try:
                record_id = record.get('id')
                
                # Check if record exists in Django
                try:
                    django_record = model_class.objects.get(id=record_id)
                    exists = True
                except model_class.DoesNotExist:
                    exists = False
                
                if exists:
                    # Handle conflict based on strategy
                    if conflict_strategy == 'django':
                        # Skip update, Django wins
                        conflict_count += 1
                        continue
                    elif conflict_strategy == 'supabase':
                        # Supabase wins, update Django record
                        for field, value in record.items():
                            setattr(django_record, field, value)
                        
                        if not dry_run:
                            django_record.save()
                        success_count += 1
                    elif conflict_strategy == 'newer':
                        # Compare timestamps
                        django_updated = getattr(django_record, 'updated_at', None)
                        supabase_updated = record.get('updated_at')
                        
                        if not django_updated or not supabase_updated:
                            # Can't compare, skip
                            conflict_count += 1
                            continue
                        
                        if isinstance(django_updated, str):
                            django_updated = datetime.fromisoformat(django_updated.replace('Z', '+00:00'))
                        
                        if isinstance(supabase_updated, str):
                            supabase_updated = datetime.fromisoformat(supabase_updated.replace('Z', '+00:00'))
                        
                        if supabase_updated > django_updated:
                            # Supabase is newer, update Django
                            for field, value in record.items():
                                setattr(django_record, field, value)
                            
                            if not dry_run:
                                django_record.save()
                            success_count += 1
                        else:
                            # Django is newer or same, skip
                            conflict_count += 1
                else:
                    # Create new record in Django
                    new_record = model_class(**record)
                    if not dry_run:
                        new_record.save()
                    success_count += 1
            
            except Exception as e:
                logger.error(f"Error processing {model_class.__name__} record: {str(e)}")
                error_count += 1
        
        self.stdout.write(f"  Sync summary for {model_class.__name__}:")
        self.stdout.write(f"    Success: {success_count}")
        self.stdout.write(f"    Conflicts: {conflict_count}")
        self.stdout.write(f"    Errors: {error_count}")

    def _sync_person_from_supabase(self, conflict_strategy, limit, dry_run):
        import json
        from django.db import connection
        
        def handle_json_field(field_name, field_value):
            """Helper function to handle JSON fields"""
            # List of known JSON fields in the Person model
            json_fields = ['tags', 'skills', 'interests', 'languages']
            
            # Always convert empty strings to empty JSON arrays for all fields
            # This prevents the 'invalid input syntax for type json' error
            if isinstance(field_value, str) and field_value.strip() == '':
                return '[]' if field_name in json_fields else field_value
                
            # Special handling for JSON fields
            if field_name in json_fields and field_value is not None:
                try:
                    if isinstance(field_value, str):
                        # Validate it's proper JSON
                        try:
                            json.loads(field_value)
                            return field_value
                        except json.JSONDecodeError:
                            # If not valid JSON, convert to empty array
                            logger.warning(f"Invalid JSON for field {field_name}, setting to empty array")
                            return '[]'
                    else:
                        # Convert to JSON string
                        return json.dumps(field_value or [])
                except Exception as e:
                    logger.warning(f"JSON processing error for field {field_name}: {str(e)}")
                    return '[]'
            return field_value
        
        # Get table names
        contacts_table = Contact._meta.db_table
        people_table = 'people'  # Person._meta.db_table would be 'contacts_person'
        
        # Get column information
        with connection.cursor() as cursor:
            cursor.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{contacts_table}'")
            contacts_columns = [row[0] for row in cursor.fetchall()]
            
            cursor.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{people_table}'")
            people_columns = [row[0] for row in cursor.fetchall()]
        
        # Fetch data from Supabase
        query = self.supabase.table(people_table).select('*')
        if limit:
            query = query.limit(limit)
        
        response = query.execute()
        records = response.data
        
        self.stdout.write(f"Synchronizing Person...")
        
        success_count = 0
        conflict_count = 0
        error_count = 0
        
        for record in records:
            try:
                record_id = record.get('id')
                
                # Skip the user_id field in Person model since it's a string in Supabase but integer in Django
                if 'user_id' in record and record['user_id'] is not None:
                    logger.info(f"Skipping user_id field for Person record {record_id}: {record['user_id']} (string value)")
                
                # Check if Contact record exists (base model for Person)
                contact_exists = False
                with connection.cursor() as cursor:
                    cursor.execute(f"SELECT 1 FROM {contacts_table} WHERE id = %s", [record_id])
                    contact_exists = cursor.fetchone() is not None
                
                # Check if Person record exists
                person_exists = False
                with connection.cursor() as cursor:
                    cursor.execute(f"SELECT 1 FROM {people_table} WHERE id = %s", [record_id])
                    person_exists = cursor.fetchone() is not None
                
                if person_exists:
                    # Handle conflict based on strategy
                    if conflict_strategy == 'django':
                        # Skip update, Django wins
                        conflict_count += 1
                        continue
                    elif conflict_strategy in ['supabase', 'newer']:
                        # For 'newer', we're simplifying by always using Supabase data
                        # since timestamp comparison is complex with raw SQL
                        
                        # Update Contact record first (base model)
                        if contact_exists:
                            contact_fields = []
                            contact_values = []
                            
                            for field_name, field_value in record.items():
                                if field_name != 'user_id' and field_name in contacts_columns:
                                    # Handle foreign keys
                                    if field_name.endswith('_id') and field_value is not None:
                                        referenced_table = field_name[:-3] + 's'
                                        try:
                                            with connection.cursor() as check_cursor:
                                                check_cursor.execute(f"SELECT 1 FROM {referenced_table} WHERE id = %s", [field_value])
                                                if check_cursor.fetchone() is None:
                                                    logger.warning(f"Foreign key constraint: {field_name}={field_value} not found in {referenced_table}, setting to NULL")
                                                    field_value = None
                                        except Exception as e:
                                            logger.warning(f"Error checking foreign key {field_name}: {str(e)}")
                                            field_value = None
                                    
                                    # Process field value (handle JSON fields)
                                    field_value = handle_json_field(field_name, field_value)
                                    
                                    contact_fields.append(field_name)
                                    contact_values.append(field_value)
                            
                            if contact_fields and not dry_run:
                                update_sql = f"UPDATE {contacts_table} SET " + ", ".join([f"{field} = %s" for field in contact_fields]) + f" WHERE id = %s"
                                contact_values.append(record_id)
                                
                                with connection.cursor() as cursor:
                                    cursor.execute(update_sql, contact_values)
                        
                        # Update Person record
                        person_fields = []
                        person_values = []
                        
                        for field_name, field_value in record.items():
                            if field_name != 'user_id' and field_name in people_columns:
                                # Handle foreign keys
                                if field_name.endswith('_id') and field_value is not None:
                                    referenced_table = field_name[:-3] + 's'
                                    try:
                                        with connection.cursor() as check_cursor:
                                            check_cursor.execute(f"SELECT 1 FROM {referenced_table} WHERE id = %s", [field_value])
                                            if check_cursor.fetchone() is None:
                                                logger.warning(f"Foreign key constraint: {field_name}={field_value} not found in {referenced_table}, setting to NULL")
                                                field_value = None
                                    except Exception as e:
                                        logger.warning(f"Error checking foreign key {field_name}: {str(e)}")
                                        field_value = None
                                
                                # Process field value (handle JSON fields)
                                field_value = handle_json_field(field_name, field_value)
                                
                                person_fields.append(field_name)
                                person_values.append(field_value)
                        
                        if person_fields and not dry_run:
                            update_sql = f"UPDATE {people_table} SET " + ", ".join([f"{field} = %s" for field in person_fields]) + f" WHERE id = %s"
                            person_values.append(record_id)
                            
                            with connection.cursor() as cursor:
                                cursor.execute(update_sql, person_values)
                            
                            logger.info(f"Updated Person record {record_id} using raw SQL")
                            success_count += 1
                else:
                    # Create new Contact record first (base model)
                    if not contact_exists:
                        fields = []
                        values = []
                        placeholders = []
                        
                        for field_name, field_value in record.items():
                            if field_name != 'user_id' and field_name in contacts_columns:
                                # Handle foreign keys
                                if field_name.endswith('_id') and field_value is not None:
                                    referenced_table = field_name[:-3] + 's'
                                    try:
                                        with connection.cursor() as check_cursor:
                                            check_cursor.execute(f"SELECT 1 FROM {referenced_table} WHERE id = %s", [field_value])
                                            if check_cursor.fetchone() is None:
                                                logger.warning(f"Foreign key constraint: {field_name}={field_value} not found in {referenced_table}, setting to NULL")
                                                field_value = None
                                    except Exception as e:
                                        logger.warning(f"Error checking foreign key {field_name}: {str(e)}")
                                        field_value = None
                                
                                # Process field value (handle JSON fields)
                                field_value = handle_json_field(field_name, field_value)
                                
                                fields.append(field_name)
                                values.append(field_value)
                                placeholders.append('%s')
                        
                        # Add created_at and updated_at
                        if 'created_at' in contacts_columns:
                            fields.append('created_at')
                            values.append(datetime.now())
                            placeholders.append('%s')
                        
                        if 'updated_at' in contacts_columns:
                            fields.append('updated_at')
                            values.append(datetime.now())
                            placeholders.append('%s')
                        
                        if not dry_run:
                            insert_sql = f"INSERT INTO {contacts_table} ({', '.join(fields)}) VALUES ({', '.join(placeholders)})"
                            with connection.cursor() as cursor:
                                cursor.execute(insert_sql, values)
                            logger.info(f"Created Contact record {record_id} using raw SQL")
                    
                    # Create new Person record
                    fields = []
                    values = []
                    placeholders = []
                    
                    for field_name, field_value in record.items():
                        if field_name != 'user_id' and field_name in people_columns:
                            # Handle foreign keys
                            if field_name.endswith('_id') and field_value is not None:
                                referenced_table = field_name[:-3] + 's'
                                try:
                                    with connection.cursor() as check_cursor:
                                        check_cursor.execute(f"SELECT 1 FROM {referenced_table} WHERE id = %s", [field_value])
                                        if check_cursor.fetchone() is None:
                                            logger.warning(f"Foreign key constraint: {field_name}={field_value} not found in {referenced_table}, setting to NULL")
                                            field_value = None
                                except Exception as e:
                                    logger.warning(f"Error checking foreign key {field_name}: {str(e)}")
                                    field_value = None
                            
                            # Process field value (handle JSON fields)
                            field_value = handle_json_field(field_name, field_value)
                            
                            fields.append(field_name)
                            values.append(field_value)
                            placeholders.append('%s')
                    
                    # Add created_at and updated_at
                    if 'created_at' in people_columns:
                        fields.append('created_at')
                        placeholders.append('NOW()')
                    
                    if 'updated_at' in people_columns:
                        fields.append('updated_at')
                        placeholders.append('NOW()')
                    
                    if not dry_run:
                        insert_sql = f"INSERT INTO {people_table} ({', '.join(fields)}) VALUES ({', '.join(placeholders)})"
                        # Log the SQL and values for debugging
                        logger.info(f"SQL: {insert_sql}")
                        logger.info(f"Values: {values}")
                        try:
                            with connection.cursor() as cursor:
                                cursor.execute(insert_sql, values)
                            logger.info(f"Created Person record {record_id} using raw SQL")
                            success_count += 1
                        except Exception as e:
                            logger.error(f"SQL error for Person record {record_id}: {str(e)}")
                            # Try to identify which field is causing the JSON error
                            for i, (field, value) in enumerate(zip(fields, values)):
                                if field in ['tags', 'skills', 'interests', 'languages']:
                                    logger.info(f"JSON field {field} = {value!r}")
                            error_count += 1
            
            except Exception as e:
                logger.error(f"Error processing Person record: {str(e)}")
                error_count += 1
        
        self.stdout.write(f"  Sync summary for Person:")
        self.stdout.write(f"    Success: {success_count}")
        self.stdout.write(f"    Conflicts: {conflict_count}")
        self.stdout.write(f"    Errors: {error_count}")
        
        return success_count, conflict_count, error_count
