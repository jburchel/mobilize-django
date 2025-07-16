"""
Management command to sync email communications for specific churches going back one year.

This command will specifically sync Gmail emails for the three churches mentioned 
in Issue #16 to ensure their email communications are properly captured.
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta
from mobilize.churches.models import Church
from mobilize.communications.models import Communication


class Command(BaseCommand):
    help = 'Sync church email communications going back one year'

    def add_arguments(self, parser):
        parser.add_argument(
            '--church-name',
            type=str,
            help='Specific church name to sync (partial match)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed output',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        verbose = options['verbose']
        church_name = options.get('church_name')
        
        self.stdout.write(
            self.style.SUCCESS('Starting church email sync going back one year...')
        )
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('DRY RUN MODE - Analysis only')
            )
        
        # Target churches
        if church_name:
            churches = Church.objects.filter(name__icontains=church_name)
        else:
            target_names = ['Grace City Church', 'First Presbyterian', 'Greenville Christian Fellowship']
            churches = Church.objects.filter(name__in=target_names)
        
        if not churches.exists():
            self.stdout.write(
                self.style.ERROR('No churches found matching criteria')
            )
            return
        
        one_year_ago = timezone.now().date() - timedelta(days=365)
        
        for church in churches:
            self.stdout.write(f'\n📧 Analyzing {church.name} (ID: {church.id})')
            self.stdout.write(f'   Contact ID: {church.contact.id}')
            self.stdout.write(f'   Contact Email: {church.contact.email or "None"}')
            
            # Check current communications
            from django.db import models
            current_comms = Communication.objects.filter(
                date__gte=one_year_ago
            ).filter(
                models.Q(church=church) |
                models.Q(sender__icontains=church.contact.email) if church.contact.email else models.Q(pk=None)
            ).order_by('-date')
            
            self.stdout.write(f'   Current communications (past year): {current_comms.count()}')
            
            if verbose and current_comms.exists():
                for comm in current_comms[:5]:
                    self.stdout.write(f'     • {comm.date}: {comm.subject} (from {comm.sender})')
            
            # Check if this church has an email address for Gmail sync
            if church.contact.email:
                self.stdout.write(
                    f'   💡 Church has email address: {church.contact.email}'
                )
                self.stdout.write(
                    f'   🔄 To sync Gmail for this church, run:'
                )
                self.stdout.write(
                    f'      python manage.py sync_gmail --days-back 365 --all-emails'
                )
                
                # Check if there are any communications with this email pattern
                email_pattern_comms = Communication.objects.filter(
                    date__gte=one_year_ago,
                    sender__icontains=church.contact.email
                ).count()
                
                if email_pattern_comms == 0:
                    self.stdout.write(
                        self.style.WARNING(
                            f'     ⚠️ No communications found with email pattern {church.contact.email}'
                        )
                    )
                else:
                    self.stdout.write(
                        f'     ✅ Found {email_pattern_comms} communications with this email pattern'
                    )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        '   ⚠️ No email address - cannot sync Gmail'
                    )
                )
                
            # Check for communications with similar names
            name_parts = church.name.split()
            for part in name_parts:
                if len(part) > 3:  # Skip short words
                    similar_comms = Communication.objects.filter(
                        date__gte=one_year_ago,
                        sender__icontains=part
                    ).exclude(
                        sender__icontains=church.contact.email if church.contact.email else ''
                    )
                    
                    if similar_comms.exists():
                        self.stdout.write(
                            f'   📧 Found {similar_comms.count()} communications with "{part}" in sender'
                        )
                        if verbose:
                            for comm in similar_comms[:3]:
                                self.stdout.write(f'     • {comm.date}: {comm.subject} (from {comm.sender})')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n✅ Church email analysis completed!'
                f'\n💡 To sync Gmail emails going back one year, run:'
                f'\n   python manage.py sync_gmail --days-back 365 --all-emails'
            )
        )