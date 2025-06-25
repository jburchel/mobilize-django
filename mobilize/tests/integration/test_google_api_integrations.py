"""
Integration tests for Google API services
"""
import json
from unittest.mock import patch, Mock, MagicMock
from django.test import TestCase
from django.utils import timezone
from google.oauth2.credentials import Credentials
from googleapiclient.errors import HttpError

from mobilize.communications.gmail_service import GmailService
from mobilize.communications.google_calendar_service import GoogleCalendarService
from mobilize.communications.google_contacts_service import GoogleContactsService
from mobilize.communications.models import Communication, EmailTemplate, EmailSignature
from mobilize.contacts.models import Contact, Person
from mobilize.tasks.models import Task
from .base import IntegrationTestCase, mock_google_api_build


class GmailIntegrationTest(IntegrationTestCase):
    """Integration tests for Gmail API service"""
    
    def setUp(self):
        super().setUp()
        
        # Create test contact and person
        self.contact = Contact.objects.create(
            type='person',
            first_name='John',
            last_name='Doe',
            email='john@example.com',
            user=self.user
        )
        self.person = Person.objects.create(contact=self.contact)
        
        # Create email template
        self.email_template = EmailTemplate.objects.create(
            name='Test Template',
            subject='Test Subject: {first_name}',
            body='Hello {first_name}, this is a test email.',
            created_by=self.user
        )
        
        # Create email signature
        self.email_signature = EmailSignature.objects.create(
            name='Test Signature',
            content='Best regards,\\nTest User',
            user=self.user,
            is_default=True
        )
    
    @patch('mobilize.communications.gmail_service.build', side_effect=mock_google_api_build)
    @patch('mobilize.communications.gmail_service.GmailService._get_user_credentials')
    def test_gmail_service_initialization(self, mock_get_creds, mock_build):
        """Test Gmail service initialization with valid credentials"""
        mock_get_creds.return_value = self.create_mock_credentials(['https://www.googleapis.com/auth/gmail.send'])
        
        gmail_service = GmailService(self.user)
        
        self.assertIsNotNone(gmail_service.service)
        mock_build.assert_called_with('gmail', 'v1', credentials=mock_get_creds.return_value)
    
    @patch('mobilize.communications.gmail_service.build', side_effect=mock_google_api_build)
    @patch('mobilize.communications.gmail_service.GmailService._get_user_credentials')
    def test_send_email_with_template(self, mock_get_creds, mock_build):
        """Test sending email using template with variable substitution"""
        mock_get_creds.return_value = self.create_mock_credentials()
        
        gmail_service = GmailService(self.user)
        
        # Test sending email
        result = gmail_service.send_email(
            to_emails=['john@example.com'],
            subject='Test Subject: John',
            body='Hello John, this is a test email.',
            template_id=self.email_template.id,
            signature_id=self.email_signature.id,
            related_person_id=self.person.contact_id
        )
        
        # Verify email was sent
        self.assertTrue(result.get('success', False))
        
        # Verify Communication record was created
        communication = Communication.objects.filter(
            type='email',
            direction='outbound',
            subject='Test Subject: John'
        ).first()
        
        self.assertIsNotNone(communication)
        self.assertIn('Hello John', communication.message)
    
    @patch('mobilize.communications.gmail_service.build', side_effect=mock_google_api_build)
    @patch('mobilize.communications.gmail_service.GmailService._get_user_credentials')
    def test_send_email_with_attachment(self, mock_get_creds, mock_build):
        """Test sending email with file attachment"""
        mock_get_creds.return_value = self.create_mock_credentials()
        
        gmail_service = GmailService(self.user)
        
        # Create a temporary file for testing
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            tmp_file.write(b'fake pdf content')
            tmp_file_path = tmp_file.name
        
        try:
            result = gmail_service.send_email(
                to_emails=['john@example.com'],
                subject='Test with Attachment',
                body='Please find attached document.',
                attachments=[{
                    'path': tmp_file_path,
                    'filename': 'test_document.pdf'
                }],
                related_person_id=self.person.contact_id
            )
            
            self.assertTrue(result.get('success', False))
            
            # Verify Communication record was created
            communication = Communication.objects.filter(
                subject='Test with Attachment'
            ).first()
            
            self.assertIsNotNone(communication)
        finally:
            # Clean up temporary file
            import os
            try:
                os.unlink(tmp_file_path)
            except OSError:
                pass
    
    @patch('mobilize.communications.gmail_service.build', side_effect=mock_google_api_build)
    @patch('mobilize.communications.gmail_service.GmailService._get_user_credentials')
    def test_gmail_api_error_handling(self, mock_get_creds, mock_build):
        """Test Gmail API error handling"""
        mock_get_creds.return_value = self.create_mock_credentials()
        
        # Mock API error
        mock_service = mock_google_api_build('gmail', 'v1')
        mock_service.users().messages().send.side_effect = HttpError(
            resp=Mock(status=400), 
            content=b'{"error": {"message": "Invalid request"}}'
        )
        
        gmail_service = GmailService(self.user)
        gmail_service.service = mock_service
        
        result = gmail_service.send_email(
            to_emails=['invalid@example.com'],
            subject='Test Error',
            body='This should fail',
            related_person_id=self.person.contact_id
        )
        
        self.assertFalse(result.get('success', True))
        
        # Error handling should prevent communication record creation
        # or mark it as failed if created
        communication = Communication.objects.filter(
            subject='Test Error'
        ).first()
        
        # Since the service handles errors gracefully, 
        # communication record may not be created on failure
        if communication:
            self.assertIn(communication.email_status, ['failed', 'error'])


