"""
Database integrity tests for the Mobilize CRM
"""
from django.test import TestCase, TransactionTestCase
from django.db import IntegrityError, transaction
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import datetime, timedelta

from mobilize.contacts.models import Contact, Person
from mobilize.churches.models import Church
from mobilize.tasks.models import Task
from mobilize.communications.models import Communication, EmailTemplate, EmailSignature
from mobilize.admin_panel.models import Office
from mobilize.authentication.models import GoogleToken, UserContactSyncSettings

User = get_user_model()


class DatabaseConstraintTests(TestCase):
    """Test database constraints and foreign key relationships"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.office = Office.objects.create(
            name="Test Office",
            code="TEST",
            is_active=True
        )
    
    def test_contact_user_foreign_key_constraint(self):
        """Test that contacts require valid user references"""
        
        # Valid contact creation should work
        contact = Contact.objects.create(
            type='person',
            first_name='John',
            last_name='Doe',
            email='john@example.com',
            user=self.user,
            office=self.office
        )
        self.assertEqual(contact.user, self.user)
        
        # Contact can exist without user (for imported data)
        contact_no_user = Contact.objects.create(
            type='person',
            first_name='Jane',
            last_name='Smith',
            email='jane@example.com',
            office=self.office
        )
        self.assertIsNone(contact_no_user.user)
    
    def test_person_contact_one_to_one_constraint(self):
        """Test Person-Contact one-to-one relationship constraint"""
        
        # Create a contact
        contact = Contact.objects.create(
            type='person',
            first_name='Alice',
            last_name='Wilson',
            email='alice@example.com',
            user=self.user,
            office=self.office
        )
        
        # Create a person linked to the contact
        person = Person.objects.create(contact=contact)
        self.assertEqual(person.contact, contact)
        
        # Attempting to create another person with the same contact should fail
        with self.assertRaises(IntegrityError):
            Person.objects.create(contact=contact)
    
    def test_church_contact_one_to_one_constraint(self):
        """Test Church-Contact one-to-one relationship constraint"""
        
        # Create a church contact
        church_contact = Contact.objects.create(
            type='church',
            first_name='Grace Community',
            last_name='Church',
            email='info@gracechurch.org',
            user=self.user,
            office=self.office
        )
        
        # Create a church linked to the contact
        church = Church.objects.create(
            contact=church_contact,
            denomination='Baptist'
        )
        self.assertEqual(church.contact, church_contact)
        
        # Attempting to create another church with the same contact should fail
        with self.assertRaises(IntegrityError):
            Church.objects.create(contact=church_contact, denomination='Methodist')
    
    def test_task_foreign_key_constraints(self):
        """Test task foreign key constraints"""
        
        contact = Contact.objects.create(
            type='person',
            first_name='Bob',
            last_name='Johnson',
            email='bob@example.com',
            user=self.user,
            office=self.office
        )
        person = Person.objects.create(contact=contact)
        
        # Valid task creation
        task = Task.objects.create(
            title='Test Task',
            description='Test description',
            due_date=timezone.now().date(),
            assigned_to=self.user,
            created_by=self.user,
            person=person,
            status='pending',
            priority='medium'
        )
        
        self.assertEqual(task.assigned_to, self.user)
        self.assertEqual(task.person, person)
        
        # Task can exist without person (general tasks)
        general_task = Task.objects.create(
            title='General Task',
            description='Not related to specific person',
            due_date=timezone.now().date(),
            assigned_to=self.user,
            created_by=self.user,
            status='pending',
            priority='low'
        )
        self.assertIsNone(general_task.person)
    
    def test_communication_foreign_key_constraints(self):
        """Test communication foreign key constraints"""
        
        contact = Contact.objects.create(
            type='person',
            first_name='Carol',
            last_name='Davis',
            email='carol@example.com',
            user=self.user,
            office=self.office
        )
        person = Person.objects.create(contact=contact)
        
        # Communication linked to person
        comm = Communication.objects.create(
            type='email',
            subject='Test Email',
            message='Test message',
            direction='outbound',
            date=timezone.now().date(),
            person=person,
            user=self.user
        )
        
        self.assertEqual(comm.person, person)
        self.assertEqual(comm.user, self.user)
        
        # Communication can exist without specific person/church
        general_comm = Communication.objects.create(
            type='email',
            subject='General Email',
            message='General message',
            direction='outbound',
            date=timezone.now().date(),
            user=self.user
        )
        self.assertIsNone(general_comm.person)
        self.assertIsNone(general_comm.church)


class DataConsistencyTests(TestCase):
    """Test data consistency rules and business logic"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.office = Office.objects.create(
            name="Test Office",
            code="TEST",
            is_active=True
        )
    
    def test_user_person_relationship_consistency(self):
        """Test that user-person relationships are consistent"""
        
        # User should be able to get or create their person record
        person = self.user.get_or_create_person()
        self.assertIsNotNone(person)
        self.assertEqual(person.user_account, self.user)
        
        # Calling again should return the same person
        person2 = self.user.get_or_create_person()
        self.assertEqual(person, person2)
        
        # User's person contact should have user's email
        self.assertEqual(person.contact.email, self.user.email)
    
    def test_contact_type_consistency(self):
        """Test that contact types are consistent with related models"""
        
        # Person contact
        person_contact = Contact.objects.create(
            type='person',
            first_name='David',
            last_name='Smith',
            email='david@example.com',
            user=self.user,
            office=self.office
        )
        
        # Should be able to create Person record for person contact
        person = Person.objects.create(contact=person_contact)
        self.assertEqual(person_contact.type, 'person')
        
        # Church contact
        church_contact = Contact.objects.create(
            type='church',
            first_name='First Baptist',
            last_name='Church',
            email='info@firstbaptist.org',
            user=self.user,
            office=self.office
        )
        
        # Should be able to create Church record for church contact
        church = Church.objects.create(contact=church_contact)
        self.assertEqual(church_contact.type, 'church')
    
    def test_task_status_progression(self):
        """Test task status progression logic"""
        
        contact = Contact.objects.create(
            type='person',
            first_name='Eva',
            last_name='Brown',
            email='eva@example.com',
            user=self.user,
            office=self.office
        )
        person = Person.objects.create(contact=contact)
        
        # Create task
        task = Task.objects.create(
            title='Status Test Task',
            description='Testing status progression',
            due_date=timezone.now().date(),
            assigned_to=self.user,
            created_by=self.user,
            person=person,
            status='pending',
            priority='medium'
        )
        
        # Task should start as pending
        self.assertEqual(task.status, 'pending')
        self.assertIsNone(task.completed_at)
        
        # Mark as completed
        task.status = 'completed'
        task.completed_at = timezone.now()
        task.save()
        
        self.assertEqual(task.status, 'completed')
        self.assertIsNotNone(task.completed_at)
    
    def test_email_signature_default_logic(self):
        """Test email signature default logic"""
        
        # First signature should be default
        signature1 = EmailSignature.objects.create(
            user=self.user,
            name='Signature 1',
            content='First signature'
        )
        signature1.refresh_from_db()
        self.assertTrue(signature1.is_default)
        
        # Second signature set as default should unset first
        signature2 = EmailSignature.objects.create(
            user=self.user,
            name='Signature 2',
            content='Second signature',
            is_default=True
        )
        
        # Refresh from database
        signature1.refresh_from_db()
        signature2.refresh_from_db()
        
        # Only signature2 should be default
        self.assertFalse(signature1.is_default)
        self.assertTrue(signature2.is_default)
    
    def test_google_token_expiry_logic(self):
        """Test Google token expiry logic"""
        
        # Create unexpired token
        unexpired_token = GoogleToken.objects.create(
            user=self.user,
            access_token='valid_token',
            expires_at=timezone.now() + timedelta(hours=1)
        )
        self.assertFalse(unexpired_token.is_expired)
        
        # Create expired token
        expired_token = GoogleToken.objects.create(
            user=self.user,
            access_token='expired_token',
            expires_at=timezone.now() - timedelta(hours=1)
        )
        self.assertTrue(expired_token.is_expired)


