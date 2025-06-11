from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from mobilize.communications.gmail_service import GmailService

User = get_user_model()


class Command(BaseCommand):
    help = 'Sync Gmail emails to communications for all users with Gmail connected'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--user-id',
            type=int,
            help='Sync emails for specific user ID only'
        )
        parser.add_argument(
            '--days-back',
            type=int,
            default=7,
            help='Number of days back to sync emails (default: 7)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be synced without actually syncing'
        )
    
    def handle(self, *args, **options):
        user_id = options.get('user_id')
        days_back = options['days_back']
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(f'[DRY RUN] Gmail sync for last {days_back} days')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'Starting Gmail sync for last {days_back} days...')
            )
        
        # Get users to sync
        if user_id:
            users = User.objects.filter(id=user_id)
        else:
            # Get all users who have Gmail tokens
            try:
                from mobilize.authentication.models import GoogleToken
                user_ids_with_tokens = GoogleToken.objects.filter(
                    access_token__isnull=False
                ).values_list('user_id', flat=True)
                users = User.objects.filter(id__in=user_ids_with_tokens)
            except Exception:
                # Fallback if GoogleToken model doesn't exist
                users = User.objects.filter(is_active=True)
        
        total_synced = 0
        users_processed = 0
        
        for user in users:
            try:
                gmail_service = GmailService(user)
                
                if not gmail_service.is_authenticated():
                    self.stdout.write(
                        self.style.WARNING(f'User {user.username} ({user.id}) - Gmail not authenticated')
                    )
                    continue
                
                if dry_run:
                    # For dry run, just check authentication
                    self.stdout.write(
                        self.style.SUCCESS(f'User {user.username} ({user.id}) - Ready for sync')
                    )
                    users_processed += 1
                else:
                    # Actually sync emails
                    result = gmail_service.sync_emails_to_communications(days_back)
                    
                    if result['success']:
                        synced_count = result['synced_count']
                        total_synced += synced_count
                        users_processed += 1
                        
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'User {user.username} ({user.id}) - Synced {synced_count} emails'
                            )
                        )
                    else:
                        self.stdout.write(
                            self.style.ERROR(
                                f'User {user.username} ({user.id}) - Sync failed: {result["error"]}'
                            )
                        )
                        
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'User {user.username} ({user.id}) - Error: {str(e)}')
                )
        
        # Summary
        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(f'[DRY RUN] {users_processed} users ready for Gmail sync')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'Gmail sync completed: {total_synced} emails synced for {users_processed} users'
                )
            )