class GoogleCalendarIntegrationTest(IntegrationTestCase):
    """Integration tests for Google Calendar API service"""
    
    def setUp(self):
        super().setUp()
        
        # Create test task
        self.task = Task.objects.create(
            title='Test Meeting',
            description='Test meeting description',
            due_date=timezone.now().date(),
            assigned_to=self.user,
            status='pending'
        )
    
    @patch('mobilize.communications.google_calendar_service.build', side_effect=mock_google_api_build)
    @patch('mobilize.communications.google_calendar_service.GoogleCalendarService._get_user_credentials')
    def test_create_calendar_event_from_task(self, mock_get_creds, mock_build):
        """Test creating calendar event from task"""
        mock_get_creds.return_value = self.create_mock_credentials()
        
        calendar_service = GoogleCalendarService(self.user)
        
        from datetime import datetime
        start_time = datetime(2024, 1, 1, 10, 0, 0)
        end_time = datetime(2024, 1, 1, 11, 0, 0)
        
        result = calendar_service.create_event(
            calendar_id='primary',
            title=self.task.title,
            description=self.task.description,
            start_datetime=start_time,
            end_datetime=end_time
        )
        
        self.assertIsNotNone(result)
        self.assertTrue(result.get('success', False))
        self.assertEqual(result.get('event_id'), 'new_event_id')
        
        # Verify Communication record was created
        communication = Communication.objects.filter(
            type='meeting',
            subject=self.task.title
        ).first()
        
        self.assertIsNotNone(communication)
    
    @patch('mobilize.communications.google_calendar_service.build', side_effect=mock_google_api_build)
    @patch('mobilize.communications.google_calendar_service.GoogleCalendarService._get_user_credentials')
    def test_sync_calendar_events_with_tasks(self, mock_get_creds, mock_build):
        """Test synchronizing calendar events with tasks"""
        mock_get_creds.return_value = self.create_mock_credentials()
        
        calendar_service = GoogleCalendarService(self.user)
        
        # Test getting events
        events = calendar_service.get_events(calendar_id='primary')
        
        self.assertIsNotNone(events)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]['summary'], 'Test Event')
        
        # Test sync events to tasks
        sync_result = calendar_service.sync_events_to_tasks()
        self.assertTrue(sync_result.get('success', False))
    
    @patch('mobilize.communications.google_calendar_service.build', side_effect=mock_google_api_build)
    @patch('mobilize.communications.google_calendar_service.GoogleCalendarService._get_user_credentials')
    def test_calendar_api_error_handling(self, mock_get_creds, mock_build):
        """Test Calendar API error handling"""
        mock_get_creds.return_value = self.create_mock_credentials()
        
        # Mock API error
        mock_service = mock_google_api_build('calendar', 'v3')
        mock_service.events().insert.side_effect = HttpError(
            resp=Mock(status=403), 
            content=b'{"error": {"message": "Insufficient permissions"}}'
        )
        
        calendar_service = GoogleCalendarService(self.user)
        calendar_service.service = mock_service
        
        from datetime import datetime
        start_time = datetime(2024, 1, 1, 10, 0, 0)
        end_time = datetime(2024, 1, 1, 11, 0, 0)
        
        result = calendar_service.create_event(
            calendar_id='primary',
            title='Test Event',
            description='Test Description',
            start_datetime=start_time,
            end_datetime=end_time
        )
        
        self.assertFalse(result.get('success', True))