class BusinessRuleTests(TestCase):
    """Test business rules and validation logic"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.office = Office.objects.create(
            name="Test Office",
            code="TEST",
            is_active=True
        )
    
    def test_contact_email_uniqueness_constraint(self):
        """Test that contact emails must be unique system-wide"""
        
        # Create contact with unique email
        contact1 = Contact.objects.create(
            type='person',
            first_name='John',
            last_name='Doe',
            email='john.doe@example.com',
            user=self.user,
            office=self.office
        )
        
        # Attempting to create another contact with same email should fail
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Contact.objects.create(
                    type='person',
                    first_name='Jane',
                    last_name='Doe',
                    email='john.doe@example.com',  # Same email
                    user=self.user,
                    office=self.office
                )
        
        # Different emails should work fine
        contact2 = Contact.objects.create(
            type='person',
            first_name='Jane',
            last_name='Smith',
            email='jane.smith@example.com',  # Different email
            user=self.user,
            office=self.office
        )
        
        self.assertNotEqual(contact1.email, contact2.email)
    
    def test_task_due_date_validation(self):
        """Test task due date business rules"""
        
        contact = Contact.objects.create(
            type='person',
            first_name='Frank',
            last_name='Wilson',
            email='frank@example.com',
            user=self.user,
            office=self.office
        )
        person = Person.objects.create(contact=contact)
        
        # Task with future due date should be allowed
        future_task = Task.objects.create(
            title='Future Task',
            description='Task due in future',
            due_date=timezone.now().date() + timedelta(days=7),
            assigned_to=self.user,
            created_by=self.user,
            person=person,
            status='pending',
            priority='medium'
        )
        self.assertGreater(future_task.due_date, timezone.now().date())
        
        # Task with past due date should be allowed (overdue tasks)
        past_task = Task.objects.create(
            title='Overdue Task',
            description='Task that is overdue',
            due_date=timezone.now().date() - timedelta(days=7),
            assigned_to=self.user,
            created_by=self.user,
            person=person,
            status='pending',
            priority='high'
        )
        self.assertLess(past_task.due_date, timezone.now().date())
    
    def test_communication_direction_validation(self):
        """Test communication direction business rules"""
        
        contact = Contact.objects.create(
            type='person',
            first_name='Grace',
            last_name='Miller',
            email='grace@example.com',
            user=self.user,
            office=self.office
        )
        person = Person.objects.create(contact=contact)
        
        # Valid directions
        valid_directions = ['inbound', 'outbound']
        
        for direction in valid_directions:
            comm = Communication.objects.create(
                type='email',
                subject=f'Test {direction}',
                message=f'Test {direction} message',
                direction=direction,
                date=timezone.now().date(),
                person=person,
                user=self.user
            )
            self.assertEqual(comm.direction, direction)
    
    def test_office_user_relationship_validation(self):
        """Test office-user relationship business rules"""
        
        # Create additional office
        office2 = Office.objects.create(
            name="Second Office",
            code="SECOND",
            is_active=True
        )
        
        # User can have contacts in multiple offices
        contact1 = Contact.objects.create(
            type='person',
            first_name='Office1',
            last_name='Contact',
            email='office1@example.com',
            user=self.user,
            office=self.office
        )
        
        contact2 = Contact.objects.create(
            type='person',
            first_name='Office2',
            last_name='Contact',
            email='office2@example.com',
            user=self.user,
            office=office2
        )
        
        self.assertEqual(contact1.office, self.office)
        self.assertEqual(contact2.office, office2)
        self.assertEqual(contact1.user, contact2.user)
    
    def test_user_contact_sync_settings_validation(self):
        """Test user contact sync settings validation"""
        
        # Valid sync preferences
        valid_preferences = ['disabled', 'crm_only', 'all_contacts']
        
        for preference in valid_preferences:
            settings = UserContactSyncSettings.objects.create(
                user=self.user,
                sync_preference=preference,
                auto_sync_enabled=True
            )
            self.assertEqual(settings.sync_preference, preference)
            
            # Clean up for next iteration
            settings.delete()
        
        # Test sync frequency validation
        settings = UserContactSyncSettings.objects.create(
            user=self.user,
            sync_preference='crm_only',
            sync_frequency_hours=24
        )
        
        # Should sync when no last sync
        self.assertTrue(settings.should_sync_now())
        
        # Update last sync to recent
        settings.last_sync_at = timezone.now()
        settings.save()
        
        # Should not sync when recently synced
        self.assertFalse(settings.should_sync_now())


class ConcurrencyTests(TransactionTestCase):
    """Test concurrent operations and transaction handling"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.office = Office.objects.create(
            name="Test Office",
            code="TEST",
            is_active=True
        )
    
    def test_concurrent_task_updates(self):
        """Test concurrent task status updates"""
        
        contact = Contact.objects.create(
            type='person',
            first_name='Concurrent',
            last_name='Test',
            email='concurrent@example.com',
            user=self.user,
            office=self.office
        )
        person = Person.objects.create(contact=contact)
        
        task = Task.objects.create(
            title='Concurrent Task',
            description='Test concurrent updates',
            due_date=timezone.now().date(),
            assigned_to=self.user,
            created_by=self.user,
            person=person,
            status='pending',
            priority='medium'
        )
        
        # Simulate concurrent updates
        task1 = Task.objects.get(id=task.id)
        task2 = Task.objects.get(id=task.id)
        
        # Both update status
        task1.status = 'in_progress'
        task2.status = 'completed'
        task2.completed_at = timezone.now()
        
        # Save order matters - last save wins
        task1.save()
        task2.save()
        
        # Refresh and verify final state
        task.refresh_from_db()
        self.assertEqual(task.status, 'completed')
        self.assertIsNotNone(task.completed_at)
    
    def test_atomic_contact_person_creation(self):
        """Test atomic creation of contact and person records"""
        
        try:
            with transaction.atomic():
                contact = Contact.objects.create(
                    type='person',
                    first_name='Atomic',
                    last_name='Test',
                    email='atomic@example.com',
                    user=self.user,
                    office=self.office
                )
                
                person = Person.objects.create(contact=contact)
                
                # Simulate error after person creation
                if person.contact_id:
                    raise Exception("Simulated error")
                    
        except Exception:
            # Both contact and person should be rolled back
            self.assertFalse(
                Contact.objects.filter(email='atomic@example.com').exists()
            )
            self.assertFalse(
                Person.objects.filter(contact__email='atomic@example.com').exists()
            )


