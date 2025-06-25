"""
Management command to test Celery background tasks.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Test Celery background tasks functionality'

    def add_arguments(self, parser):
        parser.add_argument(
            '--task',
            type=str,
            default='debug',
            help='Which task to test (debug, email, notification, sync)'
        )

    def handle(self, *args, **options):
        task_type = options['task']
        
        self.stdout.write(f"Testing Celery task: {task_type}")
        
        try:
            if task_type == 'debug':
                from mobilize.celery import debug_task
                result = debug_task.delay()
                self.stdout.write(
                    self.style.SUCCESS(f"Debug task queued with ID: {result.id}")
                )
                
            elif task_type == 'email':
                from mobilize.communications.tasks import process_pending_emails
                result = process_pending_emails.delay()
                self.stdout.write(
                    self.style.SUCCESS(f"Email processing task queued with ID: {result.id}")
                )
                
            elif task_type == 'notification':
                from mobilize.tasks.tasks import send_due_date_notifications
                result = send_due_date_notifications.delay()
                self.stdout.write(
                    self.style.SUCCESS(f"Notification task queued with ID: {result.id}")
                )
                
            elif task_type == 'sync':
                from mobilize.utils.tasks import sync_supabase_task
                result = sync_supabase_task.delay('both', None, False)
                self.stdout.write(
                    self.style.SUCCESS(f"Sync task queued with ID: {result.id}")
                )
                
            else:
                self.stdout.write(
                    self.style.ERROR(f"Unknown task type: {task_type}")
                )
                return
                
            self.stdout.write("Task queued successfully!")
            self.stdout.write("Note: You need Redis running and a Celery worker to process the task.")
            self.stdout.write("Start a worker with: celery -A mobilize worker --loglevel=info")
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Error queuing task: {str(e)}")
            )