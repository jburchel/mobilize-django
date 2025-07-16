"""
Management command to fix Rachel Ferguson's email communication linkage.

This command fixes the issue where Rachel Lively's emails were incorrectly 
linked to Rachel Ferguson's Person record. It creates a separate Contact/Person 
record for Rachel Lively and updates the Communication records accordingly.
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from mobilize.contacts.models import Contact, Person
from mobilize.communications.models import Communication
from mobilize.admin_panel.models import Office


class Command(BaseCommand):
    help = 'Fix Rachel Ferguson email communication linkage (Issue #17)'

    def add_arguments(self, parser):
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
        
        self.stdout.write(
            self.style.SUCCESS('Starting Rachel Ferguson email fix (Issue #17)...')
        )
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('DRY RUN MODE - No changes will be made')
            )
        
        try:
            with transaction.atomic():
                # Step 1: Find Rachel Ferguson's Person record
                rachel_ferguson_person = None
                try:
                    rachel_ferguson_contact = Contact.objects.get(
                        email='rbf1997@gmail.com'
                    )
                    rachel_ferguson_person = Person.objects.get(
                        contact=rachel_ferguson_contact
                    )
                    if verbose:
                        self.stdout.write(
                            f'Found Rachel Ferguson: Person ID {rachel_ferguson_person.id}, '
                            f'Contact ID {rachel_ferguson_contact.id}'
                        )
                except (Contact.DoesNotExist, Person.DoesNotExist):
                    self.stdout.write(
                        self.style.ERROR(
                            'Could not find Rachel Ferguson with email rbf1997@gmail.com'
                        )
                    )
                    return
                
                # Step 2: Find Communications from Rachel Lively's email linked to Rachel Ferguson
                rachel_lively_communications = Communication.objects.filter(
                    person=rachel_ferguson_person,
                    sender__icontains='r.lively@crossoverglobal.net'
                )
                
                if verbose:
                    self.stdout.write(
                        f'Found {rachel_lively_communications.count()} communications '
                        f'from Rachel Lively incorrectly linked to Rachel Ferguson'
                    )
                
                if rachel_lively_communications.count() == 0:
                    self.stdout.write(
                        self.style.WARNING(
                            'No communications from Rachel Lively found linked to Rachel Ferguson'
                        )
                    )
                    return
                
                # Step 3: Create Rachel Lively's Contact and Person records
                default_office = Office.objects.first()
                if not default_office:
                    self.stdout.write(
                        self.style.ERROR('No Office found in database')
                    )
                    return
                
                # Check if Rachel Lively already exists
                try:
                    rachel_lively_contact = Contact.objects.get(
                        email='r.lively@crossoverglobal.net'
                    )
                    rachel_lively_person = Person.objects.get(
                        contact=rachel_lively_contact
                    )
                    if verbose:
                        self.stdout.write(
                            f'Rachel Lively already exists: Person ID {rachel_lively_person.id}'
                        )
                except (Contact.DoesNotExist, Person.DoesNotExist):
                    # Create Rachel Lively's records
                    if not dry_run:
                        rachel_lively_contact = Contact.objects.create(
                            first_name='Rachel',
                            last_name='Lively',
                            email='r.lively@crossoverglobal.net',
                            type='person',
                            office=default_office,
                            priority='medium',
                            notes='Created automatically to fix email linkage issue #17'
                        )
                        
                        rachel_lively_person = Person.objects.create(
                            contact=rachel_lively_contact
                        )
                        
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'Created Rachel Lively: Person ID {rachel_lively_person.id}, '
                                f'Contact ID {rachel_lively_contact.id}'
                            )
                        )
                    else:
                        self.stdout.write(
                            self.style.WARNING(
                                'Would create Rachel Lively Contact and Person records'
                            )
                        )
                        rachel_lively_person = None
                
                # Step 4: Update Communications to link to Rachel Lively
                if not dry_run and rachel_lively_person:
                    updated_count = rachel_lively_communications.update(
                        person=rachel_lively_person
                    )
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Updated {updated_count} communications to link to Rachel Lively'
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            f'Would update {rachel_lively_communications.count()} '
                            f'communications to link to Rachel Lively'
                        )
                    )
                
                # Step 5: Show summary of affected communications
                if verbose:
                    self.stdout.write('\nAffected Communications:')
                    for comm in rachel_lively_communications:
                        self.stdout.write(
                            f'  ID {comm.id}: {comm.subject} - {comm.date} '
                            f'(from {comm.sender})'
                        )
                
                # Step 6: Verify Rachel Ferguson's communications
                rachel_ferguson_comms = Communication.objects.filter(
                    person=rachel_ferguson_person
                )
                
                if verbose:
                    self.stdout.write(
                        f'\nRachel Ferguson now has {rachel_ferguson_comms.count()} '
                        f'communications remaining'
                    )
                    
                    # Show remaining communications
                    for comm in rachel_ferguson_comms:
                        self.stdout.write(
                            f'  ID {comm.id}: {comm.subject} - {comm.date} '
                            f'(from {comm.sender})'
                        )
                
                if dry_run:
                    # Rollback transaction in dry run
                    transaction.set_rollback(True)
                    self.stdout.write(
                        self.style.WARNING('\nDRY RUN COMPLETE - No changes made')
                    )
                else:
                    self.stdout.write(
                        self.style.SUCCESS(
                            '\nRachel Ferguson email fix completed successfully!'
                        )
                    )
                    
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error occurred: {str(e)}')
            )
            if not dry_run:
                raise