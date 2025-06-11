# Comprehensive Prompt for Creating Mobilize CRM Application

## Project Overview

Create a complete Customer Relationship Management (CRM) system called "Mobilize CRM" designed specifically for non-profit organizations to manage contacts, churches, and communications. The system should provide comprehensive contact management, pipeline tracking, communication history, task management, and integration with Google services (Gmail, Calendar, Contacts).

## Tech Stack

### Backend

- Python 3.9+
- Django 4.2+ as the web framework
- Django ORM for database operations
- Django Migrations for database migrations
- PostgreSQL for both development and production environments
  - Local PostgreSQL instance for development  
  - Supabase PostgreSQL for production  
  - Firebase Admin SDK for authentication
- Google API Client Libraries for integration with Google services
- Django Celery for background jobs and task scheduling

### Authentication

- Firebase Authentication for user management
- Google OAuth2 for single sign-on
- Role-based access control with multiple permission levels

### Frontend

- Django Templates for server-side rendering
- HTML5, CSS3, Bootstrap 5
- JavaScript (ES6+) for interactive elements
- DataTables for tabular data display
- Chart.js for dashboard visualizations

### UI Design and Branding Guidelines

- **Color Palette**:
  - Primary Blue: Pantone 534, RGB: 24 57 99, HEX: #183963, CMYK: 99 83 35 24
  - Primary Green: Pantone 7739, RGB: 57 169 73, HEX: #39A949, CMYK: 77 7 100 0
  - Gray: Pantone 840 C, RGB: 127 127 127, HEX: #7F7F7F, CMYK: 49 39 38 20
  - White and Black for backgrounds and text

- **Typography**:
  - Primary Font: Cronos Pro (Variations 6)
  - Use Cronos Pro exclusively for titles and featured information
  - For web applications, use websafe alternatives when Cronos Pro is unavailable
  - Maintain consistent font sizing hierarchy across the application

- **Logo Usage**:
  - Multiple logo versions available: Primary (vertical), Horizontal, Icon, and Executive
  - Logo consists of the green "crossover" icon and the "CROSSOVER GLOBAL" text
  - Protection area: In digital materials, maintain at least 15px of empty space around the logo
  - Minimum size: The primary logo must never be reduced to less than 0.89 in x 1.06 in, and the horizontal logo to less than 2.11 in x 0.58 in
  - On solid backgrounds, use white logo on dark backgrounds and standard color logo on light backgrounds
  - For photos, use white, black, or standard color logos depending on what works best with the image

- **Component Styling**:
  - Buttons: Use primary blue for primary actions, green for positive/confirmative actions, gray for secondary actions
  - Forms: Clean layout with clear field labels and validation states
  - Cards: Consistent padding and border radius, subtle shadow effects
  - Tables: Zebra striping for better readability, consistent header styling
  - Navigation: Clear hierarchy with consistent hover/active states

- **Layout**:
  - Use consistent spacing system (8px increment grid)
  - Responsive design with mobile-first approach
  - Maintain consistent page structure across all views
  - Apply consistent header and footer treatments

- **Visual Style**:
  - Use imagery that reflects diverse peoples and cultures that the organization works with
  - Use clean, professional visual design that communicates reliability and organization
  - Maintain appropriate white space for readability
  - Implement accessibility best practices for all UI elements

## UI/UX Documentation

### Interface Overview

The Mobilize CRM interface is built with a consistent layout structure across all pages:

