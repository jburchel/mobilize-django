"""
Integration tests for complete user workflows
"""
from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from datetime import datetime, timedelta

from mobilize.contacts.models import Contact, Person
from mobilize.churches.models import Church
from mobilize.tasks.models import Task
from mobilize.communications.models import Communication, EmailTemplate
from mobilize.admin_panel.models import Office
from mobilize.authentication.models import UserContactSyncSettings

User = get_user_model()


class UserOnboardingWorkflowTest(TestCase):
    """Test the complete user onboarding workflow"""
    
    def setUp(self):
        # Create an office for the user
        self.office = Office.objects.create(
            name="Test Office",
            code="TEST",
            is_active=True
        )
        
    def test_complete_user_onboarding_workflow(self):
        """Test complete user onboarding from registration to first tasks"""
        
        # Step 1: User registration
        user_data = {
            'username': 'newuser@example.com',
            'email': 'newuser@example.com',
            'first_name': 'John',
            'last_name': 'Doe',
            'password': 'testpass123'
        }
        
        user = User.objects.create_user(**user_data)
        self.assertEqual(user.role, 'standard_user')  # Default role
        
        # Step 2: Automatic Person record creation
        person = user.get_or_create_person()
        self.assertIsNotNone(person)
        self.assertEqual(person.contact.email, user.email)
        self.assertEqual(person.contact.first_name, user.first_name)
        
        # Step 3: User contact sync settings creation
        sync_settings = UserContactSyncSettings.objects.create(
            user=user,
            sync_preference='crm_only',
            auto_sync_enabled=True
        )
        self.assertEqual(sync_settings.sync_preference, 'crm_only')
        
        # Step 4: User creates their first contact
        contact = Contact.objects.create(
            type='person',
            first_name='Jane',
            last_name='Smith',
            email='jane@example.com',
            user=user,
            office=self.office
        )
        person_contact = Person.objects.create(contact=contact)
        
        # Step 5: User creates their first task
        task = Task.objects.create(
            title='Follow up with Jane',
            description='Call to discuss partnership',
            due_date=timezone.now().date() + timedelta(days=7),
            assigned_to=user,
            created_by=user,
            person=person_contact,
            status='pending',
            priority='high'
        )
        
        # Step 6: User creates an email template
        template = EmailTemplate.objects.create(
            name='Follow-up Template',
            subject='Following up on our conversation',
            body='Hi {first_name}, I wanted to follow up...',
            created_by=user
        )
        
        # Verify the complete workflow
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(Contact.objects.count(), 2)  # User's person + Jane
        self.assertEqual(Person.objects.count(), 2)   # User's person + Jane
        self.assertEqual(Task.objects.count(), 1)
        self.assertEqual(EmailTemplate.objects.count(), 1)
        
        # Verify relationships
        self.assertEqual(task.person, person_contact)
        self.assertEqual(task.assigned_to, user)
        self.assertEqual(contact.user, user)


