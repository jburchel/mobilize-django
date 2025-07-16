"""
Management command to add Greenville Christian Fellowship church.

This command creates the missing Greenville Christian Fellowship church
that was mentioned in Issue #16.
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from mobilize.contacts.models import Contact
from mobilize.churches.models import Church
from mobilize.admin_panel.models import Office


class Command(BaseCommand):
    help = 'Add Greenville Christian Fellowship church (Issue #16)'

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
            self.style.SUCCESS('Adding Greenville Christian Fellowship church (Issue #16)...')
        )
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('DRY RUN MODE - No changes will be made')
            )
        
        try:
            with transaction.atomic():
                # Check if church already exists
                existing_contact = Contact.objects.filter(
                    church_name__icontains='Greenville Christian Fellowship'
                ).first()
                
                if existing_contact:
                    self.stdout.write(
                        self.style.WARNING(
                            f'Greenville Christian Fellowship already exists as Contact {existing_contact.id}'
                        )
                    )
                    
                    # Check if it has a Church record
                    try:
                        church = Church.objects.get(contact=existing_contact)
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'Church record also exists: {church.id}'
                            )
                        )
                        return
                    except Church.DoesNotExist:
                        self.stdout.write(
                            self.style.WARNING(
                                'Contact exists but no Church record found. Creating Church record...'
                            )
                        )
                        if not dry_run:
                            church = Church.objects.create(
                                contact=existing_contact,
                                name=existing_contact.church_name,
                                location='Greenville, SC'
                            )
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f'Created Church record {church.id} for existing contact'
                                )
                            )
                        else:
                            self.stdout.write(
                                self.style.WARNING(
                                    'Would create Church record for existing contact'
                                )
                            )
                        return
                
                # Get default office
                default_office = Office.objects.filter(name='US').first()
                if not default_office:
                    default_office = Office.objects.first()
                
                if not default_office:
                    self.stdout.write(
                        self.style.ERROR('No Office found in database')
                    )
                    return
                
                # Create new Contact and Church records
                if not dry_run:
                    contact = Contact.objects.create(
                        church_name='Greenville Christian Fellowship',
                        type='church',
                        office=default_office,
                        priority='medium',
                        status='active',
                        city='Greenville',
                        state='SC',
                        country='United States',
                        notes='Added automatically to fix Issue #16'
                    )
                    
                    church = Church.objects.create(
                        contact=contact,
                        name='Greenville Christian Fellowship',
                        location='Greenville, SC'
                    )
                    
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Successfully created Greenville Christian Fellowship:'
                            f'\n- Contact ID: {contact.id}'
                            f'\n- Church ID: {church.id}'
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            'Would create Greenville Christian Fellowship Contact and Church records'
                        )
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
                            '\nGreenville Christian Fellowship added successfully!'
                        )
                    )
                    
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error occurred: {str(e)}')
            )
            if not dry_run:
                raise