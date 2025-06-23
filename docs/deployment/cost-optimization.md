# Cost Optimization Guide for Mobilize CRM

This guide helps you optimize costs and stay within the Railway + Supabase free tiers while scaling your CRM application.

## Current Architecture Costs

### Free Tier Limits

**Railway (Free $5/month credit)**:
- 512MB RAM
- 1GB disk space  
- $0.000463/GB for bandwidth
- Shared CPU
- Auto-sleep after 10 minutes of inactivity

**Supabase (Free tier)**:
- 500MB database storage
- 2GB bandwidth
- 50MB file storage
- Unlimited API requests
- Daily backups

**Total Monthly Cost**: $0-5 (within Railway free credit)

## Resource Usage Monitoring

### Railway Metrics

Monitor these metrics in Railway dashboard:

1. **Memory Usage**
   ```python
   # Add to Django settings for memory debugging
   import psutil
   
   def get_memory_usage():
       process = psutil.Process()
       return process.memory_info().rss / 1024 / 1024  # MB
   ```

2. **CPU Usage**
   - Keep average below 50% to avoid throttling
   - Optimize heavy queries and calculations

3. **Bandwidth**
   - Monitor egress traffic
   - Each GB costs ~$0.10 beyond free tier

### Supabase Metrics

Check Supabase dashboard weekly:

1. **Database Size**
   ```sql
   -- Check database size
   SELECT pg_database_size('postgres') / 1024 / 1024 as size_mb;
   
   -- Check table sizes
   SELECT 
       schemaname,
       tablename,
       pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
   FROM pg_tables
   ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
   ```

2. **Connection Count**
   - Monitor active connections
   - Use connection pooling

## Optimization Strategies

### 1. Database Optimization

**Query Optimization**:

```python
# Bad - N+1 queries
for person in Person.objects.all():
    print(person.church.name)  # Extra query per person

# Good - Single query with join
persons = Person.objects.select_related('church').all()
for person in persons:
    print(person.church.name)  # No extra queries
```

**Indexing Strategy**:

```python
class Person(models.Model):
    # ... fields ...
    
    class Meta:
        indexes = [
            models.Index(fields=['last_name', 'first_name']),
            models.Index(fields=['pipeline_stage']),
            models.Index(fields=['office']),
        ]
```

**Data Cleanup**:

```python
# Management command: clean_old_data.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta

class Command(BaseCommand):
    def handle(self, *args, **options):
        # Delete old activity logs
        cutoff = timezone.now() - timedelta(days=90)
        ActivityLog.objects.filter(created_at__lt=cutoff).delete()
        
        # Archive old communications
        old_comms = Communication.objects.filter(
            sent_at__lt=cutoff
        ).values('id', 'subject', 'sent_at')
        # Save to JSON file or archive table
```

### 2. Application Memory Optimization

**Pagination**:

```python
# views.py
from django.core.paginator import Paginator

def person_list(request):
    persons = Person.objects.select_related('church').all()
    paginator = Paginator(persons, 25)  # Show 25 per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'contacts/person_list.html', {'page_obj': page_obj})
```

**Queryset Optimization**:

```python
# Use only() to load specific fields
persons = Person.objects.only('id', 'first_name', 'last_name', 'email')

# Use defer() to exclude heavy fields
persons = Person.objects.defer('notes', 'custom_fields')
```

**Caching**:

```python
# settings.py
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
        'LOCATION': 'cache_table',
    }
}

# views.py
from django.views.decorators.cache import cache_page

@cache_page(60 * 15)  # Cache for 15 minutes
def dashboard(request):
    # Dashboard logic
```

### 3. Static Files Optimization

**Use Cloudflare CDN**:

1. Sign up for Cloudflare (free)
2. Add your domain
3. Configure Page Rules:
   ```
   *yourdomain.com/static/*
   Cache Level: Cache Everything
   Edge Cache TTL: 1 month
   ```

**Compress Static Files**:

```python
# settings.py
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage'

# Use whitenoise for compression
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    # ...
]

WHITENOISE_COMPRESSION = True
WHITENOISE_USE_FINDERS = True
```

### 4. Background Tasks Optimization

Instead of Celery (memory heavy), use lightweight alternatives:

**Django-Q2**:
```python
# Lighter than Celery
pip install django-q2

# settings.py
Q_CLUSTER = {
    'name': 'mobilize',
    'workers': 1,  # Keep low for memory
    'timeout': 90,
    'django_redis': 'default'
}
```

