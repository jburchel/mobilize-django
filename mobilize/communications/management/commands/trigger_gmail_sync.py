"""
Management command to manually trigger Gmail sync for testing.

This command allows administrators to manually trigger Gmail sync
for specific users or all users, useful for testing the sync functionality.
"""

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from mobilize.communications.tasks import sync_gmail_emails, sync_all_users_gmail

User = get_user_model()


class Command(BaseCommand):
    help = 'Manually trigger Gmail sync for testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user-id',
            type=int,
            help='Sync Gmail for specific user ID'
        )
        parser.add_argument(
            '--username',
            type=str,
            help='Sync Gmail for specific username'
        )
        parser.add_argument(
            '--all-users',
            action='store_true',
            help='Sync Gmail for all authenticated users'
        )
        parser.add_argument(
            '--days-back',
            type=int,
            default=3,
            help='Number of days back to sync (default: 3)'
        )
        parser.add_argument(
            '--async',
            action='store_true',
            help='Run sync asynchronously with Celery (default: synchronous)'
        )

    def handle(self, *args, **options):
        days_back = options['days_back']
        run_async = options['async']

        if options['all_users']:
            self.stdout.write('Triggering Gmail sync for all users...')
            
            if run_async:
                task = sync_all_users_gmail.delay(days_back=days_back)
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Queued Gmail sync for all users (Task ID: {task.id})')
                )
            else:
                result = sync_all_users_gmail(days_back=days_back)
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Gmail sync completed: {result}')
                )
                
        elif options['user_id'] or options['username']:
            # Find the user
            try:
                if options['user_id']:
                    user = User.objects.get(id=options['user_id'])
                else:
                    user = User.objects.get(username=options['username'])
                    
                self.stdout.write(f'Triggering Gmail sync for user: {user.username}...')
                
                if run_async:
                    task = sync_gmail_emails.delay(user.id, days_back=days_back)
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ Queued Gmail sync for {user.username} (Task ID: {task.id})')
                    )
                else:
                    result = sync_gmail_emails(user.id, days_back=days_back)
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ Gmail sync completed for {user.username}: {result}')
                    )
                    
            except User.DoesNotExist:
                raise CommandError('User not found')
                
        else:
            raise CommandError('Must specify --user-id, --username, or --all-users')

        self.stdout.write(
            self.style.WARNING(
                '\nNote: Make sure Celery worker is running if using --async flag'
            )
        )