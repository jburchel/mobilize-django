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
        
        # Build the deletion criteria - handle both 'email' and 'Email' types
        queryset = Communication.objects.filter(type__iexact='email')
        
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
        
        # Show breakdown by user (avoid the problematic join for now)
        self.stdout.write('\n' + '='*50)
        self.stdout.write('DELETION SUMMARY')
        self.stdout.write('='*50)
        
        # Count by user_id without joining to avoid the type casting issue
        from django.db.models import Count
        user_counts = queryset.values('user_id').annotate(count=Count('id')).order_by('-count')
        
        for user_data in user_counts:
            user_id = user_data['user_id']
            count = user_data['count']
            if user_id:
                try:
                    # Try to get the username, but handle the type mismatch
                    user = User.objects.get(id=int(user_id)) if isinstance(user_id, str) else User.objects.get(id=user_id)
                    username = user.username
                except (User.DoesNotExist, ValueError, TypeError):
                    username = f'Unknown (ID: {user_id})'
            else:
                username = 'No User'
            self.stdout.write(f'{username}: {count} emails')
        
        self.stdout.write(f'\nTOTAL: {total_count} communications to be deleted')
        
        # Show sample of what will be deleted (without complex joins)
        sample_comms = queryset[:5]
        if sample_comms:
            self.stdout.write('\nSample of emails to be deleted:')
            for comm in sample_comms:
                subject = comm.subject[:50] if comm.subject else 'No Subject'
                sender = comm.sender[:30] if comm.sender else 'Unknown'
                date = comm.date or 'No Date'
                self.stdout.write(f'  - {subject}... (from {sender}, {date})')
        
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
                # Handle the missing EmailAttachment table gracefully
                from django.db import connection
                cursor = connection.cursor()
                
                # Check if the django_email_attachments table exists
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = 'django_email_attachments'
                    );
                """)
                table_exists = cursor.fetchone()[0]
                
                if not table_exists:
                    self.stdout.write(
                        self.style.WARNING('EmailAttachment table does not exist, proceeding with direct deletion...')
                    )
                    # Delete communications directly without cascade to avoid the attachment table error
                    comm_ids = list(queryset.values_list('id', flat=True))
                    deleted_count = Communication.objects.filter(id__in=comm_ids).delete()[0]
                else:
                    # Normal deletion with cascades
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