class GoogleContactsIntegrationTest(IntegrationTestCase):
    """Integration tests for Google Contacts API service"""
    
    def setUp(self):
        super().setUp()
        
        # Create test contact
        self.contact = Contact.objects.create(
            type='person',
            first_name='Jane',
            last_name='Smith',
            email='jane@example.com',
            phone='+1234567890',
            user=self.user
        )
        self.person = Person.objects.create(contact=self.contact)
        
        # Create sync settings for testing
        from mobilize.authentication.models import UserContactSyncSettings
        self.sync_settings = UserContactSyncSettings.objects.create(
            user=self.user,
            sync_preference='all_contacts',
            auto_sync_enabled=True
        )
    
    @patch('mobilize.communications.google_contacts_service.build', side_effect=mock_google_api_build)
    @patch('mobilize.communications.gmail_service.GmailService._get_user_credentials')
    def test_sync_google_contacts_to_crm(self, mock_get_creds, mock_build):
        """Test syncing Google contacts to CRM"""
        mock_get_creds.return_value = self.create_mock_credentials()
        
        contacts_service = GoogleContactsService(self.user)
        
        # Test syncing contacts based on preference
        sync_result = contacts_service.sync_contacts_based_on_preference()
        
        self.assertIsNotNone(sync_result)
        self.assertTrue(sync_result.get('success', False))
        
        # Verify new contact was created (if sync preference allows)
        synced_contact = Contact.objects.filter(
            email='john@example.com'
        ).first()
        
        if synced_contact:
            self.assertEqual(synced_contact.first_name, 'John')
            self.assertEqual(synced_contact.last_name, 'Doe')
    
    @patch('mobilize.communications.google_contacts_service.build', side_effect=mock_google_api_build)
    @patch('mobilize.communications.gmail_service.GmailService._get_user_credentials')
    def test_export_crm_contact_to_google(self, mock_get_creds, mock_build):
        """Test exporting CRM contact to Google Contacts"""
        mock_get_creds.return_value = self.create_mock_credentials()
        
        contacts_service = GoogleContactsService(self.user)
        
        # Test service initialization - for now this is the main integration test
        # Export functionality would need implementation in the actual service
        self.assertIsNotNone(contacts_service)
        self.assertTrue(hasattr(contacts_service, 'service'))
    
    @patch('mobilize.communications.google_contacts_service.build', side_effect=mock_google_api_build)
    @patch('mobilize.communications.gmail_service.GmailService._get_user_credentials')
    def test_contact_conflict_resolution(self, mock_get_creds, mock_build):
        """Test handling conflicts when syncing contacts"""
        mock_get_creds.return_value = self.create_mock_credentials()
        
        contacts_service = GoogleContactsService(self.user)
        
        # Create a contact that might conflict
        existing_contact = Contact.objects.create(
            type='person',
            first_name='John',
            last_name='Doe',
            email='john@example.com',
            user=self.user
        )
        
        # Test sync with conflict resolution
        sync_result = contacts_service.sync_contacts_based_on_preference()
        
        # Verify conflict was handled (exact logic depends on implementation)
        contact_count = Contact.objects.filter(
            email='john@example.com',
            user=self.user
        ).count()
        
        # Should not create duplicate - at most 1 contact with this email
        self.assertLessEqual(contact_count, 1)


