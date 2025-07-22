# CLAUDE.md

## Mobilize CRM - Django Project Architecture Guide

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

### Claude's Working Guidelines

- Do not commit or push any changes without my permission
- Remember we can use gcloud commands to get information on any gcp information we need

### Project Overview

Mobilize CRM is a comprehensive Customer Relationship Management system built with Django for managing church and missionary contacts, communications, and tasks. The system is designed specifically for non-profit organizations to track relationships with churches, contacts, and supporters through customizable pipeline stages.

#### Key Technologies

- **Backend**: Django 4.2, Python 3.9+, PostgreSQL
- **Authentication**: Google OAuth (Firebase Authentication removed)
- **Frontend**: Django Templates, Bootstrap 5, HTML5, CSS3, JavaScript
- **Integrations**: Google Gmail, Calendar, Contacts APIs
- **Database**: Local PostgreSQL (development), Supabase PostgreSQL (production)
- **Background Tasks**: Celery, Redis

### Project Structure and Architecture

#### Django Apps Organization

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

#### Development Commands

##### Server Management

- **Important Server Tip**: After each change go ahead and kill the processes on port 8000 and restart the server

##### Background Task Management (Celery)

- **Start Redis** (required for Celery): `brew services start redis` or `redis-server`
- **Start Celery Worker**: `./start_celery.sh worker` or `celery -A mobilize worker --loglevel=info`
- **Start Celery Beat** (scheduler): `./start_celery.sh beat` or `celery -A mobilize beat --loglevel=info`
- **Start Flower** (monitoring): `./start_celery.sh flower` (access at <http://localhost:5555>)
- **Test Celery Tasks**: `python manage.py test_celery --task=debug`
- **Celery Task Categories:**
- **Email Processing**: `mobilize.communications.tasks.*` (queue: email)
- **Notifications**: `mobilize.tasks.tasks.*` (queue: notifications)
- **Data Sync**: `mobilize.utils.tasks.*` (queue: sync)

#### Essential Django Commands

##### Development & Database

- **Run Development Server**: `python manage.py runserver`
- **Create Migrations**: `python manage.py makemigrations`
- **Apply Migrations**: `python manage.py migrate`
- **Show Migrations**: `python manage.py showmigrations`
- **Create Superuser**: `python manage.py createsuperuser`
- **Django Shell**: `python manage.py shell` (interactive Python shell with Django)
- **Database Shell**: `python manage.py dbshell` (direct database access)

##### Static Files & Assets

- **Collect Static Files**: `python manage.py collectstatic --noinput`
- **Clear Static Files**: `python manage.py collectstatic --clear --noinput`

##### Testing & Code Quality

- **Run All Tests**: `python manage.py test`
- **Run App-Specific Tests**: `python manage.py test mobilize.authentication`
- **Run with Pytest**: `pytest` (configured in requirements.txt)
- **Code Formatting**: `black .` (auto-format Python code)
- **Code Linting**: `flake8` (check code style)
- **Import Sorting**: `isort .` (organize imports)

##### Custom Management Commands

- **Sync Supabase**: `python manage.py sync_supabase [--dry-run] [--verbose]`
- **Sync Gmail**: `python manage.py sync_gmail [--contacts-only] [--all-emails]`
- **Reset Gmail Sync**: `python manage.py reset_gmail_sync`
- **Sync Contacts**: `python manage.py sync_contacts`
- **Generate Recurring Tasks**: `python manage.py generate_recurring_tasks`
- **Send Task Reminders**: `python manage.py send_task_reminders`
- **Setup Main Pipelines**: `python manage.py setup_main_pipelines`
- **Update Pipeline Contacts**: `python manage.py update_pipeline_contacts`

#### Dependencies

Key packages from requirements.txt:

- Django==4.2
- psycopg2-binary==2.9.10 (PostgreSQL adapter)
- celery==5.3.6 (Task queue)
- redis==5.0.1 (Celery broker)
- supabase==2.3.0 (Database integration)
- google-auth==2.27.0 (Authentication)
- google-api-python-client==2.115.0 (Google APIs)
- pytest==8.0.0 & pytest-django==4.7.0 (Testing)
- black==24.2.0, flake8==7.0.0, isort==5.13.2 (Code quality)

#### Environment Configuration

Required environment variables (see .env.example):

- `DJANGO_SECRET_KEY`: Django secret key
- `DATABASE_URL`: PostgreSQL connection string
- `GOOGLE_CLIENT_ID` & `GOOGLE_CLIENT_SECRET`: OAuth credentials
- `SUPABASE_URL` & `SUPABASE_KEY`: Supabase connection
- `DJANGO_DEBUG`: Debug mode (True/False)
- `ALLOWED_HOSTS`: Comma-separated list of allowed hosts

### Architectural Patterns and Key Components

#### Multi-Tenancy via Office Model

The system implements multi-tenancy through the `Office` model in `admin_panel`. Each user belongs to an office, and data access is scoped by office:

- Office-scoped managers filter querysets automatically
- Views use `get_queryset()` to filter by `request.user.office`
- Use `OfficeFilterMixin` for consistent filtering

#### Contact Management Hierarchy

```
Contact (Abstract Base)
├── Person (Individuals)
│   ├── Fields: name_first, name_last, email, phone
│   └── Relations: churches (M2M), communications
└── Church (Organizations)
    ├── Fields: name, address, website
    └── Relations: persons (M2M), pipeline_stages
```

#### Pipeline System

Churches progress through customizable pipeline stages:

- Each Office defines its own pipeline stages
- Churches can be in multiple stages simultaneously
- Pipeline positions track order and progression
- Use `pipeline.services.PipelineService` for stage transitions

#### Task Management

Tasks support both one-time and recurring patterns:

- Recurring tasks use `RecurringTaskTemplate` model
- Tasks have assignees, due dates, and completion tracking
- Automatic reminder system via Celery scheduled tasks
- Tasks linked to contacts (Person or Church)

#### Email Integration (Gmail API)

The `communications` app handles Gmail integration:

- OAuth2 authentication per user
- Sync emails to local `EmailMessage` model
- Track email metadata (labels, threads, attachments)
- Queue-based processing with Celery

#### Security & Permissions

- Role-based access control: Admin, User, Viewer
- Data Access Manager pattern for queryset filtering
- Office-level data isolation
- Google OAuth for authentication (no local passwords)

#### Database Patterns

- Use `models.BaseModel` for common fields (created_at, updated_at)
- Soft deletes via `is_active` field
- UUID primary keys for some models
- Audit logging for critical operations

#### API Design

- RESTful endpoints via Django REST Framework
- ViewSets for CRUD operations
- Custom actions for business logic
- Pagination and filtering on list endpoints

#### Frontend Architecture

- Server-side rendering with Django templates
- HTMX for dynamic interactions without full page reloads
- Bootstrap 5 for UI components
- Minimal custom JavaScrip
- t

#### Testing Strategy

- Unit tests for models and utilities
- Integration tests for views and API endpoints
- Mock external services (Gmail, Supabase)
- Use `@override_settings` for test-specific configuration
- Factory pattern for test data creation

#### Performance Considerations

- Database indexes on frequently queried fields
- Select/prefetch related for reducing queries
- Celery for async processing
- Redis caching for session data
- Pagination on all list views

#### Deployment & DevOps

- Environment-specific settings files
- Database migrations tracked in version control
- Static files served via WhiteNoise or CDN
- Health check endpoints for monitoring
- Structured logging with appropriate levels
