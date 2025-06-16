# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# Mobilize CRM - Django Project Architecture Guide

## Project Overview

Mobilize CRM is a comprehensive Customer Relationship Management system built with Django for managing church and missionary contacts, communications, and tasks. The system is designed specifically for non-profit organizations to track relationships with churches, contacts, and supporters through customizable pipeline stages.

### Key Technologies
- **Backend**: Django 4.2, Python 3.9+, PostgreSQL
- **Authentication**: Google OAuth (Firebase Authentication removed)
- **Frontend**: Django Templates, Bootstrap 5, HTML5, CSS3, JavaScript
- **Integrations**: Google Gmail, Calendar, Contacts APIs
- **Database**: Local PostgreSQL (development), Supabase PostgreSQL (production)
- **Background Tasks**: Celery, Redis

## Project Structure and Architecture

### Django Apps Organization
The project follows Django best practices with focused, single-responsibility apps:

```
mobilize/
├── authentication/     # Custom user model, roles, permissions
├── admin_panel/       # Office management, multi-tenancy
├── churches/          # Church contact management
├── communications/    # Email integration, templates, history
├── contacts/          # Base contact model (Person/Church inherit)
├── core/             # Dashboard, activity logs, shared utilities
├── pipeline/         # Pipeline stage management
├── tasks/            # Task management, recurring tasks
└── utils/            # Supabase sync, mappers, shared utilities
```

### Database Architecture

#### Core Models Hierarchy
- **Contact**: Base model for all contact types (people, churches)
- **Person**: Extends Contact for individual contacts
- **Church**: Extends Contact for church organizations
- **User**: Custom user model with role-based permissions
- **Task**: Task management with Google Calendar integration
- **Communication**: Email history and templates

#### Key Relationships
- Contact → Person/Church (inheritance via OneToOne)
- User ↔ Office (many-to-many through UserOffice)
- Contact → Communications (one-to-many)
- Contact → Tasks (one-to-many)
- User → GoogleToken (one-to-many for API access)

### Supabase Integration
The system includes sophisticated two-way synchronization with Supabase:
- **SupabaseMapper**: Handles field mapping and type conversions
- **Conflict Resolution**: Manages data conflicts between Django and Supabase
- **Management Command**: `sync_supabase` for automated synchronization

## Development Commands

### Environment Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Environment variables
cp .env.example .env
# Edit .env with your database credentials and API keys
```

### Database Operations
```bash
# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Reset database (use reset_db.sql if needed)
python manage.py flush

# Check database tables
python check_tables.py
```

### Development Server
```bash
# Always kill processes on port 8000 first
lsof -ti:8000 | xargs kill -9 2>/dev/null || true

# Run development server
python manage.py runserver 0.0.0.0:8000
```

### Testing
```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test mobilize.authentication
python manage.py test mobilize.churches
python manage.py test mobilize.contacts
python manage.py test mobilize.utils.tests.test_supabase_mapper

# Run with pytest (preferred)
pytest
pytest mobilize/contacts/tests/
pytest -v --tb=short

# Coverage reporting
coverage run --source='.' manage.py test
coverage report
coverage html
```

### Code Quality
```bash
# Format code
black .

# Sort imports
isort .

# Lint code
flake8

# Run all quality checks together
black . && isort . && flake8

# Type checking (if mypy is added)
mypy mobilize/
```

### Supabase Synchronization
```bash
# Sync contacts to Supabase
python manage.py sync_to_supabase

# Sync from Supabase
python manage.py sync_from_supabase

# Manual sync (both directions) - if implemented
python manage.py sync_supabase --direction=both

# Full sync (ignores timestamps) - if implemented
python manage.py sync_supabase --direction=both --full
```

### Background Tasks
```bash
# Start Celery worker (when implemented)
celery -A mobilize worker -l info

# Start Celery beat (scheduled tasks)
celery -A mobilize beat -l info

# Generate recurring tasks
python manage.py generate_recurring_tasks
```

## Key Architectural Patterns

### Role-Based Access Control
The system implements a sophisticated permission system:

```python
# User roles hierarchy
ROLES = [
    'super_admin',    # Full system access
    'office_admin',   # Office-level management
    'standard_user',  # Standard CRUD operations
    'limited_user',   # Read-only access
]