class PerformanceIntegrityTests(TestCase):
    """Test performance-related database integrity"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.office = Office.objects.create(
            name="Test Office",
            code="TEST",
            is_active=True
        )
    
    def test_query_optimization_integrity(self):
        """Test that optimized queries maintain data integrity"""
        
        # Create multiple contacts
        contacts = []
        for i in range(10):
            contact = Contact.objects.create(
                type='person',
                first_name=f'Person{i}',
                last_name='Test',
                email=f'person{i}@example.com',
                user=self.user,
                office=self.office
            )
            Person.objects.create(contact=contact)
            contacts.append(contact)
        
        # Test select_related query
        people_with_contacts = Person.objects.select_related('contact').all()
        
        # Verify all relationships are properly loaded
        for person in people_with_contacts:
            self.assertIsNotNone(person.contact)
            self.assertEqual(person.contact.type, 'person')
            self.assertEqual(person.contact.user, self.user)
        
        # Test prefetch_related for reverse relationships
        contacts_with_people = Contact.objects.prefetch_related('person_details').filter(
            type='person'
        )
        
        for contact in contacts_with_people:
            self.assertTrue(hasattr(contact, 'person_details'))
            self.assertEqual(contact.person_details.contact, contact)
    
    def test_index_usage_integrity(self):
        """Test that database indexes don't compromise data integrity"""
        
        # Create contacts with different statuses and priorities
        statuses = ['new', 'contacted', 'interested', 'engaged']
        priorities = ['low', 'medium', 'high']
        
        for status in statuses:
            for priority in priorities:
                Contact.objects.create(
                    type='person',
                    first_name=f'{status.title()}',
                    last_name=f'{priority.title()}',
                    email=f'{status}.{priority}@example.com',
                    user=self.user,
                    office=self.office,
                    status=status,
                    priority=priority
                )
        
        # Test indexed queries maintain data integrity
        high_priority_contacts = Contact.objects.filter(priority='high')
        self.assertEqual(high_priority_contacts.count(), 4)
        
        for contact in high_priority_contacts:
            self.assertEqual(contact.priority, 'high')
        
        # Test compound index queries
        interested_high_contacts = Contact.objects.filter(
            status='interested',
            priority='high'
        )
        self.assertEqual(interested_high_contacts.count(), 1)
        
        contact = interested_high_contacts.first()
        self.assertEqual(contact.status, 'interested')
        self.assertEqual(contact.priority, 'high')