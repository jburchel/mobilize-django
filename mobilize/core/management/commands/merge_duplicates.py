"""
Management command to detect and merge duplicate contacts

This command identifies potential duplicate contacts based on:
- Exact email matches
- Exact name matches (first + last name for people)
- Exact church name matches (for churches)
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Count
from mobilize.contacts.models import Contact, Person
from mobilize.churches.models import Church
from mobilize.communications.models import Communication
from mobilize.tasks.models import Task


class Command(BaseCommand):
    help = 'Detect and merge duplicate contacts'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be merged without making changes',
        )
        parser.add_argument(
            '--auto-merge',
            action='store_true',
            help='Automatically merge obvious duplicates',
        )
        parser.add_argument(
            '--merge-contact-ids',
            type=str,
            help='Comma-separated list of contact IDs to merge (e.g., "123,456,789")',
        )
        parser.add_argument(
            '--keep-contact-id',
            type=int,
            help='ID of contact to keep when merging specific contacts',
        )

    def handle(self, *args, **options):
        self.dry_run = options['dry_run']
        self.auto_merge = options['auto_merge']
        
        if self.dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))
        
        if options['merge_contact_ids']:
            # Merge specific contacts
            contact_ids = [int(id.strip()) for id in options['merge_contact_ids'].split(',')]
            keep_id = options['keep_contact_id']
            if not keep_id:
                self.stdout.write(self.style.ERROR('--keep-contact-id is required when merging specific contacts'))
                return
            
            self.merge_specific_contacts(contact_ids, keep_id)
        else:
            # Detect and merge duplicates
            self.detect_and_merge_duplicates()

    def detect_and_merge_duplicates(self):
        """Detect and merge duplicate contacts"""
        self.stdout.write('=== DETECTING DUPLICATE CONTACTS ===')
        
        # 1. Email duplicates (most reliable)
        email_duplicates = self.find_email_duplicates()
        self.stdout.write(f'Found {len(email_duplicates)} email duplicate groups')
        
        # 2. Name duplicates for people
        name_duplicates = self.find_name_duplicates()
        self.stdout.write(f'Found {len(name_duplicates)} name duplicate groups')
        
        # 3. Church name duplicates
        church_duplicates = self.find_church_duplicates()
        self.stdout.write(f'Found {len(church_duplicates)} church duplicate groups')
        
        total_merged = 0
        
        # Process email duplicates first (highest confidence)
        for email, contacts in email_duplicates.items():
            if self.auto_merge or self.is_obvious_duplicate(contacts):
                merged = self.merge_contacts(contacts, f"email: {email}")
                if merged:
                    total_merged += len(contacts) - 1
        
        # Process name duplicates (medium confidence)
        for name_key, contacts in name_duplicates.items():
            if self.auto_merge and self.is_obvious_duplicate(contacts):
                merged = self.merge_contacts(contacts, f"name: {name_key}")
                if merged:
                    total_merged += len(contacts) - 1
        
        # Process church duplicates (medium confidence)
        for church_name, contacts in church_duplicates.items():
            if self.auto_merge and self.is_obvious_duplicate(contacts):
                merged = self.merge_contacts(contacts, f"church: {church_name}")
                if merged:
                    total_merged += len(contacts) - 1
        
        self.stdout.write(self.style.SUCCESS(f'Total contacts merged: {total_merged}'))

    def find_email_duplicates(self):
        """Find contacts with duplicate emails"""
        email_duplicates = {}
        
        duplicate_emails = Contact.objects.values('email').annotate(
            count=Count('id')
        ).filter(count__gt=1, email__isnull=False).exclude(email='')
        
        for dup in duplicate_emails:
            email = dup['email']
            contacts = list(Contact.objects.filter(email=email).order_by('id'))
            email_duplicates[email] = contacts
            
        return email_duplicates

    def find_name_duplicates(self):
        """Find people with duplicate names"""
        name_duplicates = {}
        
        duplicate_names = Contact.objects.filter(type='person').values(
            'first_name', 'last_name'
        ).annotate(count=Count('id')).filter(
            count__gt=1, 
            first_name__isnull=False, 
            last_name__isnull=False
        ).exclude(first_name='').exclude(last_name='')
        
        for dup in duplicate_names:
            first, last = dup['first_name'], dup['last_name']
            name_key = f"{first} {last}"
            contacts = list(Contact.objects.filter(
                type='person', 
                first_name=first, 
                last_name=last
            ).order_by('id'))
            name_duplicates[name_key] = contacts
            
        return name_duplicates

    def find_church_duplicates(self):
        """Find churches with duplicate names"""
        church_duplicates = {}
        
        duplicate_churches = Contact.objects.filter(type='church').values(
            'church_name'
        ).annotate(count=Count('id')).filter(
            count__gt=1,
            church_name__isnull=False
        ).exclude(church_name='')
        
        for dup in duplicate_churches:
            church_name = dup['church_name']
            contacts = list(Contact.objects.filter(
                type='church', 
                church_name=church_name
            ).order_by('id'))
            church_duplicates[church_name] = contacts
            
        return church_duplicates

    def is_obvious_duplicate(self, contacts):
        """Determine if contacts are obvious duplicates that can be auto-merged"""
        if len(contacts) < 2:
            return False
        
        # Check if all contacts have the same email (if email exists)
        emails = [c.email for c in contacts if c.email]
        if emails and len(set(emails)) == 1:
            return True
        
        # Check if all contacts have same name and type
        if contacts[0].type == 'person':
            first_names = set(c.first_name for c in contacts if c.first_name)
            last_names = set(c.last_name for c in contacts if c.last_name)
            if len(first_names) <= 1 and len(last_names) <= 1:
                return True
        elif contacts[0].type == 'church':
            church_names = set(c.church_name for c in contacts if c.church_name)
            if len(church_names) <= 1:
                return True
        
        return False

    def merge_contacts(self, contacts, reason):
        """Merge a list of contacts into the first (oldest) one"""
        if len(contacts) < 2:
            return False
        
        primary_contact = contacts[0]  # Keep the oldest one
        duplicate_contacts = contacts[1:]
        
        self.stdout.write(f'\\nMerging contacts for {reason}:')
        self.stdout.write(f'  Keeping: ID {primary_contact.id} - {primary_contact}')
        
        for dup in duplicate_contacts:
            self.stdout.write(f'  Merging: ID {dup.id} - {dup}')
        
        if self.dry_run:
            self.stdout.write('  [DRY RUN] Would merge contacts')
            return True
        
        try:
            with transaction.atomic():
                # Merge the data
                self.merge_contact_data(primary_contact, duplicate_contacts)
                
                # Delete duplicates
                for dup in duplicate_contacts:
                    self.delete_duplicate_contact(dup)
                
                self.stdout.write(f'  ✓ Successfully merged {len(duplicate_contacts)} duplicates')
                return True
                
        except Exception as e:
            self.stdout.write(f'  ✗ Error merging contacts: {e}')
            return False

    def merge_contact_data(self, primary, duplicates):
        """Merge data from duplicate contacts into the primary contact"""
        # Collect the best data from all contacts
        all_contacts = [primary] + duplicates
        
        # Update primary contact with best available data
        updates = {}
        
        # Basic contact fields
        if not primary.email:
            for contact in duplicates:
                if contact.email:
                    updates['email'] = contact.email
                    break
        
        if not primary.phone:
            for contact in duplicates:
                if contact.phone:
                    updates['phone'] = contact.phone
                    break
        
        # Address fields
        for field in ['street_address', 'city', 'state', 'zip_code', 'country']:
            if not getattr(primary, field):
                for contact in duplicates:
                    value = getattr(contact, field)
                    if value:
                        updates[field] = value
                        break
        
        # Notes (combine them)
        notes_parts = []
        if primary.notes:
            notes_parts.append(primary.notes)
        
        for contact in duplicates:
            if contact.notes and contact.notes not in notes_parts:
                notes_parts.append(f"[From duplicate ID {contact.id}]: {contact.notes}")
        
        if len(notes_parts) > 1:
            updates['notes'] = '\\n\\n'.join(notes_parts)
        
        # Apply updates
        if updates:
            for field, value in updates.items():
                setattr(primary, field, value)
            primary.save()
        
        # Merge related objects
        self.merge_related_objects(primary, duplicates)

    def merge_related_objects(self, primary, duplicates):
        """Merge related objects from duplicates to primary"""
        for duplicate in duplicates:
            # Move tasks
            try:
                Task.objects.filter(contact=duplicate).update(contact=primary)
            except Exception as e:
                self.stdout.write(f"    Warning: Could not move tasks: {e}")
            
            # Move communications - check correct field name
            try:
                # Communications might use person/church instead of contact
                if duplicate.type == 'person':
                    Communication.objects.filter(person=duplicate.person_details).update(person=primary.person_details)
                elif duplicate.type == 'church':
                    Communication.objects.filter(church=duplicate.church_details).update(church=primary.church_details)
            except Exception as e:
                self.stdout.write(f"    Warning: Could not move communications: {e}")
            
            # For people, merge Person details
            if duplicate.type == 'person':
                try:
                    dup_person = duplicate.person_details
                    primary_person, created = Person.objects.get_or_create(contact=primary)
                    
                    # Merge person-specific data
                    person_updates = {}
                    for field in ['title', 'preferred_name', 'birthday', 'anniversary', 
                                'marital_status', 'spouse_first_name', 'spouse_last_name',
                                'home_country', 'profession', 'organization']:
                        if not getattr(primary_person, field, None) and getattr(dup_person, field, None):
                            person_updates[field] = getattr(dup_person, field)
                    
                    if person_updates:
                        for field, value in person_updates.items():
                            setattr(primary_person, field, value)
                        primary_person.save()
                        
                except Person.DoesNotExist:
                    pass
            
            # For churches, merge Church details
            elif duplicate.type == 'church':
                try:
                    dup_church = Church.objects.get(contact=duplicate)
                    primary_church, created = Church.objects.get_or_create(
                        contact=primary,
                        defaults={'name': primary.church_name}
                    )
                    
                    # Merge church-specific data
                    church_updates = {}
                    for field in ['denomination', 'website', 'congregation_size', 
                                'year_founded', 'pastor_name', 'pastor_email', 'pastor_phone']:
                        if not getattr(primary_church, field, None) and getattr(dup_church, field, None):
                            church_updates[field] = getattr(dup_church, field)
                    
                    if church_updates:
                        for field, value in church_updates.items():
                            setattr(primary_church, field, value)
                        primary_church.save()
                        
                except Church.DoesNotExist:
                    pass

    def delete_duplicate_contact(self, contact):
        """Safely delete a duplicate contact"""
        # Delete related Person or Church record first
        if contact.type == 'person':
            try:
                contact.person_details.delete()
            except Person.DoesNotExist:
                pass
        elif contact.type == 'church':
            try:
                Church.objects.get(contact=contact).delete()
            except Church.DoesNotExist:
                pass
        
        # Delete the contact
        contact.delete()

    def merge_specific_contacts(self, contact_ids, keep_id):
        """Merge specific contacts by ID"""
        self.stdout.write(f'Merging contacts {contact_ids}, keeping ID {keep_id}')
        
        if keep_id not in contact_ids:
            self.stdout.write(self.style.ERROR(f'Keep ID {keep_id} not in contact list'))
            return
        
        contacts = []
        for contact_id in contact_ids:
            try:
                contact = Contact.objects.get(id=contact_id)
                contacts.append(contact)
            except Contact.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'Contact ID {contact_id} not found'))
        
        if len(contacts) < 2:
            self.stdout.write(self.style.ERROR('Need at least 2 contacts to merge'))
            return
        
        # Reorder so the contact to keep is first
        primary = None
        others = []
        for contact in contacts:
            if contact.id == keep_id:
                primary = contact
            else:
                others.append(contact)
        
        if not primary:
            self.stdout.write(self.style.ERROR(f'Contact to keep (ID {keep_id}) not found'))
            return
        
        ordered_contacts = [primary] + others
        self.merge_contacts(ordered_contacts, f"manual merge")