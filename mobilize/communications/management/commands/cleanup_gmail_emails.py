from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.auth import get_user_model
from mobilize.communications.models import Communication

User = get_user_model()


class Command(BaseCommand):
    help = 'Clean up Gmail-synced emails while preserving manually logged communications'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--user-id',
            type=int,
            help='Clean up emails for specific user ID only'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting'
        )
        parser.add_argument(
            '--gmail-only',
            action='store_true',
            default=True,
            help='Only delete Gmail-synced emails (default: True)'
        )
        parser.add_argument(
            '--preserve-manual',
            action='store_true',
            default=True,
            help='Preserve manually logged communications (default: True)'
        )
        parser.add_argument(
            '--days-old',
            type=int,
            help='Only delete emails older than N days (optional)'
        )
    
    def handle(self, *args, **options):
        user_id = options.get('user_id')
        dry_run = options['dry_run']
        gmail_only = options['gmail_only']
        preserve_manual = options['preserve_manual']
        days_old = options.get('days_old')
        
        # Build the deletion criteria
        queryset = Communication.objects.filter(type='email')
        
        # Filter by user if specified
        if user_id:
            try:
                user = User.objects.get(id=user_id)
                queryset = queryset.filter(user=user)
                self.stdout.write(f'Filtering for user: {user.username} ({user.id})')
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'User with ID {user_id} not found')
                )
                return
        
        # Filter for Gmail-synced emails only
        if gmail_only:
            queryset = queryset.filter(gmail_message_id__isnull=False)
            self.stdout.write('Including: Gmail-synced emails only')
        
        # Preserve manually logged communications
        if preserve_manual:
            # Exclude communications without Gmail message IDs (manually created)
            queryset = queryset.exclude(gmail_message_id__isnull=True)
            self.stdout.write('Preserving: Manually logged communications')
        
        # Filter by age if specified
        if days_old:
            from datetime import datetime, timedelta
            from django.utils import timezone
            cutoff_date = timezone.now() - timedelta(days=days_old)
            queryset = queryset.filter(date__lt=cutoff_date.date())
            self.stdout.write(f'Including: Emails older than {days_old} days')
        
        # Get the count and details
        total_count = queryset.count()
        
        if total_count == 0:
            self.stdout.write(
                self.style.SUCCESS('No communications match the deletion criteria.')
            )
            return
        
        # Show breakdown by user
        self.stdout.write('\n' + '='*50)
        self.stdout.write('DELETION SUMMARY')
        self.stdout.write('='*50)
        
        user_breakdown = {}
        for comm in queryset.select_related('user'):
            username = comm.user.username if comm.user else 'Unknown'
            user_breakdown[username] = user_breakdown.get(username, 0) + 1
        
        for username, count in user_breakdown.items():
            self.stdout.write(f'{username}: {count} emails')
        
        self.stdout.write(f'\nTOTAL: {total_count} communications to be deleted')
        
        # Show sample of what will be deleted
        sample_comms = queryset.select_related('user', 'person')[:5]
        if sample_comms:
            self.stdout.write('\nSample of emails to be deleted:')
            for comm in sample_comms:
                person_name = comm.person.contact.first_name + ' ' + comm.person.contact.last_name if comm.person else 'Unknown'
                self.stdout.write(
                    f'  - {comm.subject[:50]}... (from {comm.sender or person_name}, {comm.date})'
                )
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('\n[DRY RUN] No communications were actually deleted.')
            )
            self.stdout.write(
                self.style.SUCCESS(f'Would delete {total_count} Gmail-synced communications.')
            )
            return
        
        # Confirm deletion
        self.stdout.write(
            self.style.WARNING(f'\nThis will permanently delete {total_count} communications!')
        )
        confirm = input('Are you sure you want to proceed? (yes/no): ')
        
        if confirm.lower() != 'yes':
            self.stdout.write(self.style.ERROR('Deletion cancelled.'))
            return
        
        # Perform the deletion
        try:
            with transaction.atomic():
                deleted_count = queryset.delete()[0]
                
            self.stdout.write(
                self.style.SUCCESS(f'Successfully deleted {deleted_count} communications.')
            )
            
            # Suggest next steps
            self.stdout.write('\n' + '='*50)
            self.stdout.write('NEXT STEPS')
            self.stdout.write('='*50)
            self.stdout.write('To resync emails from known contacts only, run:')
            self.stdout.write('  python manage.py sync_gmail --contacts-only')
            self.stdout.write('\nOr to sync all emails:')
            self.stdout.write('  python manage.py sync_gmail --all-emails')
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error during deletion: {str(e)}')
            )