from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db.models import Q
from email.utils import parseaddr
from mobilize.communications.gmail_service import GmailService
from mobilize.contacts.models import Person
from mobilize.churches.models import Church
from mobilize.communications.models import Communication

User = get_user_model()


class Command(BaseCommand):
    help = 'Sync Gmail emails using fuzzy name matching when email addresses don\'t match'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--user-id',
            type=int,
            help='Sync emails for specific user ID only'
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
            help='Show what would be synced without actually syncing'
        )
        parser.add_argument(
            '--show-unmatched',
            action='store_true',
            help='Show names that could not be matched to contacts'
        )
    
    def extract_name_from_email(self, sender_string):
        """Extract name from email sender string"""
        name, email = parseaddr(sender_string)
        return name.strip() if name else None, email.strip() if email else None
    
    def find_contact_by_name_or_email(self, name, email):
        """Find contact by email first, then by name fuzzy matching"""
        # First try email match
        if email:
            person = Person.objects.filter(contact__email__iexact=email).first()
            if person:
                return person, 'person', 'email'
                
            church = Church.objects.filter(contact__email__iexact=email).first()
            if church:
                return church, 'church', 'email'
        
        # Then try name matching
        if name:
            # Split name into parts
            name_parts = name.lower().split()
            if len(name_parts) >= 2:
                first_name = name_parts[0]
                last_name = ' '.join(name_parts[1:])
                
                # Try exact match
                person = Person.objects.filter(
                    Q(contact__first_name__iexact=first_name) & 
                    Q(contact__last_name__iexact=last_name)
                ).first()
                
                if person:
                    return person, 'person', 'name'
                
                # Try partial match on both names
                person = Person.objects.filter(
                    Q(contact__first_name__icontains=first_name) & 
                    Q(contact__last_name__icontains=last_name)
                ).first()
                
                if person:
                    return person, 'person', 'name_partial'
            
            # Try single name match
            if name_parts:
                single_name = name_parts[0]
                person = Person.objects.filter(
                    Q(contact__first_name__iexact=single_name) |
                    Q(contact__last_name__iexact=single_name)
                ).first()
                
                if person:
                    return person, 'person', 'name_single'
            
            # Try church name match
            church = Church.objects.filter(
                Q(name__icontains=name) |
                Q(contact__church_name__icontains=name)
            ).first()
            
            if church:
                return church, 'church', 'name'
        
        return None, None, None
    
    def handle(self, *args, **options):
        user_id = options.get('user_id')
        days_back = options['days_back']
        dry_run = options['dry_run']
        show_unmatched = options['show_unmatched']
        
        self.stdout.write('='*60)
        self.stdout.write('GMAIL SYNC WITH FUZZY NAME MATCHING')
        self.stdout.write('='*60)
        
        if dry_run:
            self.stdout.write(self.style.WARNING('[DRY RUN MODE]'))
        
        # Get users to sync
        if user_id:
            users = User.objects.filter(id=user_id)
        else:
            from mobilize.authentication.models import GoogleToken
            authenticated_users = GoogleToken.objects.filter(
                access_token__isnull=False
            ).values_list('user_id', flat=True)
            users = User.objects.filter(id__in=authenticated_users, is_active=True)
        
        total_synced = 0
        total_matched_by_name = 0
        unmatched_senders = set()
        
        for user in users:
            self.stdout.write(f'\nProcessing user: {user.username}')
            
            gmail_service = GmailService(user)
            if not gmail_service.is_authenticated():
                self.stdout.write(self.style.WARNING(f'Gmail not authenticated for {user.username}'))
                continue
            
            # Get messages
            from datetime import datetime, timedelta
            since_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y/%m/%d')
            query = f'after:{since_date}'
            
            messages = gmail_service.get_messages(query=query, max_results=500)
            self.stdout.write(f'Found {len(messages)} emails in the last {days_back} days')
            
            user_synced = 0
            user_name_matched = 0
            
            for msg in messages:
                # Skip if already synced
                if Communication.objects.filter(gmail_message_id=msg['id']).exists():
                    continue
                
                sender_full = msg.get('sender', '')
                sender_name, sender_email = self.extract_name_from_email(sender_full)
                
                # Find matching contact
                contact, contact_type, match_type = self.find_contact_by_name_or_email(
                    sender_name, sender_email
                )
                
                if contact:
                    if match_type != 'email':
                        user_name_matched += 1
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'  ✓ Matched by {match_type}: "{sender_name}" -> {contact}'
                            )
                        )
                    
                    if not dry_run:
                        # Create communication record
                        person = contact if contact_type == 'person' else None
                        church = contact if contact_type == 'church' else None
                        
                        # Update contact's email if matched by name
                        if match_type != 'email' and sender_email:
                            if not contact.contact.email:
                                contact.contact.email = sender_email
                                contact.contact.save()
                                self.stdout.write(
                                    self.style.SUCCESS(
                                        f'    Updated email for {contact}: {sender_email}'
                                    )
                                )
                        
                        Communication.objects.create(
                            type='Email',
                            subject=msg.get('subject', ''),
                            message=msg.get('body', '')[:250],
                            direction='inbound',
                            date=msg.get('date'),
                            person=person,
                            church=church,
                            gmail_message_id=msg['id'],
                            gmail_thread_id=msg.get('thread_id'),
                            email_status='received',
                            sender=sender_full,
                            user=user
                        )
                        user_synced += 1
                    else:
                        user_synced += 1
                else:
                    if sender_name and show_unmatched:
                        unmatched_senders.add(f"{sender_name} <{sender_email}>")
            
            self.stdout.write(
                f'User {user.username}: {user_synced} emails synced '
                f'({user_name_matched} matched by name)'
            )
            total_synced += user_synced
            total_matched_by_name += user_name_matched
        
        # Summary
        self.stdout.write('\n' + '='*30)
        self.stdout.write('SUMMARY')
        self.stdout.write('='*30)
        self.stdout.write(f'Total emails synced: {total_synced}')
        self.stdout.write(f'Matched by name (not email): {total_matched_by_name}')
        
        if show_unmatched and unmatched_senders:
            self.stdout.write('\n' + '='*30)
            self.stdout.write('UNMATCHED SENDERS')
            self.stdout.write('='*30)
            for sender in sorted(unmatched_senders)[:20]:
                self.stdout.write(f'  - {sender}')
            if len(unmatched_senders) > 20:
                self.stdout.write(f'  ... and {len(unmatched_senders) - 20} more')
                
        if dry_run:
            self.stdout.write(
                self.style.WARNING('\n[DRY RUN] No changes were made to the database')
            )