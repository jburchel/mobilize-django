# Render Service Update Instructions

## 🚨 Critical Production Fix Required

The production logs show **worker timeout issues** that are causing email sync failures. The changes in commit `df59f34` fix these issues, but you need to update the Render service configuration.

## Current Issues in Production:
```
[CRITICAL] WORKER TIMEOUT (pid:83)
[ERROR] Worker (pid:83) exited with code 1
```

## What Was Fixed:
1. **Gunicorn timeout increased** from 30s to 300s (5 minutes)
2. **Email sync converted to async** background task using Celery
3. **Added task status polling** for real-time progress updates
4. **Optimized start script** for better deployment

## Required Steps to Update Render:

### Step 1: Update Start Command in Render Dashboard

1. Go to https://dashboard.render.com/web/srv-d1elh4ngi27c73epfshg
2. Click **Settings**
3. Scroll to **Build & Deploy** section
4. Update the **Start Command** from:
   ```bash
   python manage.py comprehensive_schema_sync --verbose && python manage.py fix_supabase_data_types && python manage.py migrate && python manage.py showmigrations django_celery_beat && python manage.py showmigrations django_celery_results && python manage.py createcachetable && python manage.py compress && gunicorn mobilize.wsgi:application
   ```
   
   **To:**
   ```bash
   ./start_render.sh
   ```

5. Click **Save Changes**

### Step 2: Set Environment Variables (if not already set)

In the Render dashboard, ensure these environment variables are set:

- `LOG_LEVEL=INFO` (reduces debug output in production)
- `WEB_CONCURRENCY=1` (for Render starter plan)
- Any other environment variables already configured

### Step 3: Deploy

1. The service should automatically redeploy after saving the start command
2. Monitor the logs during deployment
3. The new start script uses the optimized Gunicorn configuration

## Expected Improvements:

### ✅ **Before Fix (Current Issues):**
- ❌ Email sync causes worker timeouts
- ❌ "Syncing" button gets stuck
- ❌ No email communications appear after sync
- ❌ Worker processes crash and restart

### ✅ **After Fix:**
- ✅ Email sync runs in background (no timeouts)
- ✅ Real-time progress updates every 3 seconds
- ✅ Proper error handling and user feedback
- ✅ Workers remain stable during long operations
- ✅ Synced emails appear in Recent Communications

## Testing After Update:

1. **Navigate to any person's detail page**
2. **Click "Sync Emails" button**
3. **Verify:**
   - Button shows "Starting sync..." then "Syncing emails..."
   - Progress updates appear every few seconds
   - Success message shows when complete
   - Page reloads to show new communications
   - No worker timeout errors in logs

## Alternative (Manual Command Update):

If you prefer not to use the shell script, you can use this optimized command directly:

```bash
python manage.py comprehensive_schema_sync --verbose && python manage.py fix_supabase_data_types && python manage.py migrate && python manage.py showmigrations django_celery_beat && python manage.py showmigrations django_celery_results && python manage.py createcachetable && python manage.py compress && gunicorn --config gunicorn.conf.py mobilize.wsgi:application
```

The key change is using `--config gunicorn.conf.py` which sets the timeout to 300 seconds instead of the default 30 seconds.

## Monitoring:

After the update, monitor the Render logs for:
- ✅ No more "WORKER TIMEOUT" errors
- ✅ Background task messages like "Syncing emails for 1 specific email addresses"
- ✅ Successful email sync completions

## Support:

If you encounter any issues during the update, the changes are backward compatible. The old email sync method will still work, but may timeout on large email histories.