# Permission checking
@admin_required
def office_management_view(request):
    # Only super_admin and office_admin can access
    pass

# Data visibility rules
# - Super admins: See all data across offices
# - Office admins: See data for their assigned offices
# - Standard users: See only data assigned to them
# - Limited users: Read-only access to assigned data
```

### Multi-Office Support
Users can be assigned to multiple offices with different roles:

```python
# UserOffice model handles office assignments
user_office = UserOffice.objects.create(
    user=user,
    office=office,
    role='office_admin'
)

# Check office permissions
if user.has_office_permission(office_id, 'office_admin'):
    # Allow office admin actions
```

### Supabase Synchronization Pattern
The system maintains data consistency between Django and Supabase using the SupabaseMapper utility:

```python
# SupabaseMapper handles field conversions and type mapping
# TYPE_MAPPING converts Django fields to Supabase format
TYPE_MAPPING = {
    'Person.user_id': {
        'to_supabase': lambda x: str(x) if x else None,
        'from_supabase': lambda x: int(x) if x else None
    },
    'office_id': {
        'to_supabase': lambda x: str(x) if x else None,
        'from_supabase': lambda x: int(x) if x else None
    }
}

# FIELD_MAPPING handles model-specific field transformations
# Most models pass data through unchanged, but customizable per model

# Convert Django model to Supabase format
supabase_data = SupabaseMapper.to_supabase(django_instance)

# Convert Supabase data to Django format  
django_data = SupabaseMapper.from_supabase(supabase_data, ModelClass)

# Handle conflicts automatically
if has_conflict:
    resolve_conflict(django_instance, supabase_data)
```

### Activity Logging
Comprehensive audit trail for all user actions:

```python
# Log user activities automatically
ActivityLog.log_activity(
    user=request.user,
    action_type='create',
    entity_type='person',
    entity_id=person.id,
    request=request
)
```

## Configuration Files

### Django Settings (`mobilize/settings.py`)
- Database configuration for PostgreSQL
- Google OAuth settings
- Supabase connection details
- Logging configuration
- Cron job scheduling
- Static files and media handling

### Environment Variables (`.env`)
```env
# Django configuration
DJANGO_SECRET_KEY=your-secret-key
DJANGO_DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DB_NAME=mobilize
DB_USER=postgres
DB_PASS=your-password
DB_HOST=localhost
DB_PORT=5432

