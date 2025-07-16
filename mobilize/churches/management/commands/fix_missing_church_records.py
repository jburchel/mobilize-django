"""
Management command to fix missing Church records for existing Contact records.

This command finds Contact records of type 'church' that don't have corresponding
Church records and creates them. This fixes the issue where churches appear in
the Contact database but not in the Churches list page.
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from mobilize.contacts.models import Contact
from mobilize.churches.models import Church


class Command(BaseCommand):
    help = 'Fix missing Church records for existing Contact records (Issue #16)'

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
            self.style.SUCCESS('Starting fix for missing Church records (Issue #16)...')
        )
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('DRY RUN MODE - No changes will be made')
            )
        
        try:
            with transaction.atomic():
                # Find Contact records of type 'church' that don't have Church records
                church_contacts = Contact.objects.filter(type='church')
                
                self.stdout.write(
                    f'Found {church_contacts.count()} church contacts in database'
                )
                
                missing_church_records = []
                
                for contact in church_contacts:
                    try:
                        # Try to get the corresponding Church record
                        church = Church.objects.get(contact=contact)
                        if verbose:
                            self.stdout.write(
                                f'✓ Contact {contact.id} ({contact.church_name}) has Church record {church.id}'
                            )
                    except Church.DoesNotExist:
                        missing_church_records.append(contact)
                        if verbose:
                            self.stdout.write(
                                f'✗ Contact {contact.id} ({contact.church_name}) is missing Church record'
                            )
                    except Church.MultipleObjectsReturned:
                        # Handle case where there are multiple Church records for same contact
                        churches = Church.objects.filter(contact=contact)
                        if verbose:
                            self.stdout.write(
                                f'⚠ Contact {contact.id} ({contact.church_name}) has multiple Church records: {[c.id for c in churches]}'
                            )
                
                self.stdout.write(
                    f'Found {len(missing_church_records)} contacts missing Church records'
                )
                
                if not missing_church_records:
                    self.stdout.write(
                        self.style.SUCCESS('No missing Church records found. All contacts have corresponding Church records.')
                    )
                    return
                
                # Show details of missing records
                self.stdout.write('\nMissing Church records:')
                for contact in missing_church_records:
                    self.stdout.write(
                        f'  Contact ID {contact.id}: {contact.church_name} '
                        f'(Email: {contact.email or "None"}, Office: {contact.office})'
                    )
                
                # Create missing Church records
                if not dry_run:
                    created_count = 0
                    for contact in missing_church_records:
                        try:
                            church = Church.objects.create(
                                contact=contact,
                                name=contact.church_name,
                                location=f"{contact.city}, {contact.state}".strip(', ') if contact.city or contact.state else '',
                                # Additional fields can be populated from contact data
                            )
                            created_count += 1
                            
                            if verbose:
                                self.stdout.write(
                                    f'Created Church record {church.id} for Contact {contact.id} ({contact.church_name})'
                                )
                        except Exception as e:
                            self.stdout.write(
                                self.style.ERROR(
                                    f'Failed to create Church record for Contact {contact.id}: {str(e)}'
                                )
                            )
                    
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Successfully created {created_count} Church records'
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            f'Would create {len(missing_church_records)} Church records'
                        )
                    )
                
                # Verify results
                if not dry_run:
                    total_churches = Church.objects.count()
                    total_church_contacts = Contact.objects.filter(type='church').count()
                    
                    self.stdout.write(
                        f'\nFinal counts:'
                        f'\n- Church records: {total_churches}'
                        f'\n- Church contacts: {total_church_contacts}'
                    )
                    
                    if total_churches == total_church_contacts:
                        self.stdout.write(
                            self.style.SUCCESS(
                                'All church contacts now have corresponding Church records!'
                            )
                        )
                    else:
                        self.stdout.write(
                            self.style.WARNING(
                                'Some church contacts still missing Church records'
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
                            '\nMissing Church records fix completed successfully!'
                        )
                    )
                    
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error occurred: {str(e)}')
            )
            if not dry_run:
                raise