class ContactManagementWorkflowTest(TestCase):
    """Test contact management workflows"""
    
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
    
    def test_contact_to_pipeline_progression_workflow(self):
        """Test moving a contact through pipeline stages"""
        
        # Step 1: Create initial contact
        contact = Contact.objects.create(
            type='person',
            first_name='Sarah',
            last_name='Johnson',
            email='sarah@example.com',
            phone='+1234567890',
            user=self.user,
            office=self.office,
            status='new',
            priority='medium'
        )
        person = Person.objects.create(contact=contact)
        
        # Step 2: First interaction - create communication record
        communication = Communication.objects.create(
            type='email',
            subject='Initial outreach',
            message='Sent initial introduction email',
            direction='outbound',
            date=timezone.now().date(),
            person=person,
            user=self.user,
            email_status='sent'
        )
        
        # Step 3: Update contact status after first contact
        contact.status = 'contacted'
        contact.save()
        
        # Step 4: Schedule follow-up task
        follow_up_task = Task.objects.create(
            title='Follow up with Sarah',
            description='Call to discuss next steps',
            due_date=timezone.now().date() + timedelta(days=3),
            assigned_to=self.user,
            created_by=self.user,
            person=person,
            status='pending',
            priority='high'
        )
        
        # Step 5: Second interaction - phone call
        phone_communication = Communication.objects.create(
            type='phone',
            subject='Follow-up call',
            message='Discussed partnership opportunities',
            direction='outbound',
            date=timezone.now().date(),
            person=person,
            user=self.user
        )
        
        # Step 6: Mark task as completed
        follow_up_task.status = 'completed'
        follow_up_task.completed_at = timezone.now()
        follow_up_task.save()
        
        # Step 7: Progress contact to next stage
        contact.status = 'interested'
        contact.priority = 'high'
        contact.save()
        
        # Step 8: Create next phase task
        next_task = Task.objects.create(
            title='Send proposal to Sarah',
            description='Prepare and send partnership proposal',
            due_date=timezone.now().date() + timedelta(days=5),
            assigned_to=self.user,
            created_by=self.user,
            person=person,
            status='pending',
            priority='high'
        )
        
        # Verify the workflow progression
        self.assertEqual(contact.status, 'interested')
        self.assertEqual(contact.priority, 'high')
        self.assertEqual(Communication.objects.filter(person=person).count(), 2)
        self.assertEqual(Task.objects.filter(person=person, status='completed').count(), 1)
        self.assertEqual(Task.objects.filter(person=person, status='pending').count(), 1)
        
        # Verify task completion
        completed_task = Task.objects.get(status='completed')
        self.assertEqual(completed_task.title, 'Follow up with Sarah')
        self.assertIsNotNone(completed_task.completed_at)


class ChurchManagementWorkflowTest(TestCase):
    """Test church management workflows"""
    
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
    
    def test_church_contact_management_workflow(self):
        """Test managing church contacts and relationships"""
        
        # Step 1: Create church contact
        church_contact = Contact.objects.create(
            type='church',
            first_name='Grace Community',
            last_name='Church',
            email='info@gracecommunitychurch.org',
            phone='+1555123456',
            street_address='123 Main St',
            city='Anytown',
            state='CA',
            zip_code='12345',
            user=self.user,
            office=self.office,
            status='new',
            priority='medium'
        )
        
        # Step 2: Create church record
        church = Church.objects.create(
            contact=church_contact,
            denomination='Non-denominational',
            congregation_size=250,
            website='https://gracecommunitychurch.org'
        )
        
        # Step 3: Create pastor contact
        pastor_contact = Contact.objects.create(
            type='person',
            first_name='Michael',
            last_name='Thompson',
            email='pastor@gracecommunitychurch.org',
            phone='+1555123457',
            user=self.user,
            office=self.office,
            status='new',
            priority='high'
        )
        
        # Step 4: Create pastor person record
        pastor = Person.objects.create(
            contact=pastor_contact,
            title='Senior Pastor',
            primary_church=church
        )
        
        # Step 5: Initial outreach to church
        church_communication = Communication.objects.create(
            type='email',
            subject='Partnership opportunity',
            message='Sent initial partnership proposal',
            direction='outbound',
            date=timezone.now().date(),
            church=church,
            user=self.user,
            email_status='sent'
        )
        
        # Step 6: Follow-up with pastor
        pastor_communication = Communication.objects.create(
            type='phone',
            subject='Pastor meeting request',
            message='Called to schedule in-person meeting',
            direction='outbound',
            date=timezone.now().date(),
            person=pastor,
            user=self.user
        )
        
        # Step 7: Schedule meeting task
        meeting_task = Task.objects.create(
            title='Meet with Pastor Thompson',
            description='In-person meeting to discuss partnership',
            due_date=timezone.now().date() + timedelta(days=10),
            assigned_to=self.user,
            created_by=self.user,
            person=pastor,
            church=church,
            status='pending',
            priority='high'
        )
        
        # Step 8: Create meeting communication record
        meeting_communication = Communication.objects.create(
            type='meeting',
            subject='Partnership meeting',
            message='Met to discuss missionary support partnership',
            direction='outbound',
            date=timezone.now().date() + timedelta(days=10),
            person=pastor,
            church=church,
            user=self.user
        )
        
        # Step 9: Update church status after meeting
        church_contact.status = 'interested'
        church_contact.priority = 'high'
        church_contact.save()
        
        # Step 10: Complete meeting task
        meeting_task.status = 'completed'
        meeting_task.completed_at = timezone.now()
        meeting_task.save()
        
        # Verify the complete workflow
        self.assertEqual(Contact.objects.filter(type='church').count(), 1)
        # Account for user's own Person record + pastor
        self.assertEqual(Contact.objects.filter(type='person').count(), 2)
        self.assertEqual(Church.objects.count(), 1)
        # User's Person record is created automatically + pastor
        self.assertEqual(Person.objects.count(), 2)
        self.assertEqual(Communication.objects.count(), 3)
        self.assertEqual(Task.objects.count(), 1)
        
        # Verify relationships
        self.assertEqual(pastor.primary_church, church)
        self.assertEqual(church_contact.status, 'interested')
        self.assertEqual(pastor_contact.priority, 'high')
        
        # Verify communications are linked correctly
        church_comms = Communication.objects.filter(church=church)
        pastor_comms = Communication.objects.filter(person=pastor)
        self.assertEqual(church_comms.count(), 2)  # Church email + meeting
        self.assertEqual(pastor_comms.count(), 2)  # Pastor call + meeting