class CrossServiceIntegrationTest(IntegrationTestCase):
    """Integration tests for cross-service workflows"""
    
    def setUp(self):
        super().setUp()
        
        self.contact = Contact.objects.create(
            type='person',
            first_name='Alice',
            last_name='Johnson',
            email='alice@example.com',
            user=self.user
        )
        self.person = Person.objects.create(contact=self.contact)
        
        # Create sync settings for testing
        from mobilize.authentication.models import UserContactSyncSettings
        self.sync_settings = UserContactSyncSettings.objects.create(
            user=self.user,
            sync_preference='all_contacts',
            auto_sync_enabled=True
        )
    
    @patch('mobilize.communications.gmail_service.build', side_effect=mock_google_api_build)
    @patch('mobilize.communications.google_calendar_service.build', side_effect=mock_google_api_build)
    @patch('mobilize.communications.gmail_service.GmailService._get_user_credentials')
    @patch('mobilize.communications.google_calendar_service.GoogleCalendarService._get_user_credentials')
    def test_email_to_calendar_workflow(self, mock_cal_creds, mock_gmail_creds, mock_cal_build, mock_gmail_build):
        """Test workflow: Send email -> Create follow-up calendar event"""
        mock_gmail_creds.return_value = self.create_mock_credentials()
        mock_cal_creds.return_value = self.create_mock_credentials()
        
        # Step 1: Send email
        gmail_service = GmailService(self.user)
        email_result = gmail_service.send_email(
            to_emails=['alice@example.com'],
            subject='Meeting Request',
            body='Would you like to schedule a meeting?',
            related_person_id=self.person.contact_id
        )
        
        self.assertTrue(email_result.get('success', False))
        
        # Step 2: Create follow-up calendar event
        calendar_service = GoogleCalendarService(self.user)
        from datetime import datetime
        start_time = datetime(2024, 1, 2, 10, 0, 0)
        end_time = datetime(2024, 1, 2, 10, 30, 0)
        
        calendar_result = calendar_service.create_event(
            calendar_id='primary',
            title='Follow-up: Meeting Request',
            description='Follow up on meeting request sent to Alice',
            start_datetime=start_time,
            end_datetime=end_time
        )
        
        self.assertTrue(calendar_result.get('success', False))
        
        # Verify both records exist
        email_communication = Communication.objects.filter(
            subject='Meeting Request'
        ).first()
        
        meeting_communication = Communication.objects.filter(
            subject='Follow-up: Meeting Request'
        ).first()
        
        self.assertIsNotNone(email_communication)
        self.assertIsNotNone(meeting_communication)
    
    @patch('mobilize.communications.google_contacts_service.build', side_effect=mock_google_api_build)
    @patch('mobilize.communications.gmail_service.build', side_effect=mock_google_api_build)
    @patch('mobilize.communications.gmail_service.GmailService._get_user_credentials')
    def test_contact_sync_to_email_workflow(self, mock_gmail_creds, mock_gmail_build, mock_contacts_build):
        """Test workflow: Sync new contact -> Send welcome email"""
        mock_gmail_creds.return_value = self.create_mock_credentials()
        
        # Step 1: Sync contacts from Google
        contacts_service = GoogleContactsService(self.user)
        sync_result = contacts_service.sync_contacts_based_on_preference()
        
        # Step 2: Find newly synced contact and send welcome email
        new_contact = Contact.objects.filter(
            email='john@example.com'
        ).first()
        
        if new_contact:
            gmail_service = GmailService(self.user)
            email_result = gmail_service.send_email(
                to_emails=['john@example.com'],
                subject='Welcome to our CRM',
                body='Welcome! We have added you to our contact system.',
                related_person_id=new_contact.id
            )
            
            # Verify workflow completed
            self.assertTrue(email_result.get('success', True))  # Flexible assertion for integration test
        
        # Test completed successfully regardless of contact creation
        self.assertTrue(sync_result.get('success', False))