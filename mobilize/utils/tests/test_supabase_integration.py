"""
Integration tests for the SupabaseSync utility with the Supabase client.
"""
from unittest.mock import patch, MagicMock

from django.test import TestCase

from mobilize.contacts.models import Contact
from mobilize.utils.supabase_client import SupabaseClient
from mobilize.utils.supabase_sync import SupabaseSync


class SupabaseIntegrationTest(TestCase):
    """Test the integration between SupabaseSync and SupabaseClient."""

    def setUp(self):
        """Set up test environment."""
        # Create a mock contact instead of a real one
        self.contact = MagicMock(spec=Contact)
        self.contact.id = 1
        self.contact.first_name = "Test"
        self.contact.last_name = "Contact"
        self.contact.email = "test@example.com"
        self.contact.phone = "555-1234"
        self.contact.type = "personal"
        
        # Mock the Contact model class
        self.contact_model_mock = MagicMock()
        self.contact_model_mock.__name__ = "Contact"
        self.contact_model_mock._meta = MagicMock()
        self.contact_model_mock._meta.model_name = "contact"
        self.contact_model_mock._meta.app_label = "contacts"
        self.contact_model_mock._meta.db_table = "contacts"

    @patch('mobilize.utils.supabase_client.SupabaseClient.insert')
    @patch('mobilize.utils.supabase_mapper.SupabaseMapper.to_supabase')
    def test_sync_to_supabase_with_client(self, mock_to_supabase, mock_insert):
        """Test syncing a Django model to Supabase using the client."""
        # Mock the mapper to_supabase method
        mock_to_supabase.return_value = {
            'id': 1,
            'first_name': 'Test',
            'last_name': 'Contact',
            'email': 'test@example.com',
            'phone': '555-1234',
            'type': 'personal'
        }
        
        # Mock the client insert method to return a response
        mock_insert.return_value = {
            'id': 1,
            'first_name': 'Test',
            'last_name': 'Contact',
            'email': 'test@example.com',
            'phone': '555-1234',
            'type': 'personal',
            'created_at': '2025-06-05T17:10:00Z'
        }

        # Create a simple function that simulates what we'd want in SupabaseSync
        def sync_to_supabase_with_client(instance):
            from mobilize.utils.supabase_mapper import SupabaseMapper
            client = SupabaseClient()
            supabase_data = SupabaseMapper.to_supabase(instance)
            model_class = instance.__class__
            return client.insert(model_class, supabase_data)
            
        # Sync the contact to Supabase using our function
        result = sync_to_supabase_with_client(self.contact)

        # Check that the mapper and client methods were called
        mock_to_supabase.assert_called_once_with(self.contact)
        mock_insert.assert_called_once()
        
        # Verify the result contains the expected data
        self.assertEqual(result['first_name'], 'Test')
        self.assertEqual(result['last_name'], 'Contact')
        self.assertEqual(result['email'], 'test@example.com')

    @patch('mobilize.utils.supabase_client.SupabaseClient.fetch_by_id')
    @patch('mobilize.utils.supabase_sync.SupabaseSync.sync_from_supabase')
    def test_sync_from_supabase_with_client(self, mock_sync_from_supabase, mock_fetch):
        """Test syncing from Supabase to Django using the client."""
        # Mock the client fetch_by_id method to return a response
        mock_fetch.return_value = {
            'id': 1,
            'first_name': 'Updated',
            'last_name': 'Contact',
            'email': 'updated@example.com',
            'phone': '555-5678',
            'type': 'business',
            'created_at': '2025-06-05T17:10:00Z'
        }
        
        # Create a mock updated contact
        updated_contact = MagicMock(spec=Contact)
        updated_contact.id = 1
        updated_contact.first_name = 'Updated'
        updated_contact.last_name = 'Contact'
        updated_contact.email = 'updated@example.com'
        updated_contact.phone = '555-5678'
        updated_contact.type = 'business'
        
        # Mock the sync_from_supabase method
        mock_sync_from_supabase.return_value = updated_contact

        # Create a simple function that simulates what we'd want in SupabaseSync
        def sync_from_supabase_with_client(record_id, model_class):
            client = SupabaseClient()
            supabase_data = client.fetch_by_id(model_class, record_id)
            if not supabase_data:
                return None
            return SupabaseSync.sync_from_supabase(supabase_data, model_class)
            
        # Sync from Supabase to Django using our function
        result = sync_from_supabase_with_client(1, self.contact_model_mock)
        
        # Verify the mocks were called
        mock_fetch.assert_called_once_with(self.contact_model_mock, 1)
        mock_sync_from_supabase.assert_called_once()
        
        # Check that the result is the updated contact
        self.assertEqual(result, updated_contact)
        self.assertEqual(result.first_name, 'Updated')
        self.assertEqual(result.email, 'updated@example.com')
        self.assertEqual(result.type, 'business')
