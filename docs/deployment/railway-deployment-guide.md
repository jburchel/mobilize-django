# Railway Deployment Guide for Mobilize CRM

This guide provides comprehensive instructions for deploying the Mobilize CRM Django application to Railway with Supabase as the database backend.

## Overview

We use a hybrid deployment approach:
- **Railway**: Hosts the Django application ($5/month credit)
- **Supabase**: Provides PostgreSQL database (free tier)
- **Cloudflare**: CDN for static assets (free)

This setup can handle 50+ users and thousands of contacts while staying within minimal costs.

## Prerequisites

1. GitHub account with your repository
2. Railway account (sign up at https://railway.app)
3. Supabase account (sign up at https://supabase.com)
4. Cloudflare account (optional but recommended)

## Step 1: Supabase Database Setup

### Create Supabase Project

1. Log into Supabase Dashboard
2. Click "New Project"
3. Configure:
   - Project name: `mobilize-crm-db`
   - Database password: Generate a strong password and save it
   - Region: Choose closest to your users
   - Pricing plan: Free tier

### Configure Database

1. Go to Settings → Database
2. Enable "Connection Pooling" (Transaction mode)
3. Copy connection string from "Connection String" → "URI"
4. Replace `[YOUR-PASSWORD]` with your actual password
5. Add `?pgbouncer=true` to the end for pooling

Example connection string:
```
postgresql://postgres:YOUR-PASSWORD@db.xxxxxxxxxxxx.supabase.co:5432/postgres?pgbouncer=true
```

### Database Security

1. Go to Settings → Database → Connection Info
2. Note down:
   - Host
   - Database name
   - Port
   - User

## Step 2: Prepare Your Django Application

### Create railway.json

Create `railway.json` in your project root:

```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS",
    "buildCommand": "python manage.py collectstatic --noinput"
  },
  "deploy": {
    "startCommand": "gunicorn mobilize.wsgi:application --bind 0.0.0.0:$PORT",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

### Create Procfile (Alternative)

If you prefer Procfile over railway.json:

```
web: python manage.py migrate && python manage.py collectstatic --noinput && gunicorn mobilize.wsgi:application --bind 0.0.0.0:$PORT
```

### Update settings.py for Railway

```python
import os
import dj_database_url

# Railway provides PORT
if 'PORT' in os.environ:
    ALLOWED_HOSTS = ['*']  # Update with your domain later
    DEBUG = False
else:
    ALLOWED_HOSTS = ['localhost', '127.0.0.1']
    DEBUG = True

# Database configuration
DATABASES = {
    'default': dj_database_url.config(
        default=os.environ.get('DATABASE_URL'),
        conn_max_age=600,
        conn_health_checks=True,
    )
}

# Static files configuration for Railway
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

# Security settings for production
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
```

### Update requirements.txt

Ensure these packages are included:

```
Django==4.2.0
gunicorn==20.1.0
dj-database-url==2.0.0
psycopg2-binary==2.9.6
whitenoise==6.4.0
python-decouple==3.8
```

## Step 3: Deploy to Railway

### Connect GitHub Repository

1. Log into Railway Dashboard
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Authorize Railway to access your GitHub
5. Select your repository

### Configure Environment Variables

In Railway project settings, add these variables:

```bash
# Django
DJANGO_SECRET_KEY=your-secret-key-here
DJANGO_SETTINGS_MODULE=mobilize.settings

# Database (Supabase)
DATABASE_URL=postgresql://postgres:YOUR-PASSWORD@db.xxxxxxxxxxxx.supabase.co:5432/postgres?pgbouncer=true

# Google OAuth
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

# Supabase API (for sync)
SUPABASE_URL=https://xxxxxxxxxxxx.supabase.co
SUPABASE_KEY=your-supabase-anon-key

# Email settings (optional)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

### Deploy

1. Railway automatically deploys when you connect the repo
2. Monitor deployment in the Railway dashboard
3. Check logs for any errors

## Step 4: Post-Deployment Setup

### Run Database Migrations

1. In Railway dashboard, go to your project
2. Click on the deployment
3. Go to "Settings" → "Deploy"
4. Add a deploy command: `python manage.py migrate`
5. Redeploy to run migrations

### Create Superuser

Using Railway's CLI:

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Link to your project
railway link

# Run command
railway run python manage.py createsuperuser
```

### Configure Custom Domain (Optional)

1. In Railway project settings, go to "Settings"
2. Under "Domains", click "Generate Domain" for a railway.app subdomain
3. Or add your custom domain and follow DNS instructions

## Step 5: Optimize for Cost

### Static Files with Cloudflare

1. Create Cloudflare account
2. Set up Cloudflare Pages:
   ```bash
   # Build static files locally
   python manage.py collectstatic
   
   # Deploy to Cloudflare Pages
   npx wrangler pages publish staticfiles
   ```

3. Update Django settings:
   ```python
   STATIC_URL = 'https://your-cf-pages.pages.dev/static/'
   ```

### Database Optimization

1. Monitor Supabase dashboard for usage
2. Implement query optimization:
   - Use `select_related()` and `prefetch_related()`
   - Add database indexes
   - Cache frequently accessed data

### Application Optimization

1. Use Railway's metrics to monitor:
   - Memory usage (aim for < 512MB)
   - CPU usage
   - Response times

2. Optimize as needed:
   - Implement caching
   - Optimize database queries
   - Use pagination

## Step 6: Monitoring and Maintenance

### Railway Monitoring

- Check deployment logs regularly
- Monitor resource usage
- Set up alerts for failures

### Database Backups

Supabase provides automatic daily backups on free tier:
1. Go to Supabase Dashboard → Settings → Backups
2. Download backups periodically
3. Test restore procedures

### Scaling Considerations

When to upgrade from free tier:

**Railway ($5 → $20/month)**:
- Consistent memory usage > 512MB
- Need for multiple workers
- High traffic (>10k requests/day)

**Supabase (Free → $25/month)**:
- Database size > 500MB
- Need for more connections
- Advanced features required

## Troubleshooting

### Common Issues

1. **Import errors on deployment**
   - Check requirements.txt is complete
   - Ensure all dependencies are pip-installable

2. **Database connection errors**
   - Verify DATABASE_URL is correct
   - Check Supabase connection pooling is enabled
   - Ensure pgbouncer=true in connection string

3. **Static files not loading**
   - Run collectstatic in build command
   - Check STATIC_ROOT and STATIC_URL settings
   - Consider using WhiteNoise or CDN

4. **Memory exceeded errors**
   - Optimize queries
   - Implement pagination
   - Reduce worker count

### Debug Commands

```bash
# View logs
railway logs

# Run Django shell
railway run python manage.py shell

# Run management commands
railway run python manage.py [command]
```

## Security Best Practices

1. **Environment Variables**
   - Never commit secrets to Git
   - Use Railway's environment variables
   - Rotate keys regularly

2. **Database Security**
   - Use connection pooling
   - Implement row-level security in Supabase
   - Regular backups

3. **Application Security**
   - Keep dependencies updated
   - Enable Django security middleware
   - Use HTTPS (Railway provides by default)

## Continuous Deployment

Railway automatically deploys on push to main branch:

1. **Development Workflow**
   ```bash
   # Create feature branch
   git checkout -b feature/new-feature
   
   # Make changes and test locally
   python manage.py runserver
   
   # Commit and push
   git add .
   git commit -m "Add new feature"
   git push origin feature/new-feature
   
   # Create PR and merge to main
   # Railway auto-deploys
   ```

2. **Rollback Process**
   - Go to Railway dashboard
   - Select deployment history
   - Click "Rollback" on previous deployment

## Cost Monitoring

Track your usage:

1. **Railway Dashboard**
   - View current usage
   - Estimate monthly costs
   - Set up billing alerts

2. **Supabase Dashboard**
   - Monitor database size
   - Check bandwidth usage
   - API request counts

Expected costs for 50 users:
- Railway: $0-5/month (within free credit)
- Supabase: $0 (free tier sufficient)
- Total: $0-5/month

## Support Resources

- Railway Documentation: https://docs.railway.app
- Railway Discord: https://discord.gg/railway
- Supabase Documentation: https://supabase.com/docs
- Django Deployment Guide: https://docs.djangoproject.com/en/4.2/howto/deployment/