# Google OAuth
GOOGLE_CLIENT_ID=your-client-id
GOOGLE_CLIENT_SECRET=your-client-secret

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-key
```

### Development Rules (`.windsurfrules`)
The project includes comprehensive development guidelines covering:
- Code quality standards (PEP 8, Black formatting)
- Git workflow (branching, commit messages)
- Testing requirements (80% coverage minimum)
- Security practices
- Performance considerations
- Django-specific patterns

## Google API Integrations

### Gmail Integration
- OAuth2 authentication flow
- Email synchronization and sending
- Thread management
- Communication history tracking
- Template system with variables

### Google Calendar Integration
- Event creation and synchronization
- Task scheduling integration
- Recurring event support
- Notification management

### Google Contacts Integration
- Contact synchronization with CRM
- Conflict detection and resolution
- User-configurable sync preferences
- Batch operations support

## Testing Strategy

### Test Structure
```
{app}/tests/
├── test_{model}_model.py    # Model validation and relationships
├── test_{view}_views.py     # View logic and permissions  
├── test_forms.py           # Form validation
├── test_permissions.py     # Role-based access control
└── test_supabase.py        # Supabase integration (in utils app)
```

### Testing Patterns
- Model tests validate business logic and relationships
- View tests check permissions and response handling
- Integration tests verify Google API interactions
- Supabase tests ensure data consistency
- Mock external dependencies (Supabase API, Google services)
- Office-level data scoping tests ensure proper isolation

### Test Data Management
- Use Django fixtures for consistent test data
- Factory pattern for complex object creation
- Mock external API calls (Google services, Supabase)
- Separate test database configuration
- Test coverage expectations: Models 100%, Views comprehensive permission testing

### Common Test Issues
- SupabaseMapper tests: Use correct TYPE_MAPPING keys (e.g., 'Person.user_id' not 'user_id')
- Field mapping tests: Most models have empty FIELD_MAPPING (data passes through unchanged)
- External API tests: Mock unavailable dependencies to avoid ModuleNotFoundError

## Deployment Architecture

### Development Environment
- Local PostgreSQL database
- Django development server
- Debug toolbar enabled
- Comprehensive logging to console and files

### Production Environment (Planned)
- Google Cloud Run for hosting
- Supabase PostgreSQL database
- Google Cloud Storage for static/media files
- Redis for caching and Celery
- Continuous deployment pipeline

## Performance Considerations

### Database Optimization
- Appropriate indexes on frequently queried fields
- Use of `select_related` and `prefetch_related`
- Pagination for large datasets
- Query optimization with Django Debug Toolbar

### Caching Strategy
- Template fragment caching for dashboard widgets
- QuerySet caching for frequently accessed data
- Redis integration for session storage
- Google API response caching

### Frontend Performance
- Bootstrap 5 for responsive design
- Lazy loading for data tables
- Progressive enhancement with JavaScript
- Optimized static file delivery

## Security Implementation

### Authentication Security
- Google OAuth2 integration
- Secure session management
- CSRF protection enabled
- Rate limiting planned

### Data Security
- Role-based access control
- Office-level data segregation
- Input validation and sanitization
- Audit trail for all actions

### API Security
- Google API token management
- Refresh token rotation
- Scope limitation for API access
- Error handling without information leakage

## Static Files Management

The project uses Django's static files system:

- `/static/`: Project-level static files (CSS, JS, images)  
- `/staticfiles/`: Auto-generated during collectstatic
- Custom CSS files: `static/css/base.css`, `static/css/responsive.css`
- No app-level static directories to avoid duplication

### CSS Architecture

- `base.css`: Core design system with CSS custom properties, brand colors, typography
- `responsive.css`: Mobile-first responsive design with comprehensive breakpoints
- Bootstrap 5 integration with custom overrides
- Accessibility features: focus states, skip links, high contrast support

## Common Development Tasks

### Adding a New Model

1. Create model in appropriate app with office_id field for data scoping
2. Add to Supabase mapper TYPE_MAPPING if field conversions needed
3. Create and run migrations: `python manage.py makemigrations && python manage.py migrate`
4. Add comprehensive tests for model (aim for 100% coverage)
5. Update admin interface if needed

### Implementing New Permissions

1. Add permission to User model or create custom permission
2. Create permission decorator following existing patterns
3. Update view with @admin_required, @permission_required, or similar
4. Add tests for all permission scenarios (different roles, office access)
5. Update UI to reflect permission changes

### Adding Google API Integration

1. Configure API credentials in settings and .env
2. Create service class for API interaction following existing patterns
3. Handle OAuth2 flow and token management (refresh tokens)
4. Implement error handling and retries for API failures
5. Add tests with mocked API responses (avoid external dependencies)

### Working with Supabase Integration

1. Update TYPE_MAPPING in SupabaseMapper for new field types
2. Test field conversions with unit tests
3. Handle conflicts between Django and Supabase data
4. Use management commands for bulk sync operations
5. Mock Supabase API calls in tests

### Debugging Common Issues

- Check `.env` file for missing variables
- Verify database connection and migrations status
- Review Google API credentials and scopes
- Check Supabase synchronization logs and TYPE_MAPPING
- Use Django Debug Toolbar for query analysis
- Kill port 8000 processes if server won't start: `lsof -ti:8000 | xargs kill -9`

## Future Architecture Considerations

### Planned Enhancements

- Celery integration for background tasks
- Enhanced caching with Redis
- API endpoints for mobile app
- Advanced reporting and analytics
- Document management system

### Scalability Patterns

- Database connection pooling
- Read replicas for reporting
- Microservices for specific functions
- CDN for static asset delivery
- Horizontal scaling with load balancers

This architecture guide provides the foundation for understanding and extending the Mobilize CRM system. The codebase follows Django best practices while implementing sophisticated business logic for non-profit contact management and Google API integration.
