"""
Base classes and utilities for integration testing
"""
import json
from unittest.mock import Mock, patch, MagicMock
from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from google.oauth2.credentials import Credentials

User = get_user_model()


class GoogleAPITestMixin:
    """Mixin for testing Google API integrations"""
    
    def setUp(self):
        super().setUp()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
    def create_mock_credentials(self, scopes=None):
        """Create mock Google OAuth credentials"""
        mock_creds = Mock(spec=Credentials)
        mock_creds.valid = True
        mock_creds.expired = False
        mock_creds.refresh_token = 'mock_refresh_token'
        mock_creds.token = 'mock_access_token'
        mock_creds.scopes = scopes or []
        return mock_creds
    
    def create_mock_gmail_service(self):
        """Create a mock Gmail service"""
        mock_service = MagicMock()
        
        # Mock users().messages() methods
        mock_service.users().messages().list.return_value.execute.return_value = {
            'messages': [
                {'id': 'msg1', 'threadId': 'thread1'},
                {'id': 'msg2', 'threadId': 'thread2'}
            ],
            'nextPageToken': None
        }
        
        mock_service.users().messages().get.return_value.execute.return_value = {
            'id': 'msg1',
            'threadId': 'thread1',
            'payload': {
                'headers': [
                    {'name': 'Subject', 'value': 'Test Subject'},
                    {'name': 'From', 'value': 'sender@example.com'},
                    {'name': 'To', 'value': 'recipient@example.com'},
                    {'name': 'Date', 'value': 'Mon, 1 Jan 2024 10:00:00 +0000'}
                ],
                'body': {'data': 'VGVzdCBtZXNzYWdlIGJvZHk='}  # Base64 encoded "Test message body"
            }
        }
        
        mock_service.users().messages().send.return_value.execute.return_value = {
            'id': 'sent_msg_id',
            'threadId': 'sent_thread_id'
        }
        
        return mock_service
    
    def create_mock_calendar_service(self):
        """Create a mock Google Calendar service"""
        mock_service = MagicMock()
        
        # Mock calendars list
        mock_service.calendarList().list.return_value.execute.return_value = {
            'items': [
                {
                    'id': 'primary',
                    'summary': 'Test Calendar',
                    'primary': True,
                    'accessRole': 'owner'
                }
            ]
        }
        
        # Mock events
        mock_service.events().list.return_value.execute.return_value = {
            'items': [
                {
                    'id': 'event1',
                    'summary': 'Test Event',
                    'start': {'dateTime': '2024-01-01T10:00:00Z'},
                    'end': {'dateTime': '2024-01-01T11:00:00Z'},
                    'status': 'confirmed'
                }
            ],
            'nextPageToken': None
        }
        
        mock_service.events().insert.return_value.execute.return_value = {
            'id': 'new_event_id',
            'summary': 'New Event',
            'start': {'dateTime': '2024-01-01T10:00:00Z'},
            'end': {'dateTime': '2024-01-01T11:00:00Z'},
            'status': 'confirmed',
            'htmlLink': 'https://calendar.google.com/event?eid=123'
        }
        
        return mock_service
    
    def create_mock_contacts_service(self):
        """Create a mock Google Contacts service"""
        mock_service = MagicMock()
        
        # Mock people connections list
        mock_service.people().connections().list.return_value.execute.return_value = {
            'connections': [
                {
                    'resourceName': 'people/123',
                    'names': [{'displayName': 'John Doe', 'givenName': 'John', 'familyName': 'Doe'}],
                    'emailAddresses': [{'value': 'john@example.com', 'type': 'home'}],
                    'phoneNumbers': [{'value': '+1234567890', 'type': 'mobile'}]
                }
            ],
            'nextPageToken': None
        }
        
        return mock_service


class IntegrationTestCase(GoogleAPITestMixin, TestCase):
    """Base class for integration tests"""
    pass


class TransactionalIntegrationTestCase(GoogleAPITestMixin, TransactionTestCase):
    """Base class for integration tests requiring database transactions"""
    pass


def mock_google_api_build(service_name, version, credentials=None):
    """Mock factory for Google API services"""
    if service_name == 'gmail':
        return GoogleAPITestMixin().create_mock_gmail_service()
    elif service_name == 'calendar':
        return GoogleAPITestMixin().create_mock_calendar_service()
    elif service_name == 'people':
        return GoogleAPITestMixin().create_mock_contacts_service()
    else:
        return MagicMock()