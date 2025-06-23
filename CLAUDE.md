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

[Rest of the existing content remains unchanged...]