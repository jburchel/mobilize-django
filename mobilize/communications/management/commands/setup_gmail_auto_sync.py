"""
Management command to set up automatic Gmail syncing with Celery Beat.

This command creates or updates the periodic task for automatic Gmail sync
that runs every hour for all authenticated users.
"""

from django.core.management.base import BaseCommand
from django.core.management.color import no_style


class Command(BaseCommand):
    help = 'Set up automatic Gmail syncing with Celery Beat scheduler'

    def add_arguments(self, parser):
        parser.add_argument(
            '--interval-minutes',
            type=int,
            default=60,
            help='Sync interval in minutes (default: 60 for hourly)',
        )
        parser.add_argument(
            '--days-back',
            type=int,
            default=1,
            help='Number of days back to sync emails (default: 1)',
        )
        parser.add_argument(
            '--disable',
            action='store_true',
            help='Disable the automatic sync task',
        )

    def handle(self, *args, **options):
        try:
            from django_celery_beat.models import PeriodicTask, IntervalSchedule
        except ImportError:
            self.stdout.write(
                self.style.ERROR(
                    'django-celery-beat is not installed. '
                    'Please install it to use automatic Gmail sync.'
                )
            )
            return

        interval_minutes = options['interval_minutes']
        days_back = options['days_back']
        disable = options['disable']

        task_name = 'Auto-sync Gmail for all users'

        if disable:
            # Disable the task
            try:
                task = PeriodicTask.objects.get(name=task_name)
                task.enabled = False
                task.save()
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Disabled automatic Gmail sync task: {task_name}')
                )
            except PeriodicTask.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(f'⚠️  No automatic Gmail sync task found to disable')
                )
            return

        # Create or get the interval schedule
        schedule, created = IntervalSchedule.objects.get_or_create(
            every=interval_minutes,
            period=IntervalSchedule.MINUTES,
        )

        if created:
            self.stdout.write(
                self.style.SUCCESS(f'✅ Created new interval schedule: every {interval_minutes} minutes')
            )

        # Create or update the periodic task
        task, created = PeriodicTask.objects.get_or_create(
            name=task_name,
            defaults={
                'task': 'mobilize.communications.tasks.sync_all_users_gmail',
                'interval': schedule,
                'args': f'[{days_back}]',  # Pass days_back as argument
                'enabled': True,
                'description': f'Automatically sync Gmail emails for all authenticated users every {interval_minutes} minutes'
            }
        )

        if not created:
            # Update existing task
            task.interval = schedule
            task.args = f'[{days_back}]'
            task.enabled = True
            task.description = f'Automatically sync Gmail emails for all authenticated users every {interval_minutes} minutes'
            task.save()
            self.stdout.write(
                self.style.SUCCESS(f'✅ Updated existing automatic Gmail sync task')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'✅ Created new automatic Gmail sync task')
            )

        # Display task information
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('📋 Gmail Auto-Sync Configuration:'))
        self.stdout.write(f'   Task Name: {task.name}')
        self.stdout.write(f'   Task Function: {task.task}')
        self.stdout.write(f'   Interval: Every {interval_minutes} minutes')
        self.stdout.write(f'   Days Back: {days_back} day(s)')
        self.stdout.write(f'   Enabled: {task.enabled}')
        self.stdout.write(f'   Last Run: {task.last_run_at or "Never"}')
        self.stdout.write('')
        
        # Check Celery Beat status
        self.stdout.write(self.style.WARNING('📝 Next Steps:'))
        self.stdout.write('   1. Make sure Celery worker is running: ./start_celery.sh worker')
        self.stdout.write('   2. Make sure Celery beat scheduler is running: ./start_celery.sh beat')
        self.stdout.write('   3. Monitor the logs to ensure sync is working')
        self.stdout.write('')
        self.stdout.write('   To check task status: python manage.py shell')
        self.stdout.write('   >>> from django_celery_beat.models import PeriodicTask')
        self.stdout.write(f'   >>> task = PeriodicTask.objects.get(name="{task_name}")')
        self.stdout.write('   >>> print(f"Last run: {task.last_run_at}, Enabled: {task.enabled}")')