1. **Navigation**
   - Persistent left sidebar with dark green background (#0A4D2C)
   - White icons and text for high contrast
   - Collapsible menu items for space efficiency
   - Current section highlighted with lighter background

2. **Header Area**
   - Gradient background from dark blue (#183963) to green (#39A949)
   - Page title and contextual information
   - Consistent padding and text hierarchy
   - Breadcrumb navigation when applicable

### Key Interface Components

1. **Dashboard (/ or /dashboard)**
   - Quick stats cards showing People (160) and Churches (97) counts
   - Office overview with role badges (Super Admin)
   - Recent activity feed
   - Pending tasks table
   - Action buttons for common tasks
   Technical Implementation:```python
   # views.py
   from django.shortcuts import render
   from django.contrib.auth.decorators import login_required
   from .models import Person, Church, Task
   
   @login_required
   def dashboard(request):
       user_id = request.user.id
       people_count = Person.objects.count()
       churches_count = Church.objects.count()
       pending_tasks = Task.objects.filter(status='pending')[:5]
       return render(request, 'dashboard.html',
                   {'people_count': people_count,
                    'churches_count': churches_count,
                    'pending_tasks': pending_tasks})```

2. **People Management (/people/list)**
   - Search and filter interface
   - Pipeline stage dropdown filter
   - Data table with columns:
     - NAME (linked to profile)
     - EMAIL
     - PHONE
     - PIPELINE
     - PRIORITY
     - ACTIONS (View/Edit)
   - Bulk selection capability
   - "Add Person" action button
   - Database Schema:```python
   # models.py
   from django.db import models
   
   class Contact(models.Model):
       first_name = models.CharField(max_length=100)
       last_name = models.CharField(max_length=100)
       email = models.EmailField(max_length=255, blank=True, null=True)
       phone = models.CharField(max_length=20, blank=True, null=True)
       pipeline_stage = models.CharField(max_length=50, blank=True, null=True)
       priority = models.CharField(max_length=20, blank=True, null=True)
       type = models.CharField(max_length=20)
       
       class Meta:
           db_table = 'contacts'```

3. **Churches Management (/churches/list)**
   - Similar layout to People section
   - Office-based filtering
   - Church-specific fields:
     - NAME
     - LOCATION
     - CONTACT
     - OFFICE
     - ACTIONS
   - Integration with contacts table:```python
   # views.py
   from django.db.models import Q
   
   def church_list(request):
       churches = Contact.objects.filter(type='church').select_related('church')
       return render(request, 'churches/list.html', {'churches': churches})```

4. **Communications Hub (/communications)**
   - Email integration display
   - Communication history table
   - Sync status indicator
   - Message preview functionality
   - Filter by date and type
   - API Integration:```javascript
   // Gmail sync status checking
   setInterval(async () => {
       try {
           const response = await fetch('/api/gmail/sync-status');
           const status = await response.json();
           updateSyncStatus(status);
       } catch (error) {
           console.error('Failed to fetch sync status:', error);
       }
   }, 10000);```

5. **Administration Interface (/admin/offices)**
   - Office management grid
   - User assignment interface
   - Church association tools
   - Bulk operations support
   - Permission Structure:```python
   # decorators.py
   from django.contrib.auth.decorators import user_passes_test
   from django.http import HttpResponseForbidden
   from functools import wraps
   def admin_required(view_func):
       @wraps(view_func)
       def _wrapped_view(request, *args, **kwargs):
           if not request.user.has_perm('manage_office'):
               return HttpResponseForbidden()
           return view_func(request, *args, **kwargs)
       return _wrapped_view```

6. **Form Interfaces**
   - Consistent form layout across all edit pages
   - Clear section grouping:
     - Personal/Basic Information
     - Contact Details
     - Additional Information
   - Required field indicators (*)
   - Inline validation
   - Action buttons consistently placed
   - Form Validation:```javascript
   const validateForm = () => {
       const requiredFields = document.querySelectorAll('[required]');
       let isValid = true;
       requiredFields.forEach(field => {
           if (!field.value) {
               field.classList.add('is-invalid');
               isValid = false;
           }
       });
       return isValid;
   };```

### Responsive Design

- Mobile-first approach
- Breakpoints:
  - Mobile: < 768px
  - Tablet: 768px - 1024px
  - Desktop: > 1024px
- Collapsible sidebar on mobile
- Responsive tables with horizontal scroll
- Adaptive form layouts

### Performance Considerations

- Lazy loading for data tables
- Pagination implementation
- Image optimization
- Caching strategies
- Background sync for Gmail integration

### Accessibility Features

- ARIA labels implementation
- Keyboard navigation support
- Color contrast compliance
- Screen reader compatibility
- Focus management

### Error Handling

- Form validation feedback
- Error state displays
- Loading states
- Empty state handling
- Network error recovery

### Deployment

- Google Cloud Run for hosting
- Supabase for PostgreSQL database
- Google Cloud Storage for assets
- GitHub for version control
- Continuous Integration/Continuous Deployment pipeline

## Core Functionality

1. **User Authentication and Authorization**
   - Multi-level user roles: super_admin, office_admin, standard_user, limited_user
   - Office-based permissions system
   - Google OAuth2 integration for easy login

### 1.1. Data Visibility and Access Control Details

The following rules define what data users can see and interact with, primarily based on their role and office assignments. An `assigned_to` field (linking to a `User`) will be necessary on the `Person` model to support user-specific assignments.

**General Principles:**

- Users are primarily scoped by their assigned office(s).
- Each user must be assigned to at least one primary office. They can be associated with multiple offices.

**Church Visibility:**

- **All Authenticated Users (Super Admin, Office Admin, Standard User, Limited User):** Can view all `Church` records assigned to *any* of their own active office assignments.

**People Visibility:**

- **Super Admin:**
  - Can view all `Person` records across all offices in the system.
  - UI should provide filters to view `Person` records by a specific office.
  - UI should provide a filter to view only `Person` records explicitly assigned to them.

- **Office Admin:**
  - Can view all `Person` records associated with *any* of their active office assignments.
  - UI should provide a filter to view only `Person` records explicitly assigned to them within their office(s).

- **Standard User:**
  - Can view only `Person` records explicitly assigned to them (e.g., via an `assigned_to` foreign key to the `User` model on the `Person` record).

- **Limited User:**
  - Can view only `Person` records explicitly assigned to them (similar to Standard User), typically with read-only access to the details.

**Filtering Requirements:**

- List views for People should incorporate the above visibility rules by default.
- Admins (Super and Office) should have clear UI options to switch between viewing "all accessible" people versus "only my assigned" people.
- Super Admins should additionally be able to filter the "all accessible" people list by specific offices.

---

1. **Contact Management**
   - Comprehensive contact records for individuals and churches
   - Customizable fields and categories
   - Contact history and notes
   - Google Contacts synchronization

2. **Pipeline Management**
   - Track contacts through customizable pipeline stages
   - Visual pipeline representation
   - Automatic stage transitions based on activity

3. **Communication Tools**
   - Email integration with Gmail
   - Communication history tracking
   - Email template management
   - Custom email signatures

4. **Task Management**
   - Create, assign, and track tasks
   - Due date notifications
   - Task categories and priorities
   - Google Calendar integration

5. **Dashboard and Reporting**
   - Visual analytics and KPIs
   - Customizable dashboard widgets
   - Exportable reports

6. **Multi-office Support**
   - Manage multiple offices/regions
   - Office-specific data segregation
   - Cross-office reporting capabilities

7. **Import/Export Tools**
   - CSV import functionality
   - Data export in multiple formats
   - Bulk operations

## Database Schema

### Database Overview

The Mobilize CRM uses a relational PostgreSQL database for both development and production environments:

- **Development Environment**: Local PostgreSQL database (postgresql://jimburchel@localhost:5432/mobilize)
- **Production Environment**: Supabase PostgreSQL database (postgresql://postgres@db.fwnitauuyzxnsvgsbrzr.supabase.co:5432/postgres)

The schema is designed around a core contacts table that serves as the base for both people and churches, with additional tables for tasks, communications, and organizational structure.

### Core Models

1. **Contacts (Base Model)**
```python
# models.py
from django.db import models
from django.utils import timezone

class Contact(models.Model):
    TYPE_CHOICES = (
        ('person', 'Person'),
        ('church', 'Church'),
    )
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    user = models.ForeignKey('User', on_delete=models.CASCADE)
    office = models.ForeignKey('Office', on_delete=models.SET_NULL, null=True)
    email = models.EmailField(max_length=255, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address_street = models.CharField(max_length=255, blank=True, null=True)
    address_city = models.CharField(max_length=100, blank=True, null=True)
    address_state = models.CharField(max_length=50, blank=True, null=True)
    address_zip = models.CharField(max_length=20, blank=True, null=True)
    address_country = models.CharField(max_length=100, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    pipeline_stage = models.CharField(max_length=50, blank=True, null=True)
    priority = models.CharField(max_length=20, blank=True, null=True)
    status = models.CharField(max_length=20, default='active')
    last_contact_date = models.DateTimeField(blank=True, null=True)
    next_contact_date = models.DateTimeField(blank=True, null=True)
    tags = models.JSONField(blank=True, null=True)
    custom_fields = models.JSONField(blank=True, null=True)
    
    class Meta:
        db_table = 'contacts'
        indexes = [
            models.Index(fields=['type']),
            models.Index(fields=['pipeline_stage']),
            models.Index(fields=['office']),
        ]
```

2. **Person (Extends Contacts)**
```python
class Person(models.Model):
    contact = models.OneToOneField(Contact, on_delete=models.CASCADE, primary_key=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    title = models.CharField(max_length=50, blank=True, null=True)
    preferred_name = models.CharField(max_length=100, blank=True, null=True)
    preferred_contact_method = models.CharField(max_length=20, blank=True, null=True)
    birth_date = models.DateField(blank=True, null=True)
    marital_status = models.CharField(max_length=20, blank=True, null=True)
    spouse_first_name = models.CharField(max_length=100, blank=True, null=True)
    spouse_last_name = models.CharField(max_length=100, blank=True, null=True)
    home_country = models.CharField(max_length=100, blank=True, null=True)
    languages = models.JSONField(blank=True, null=True)
    profession = models.CharField(max_length=100, blank=True, null=True)
    organization = models.CharField(max_length=255, blank=True, null=True)
    church_role = models.CharField(max_length=100, blank=True, null=True)
    primary_church = models.ForeignKey('Church', on_delete=models.SET_NULL, null=True, related_name='members')
    linkedin_url = models.URLField(max_length=255, blank=True, null=True)
    facebook_url = models.URLField(max_length=255, blank=True, null=True)
    twitter_url = models.URLField(max_length=255, blank=True, null=True)
    instagram_url = models.URLField(max_length=255, blank=True, null=True)
    google_contact_id = models.CharField(max_length=255, blank=True, null=True)
    
    class Meta:
        db_table = 'people'
        indexes = [
            models.Index(fields=['last_name', 'first_name']),
        ]
```

3. **Church (Extends Contacts)**
```python
class Church(models.Model):
    contact = models.OneToOneField(Contact, on_delete=models.CASCADE, primary_key=True)
    name = models.CharField(max_length=255)
    denomination = models.CharField(max_length=100, blank=True, null=True)
    website = models.URLField(max_length=255, blank=True, null=True)
    congregation_size = models.IntegerField(blank=True, null=True)
    year_founded = models.IntegerField(blank=True, null=True)
    service_times = models.JSONField(blank=True, null=True)
    pastor_name = models.CharField(max_length=200, blank=True, null=True)
    pastor_email = models.EmailField(max_length=255, blank=True, null=True)
    pastor_phone = models.CharField(max_length=20, blank=True, null=True)
    facilities = models.JSONField(blank=True, null=True)
    ministries = models.JSONField(blank=True, null=True)
    primary_language = models.CharField(max_length=50, blank=True, null=True)
    secondary_languages = models.JSONField(blank=True, null=True)
    
    class Meta:
        db_table = 'churches'
        indexes = [
            models.Index(fields=['name']),
        ]
```

4. **Task**
```python
class Task(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    due_date = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=20, default='pending')
    priority = models.CharField(max_length=20, default='medium')
    assigned_to = models.ForeignKey('User', on_delete=models.SET_NULL, null=True, related_name='assigned_tasks')
    created_by = models.ForeignKey('User', on_delete=models.CASCADE, related_name='created_tasks')
    contact = models.ForeignKey(Contact, on_delete=models.CASCADE, null=True)
    category = models.CharField(max_length=50, blank=True, null=True)
    google_calendar_event_id = models.CharField(max_length=255, blank=True, null=True)
    reminder_sent = models.BooleanField(default=False)
    recurring_pattern = models.JSONField(blank=True, null=True)
    completion_notes = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'tasks'
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['assigned_to']),
            models.Index(fields=['due_date']),
        ]
```

5. **Communication**
```python
class Communication(models.Model):
    type = models.CharField(max_length=20)
    subject = models.CharField(max_length=255, blank=True, null=True)
    content = models.TextField(blank=True, null=True)
    sent_at = models.DateTimeField(default=timezone.now)
    sender = models.ForeignKey('User', on_delete=models.CASCADE)
    recipient_contact = models.ForeignKey(Contact, on_delete=models.CASCADE, null=True)
    status = models.CharField(max_length=20, default='sent')
    gmail_thread_id = models.CharField(max_length=255, blank=True, null=True)
    gmail_message_id = models.CharField(max_length=255, blank=True, null=True)
    attachments = models.JSONField(blank=True, null=True)
    metadata = models.JSONField(blank=True, null=True)
    template_used = models.ForeignKey('EmailTemplate', on_delete=models.SET_NULL, null=True)
    read_status = models.BooleanField(default=False)
    read_timestamp = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        db_table = 'communications'
        indexes = [
            models.Index(fields=['recipient_contact']),
            models.Index(fields=['gmail_message_id']),
        ]
```

6. **User**
```python
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    firebase_uid = models.CharField(max_length=128, unique=True)
    last_login = models.DateTimeField(blank=True, null=True)    
    is_active = models.BooleanField(default=True)
    role = models.CharField(max_length=20, default='standard_user')
    preferences = models.JSONField(blank=True, null=True)
    email_signature = models.TextField(blank=True, null=True)
    notification_settings = models.JSONField(blank=True, null=True)
    theme_preferences = models.JSONField(blank=True, null=True)
    google_refresh_token = models.TextField(blank=True, null=True)
    profile_picture_url = models.URLField(max_length=255, blank=True, null=True)
    
    class Meta:
        db_table = 'users'
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['firebase_uid']),
        ]
```

7. **Office**
```python
class Office(models.Model):
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=255, blank=True, null=True)
    timezone = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=20, default='active')
    contact_email = models.EmailField(max_length=255, blank=True, null=True)
    contact_phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.JSONField(blank=True, null=True)
    settings = models.JSONField(blank=True, null=True)
    
    class Meta:
        db_table = 'offices'
```

8. **UserOffice (Junction Table)**
```python
class UserOffice(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    office = models.ForeignKey(Office, on_delete=models.CASCADE)
    role = models.CharField(max_length=20)
    assigned_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'user_offices'
        unique_together = ('user', 'office')
        indexes = [
            models.Index(fields=['user', 'office']),
        ]
```

9. **GoogleToken**

```python
class GoogleToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    access_token = models.TextField()
    refresh_token = models.TextField(blank=True, null=True)
    token_type = models.CharField(max_length=50, blank=True, null=True)
    expires_at = models.DateTimeField()
    scopes = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'google_tokens'
        indexes = [
            models.Index(fields=['user']),
        ]
```

### Additional Supporting Tables

1. **EmailTemplate**

```python
class EmailTemplate(models.Model):
    name = models.CharField(max_length=100)
    subject = models.CharField(max_length=255)
    content = models.TextField()
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    category = models.CharField(max_length=50, blank=True, null=True)
    variables = models.JSONField(blank=True, null=True)
    
    class Meta:
        db_table = 'email_templates'
```

2. **ActivityLog**

```python
class ActivityLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action_type = models.CharField(max_length=50)
    entity_type = models.CharField(max_length=50)
    entity_id = models.IntegerField()
    timestamp = models.DateTimeField(default=timezone.now)
    details = models.JSONField(blank=True, null=True)
    ip_address = models.CharField(max_length=45, blank=True, null=True)
    
    class Meta:
        db_table = 'activity_logs'
        indexes = [
            models.Index(fields=['entity_type', 'entity_id']),
        ]
```

### Key Relationships

1. **Contact Relationships**

- Contacts serve as the base table for both People and Churches
- One-to-many relationship with Tasks
- One-to-many relationship with Communications
- Many-to-one relationship with Offices

2. **User Relationships**

- Many-to-many relationship with Offices through UserOffice
- One-to-many relationship with Tasks (as creator and assignee)
- One-to-many relationship with Communications
- One-to-one relationship with GoogleToken

3. **Church-Person Relationships**

- Many-to-many relationship between People and Churches
- Primary church designation in People table

### Database Migrations

Migrations are handled using Django's built-in migration system. Key migration files:

```
migrations/
├── 0001_initial.py
├── 0002_add_contact_fields.py
├── 0003_add_church_fields.py
└── 0004_add_activity_logging.py
```

### Indexing Strategy

- Primary keys on all tables
- Foreign key indexes for all relationships
- Composite indexes for frequently queried combinations
- Full-text search indexes on searchable fields
- Indexes on frequently filtered fields (status, type, etc.)

### Data Integrity

- Foreign key constraints ensure referential integrity
- Check constraints on enumerated fields
- NOT NULL constraints on required fields
- Unique constraints on email addresses and external IDs
- Cascade deletes where appropriate

## API Endpoints

### Authentication

- `/auth/login/` - Google authentication
- `/api/auth/verify/` - Verify authentication tokens

### Contacts API

- `/api/contacts/` - CRUD operations for contacts
- `/api/contacts/search/` - Search functionality

### Gmail API

- `/api/gmail/sync/` - Synchronize emails
- `/api/gmail/send/` - Send emails
- `/api/gmail/threads/` - Manage email threads

### Calendar API

- `/api/calendar/events/` - Manage calendar events
- `/api/calendar/sync/` - Synchronize calendar

### Web Routes

- `/dashboard/` - Main dashboard view
- `/people/` - People management
- `/churches/` - Church management
- `/tasks/` - Task management
- `/communications/` - Communication history
- `/settings/` - User and system settings
- `/admin/offices/` - Office administration

## Configuration

### Environment Variables

Create appropriate .env files for different environments:

Development (.env.development):

```env
# Django configuration
DJANGO_SECRET_KEY=4e108cd937a0edb6c0edbc2b59dc194a48944c075622efb4
DJANGO_DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
BASE_URL=http://localhost:8000

# Database Configuration for Local Development
DATABASE_URL=postgresql://jimburchel@localhost:5432/mobilize

# Google OAuth Configuration
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

# Firebase Configuration
FIREBASE_API_KEY=AIzaSyD-Ch-gB7HBoRFcO0mupDfVVEXbAJ9Yi8c
FIREBASE_AUTH_DOMAIN=mobilize-crm.firebaseapp.com
FIREBASE_PROJECT_ID=mobilize-crm
FIREBASE_STORAGE_BUCKET=mobilize-crm.appspot.com
FIREBASE_MESSAGING_SENDER_ID=1069318103780
FIREBASE_APP_ID=1:1069318103780:web:f0035b172d4cfcf6e182f1
FIREBASE_MEASUREMENT_ID=G-1069318103780

# Logging
LOG_LEVEL=DEBUG
LOG_TO_STDOUT=True
```

Production (.env.production):

```env
# Django configuration
DJANGO_SECRET_KEY=4e108cd937a0edb6c0edbc2b59dc194a48944c075622efb4
DJANGO_DEBUG=False
ALLOWED_HOSTS=your-production-url.com
BASE_URL=https://your-production-url.com

# Database Configuration
DATABASE_URL=postgresql://postgres.fwnitauuyzxnsvgsbrzr:Fruitin2025!@aws-0-us-east-1.pooler.supabase.com:5432/postgres

# Google OAuth Configuration
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

# Firebase Configuration
FIREBASE_API_KEY=AIzaSyD-Ch-gB7HBoRFcO0mupDfVVEXbAJ9Yi8c
FIREBASE_AUTH_DOMAIN=mobilize-crm.firebaseapp.com
FIREBASE_PROJECT_ID=mobilize-crm
FIREBASE_STORAGE_BUCKET=mobilize-crm.appspot.com
FIREBASE_MESSAGING_SENDER_ID=1069318103780
FIREBASE_APP_ID=1:1069318103780:web:f0035b172d4cfcf6e182f1
FIREBASE_MEASUREMENT_ID=G-1069318103780

# Logging
LOG_LEVEL=INFO
LOG_TO_STDOUT=True
```

## Development Workflow

1. **Local Development**
   - Use PostgreSQL database for development
   - Run Django development server: `python manage.py runserver`
   - Test all routes locally
   - Verify Gmail sync functionality
   - Check authentication

2. **Testing**
   - Write comprehensive unit and integration tests
   - Test all core functionality
   - Validate form inputs and API responses
   - Test authentication and authorization

3. **Pre-Deployment Checks**
   - Verify database connections
   - Test all routes
   - Check authentication
   - Verify Gmail sync
   - Ensure environment variables are set correctly

4. **Deployment Process**
   - Ensure you're on the stable branch
   - Run `./deploy.sh` script for Google Cloud Run deployment
   - Update environment variables in Cloud Run console
   - Verify deployment success

5. **Post-Deployment Verification**
   - Check application logs
   - Verify people/churches pages
   - Test Gmail sync
   - Verify authentication
   - Test email sending
   - Check background jobs

## Deployment Instructions

### Setting up Supabase

1. Create a Supabase account at https://supabase.com/
2. Create a new project
3. Get database connection details from Project Settings > Database
4. Set environment variables:
   ```
   export DB_USER=postgres
   export DB_PASS=your-supabase-password
   export DB_NAME=postgres
   export DB_HOST=db.your-project-ref.supabase.co
   export DB_PORT=5432
   ```
5. Run migration script to set up your Supabase database:
   ```
   python manage.py migrate
   ```

### Deploying to Google Cloud Run

1. Install Google Cloud SDK
2. Update `PROJECT_ID` and `REGION` in `deploy.sh`
3. Make the script executable:
   ```
   chmod +x deploy.sh
   ```
4. Run deployment script:
   ```
   ./deploy.sh
   ```
5. After first deployment, set up environment variables in Cloud Run console

## Important Deployment Checks

1. **App Configuration**
   - Ensure Django settings are properly configured for production
   - Verify static files are being served correctly
   - Check that CSRF protection is properly configured

2. **Gmail API Specific Checks**
   - Ensure API calls are properly rate-limited
   - Use appropriate caching strategies

3. **Deployment Branch**
   - Make sure you're on the `stable-working-version` branch before deploying

4. **Emergency Rollback Procedure**
   - Follow the Rollback Procedure in DeploymentandMaintenenceChecklist.md if deployment fails

## Final Notes

The Mobilize CRM should be built with extensibility in mind. The system should allow for future enhancements and integration with additional services. The code should be well-documented and follow best practices for maintainability and security.

The system must be performant even with large datasets and should gracefully handle API rate limits, especially for Gmail and Google Calendar integration. Appropriate error handling and user feedback mechanisms should be implemented throughout.

Please implement all core functionality described above, following the provided tech stack and database schema. The completed application should be ready for deployment using the instructions provided.
