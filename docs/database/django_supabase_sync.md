# Django and Supabase Schema Synchronization

This document outlines the synchronization between Django models and the Supabase database schema.

## Synchronization Strategy

We've encountered challenges with Django's migration system when trying to synchronize our models with the existing Supabase schema. The main issues are:

1. Field name conflicts between parent and child models (e.g., `first_name` in both Contact and Person)
2. Field type differences between Django models and Supabase schema
3. Existing migrations in the codebase that conflict with our changes

To address these issues, we've adopted the following strategy:

1. **Avoid field overrides in child models**: Instead of overriding fields in child models (Person, Church) that already exist in the parent model (Contact), we'll handle any differences at the data layer.
2. **Use the existing field names**: We'll use the field names that already exist in the Django models (e.g., `church_name` instead of `name` for Church).
3. **Document the mapping**: We'll document the mapping between Django model fields and Supabase schema fields for reference.

## Contact Model

The `Contact` model serves as the base model for both `Person` and `Church` models. It contains common fields that are shared between these two models.

### Fields from Supabase `contacts` table

- `id`: Primary key
- `first_name`: First name of the contact
- `last_name`: Last name of the contact
- `church_name`: Name of the church (used for Church model)
- `email`: Email address
- `phone`: Phone number
- `preferred_contact_method`: Preferred method of contact
- `street_address`: Street address
- `city`: City
- `state`: State
- `zip_code`: ZIP code
- `country`: Country
- `notes`: General notes
- `created_at`: Creation timestamp
- `updated_at`: Last update timestamp
- `type`: Type of contact (person, church)
- `user_id`: ID of the user who owns this contact
- `office_id`: ID of the office this contact belongs to
- `google_contact_id`: Google Contact ID for integration
- `conflict_data`: JSON data for conflict resolution
- `has_conflict`: Boolean indicating if there's a conflict
- `last_synced_at`: Last synchronization timestamp

## Person Model

The `Person` model extends the `Contact` model and adds person-specific fields.

### Fields from Supabase `people` table

- All fields inherited from `Contact`
- `title`: Title (Mr., Mrs., Dr., etc.)
- `birthday`: Date of birth
- `anniversary`: Anniversary date
- `marital_status`: Marital status
- `spouse_first_name`: First name of spouse
- `spouse_last_name`: Last name of spouse
- `home_country`: Home country
- `languages`: Languages spoken
- `occupation`: Occupation
- `employer`: Employer
- `skills`: Skills
- `interests`: Interests
- `church_id`: ID of the church they belong to
- `church_role`: Role in the church
- `is_primary_contact`: Whether they are the primary contact
- `pipeline_stage`: Stage in the pipeline
- `people_pipeline`: Pipeline category
- `priority`: Priority level
- `status`: Current status
- `last_contact`: Date of last contact
- `next_contact`: Date of next planned contact
- `date_closed`: Date when closed
- `info_given`: Information provided
- `desired_service`: Service they are interested in
- `reason_closed`: Reason for closing
- `tags`: Tags
- `assigned_to`: Person assigned to handle this contact
- `source`: Source of the contact
- `referred_by`: Who referred this contact
- `website`: Website
- `facebook`: Facebook profile
- `twitter`: Twitter profile
- `linkedin`: LinkedIn profile
- `instagram`: Instagram profile
- `virtuous`: Virtuous integration flag

### Field Mapping Notes

- In Supabase, the `people` table has its own `first_name`, `last_name`, `type`, etc. fields, which would conflict with those inherited from Contact. We're using the inherited fields and will handle any differences at the data layer.
- The `user_id` field in Supabase's `people` table is a character varying, while in Django's Contact model it's an integer. We'll handle this difference at the data layer.

## Church Model

The `Church` model extends the `Contact` model and adds church-specific fields.

### Fields from Supabase `churches` table

- All fields inherited from `Contact`
- `location`: Location description
- `denomination`: Denomination
- `year_founded`: Year founded
- `congregation_size`: Size of congregation
- `weekly_attendance`: Weekly attendance
- `senior_pastor_name`: Name of senior pastor
- `senior_pastor_first_name`: First name of senior pastor
- `senior_pastor_last_name`: Last name of senior pastor
- `senior_pastor_phone`: Phone of senior pastor
- `senior_pastor_email`: Email of senior pastor
- `missions_pastor_first_name`: First name of missions pastor
- `missions_pastor_last_name`: Last name of missions pastor
- `mission_pastor_phone`: Phone of missions pastor
- `mission_pastor_email`: Email of missions pastor
- `primary_contact_first_name`: First name of primary contact
- `primary_contact_last_name`: Last name of primary contact
- `primary_contact_phone`: Phone of primary contact
- `primary_contact_email`: Email of primary contact
- `main_contact_id`: ID of main contact
- `website`: Website
- `church_pipeline`: Pipeline category
- `priority`: Priority level
- `assigned_to`: Person assigned to handle this church
- `virtuous`: Virtuous integration flag
- `date_closed`: Date when closed
- `source`: Source of the church contact
- `referred_by`: Who referred this church
- `info_given`: Information provided
- `reason_closed`: Reason for closing
- `owner_id`: ID of the owner

### Church Field Mapping Notes

- In Supabase, the `churches` table uses `name` for the church name, while our Django model uses `church_name` (inherited from Contact). We'll use `church_name` in Django and handle the mapping at the data layer.
- The `office_id` field exists in both Contact and Church tables in Supabase. We'll use the inherited field from Contact.

## Form Updates

### Church Form

The `ChurchForm` has been updated to include all the fields from the `Church` model that are relevant for user input. The form layout has been organized into logical sections for better user experience.