class TaskManagementWorkflowTest(TestCase):
    """Test task management workflows"""
    
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
        
        # Create a contact for tasks
        self.contact = Contact.objects.create(
            type='person',
            first_name='Alice',
            last_name='Wilson',
            email='alice@example.com',
            user=self.user,
            office=self.office
        )
        self.person = Person.objects.create(contact=self.contact)
    
    def test_task_lifecycle_workflow(self):
        """Test complete task lifecycle from creation to completion"""
        
        # Step 1: Create high-priority task
        task = Task.objects.create(
            title='Prepare donor presentation',
            description='Create presentation for potential major donor Alice Wilson',
            due_date=timezone.now().date() + timedelta(days=14),
            assigned_to=self.user,
            created_by=self.user,
            person=self.person,
            status='pending',
            priority='high'
        )
        
        # Step 2: Start working on task
        task.status = 'in_progress'
        task.save()
        
        # Step 3: Add notes/comments through communication
        progress_communication = Communication.objects.create(
            type='email',  # Use email instead of note for consistency
            subject='Presentation progress update',
            message='Completed research on donor interests and giving history',
            direction='outbound',  # Use outbound instead of internal
            date=timezone.now().date(),
            person=self.person,
            user=self.user
        )
        
        # Step 4: Create subtask for preparation
        subtask = Task.objects.create(
            title='Gather Alice\'s giving history',
            description='Research past donations and interests',
            due_date=timezone.now().date() + timedelta(days=7),
            assigned_to=self.user,
            created_by=self.user,
            person=self.person,
            status='pending',
            priority='medium'
        )
        
        # Step 5: Complete subtask
        subtask.status = 'completed'
        subtask.completed_at = timezone.now()
        subtask.save()
        
        # Step 6: Schedule presentation meeting
        presentation_task = Task.objects.create(
            title='Present to Alice Wilson',
            description='Deliver donor presentation',
            due_date=timezone.now().date() + timedelta(days=15),
            assigned_to=self.user,
            created_by=self.user,
            person=self.person,
            status='pending',
            priority='high'
        )
        
        # Step 7: Complete main task
        task.status = 'completed'
        task.completed_at = timezone.now()
        task.save()
        
        # Step 8: Log presentation meeting
        presentation_communication = Communication.objects.create(
            type='meeting',
            subject='Donor presentation meeting',
            message='Successfully presented missionary work and funding needs',
            direction='outbound',
            date=timezone.now().date() + timedelta(days=15),
            person=self.person,
            user=self.user
        )
        
        # Step 9: Complete presentation task
        presentation_task.status = 'completed'
        presentation_task.completed_at = timezone.now()
        presentation_task.save()
        
        # Step 10: Follow-up task
        followup_task = Task.objects.create(
            title='Follow up on presentation',
            description='Send thank you note and follow up on commitment',
            due_date=timezone.now().date() + timedelta(days=18),
            assigned_to=self.user,
            created_by=self.user,
            person=self.person,
            status='pending',
            priority='medium'
        )
        
        # Verify the complete workflow
        total_tasks = Task.objects.filter(person=self.person)
        completed_tasks = total_tasks.filter(status='completed')
        pending_tasks = total_tasks.filter(status='pending')
        
        self.assertEqual(total_tasks.count(), 4)
        self.assertEqual(completed_tasks.count(), 3)
        self.assertEqual(pending_tasks.count(), 1)
        
        # Verify task completion timestamps
        for task in completed_tasks:
            self.assertIsNotNone(task.completed_at)
        
        # Verify communications were created
        communications = Communication.objects.filter(person=self.person)
        # Should have: progress update + presentation meeting = 2 communications
        self.assertEqual(communications.count(), 2)
        
        # Verify task priority handling
        high_priority_tasks = total_tasks.filter(priority='high')
        self.assertEqual(high_priority_tasks.count(), 2)


