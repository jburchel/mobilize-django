# Mobilize CRM

A comprehensive Customer Relationship Management system built with Django for managing church and missionary contacts, communications, and tasks.

## Project Overview

Mobilize CRM is designed to help missionaries and church organizations manage their relationships with churches, contacts, and supporters. The system provides tools for tracking communications, managing tasks, scheduling events, and maintaining detailed records of interactions.

### Key Features

- **Contact Management**: Track churches, individuals, and organizations
- **Communication Tools**: Email integration, templates, and communication history
- **Task Management**: Assign tasks, set due dates, and track completion
- **Pipeline Management**: Move contacts through customizable stages
- **Multi-office Support**: Manage data across multiple offices or regions
- **Google Integration**: Sync with Gmail and Google Calendar
- **Reporting**: Generate insights and analytics on activities and relationships

## Technology Stack

- **Backend**: Django 4.2, Python 3.9+
- **Database**: PostgreSQL (Supabase)
- **Hosting**: Railway
- **Authentication**: Google OAuth
- **Frontend**: HTML5, CSS3, Bootstrap 5, JavaScript
- **Email Integration**: Gmail API
- **Calendar Integration**: Google Calendar API
- **CDN**: Cloudflare (optional)

## Setup Instructions

### Prerequisites

- Python 3.9 or higher
- PostgreSQL 12 or higher
- Node.js and npm (for frontend assets)
- Git

### Installation

1. **Clone the repository**

```bash
git clone https://github.com/yourusername/mobilize-django.git
cd mobilize-django
```

2.**Create and activate a virtual environment**

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3.**Install dependencies**

```bash
pip install -r requirements.txt
```

4.**Set up environment variables**

Copy the example environment file and update it with your settings:

```bash
cp .env.example .env
```

Edit the `.env` file with your database credentials and Google API keys.

5.**Set up the database**

```bash
python manage.py migrate
```

6.**Create a superuser**

```bash
python manage.py createsuperuser
```

7.**Run the development server**

```bash
python manage.py runserver
```

The application will be available at http://localhost:8000

## Deployment

### Quick Deploy to Railway

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new/template?template=https://github.com/yourusername/mobilize-django)

### Manual Deployment

1. **Set up Supabase Database**
   - Create a free account at [Supabase](https://supabase.com)
   - Create a new project and copy the database URL

2. **Deploy to Railway**
   - Create account at [Railway](https://railway.app)
   - Connect your GitHub repository
   - Add environment variables from `.env.example`
   - Deploy!

For detailed deployment instructions, see [Railway Deployment Guide](docs/deployment/railway-deployment-guide.md).

## Project Structure

```
mobilize-django/
├── docs/                # Documentation files
├── mobilize/            # Main Django project directory
│   ├── authentication/  # User authentication and permissions
│   ├── churches/        # Church management
│   ├── communications/  # Email and communication tools
│   ├── contacts/        # Contact management
│   ├── core/            # Core functionality and shared components
│   ├── tasks/           # Task management
│   └── utils/           # Utility functions and helpers
├── static/              # Static files (CSS, JS, images)
├── templates/           # HTML templates
└── media/               # User-uploaded files
```

## Development Guidelines

- Follow PEP 8 style guidelines for Python code
- Write tests for all new functionality
- Document code with docstrings and comments
- Use Django's class-based views where appropriate
- Follow the Git workflow outlined in the project documentation

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributors

- [Your Name](https://github.com/yourusername) - Initial work