### ImportChurchesForm

The `ImportChurchesForm` has been updated to include instructions for the CSV format that matches the fields in the `Church` model.

## Data Layer Considerations

To handle the differences between Django models and Supabase schema, we'll need to implement custom logic in the data layer:

1. **Field name mapping**: When saving or retrieving data, map between Django field names and Supabase column names as needed.
2. **Field type conversion**: Handle type conversions (e.g., integer to string for user_id) when interacting with Supabase.
3. **Custom queries**: Use raw SQL or custom ORM queries when necessary to handle complex mapping scenarios.

### Additional Form Fields

- Added optional fields: `location`, `website`, `assigned_to`, `source`, `referred_by`

## Implementation Status

### Migrations

We've successfully created and applied the following migrations:

1. `contacts/migrations/0002_update_models_for_supabase.py`: Adds new fields to the Contact model using conditional SQL to avoid duplicate column errors.
2. `churches/migrations/0002_update_church_for_supabase.py`: Adds new fields to the Church model using conditional SQL to avoid duplicate column errors.
3. `contacts/migrations/0004_merge_20250605_1240.py`: Merge migration to resolve conflicts between migration branches.
4. `churches/migrations/0004_merge_20250605_1240.py`: Merge migration to resolve conflicts between migration branches.

All migrations have been successfully applied to the database.

### Model Updates

1. **Contact Model**: Updated to match Supabase schema with appropriate field types and nullability.
2. **Person Model**: Updated to inherit from Contact without overriding conflicting fields. Type differences (e.g., `user_id` as string in Supabase vs integer in Django) will be handled by the SupabaseMapper.
3. **Church Model**: Updated to include Supabase-specific fields like `name` (which maps to `church_name` in Django), `weekly_attendance`, `senior_pastor_name`, etc.

### Synchronization Utilities

We've implemented three key utilities for handling synchronization between Django models and Supabase:

1. **SupabaseClient**: A utility class that provides a direct interface to the Supabase database using the official Supabase Python client. It provides methods for:
   - Fetching all records from a table (`fetch_all`)
   - Fetching a specific record by ID (`fetch_by_id`)
   - Inserting new records (`insert`)
   - Updating existing records (`update`)
   - Deleting records (`delete`)
   - Error handling and logging for all operations

2. **SupabaseMapper**: A utility class that handles field name mapping and type conversions between Django models and Supabase schema. It provides methods for:
   - Converting Django model instances to Supabase-compatible dictionaries (`to_supabase`)
   - Converting Supabase data to Django-compatible dictionaries (`from_supabase`)
   - Creating new Django model instances from Supabase data (`create_from_supabase`)
   - Updating existing Django model instances from Supabase data (`update_from_supabase`)
   - Bulk operations for converting multiple records at once

3. **SupabaseSync**: A higher-level utility that builds on SupabaseMapper and SupabaseClient to provide synchronization functionality:
   - Synchronizing Django model instances to Supabase (`sync_to_supabase`) using the real Supabase client
   - Synchronizing Supabase data to Django models (`sync_from_supabase`) with proper error handling
   - Bulk synchronization operations with detailed reporting
   - Conflict detection and resolution with customizable strategies

### Management Command

A Django management command `sync_supabase` has been implemented to provide a command-line interface for synchronization operations:

```bash
python manage.py sync_supabase [options]
```

**Options:**

- `--direction`: Direction of synchronization (`to_supabase`, `from_supabase`, or `both`)
- `--model`: Model to synchronize (`contact`, `person`, `church`, or `all`)
- `--conflict-strategy`: Strategy for resolving conflicts (`django`, `supabase`, or `skip`)
- `--limit`: Limit the number of records to synchronize
- `--dry-run`: Perform a dry run without making any changes
- `--verbose`: Show detailed output

**Example usage:**

```bash
# Sync all models in both directions
python manage.py sync_supabase

# Sync only Contact model to Supabase
python manage.py sync_supabase --direction=to_supabase --model=contact

# Dry run with verbose output
python manage.py sync_supabase --dry-run --verbose
```

The command includes error handling for missing database tables and provides detailed feedback on the synchronization process.

### Unit Tests

We've created comprehensive unit tests to ensure the synchronization utilities work correctly:

1. **SupabaseMapper Tests**: Verify field name mapping, type conversions, and bulk operations.
2. **SupabaseSync Tests**: Verify synchronization functionality, conflict detection, and resolution strategies.
3. **Model-Specific Tests**: Verify that the synchronization utilities work correctly with our actual models (Contact, Person, Church).

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

## Next Steps

1. ✅ Run migrations to update the database schema
2. ✅ Implement and test the SupabaseMapper utility
3. ✅ Implement the SupabaseSync utility for data synchronization
4. ✅ Create unit tests for the synchronization utilities
5. ✅ Implement a command-line interface for synchronization operations
6. ✅ Add logging and error handling for synchronization operations
7. ✅ Implement Supabase client integration for two-way synchronization
8. Create a scheduled task for regular synchronization
9. Update any views that reference the updated fields
10. Update any templates that display the updated fields
11. Consider implementing automated schema synchronization between Django and Supabase
12. Implement batch processing for large datasets
13. Add more detailed conflict resolution strategies
14. Extend synchronization to additional models beyond Contact, Person, and Church

## Notes

- Field types have been matched to the Supabase schema (e.g., using TextField for text fields, CharField for character varying fields)
- Some fields in the Person and Church models override fields from the Contact model to ensure they match the Supabase schema exactly
- The database table names have been set to match the Supabase table names using the Meta class
