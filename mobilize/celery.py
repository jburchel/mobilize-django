"""
Celery configuration for Mobilize CRM.

This module contains the configuration for Celery, which handles
background and scheduled tasks in the Mobilize CRM application.
"""

import os
from celery import Celery

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mobilize.settings')

app = Celery('mobilize')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Debug task for testing Celery configuration."""
    print(f'Request: {self.request!r}')


# Error handling for tasks
@app.task(bind=True)
def safe_task(self, task_func, *args, **kwargs):
    """
    Wrapper task that provides error handling and logging for other tasks.
    """
    try:
        return task_func(*args, **kwargs)
    except Exception as exc:
        # Log the error
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f'Task {task_func.__name__} failed: {str(exc)}')
        
        # Re-raise with exponential backoff
        raise self.retry(
            exc=exc,
            countdown=60 * (2 ** self.request.retries),
            max_retries=3
        )


# Task signals for monitoring
@app.task(bind=True)
def task_success_handler(self, sender=None, task_id=None, result=None, retries=None, einfo=None, **kwargs):
    """Handle successful task completion."""
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f'Task {sender} ({task_id}) completed successfully')


@app.task(bind=True)
def task_failure_handler(self, sender=None, task_id=None, exception=None, traceback=None, einfo=None, **kwargs):
    """Handle task failure."""
    import logging
    logger = logging.getLogger(__name__)
    logger.error(f'Task {sender} ({task_id}) failed: {str(exception)}')


# Connect signals
from celery.signals import task_success, task_failure
task_success.connect(task_success_handler)
task_failure.connect(task_failure_handler)