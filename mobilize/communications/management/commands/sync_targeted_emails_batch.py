from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db.models import Q
from datetime import datetime, timedelta
from mobilize.contacts.models import Person, Contact
import logging
import time

User = get_user_model()
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Sync last 2 years of Gmail emails for specific targeted contacts in batches'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be synced without actually syncing',
        )
        parser.add_argument(
            '--days',
            type=int,
            default=730,  # 2 years
            help='Number of days back to sync (default: 730 for 2 years)',
        )
        parser.add_argument(
            '--user-email',
            type=str,
            help='Specific user email to sync for (if not provided, will try to find appropriate user)',
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=5,
            help='Number of contacts to process in each batch (default: 5)',
        )
        parser.add_argument(
            '--batch-delay',
            type=int,
            default=30,
            help='Seconds to wait between batches (default: 30)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        days_back = options['days']
        user_email = options['user_email']
        batch_size = options['batch_size']
        batch_delay = options['batch_delay']
        
        # Target contact names (combined list) - corrected spellings
        target_names = [
            # Original list
            'Niranjan Madhavan',  # Fixed spelling: Madhavan not Madhaven
            'Beka Ahlstrom', 
            'Ellie Montgomery',
            'Austin Riggs',
            'Gracie Taylor',
            'Teresa McAfee',
            'Paul Wilkins',
            'Ben Cimorelli',
            'Scott And Chrissy Wallace',
            'Scott Simmons',
            
            # Additional list
            'Barb Jackowski',
            'Chris Vernon',
            'Chuck Hill',
            'Edith Parks',
            'Efran Klund',
            'Erich Schultz',
            'Heather Pastva',
            'Janette Brown',
            'Jenny Tarpley',
            'Jim Turnage',
            'Jimmy Currence',
            'Jimmy Kniss',
            'Jonathan St Clair',
            'Joshua Knott',
            'Judy Davis',
            'Kendall Hicks',
            'Kenny And Nikki Coker',
            'Kent Fancher',
            'Kyle Donn',
            'Laura Roe Jones',
            'Marc Rattray',
            'Mark Stanley',
            'Matt Rhodes',
            'Michael Hull',
            'David Bunn',  # Database has no "Rev." prefix
            'Richard Thomas',
            'Rob Campbell',
            'Ruthanne Lynch',
            'Savannah Simpson',
        ]
        
        self.stdout.write(f'Searching for {len(target_names)} target contacts...')
        
        # Find matching contacts using flexible name matching
        found_contacts = []
        missing_contacts = []
        
        for target_name in target_names:
            contact_found = False
            
            # Strategy 1: Full name exact match
            contacts = Contact.objects.filter(type='person')
            for contact in contacts:
                full_name = f"{contact.first_name or ''} {contact.last_name or ''}".strip()
                if target_name.lower() == full_name.lower():
                    if hasattr(contact, 'person_details'):
                        found_contacts.append((contact, target_name))
                        contact_found = True
                        break
            
            # Strategy 2: Partial name match (first + last)
            if not contact_found:
                name_parts = target_name.split()
                if len(name_parts) >= 2:
                    first_name = name_parts[0]
                    last_name = ' '.join(name_parts[1:])
                    
                    contact = Contact.objects.filter(
                        first_name__icontains=first_name,
                        last_name__icontains=last_name,
                        type='person'
                    ).first()
                    
                    if contact and hasattr(contact, 'person_details'):
                        found_contacts.append((contact, target_name))
                        contact_found = True
            
            if not contact_found:
                missing_contacts.append(target_name)
        
        self.stdout.write(self.style.SUCCESS(f'Found {len(found_contacts)} matching contacts'))
        
        if missing_contacts:
            self.stdout.write(self.style.WARNING(f'Missing {len(missing_contacts)} contacts: {", ".join(missing_contacts)}'))
        
        if not found_contacts:
            self.stdout.write(self.style.ERROR('No contacts found to sync!'))
            return
        
        # Get sync user
        sync_user = None
        if user_email:
            try:
                sync_user = User.objects.get(email=user_email)
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'User with email {user_email} not found'))
                return
        else:
            sync_user = User.objects.filter(is_staff=True, is_active=True).first()
        
        if not sync_user:
            self.stdout.write(self.style.ERROR('No user found for Gmail sync'))
            return
        
        # Extract emails and create batches
        contact_emails = [(contact.email, target_name) for contact, target_name in found_contacts if contact.email]
        
        if not contact_emails:
            self.stdout.write(self.style.WARNING('No email addresses found'))
            return
        
        # Create batches
        batches = [contact_emails[i:i + batch_size] for i in range(0, len(contact_emails), batch_size)]
        
        self.stdout.write(f'Processing {len(contact_emails)} emails in {len(batches)} batches of {batch_size}')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN - Would process the following batches:'))
            for i, batch in enumerate(batches, 1):
                self.stdout.write(f'  Batch {i}: {", ".join([name for _, name in batch])}')
            return
        
        # Initialize Gmail service
        from mobilize.communications.gmail_service import GmailService
        
        gmail_service = GmailService(sync_user)
        if not gmail_service.is_authenticated():
            self.stdout.write(self.style.ERROR('Gmail not authenticated for user'))
            return
        
        # Process each batch
        total_synced = 0
        
        for batch_num, batch in enumerate(batches, 1):
            batch_emails = [email for email, _ in batch]
            batch_names = [name for _, name in batch]
            
            self.stdout.write(f'\n--- Processing Batch {batch_num}/{len(batches)} ---')
            self.stdout.write(f'Contacts: {", ".join(batch_names)}')
            
            try:
                # Run sync for this batch
                result = gmail_service.sync_emails_to_communications(
                    days_back=days_back,
                    contacts_only=False,
                    specific_emails=batch_emails
                )
                
                if result['success']:
                    batch_count = result['synced_count']
                    total_synced += batch_count
                    self.stdout.write(self.style.SUCCESS(f'✓ Batch {batch_num}: Synced {batch_count} emails'))
                else:
                    self.stdout.write(self.style.ERROR(f'✗ Batch {batch_num}: {result.get("error", "Unknown error")}'))
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'✗ Batch {batch_num}: Exception - {e}'))
            
            # Wait between batches (except for the last one)
            if batch_num < len(batches):
                self.stdout.write(f'Waiting {batch_delay} seconds before next batch...')
                time.sleep(batch_delay)
        
        self.stdout.write(f'\n{self.style.SUCCESS("=== SYNC COMPLETE ===")}')
        self.stdout.write(f'Total emails synced: {total_synced}')
        self.stdout.write(f'Processed {len(batches)} batches for {len(contact_emails)} contacts')