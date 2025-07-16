"""
Management command to comprehensively scan for ALL emails to and from the 3 specific church contacts.

This command will thoroughly search the database for any emails involving:
- thiggins@thegracecity.com
- reparks94@aol.com  
- cactuscreek44@gmail.com

It will check all possible fields and variations to ensure comprehensive coverage.
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta
from mobilize.contacts.models import Person, Contact
from mobilize.communications.models import Communication
from django.db.models import Q


class Command(BaseCommand):
    help = 'Comprehensive scan for ALL emails to/from 3 specific church contacts'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days-back',
            type=int,
            default=365,
            help='Number of days to go back (default: 365)'
        )

    def handle(self, *args, **options):
        days_back = options.get('days_back', 365)
        
        # The 3 target email addresses
        target_emails = [
            'thiggins@thegracecity.com',      # Grace City Church and TJ Higgins
            'reparks94@aol.com',              # Edith Parks - First Presbyterian
            'cactuscreek44@gmail.com'         # Danny Mayfield - Greenville Christian Fellowship
        ]
        
        start_date = timezone.now().date() - timedelta(days=days_back)
        
        self.stdout.write(
            self.style.SUCCESS(
                f'COMPREHENSIVE EMAIL SCAN for 3 church contacts (past {days_back} days since {start_date})...'
            )
        )
        self.stdout.write('=' * 90)
        
        all_found_communications = []
        
        for email_addr in target_emails:
            self.stdout.write(f'\\n🔍 COMPREHENSIVE SEARCH: {email_addr}')
            
            # Find associated people
            people = Person.objects.filter(contact__email=email_addr)
            church_contacts = Contact.objects.filter(email=email_addr, type='church')
            
            if people.exists():
                for person in people:
                    self.stdout.write(f'   👤 Person: {person.name} (ID: {person.id})')
            
            if church_contacts.exists():
                for contact in church_contacts:
                    self.stdout.write(f'   🏛️ Church: {contact.church_name} (Contact ID: {contact.id})')
            
            # COMPREHENSIVE SEARCH - Check ALL possible ways this email could appear
            email_communications = Communication.objects.filter(
                date__gte=start_date
            ).filter(
                # 1. Sender field contains the email (FROM this email)
                Q(sender__icontains=email_addr) |
                # 2. Message content contains the email (TO this email)
                Q(message__icontains=email_addr) |
                # 3. Subject contains the email
                Q(subject__icontains=email_addr) |
                # 4. CC recipients contain the email
                Q(cc_recipients__icontains=email_addr) |
                # 5. BCC recipients contain the email
                Q(bcc_recipients__icontains=email_addr) |
                # 6. Content field contains the email
                Q(content__icontains=email_addr)
            ).distinct().order_by('-date')
            
            # Also search for variations and partial matches
            email_parts = email_addr.split('@')
            local_part = email_parts[0]
            domain_part = email_parts[1]
            
            # Search for the local part (e.g., "thiggins", "reparks94", "cactuscreek44")
            partial_communications = Communication.objects.filter(
                date__gte=start_date
            ).filter(
                Q(sender__icontains=local_part) |
                Q(message__icontains=local_part) |
                Q(subject__icontains=local_part)
            ).distinct().order_by('-date')
            
            # Search for communications linked to the person directly
            person_communications = Communication.objects.none()
            if people.exists():
                for person in people:
                    person_comms = Communication.objects.filter(
                        person=person,
                        date__gte=start_date
                    ).order_by('-date')
                    person_communications = person_communications.union(person_comms)
            
            # Combine all searches and deduplicate
            all_comm_ids = set()
            email_related_comms = []
            
            # Process email communications
            for comm in email_communications:
                if comm.id not in all_comm_ids:
                    all_comm_ids.add(comm.id)
                    email_related_comms.append(comm)
            
            # Process partial matches (but only if they seem relevant)
            for comm in partial_communications:
                if comm.id not in all_comm_ids:
                    # Check if this is actually relevant to our email
                    if (email_addr.lower() in (comm.sender or '').lower() or
                        email_addr.lower() in (comm.message or '').lower() or
                        local_part.lower() in (comm.sender or '').lower()):
                        all_comm_ids.add(comm.id)
                        email_related_comms.append(comm)
            
            # Process person communications
            for comm in person_communications:
                if comm.id not in all_comm_ids:
                    all_comm_ids.add(comm.id)
                    email_related_comms.append(comm)
            
            # Sort by date
            email_related_comms.sort(key=lambda x: x.date or timezone.now().date(), reverse=True)
            
            self.stdout.write(f'   📊 TOTAL COMMUNICATIONS FOUND: {len(email_related_comms)}')
            
            # Add to overall list
            all_found_communications.extend(email_related_comms)
            
            # Display all communications
            if email_related_comms:
                self.stdout.write(f'   📋 ALL COMMUNICATIONS:')
                for i, comm in enumerate(email_related_comms, 1):
                    comm_type = comm.type or 'Unknown'
                    sender = comm.sender or 'Unknown sender'
                    subject = comm.subject or 'No subject'
                    
                    # Determine direction
                    direction = 'UNKNOWN'
                    if email_addr.lower() in sender.lower():
                        direction = 'FROM'
                    elif comm.person and comm.person.contact.email == email_addr:
                        direction = 'TO'
                    elif email_addr.lower() in (comm.message or '').lower():
                        direction = 'TO/MENTIONS'
                    
                    self.stdout.write(f'     {i:2d}. {comm.date}: [{comm_type}] {direction}')
                    self.stdout.write(f'         Subject: {subject}')
                    self.stdout.write(f'         Sender: {sender}')
                    if comm.person:
                        self.stdout.write(f'         Person: {comm.person.name}')
                    self.stdout.write('')
            else:
                self.stdout.write(f'   ❌ NO COMMUNICATIONS FOUND')
                self.stdout.write(f'   💡 This might indicate the emails have not been synced yet')
        
        # Summary
        total_unique_comms = len(set(comm.id for comm in all_found_communications))
        
        self.stdout.write('\\n' + '=' * 90)
        self.stdout.write(
            self.style.SUCCESS(
                f'COMPREHENSIVE SCAN COMPLETE!\\n'
                f'Total unique communications found: {total_unique_comms}\\n'
                f'Date range: {start_date} to {timezone.now().date()}'
            )
        )
        
        if total_unique_comms == 0:
            self.stdout.write(
                self.style.WARNING(
                    'No communications found for any of the 3 email addresses.\\n'
                    'This suggests that Gmail sync may not have captured all emails yet.\\n'
                    'Consider running: python manage.py sync_gmail --days-back 365 --all-emails'
                )
            )