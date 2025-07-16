"""
Management command to scan for existing emails to/from specific church contacts
in the current database going back one year.

This command searches through existing communications to find emails involving
the target church contacts without needing to sync all Gmail emails.
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta
from mobilize.contacts.models import Person, Contact
from mobilize.communications.models import Communication
from django.db.models import Q


class Command(BaseCommand):
    help = 'Scan for emails to/from specific church contacts in existing database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed output'
        )

    def handle(self, *args, **options):
        verbose = options.get('verbose', False)
        
        # Target email addresses (updated after user fixed TJ Higgins email)
        target_emails = [
            'thiggins@thegracecity.com',      # Grace City Church and TJ Higgins
            'reparks94@aol.com',              # Edith Parks - First Presbyterian
            'cactuscreek44@gmail.com'         # Danny Mayfield - Greenville Christian Fellowship
        ]
        
        one_year_ago = timezone.now().date() - timedelta(days=365)
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Scanning existing communications for church contacts (past year since {one_year_ago})...'
            )
        )
        self.stdout.write('=' * 80)
        
        total_found = 0
        
        for email_addr in target_emails:
            self.stdout.write(f'\\n📧 Scanning for: {email_addr}')
            
            # Find person with this email
            person = Person.objects.filter(contact__email=email_addr).first()
            church_contact = Contact.objects.filter(email=email_addr, type='church').first()
            
            if person:
                self.stdout.write(f'   👤 Person: {person.name} (ID: {person.id})')
            elif church_contact:
                self.stdout.write(f'   🏛️ Church: {church_contact.church_name} (Contact ID: {church_contact.id})')
            else:
                self.stdout.write(f'   ❌ No person or church contact found with this email')
                continue
            
            # Search for communications involving this email address
            # 1. Communications FROM this email (sender contains email)
            from_comms = Communication.objects.filter(
                date__gte=one_year_ago,
                sender__icontains=email_addr
            ).order_by('-date')
            
            # 2. Communications TO this email (in message content, CC, BCC)
            to_comms = Communication.objects.filter(
                date__gte=one_year_ago
            ).filter(
                Q(message__icontains=email_addr) |
                Q(cc_recipients__icontains=email_addr) |
                Q(bcc_recipients__icontains=email_addr)
            ).order_by('-date')
            
            # 3. Communications linked to this person directly
            person_comms = Communication.objects.none()
            if person:
                person_comms = Communication.objects.filter(
                    person=person,
                    date__gte=one_year_ago
                ).order_by('-date')
            
            # 4. Communications mentioning this email in subject
            subject_comms = Communication.objects.filter(
                date__gte=one_year_ago,
                subject__icontains=email_addr
            ).order_by('-date')
            
            # Combine all and deduplicate
            all_comm_ids = set()
            all_related_comms = []
            
            for comm_set in [from_comms, to_comms, person_comms, subject_comms]:
                for comm in comm_set:
                    if comm.id not in all_comm_ids:
                        all_comm_ids.add(comm.id)
                        all_related_comms.append(comm)
            
            # Sort by date
            all_related_comms.sort(key=lambda x: x.date or timezone.now().date(), reverse=True)
            
            self.stdout.write(f'   📊 Total related communications found: {len(all_related_comms)}')
            total_found += len(all_related_comms)
            
            if all_related_comms:
                self.stdout.write(f'   📋 Communications:')
                for comm in all_related_comms:
                    comm_type = comm.type or 'Unknown'
                    sender = comm.sender or 'Unknown sender'
                    subject = comm.subject or 'No subject'
                    
                    # Determine direction
                    if email_addr.lower() in sender.lower():
                        direction = 'FROM'
                    elif comm.person == person:
                        direction = 'TO'
                    else:
                        direction = 'RELATED'
                    
                    if verbose:
                        self.stdout.write(f'     • {comm.date}: [{comm_type}] {direction} - {subject}')
                        self.stdout.write(f'       Sender: {sender}')
                        if comm.person:
                            self.stdout.write(f'       Person: {comm.person.name}')
                    else:
                        self.stdout.write(f'     • {comm.date}: [{comm_type}] {direction} - {subject}')
            else:
                self.stdout.write(f'   ❌ No communications found for this email')
                
                # Suggest potential matches
                domain = email_addr.split('@')[-1] if '@' in email_addr else ''
                if domain:
                    domain_comms = Communication.objects.filter(
                        date__gte=one_year_ago,
                        sender__icontains=domain
                    ).count()
                    
                    if domain_comms > 0:
                        self.stdout.write(f'   💡 Found {domain_comms} communications from domain {domain}')
        
        self.stdout.write('\\n' + '=' * 80)
        self.stdout.write(
            self.style.SUCCESS(
                f'Scan completed! Found {total_found} total communications involving target email addresses.'
            )
        )
        
        if total_found == 0:
            self.stdout.write(
                self.style.WARNING(
                    'No communications found. This could mean:\\n'
                    '1. These email addresses have not been involved in communications\\n'
                    '2. Gmail sync has not captured these specific emails yet\\n'
                    '3. The emails might be in the system but not properly linked\\n\\n'
                    'Consider running: python manage.py sync_gmail --days-back 365 --all-emails'
                )
            )