# Render Deployment Guide for Mobilize CRM

This guide provides step-by-step instructions for deploying the Mobilize CRM Django application to Render.

## Prerequisites

- GitHub repository with your Mobilize CRM code
- Supabase account with a configured PostgreSQL database
- Google OAuth credentials configured
- Render account (free tier available)

## Deployment Steps

### 1. Prepare Your Repository

Ensure your repository contains:
- `render.yaml` - Render service configuration
- `deploy.sh` - Deployment script
- `requirements.txt` - Python dependencies
- `.env` file with environment variables (for reference)

### 2. Create Render Account

1. Sign up at [render.com](https://render.com)
2. Connect your GitHub account
3. Authorize Render to access your repositories

### 3. Create Web Service

1. From the Render dashboard, click "New +"
2. Select "Web Service"
3. Connect your GitHub repository
4. Configure the service:

   **Basic Settings:**
   - **Name**: `mobilize-crm`
   - **Environment**: `Python 3`
   - **Region**: Choose closest to your users
   - **Branch**: `main` (or your production branch)

   **Build & Deploy:**
   - **Build Command**: `pip install -r requirements.txt && python manage.py collectstatic --noinput`
   - **Start Command**: `./deploy.sh`

### 4. Configure Environment Variables

Add the following environment variables in the Render dashboard:

```bash
# Django Configuration
DJANGO_SECRET_KEY=your-secret-key-here
DJANGO_DEBUG=False
DJANGO_SETTINGS_MODULE=mobilize.settings

# Database Configuration
SUPABASE_DATABASE_URL=postgresql://postgres.xxx:password@aws-0-us-east-1.pooler.supabase.com:6543/postgres

# Google OAuth
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

# Supabase Configuration
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=your-supabase-anon-key

# Render Configuration
RENDER_EXTERNAL_URL=https://your-app-name.onrender.com

# Logging
LOG_LEVEL=INFO
LOG_TO_STDOUT=True
```

### 5. Deploy

1. Click "Create Web Service"
2. Render will automatically start building and deploying
3. Monitor the deployment logs for any issues
4. Once complete, your app will be available at the provided URL

## Current Production Deployment

- **URL**: https://mobilize-crm-new.onrender.com
- **Plan**: Starter (512MB RAM, shared CPU) - $7/month
- **Static Files**: Served via WhiteNoise middleware
- **Database**: Supabase PostgreSQL (free tier)

## Static Files Configuration

The application uses WhiteNoise middleware for serving static files:

```python
# In settings.py
MIDDLEWARE = [
    # ...
    'whitenoise.middleware.WhiteNoiseMiddleware',
    # ...
]

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
```

Static files are collected during the build process via `collectstatic` command.

## Background Tasks and Celery

Currently, the application is configured for Celery but not running background workers:

**Current Status:**
- Celery is configured in settings
- Redis is not deployed
- Tasks run synchronously in the main process

**To Enable Background Processing:**

1. Add a Redis service in Render:
   ```yaml
   # In render.yaml
   - type: redis
     name: mobilize-redis
     region: oregon
     plan: starter
   ```

2. Add a Worker service:
   ```yaml
   # In render.yaml
   - type: worker
     name: mobilize-worker
     runtime: python
     buildCommand: pip install -r requirements.txt
     startCommand: celery -A mobilize worker --loglevel=info
   ```

3. Update environment variables:
   ```bash
   CELERY_BROKER_URL=redis://mobilize-redis:6379/0
   ```

## Monitoring and Maintenance

### Deployment Logs
- Access logs via Render dashboard
- Monitor build and runtime logs
- Set up log alerts for errors

### Health Monitoring
- Render provides built-in health checks
- Monitor response times and uptime
- Set up email notifications for downtime

### Updates and Rollbacks
- Manual deployments via Render dashboard
- Use "Manual Deploy" button to trigger rebuilds
- Rollback via deployment history in dashboard

## Troubleshooting

### Common Issues

1. **Build Failures**
   - Check requirements.txt for version conflicts
   - Verify Python version compatibility
   - Review build logs for specific errors

2. **Database Connection Issues**
   - Verify SUPABASE_DATABASE_URL format
   - Check Supabase connection limits
   - Ensure IP restrictions allow Render servers

3. **Static Files Not Loading**
   - Verify collectstatic runs during build
   - Check STATIC_ROOT and STATIC_URL settings
   - Ensure WhiteNoise is properly configured

4. **Environment Variable Issues**
   - Verify all required variables are set
   - Check for typos in variable names
   - Ensure sensitive values are not logged

### Getting Help

- **Render Documentation**: [render.com/docs](https://render.com/docs)
- **Render Community**: [community.render.com](https://community.render.com)
- **Django Deployment**: [docs.djangoproject.com](https://docs.djangoproject.com/en/4.2/howto/deployment/)

## Security Considerations

1. **Environment Variables**
   - Never commit secrets to version control
   - Use Render's environment variable management
   - Rotate credentials regularly

2. **Database Security**
   - Use Supabase's built-in security features
   - Enable connection pooling
   - Monitor for unusual activity

3. **Application Security**
   - Keep dependencies updated
   - Enable HTTPS (automatic with Render)
   - Configure proper ALLOWED_HOSTS

## Cost Optimization

- **Render Starter Plan**: $7/month
- **Supabase Free Tier**: $0/month (500MB storage)
- **Total Monthly Cost**: ~$7

Consider upgrading to higher tiers as usage grows:
- More RAM and CPU for better performance
- Professional plan for better availability SLA
- Dedicated database for high-traffic scenarios