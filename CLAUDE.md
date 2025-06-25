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

### Development Commands

#### Server Management
- **Important Server Tip**: After each change go ahead and kill the processes on port 8000 and restart the server

#### Background Task Management (Celery)
- **Start Redis** (required for Celery): `brew services start redis` or `redis-server`
- **Start Celery Worker**: `./start_celery.sh worker` or `celery -A mobilize worker --loglevel=info`
- **Start Celery Beat** (scheduler): `./start_celery.sh beat` or `celery -A mobilize beat --loglevel=info`
- **Start Flower** (monitoring): `./start_celery.sh flower` (access at http://localhost:5555)
- **Test Celery Tasks**: `python manage.py test_celery --task=debug`

**Celery Task Categories:**
- **Email Processing**: `mobilize.communications.tasks.*` (queue: email)
- **Notifications**: `mobilize.tasks.tasks.*` (queue: notifications) 
- **Data Sync**: `mobilize.utils.tasks.*` (queue: sync)

[Rest of the existing content remains unchanged...]