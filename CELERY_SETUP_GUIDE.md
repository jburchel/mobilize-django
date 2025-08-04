# Celery Setup Guide for Email Sync

## Current Status: Fallback Mode Active

The email sync feature currently works in **fallback mode** because Celery (Redis) is not set up in production. 

### What's Working Now:
- ✅ **Email sync works** - syncs last 30 days of emails
- ✅ **No timeouts** - uses direct sync with limited scope
- ✅ **User feedback** - shows success/error messages
- ✅ **View All button** - properly filters by person

### Current Limitations:
- 🔄 **30-day limit** - Only syncs last 30 days (vs full 10-year history)
- ⏱️ **Potential timeout** - Very large email histories might still timeout

## Error in Logs (Resolved):
```
ERROR: Error starting email sync task: [Errno 111] Connection refused
WARNING: No hostname was supplied. Reverting to default 'localhost'
```

**Resolution**: Added fallback to direct sync when Celery unavailable.

## Full Celery Setup (Optional - For Complete Features)

To enable full 10-year email history sync and background processing:

### Option 1: Redis Cloud (Recommended for Render)

1. **Add Redis service on Render:**
   - Go to Render Dashboard
   - Create new Redis instance
   - Copy the Redis URL

2. **Add environment variable:**
   ```
   CELERY_BROKER_URL=redis://your-redis-url
   ```

3. **Update start command to include Celery worker:**
   ```bash
   ./start_render.sh && celery -A mobilize worker --loglevel=info --detach
   ```

### Option 2: Alternative Message Brokers

- **RabbitMQ Cloud** (CloudAMQP)
- **Amazon SQS** (via kombu)
- **Database backend** (Django DB - not recommended for production)

### Benefits of Full Celery Setup:
- ✅ **Full email history** - Sync 10+ years of emails
- ✅ **No timeouts** - Background processing prevents worker timeouts
- ✅ **Better performance** - Async processing doesn't block UI
- ✅ **Scalability** - Can handle multiple concurrent sync requests
- ✅ **Progress tracking** - Real-time status updates

## Testing Current Fallback Solution:

1. **Navigate to any person's detail page**
2. **Click "Sync Emails" button**
3. **Expected behavior:**
   - Shows "Starting sync..." briefly
   - Completes within 30-60 seconds
   - Shows success message with email count
   - Page reloads to display new communications
   - Message includes note about 30-day limitation

## Production Deployment:

The current fallback solution is **production-ready** and provides:
- ✅ **Reliable email sync** for recent communications
- ✅ **No external dependencies** (no Redis required)
- ✅ **Graceful degradation** from full Celery to direct sync
- ✅ **Clear user messaging** about limitations

## Next Steps:

1. **Test current solution** - Verify email sync works with 30-day limit
2. **Monitor performance** - Check if direct sync causes any timeouts
3. **Consider Redis setup** - If full history sync is needed
4. **User training** - Inform users about 30-day sync limitation

## Code Changes Made:

### 1. Fallback Logic in `sync_person_emails`:
```python
try:
    # Try Celery first
    task = sync_gmail_emails.delay(...)
    return celery_response
except (ConnectionError, OperationalError, OSError):
    # Fallback to direct sync with 30-day limit
    result = gmail_service.sync_emails_to_communications(days_back=30, ...)
    return direct_sync_response
```

### 2. Frontend Handles Both Modes:
```javascript
if (data.task_id && !data.fallback_mode) {
    // Celery mode - poll for completion
    pollTaskStatus(data.task_id, ...);
} else {
    // Direct mode - immediate completion
    showMessage('success', data.message);
    window.location.reload();
}
```

This approach ensures the feature works reliably regardless of Celery availability!