**Cron Jobs via Railway**:
```javascript
// railway.json
{
  "services": {
    "web": {
      "startCommand": "gunicorn mobilize.wsgi"
    },
    "cron": {
      "startCommand": "python manage.py crontab add",
      "cronSchedule": "0 */6 * * *"  // Every 6 hours
    }
  }
}
```

### 5. API Rate Limiting

Prevent abuse and reduce load:

```python
# Install django-ratelimit
pip install django-ratelimit

# views.py
from django_ratelimit.decorators import ratelimit

@ratelimit(key='ip', rate='100/h')
def api_endpoint(request):
    # API logic
```

## Scaling Triggers

### When to Upgrade Railway ($5 → $20/month)

Monitor these metrics:

1. **Memory Usage > 400MB consistently**
   - Current: ~200-300MB for typical Django app
   - Action: Optimize queries first

2. **Response Time > 1s average**
   - Current target: < 500ms
   - Action: Add caching layer

3. **Worker Timeouts**
   - If seeing H12 errors in logs
   - Action: Optimize slow endpoints

### When to Upgrade Supabase (Free → $25/month)

1. **Database Size > 400MB**
   - Current with 50 users: ~100-200MB
   - Action: Archive old data first

2. **Bandwidth > 1.5GB/month**
   - Monitor file uploads
   - Action: Use external storage

3. **Need Point-in-Time Recovery**
   - Free tier: Daily backups only
   - Pro tier: PITR to any second

## Cost Monitoring Script

Create a monitoring script:

```python
# management/commands/check_resources.py
from django.core.management.base import BaseCommand
from django.db import connection
import requests
import os

class Command(BaseCommand):
    def handle(self, *args, **options):
        # Check database size
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT pg_database_size('postgres') / 1024 / 1024 as size_mb"
            )
            db_size = cursor.fetchone()[0]
            
        # Check table counts
        models_count = {
            'persons': Person.objects.count(),
            'churches': Church.objects.count(),
            'tasks': Task.objects.count(),
            'communications': Communication.objects.count(),
        }
        
        # Alert if approaching limits
        if db_size > 400:  # 400MB warning
            self.stdout.write(
                self.style.WARNING(f'Database size: {db_size}MB - approaching limit!')
            )
            
        self.stdout.write(f"Database size: {db_size}MB")
        self.stdout.write(f"Record counts: {models_count}")
```

## Monthly Cost Projections

### 10 Users (Starting)
- Railway: $0-2/month
- Supabase: $0
- **Total: $0-2/month**

### 25 Users (Growing)
- Railway: $3-4/month
- Supabase: $0
- **Total: $3-4/month**

### 50 Users (Target)
- Railway: $4-5/month (within credit)
- Supabase: $0
- **Total: $4-5/month**

### 100 Users (Scale up)
- Railway: $10-15/month
- Supabase: $0-25/month
- **Total: $10-40/month**

## Emergency Cost Reduction

If exceeding budget:

1. **Immediate Actions**:
   ```bash
   # Reduce worker processes
   web: gunicorn mobilize.wsgi --workers 1
   
   # Increase cache times
   CACHE_MIDDLEWARE_SECONDS = 600  # 10 minutes
   
   # Disable debug toolbar
   DEBUG = False
   ```

2. **Archive Old Data**:
   ```python
   # Move to cold storage
   old_date = timezone.now() - timedelta(days=365)
   old_comms = Communication.objects.filter(sent_at__lt=old_date)
   # Export to JSON and delete
   ```

3. **Reduce Polling Intervals**:
   ```python
   # Reduce background job frequency
   # From every hour to every 6 hours
   schedule('sync_tasks', 'H */6 * * *')
   ```

## Best Practices

1. **Regular Monitoring**
   - Check Railway dashboard weekly
   - Monitor Supabase usage monthly
   - Set up alerts for 80% usage

2. **Proactive Optimization**
   - Archive data before hitting limits
   - Optimize queries before scaling
   - Use caching aggressively

3. **Cost Attribution**
   - Track which features use most resources
   - Consider feature flags for heavy operations
   - Monitor per-user resource usage

4. **Backup Strategy**
   - Download Supabase backups weekly
   - Keep local copies of critical data
   - Test restore procedures

## Conclusion

With proper optimization, the Mobilize CRM can handle 50+ active users within the Railway free tier. Focus on:

1. Efficient database queries
2. Aggressive caching
3. Static file CDN
4. Regular monitoring

Only scale up when optimization no longer provides benefits. The hybrid Railway + Supabase approach provides excellent value for small to medium deployments.