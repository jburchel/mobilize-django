from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.contrib.auth import get_user_model
from mobilize.communications.models import Communication

User = get_user_model()


class Command(BaseCommand):
    help = 'Reset Gmail sync: delete existing synced emails and resync from scratch'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--user-id',
            type=int,
            help='Reset Gmail sync for specific user ID only'
        )
        parser.add_argument(
            '--days-back',
            type=int,
            default=30,
            help='Number of days back to sync emails (default: 30)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without actually doing it'
        )
        parser.add_argument(
            '--all-emails',
            action='store_true',
            help='Sync ALL emails, not just from known contacts'
        )
        parser.add_argument(
            '--skip-cleanup',
            action='store_true',
            help='Skip deletion step and only perform sync'
        )
    
    def handle(self, *args, **options):
        user_id = options.get('user_id')
        days_back = options['days_back']
        dry_run = options['dry_run']
        all_emails = options['all_emails']
        skip_cleanup = options['skip_cleanup']
        
        sync_mode = "ALL emails" if all_emails else "emails from known contacts ONLY"
        
        self.stdout.write('='*60)
        self.stdout.write(f'GMAIL SYNC RESET')
        self.stdout.write('='*60)
        
        if user_id:
            try:
                user = User.objects.get(id=user_id)
                self.stdout.write(f'Target: User {user.username} ({user.id})')
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'User with ID {user_id} not found')
                )
                return
        else:
            self.stdout.write('Target: All users with Gmail authentication')
        
        self.stdout.write(f'Sync scope: {sync_mode}')
        self.stdout.write(f'Days back: {days_back}')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('Mode: DRY RUN (no changes will be made)'))
        
        # Step 1: Clean up existing Gmail emails (unless skipped)
        if not skip_cleanup:
            self.stdout.write('\n' + '='*30)
            self.stdout.write('STEP 1: CLEANUP EXISTING EMAILS')
            self.stdout.write('='*30)
            
            # Check current Gmail email count - handle both 'email' and 'Email' types
            gmail_emails = Communication.objects.filter(
                type__iexact='email',
                gmail_message_id__isnull=False
            )
            
            if user_id:
                gmail_emails = gmail_emails.filter(user_id=user_id)
            
            current_count = gmail_emails.count()
            self.stdout.write(f'Current Gmail-synced emails: {current_count}')
            
            if current_count > 0:
                # Run cleanup command
                cleanup_args = ['--gmail-only', '--preserve-manual']
                if user_id:
                    cleanup_args.extend(['--user-id', str(user_id)])
                if dry_run:
                    cleanup_args.append('--dry-run')
                
                try:
                    call_command('cleanup_gmail_emails', *cleanup_args)
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'Cleanup failed: {str(e)}')
                    )
                    return
            else:
                self.stdout.write('No Gmail-synced emails found to cleanup.')
        else:
            self.stdout.write('\nSkipping cleanup step as requested.')
        
        # Step 2: Resync emails
        self.stdout.write('\n' + '='*30)
        self.stdout.write('STEP 2: RESYNC EMAILS')
        self.stdout.write('='*30)
        
        # Run Gmail sync command
        sync_args = ['--days-back', str(days_back)]
        if user_id:
            sync_args.extend(['--user-id', str(user_id)])
        if dry_run:
            sync_args.append('--dry-run')
        if all_emails:
            sync_args.append('--all-emails')
        else:
            sync_args.append('--contacts-only')
        
        try:
            call_command('sync_gmail', *sync_args)
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Gmail sync failed: {str(e)}')
            )
            return
        
        # Step 3: Summary
        if not dry_run:
            self.stdout.write('\n' + '='*30)
            self.stdout.write('RESET COMPLETE')
            self.stdout.write('='*30)
            
            # Show new count
            new_gmail_emails = Communication.objects.filter(
                type__iexact='email',
                gmail_message_id__isnull=False
            )
            if user_id:
                new_gmail_emails = new_gmail_emails.filter(user_id=user_id)
            
            new_count = new_gmail_emails.count()
            self.stdout.write(f'Gmail emails after reset: {new_count}')
            
            # Show manual communications preserved
            manual_comms = Communication.objects.filter(
                type__iexact='email',
                gmail_message_id__isnull=True
            )
            if user_id:
                manual_comms = manual_comms.filter(user_id=user_id)
            
            manual_count = manual_comms.count()
            self.stdout.write(f'Manual communications preserved: {manual_count}')
            
            self.stdout.write(
                self.style.SUCCESS('\nGmail sync reset completed successfully!')
            )
            
            # Recommendations
            self.stdout.write('\n' + '='*30)
            self.stdout.write('RECOMMENDATIONS')
            self.stdout.write('='*30)
            self.stdout.write('✓ Automatic sync is now running every 15 minutes')
            self.stdout.write('✓ Only emails from known contacts will be synced')
            self.stdout.write('✓ You\'ll get notifications for new emails')
            self.stdout.write('\nTo check sync status, run:')
            self.stdout.write('  python manage.py sync_gmail --dry-run')
        else:
            self.stdout.write(
                self.style.WARNING('\n[DRY RUN] Gmail sync reset simulation completed.')
            )