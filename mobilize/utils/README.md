# Mobilize Django Utilities

## Supabase Synchronization Utilities

This directory contains utilities for synchronizing data between Django models and Supabase. The integration uses the official Supabase Python client to provide robust bi-directional synchronization with proper error handling and logging.

### SupabaseMapper

The `SupabaseMapper` utility handles field mapping and type conversion between Django models and Supabase.

```python
from mobilize.utils.supabase_mapper import SupabaseMapper

# Convert a Django model instance to Supabase format
supabase_data = SupabaseMapper.to_supabase(django_instance)

# Convert Supabase data to Django format
django_data = SupabaseMapper.from_supabase(supabase_data, model_class)

# Create a new Django model instance from Supabase data
new_instance = SupabaseMapper.create_from_supabase(supabase_data, model_class)

# Update an existing Django model instance with Supabase data
updated_instance = SupabaseMapper.update_from_supabase(django_instance, supabase_data)
```

### SupabaseClient

The `SupabaseClient` utility provides direct access to the Supabase database through the official Python client:

```python
from mobilize.utils.supabase_client import supabase

# Fetch all records from a table
records = supabase.fetch_all(Contact)

# Fetch a specific record by ID
record = supabase.fetch_by_id(Contact, record_id)

# Insert a new record
new_record = supabase.insert(Contact, data)

# Update an existing record
updated_record = supabase.update(Contact, record_id, data)

# Delete a record
supabase.delete(Contact, record_id)
```

### SupabaseSync

The `SupabaseSync` utility provides higher-level synchronization functionality using the Supabase client:

```python
from mobilize.utils.supabase_sync import SupabaseSync

# Sync a Django model instance to Supabase
supabase_data = SupabaseSync.sync_to_supabase(django_instance)

# Sync Supabase data to a Django model (create or update)
django_instance = SupabaseSync.sync_from_supabase(supabase_data, model_class)

# Detect conflicts between Django and Supabase data
conflicts = SupabaseSync.detect_conflicts(django_instance, supabase_data)

# Resolve conflicts using a specific strategy
resolved_data = SupabaseSync.resolve_conflicts(
    django_instance, 
    supabase_data, 
    strategy='django'  # or 'supabase' or 'skip'
)
```

### Management Command

A Django management command is available for synchronizing data from the command line:

```bash
# Sync all models in both directions
python manage.py sync_supabase

# Sync only Contact model to Supabase
python manage.py sync_supabase --direction=to_supabase --model=contact

# Dry run with verbose output
python manage.py sync_supabase --dry-run --verbose
```

Available options:

- `--direction`: Direction of synchronization (`to_supabase`, `from_supabase`, or `both`)
- `--model`: Model to synchronize (`contact`, `person`, `church`, or `all`)
- `--conflict-strategy`: Strategy for resolving conflicts (`django`, `supabase`, or `skip`)
- `--limit`: Limit the number of records to synchronize
- `--dry-run`: Perform a dry run without making any changes
- `--verbose`: Show detailed output

## Configuration

The Supabase client requires the following environment variables or Django settings:

- `SUPABASE_URL`: The URL of your Supabase project
- `SUPABASE_KEY`: The API key for your Supabase project

These can be set in your `.env` file or in Django settings:

```python
# settings.py
SUPABASE_URL = 'https://your-project.supabase.co'
SUPABASE_KEY = 'your-supabase-key'
```

## Next Steps for Supabase Integration

1. ✅ Implement Supabase client integration for two-way synchronization
2. Create a scheduled task for regular synchronization
3. Add support for additional models beyond Contact, Person, and Church
4. Implement batch processing for large datasets
5. Add more detailed conflict resolution strategies