class CommunicationWorkflowTest(TestCase):
    """Test communication tracking workflows"""
    
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
        
        # Create contacts for communication testing
        self.contact = Contact.objects.create(
            type='person',
            first_name='Robert',
            last_name='Davis',
            email='robert@example.com',
            phone='+1555987654',
            user=self.user,
            office=self.office
        )
        self.person = Person.objects.create(contact=self.contact)
    
    def test_multichannel_communication_workflow(self):
        """Test tracking communications across multiple channels"""
        
        # Step 1: Initial email outreach
        email_comm = Communication.objects.create(
            type='email',
            subject='Introduction and ministry overview',
            message='Sent detailed introduction about our missionary work',
            direction='outbound',
            date=timezone.now().date(),
            person=self.person,
            user=self.user,
            email_status='sent',
            sender=self.user.email
        )
        
        # Step 2: Phone follow-up
        phone_comm = Communication.objects.create(
            type='phone',
            subject='Follow-up call',
            message='Called to discuss email and answer questions',
            direction='outbound',
            date=timezone.now().date() + timedelta(days=2),
            person=self.person,
            user=self.user
        )
        
        # Step 3: Text message for scheduling
        text_comm = Communication.objects.create(
            type='text',
            subject='Meeting confirmation',
            message='Confirmed meeting time and location via SMS',
            direction='outbound',
            date=timezone.now().date() + timedelta(days=3),
            person=self.person,
            user=self.user
        )
        
        # Step 4: In-person meeting
        meeting_comm = Communication.objects.create(
            type='meeting',
            subject='In-person coffee meeting',
            message='Met at local coffee shop to discuss partnership',
            direction='outbound',
            date=timezone.now().date() + timedelta(days=7),
            person=self.person,
            user=self.user
        )
        
        # Step 5: Follow-up email with resources
        followup_email = Communication.objects.create(
            type='email',
            subject='Thank you and resources',
            message='Sent thank you note with ministry resources and prayer card',
            direction='outbound',
            date=timezone.now().date() + timedelta(days=8),
            person=self.person,
            user=self.user,
            email_status='sent'
        )
        
        # Step 6: Update contact status based on communications
        self.contact.status = 'engaged'
        self.contact.priority = 'high'
        self.contact.save()
        
        # Verify communication tracking
        all_communications = Communication.objects.filter(person=self.person)
        self.assertEqual(all_communications.count(), 5)
        
        # Verify communication types
        email_count = all_communications.filter(type='email').count()
        phone_count = all_communications.filter(type='phone').count()
        text_count = all_communications.filter(type='text').count()
        meeting_count = all_communications.filter(type='meeting').count()
        
        self.assertEqual(email_count, 2)
        self.assertEqual(phone_count, 1)
        self.assertEqual(text_count, 1)
        self.assertEqual(meeting_count, 1)
        
        # Verify chronological order
        communications = all_communications.order_by('date')
        self.assertEqual(communications.first().type, 'email')
        self.assertEqual(communications.last().type, 'email')
        
        # Verify contact status progression
        self.assertEqual(self.contact.status, 'engaged')
        self.assertEqual(self.contact.priority, 'high')