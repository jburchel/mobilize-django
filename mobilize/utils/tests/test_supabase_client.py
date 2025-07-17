"""
Tests for the Supabase client integration.
"""

import os
from unittest.mock import patch, MagicMock

from django.test import TestCase

from mobilize.contacts.models import Contact
from mobilize.utils.supabase_client import SupabaseClient


class SupabaseClientTest(TestCase):
    """Test the Supabase client integration."""

    def setUp(self):
        """Set up test environment."""
        self.client = SupabaseClient()
        # Create a mock response object that mimics the Supabase response structure
        self.mock_response = MagicMock()
        self.mock_response.data = [
            {"id": 1, "name": "Test Contact", "email": "test@example.com"}
        ]

    def test_get_table_name(self):
        """Test getting the table name for a model."""
        # Test with Contact model
        table_name = self.client.get_table_name(Contact)
        self.assertEqual(table_name, "contacts")

    @patch.dict(
        os.environ,
        {"SUPABASE_URL": "https://example.supabase.co", "SUPABASE_KEY": "test-key"},
    )
    @patch("mobilize.utils.supabase_client.create_client")
    def test_init_with_env_vars(self, mock_create_client):
        """Test initialization with environment variables."""
        mock_create_client.return_value = MagicMock()
        client = SupabaseClient()
        self.assertEqual(client.supabase_url, "https://example.supabase.co")
        self.assertEqual(client.supabase_key, "test-key")
        mock_create_client.assert_called_once_with(
            "https://example.supabase.co", "test-key"
        )

    @patch.dict(
        os.environ,
        {"SUPABASE_URL": "https://example.supabase.co", "SUPABASE_KEY": "test-key"},
    )
    @patch("mobilize.utils.supabase_client.create_client")
    def test_fetch_all(self, mock_create_client):
        """Test the implementation of fetch_all with mocked client."""
        # Setup the mock
        mock_client = MagicMock()
        mock_table = MagicMock()
        mock_select = MagicMock()
        mock_limit = MagicMock()

        mock_create_client.return_value = mock_client
        mock_client.table.return_value = mock_table
        mock_table.select.return_value = mock_select
        mock_select.limit.return_value = mock_limit
        mock_select.execute.return_value = self.mock_response
        mock_limit.execute.return_value = self.mock_response

        # Test without limit
        # Create a new client instance to use our mock
        client = SupabaseClient()
        result = client.fetch_all(Contact)

        mock_client.table.assert_called_with("contacts")
        mock_table.select.assert_called_with("*")
        mock_select.execute.assert_called_once()
        self.assertEqual(result, self.mock_response.data)

        # Test with limit
        mock_client.reset_mock()
        mock_table.reset_mock()
        mock_select.reset_mock()

        result = client.fetch_all(Contact, limit=10)
        mock_client.table.assert_called_with("contacts")
        mock_table.select.assert_called_with("*")
        mock_select.limit.assert_called_with(10)
        mock_limit.execute.assert_called_once()

    @patch.dict(
        os.environ,
        {"SUPABASE_URL": "https://example.supabase.co", "SUPABASE_KEY": "test-key"},
    )
    @patch("mobilize.utils.supabase_client.create_client")
    def test_fetch_by_id(self, mock_create_client):
        """Test the implementation of fetch_by_id with mocked client."""
        # Setup the mock
        mock_client = MagicMock()
        mock_table = MagicMock()
        mock_select = MagicMock()
        mock_eq = MagicMock()

        mock_create_client.return_value = mock_client
        mock_client.table.return_value = mock_table
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value = mock_eq
        mock_eq.execute.return_value = self.mock_response

        # Test fetch by id
        client = SupabaseClient()
        result = client.fetch_by_id(Contact, 1)

        mock_client.table.assert_called_with("contacts")
        mock_table.select.assert_called_with("*")
        mock_select.eq.assert_called_with("id", 1)
        mock_eq.execute.assert_called_once()
        self.assertEqual(result, self.mock_response.data[0])

    @patch.dict(
        os.environ,
        {"SUPABASE_URL": "https://example.supabase.co", "SUPABASE_KEY": "test-key"},
    )
    @patch("mobilize.utils.supabase_client.create_client")
    def test_insert(self, mock_create_client):
        """Test the implementation of insert with mocked client."""
        # Setup the mock
        mock_client = MagicMock()
        mock_table = MagicMock()
        mock_insert = MagicMock()

        mock_create_client.return_value = mock_client
        mock_client.table.return_value = mock_table
        mock_table.insert.return_value = mock_insert
        mock_insert.execute.return_value = self.mock_response

        # Test insert
        data = {"name": "Test Contact", "email": "test@example.com"}
        client = SupabaseClient()
        result = client.insert(Contact, data)

        mock_client.table.assert_called_with("contacts")
        mock_table.insert.assert_called_with(data)
        mock_insert.execute.assert_called_once()
        self.assertEqual(result, self.mock_response.data[0])

    @patch.dict(
        os.environ,
        {"SUPABASE_URL": "https://example.supabase.co", "SUPABASE_KEY": "test-key"},
    )
    @patch("mobilize.utils.supabase_client.create_client")
    def test_update(self, mock_create_client):
        """Test the implementation of update with mocked client."""
        # Setup the mock
        mock_client = MagicMock()
        mock_table = MagicMock()
        mock_update = MagicMock()
        mock_eq = MagicMock()

        mock_create_client.return_value = mock_client
        mock_client.table.return_value = mock_table
        mock_table.update.return_value = mock_update
        mock_update.eq.return_value = mock_eq
        mock_eq.execute.return_value = self.mock_response

        # Test update
        data = {"name": "Updated Contact", "email": "updated@example.com"}
        client = SupabaseClient()
        result = client.update(Contact, 1, data)

        mock_client.table.assert_called_with("contacts")
        mock_table.update.assert_called_with(data)
        mock_update.eq.assert_called_with("id", 1)
        mock_eq.execute.assert_called_once()
        self.assertEqual(result, self.mock_response.data[0])

    @patch.dict(
        os.environ,
        {"SUPABASE_URL": "https://example.supabase.co", "SUPABASE_KEY": "test-key"},
    )
    @patch("mobilize.utils.supabase_client.create_client")
    def test_delete(self, mock_create_client):
        """Test the implementation of delete with mocked client."""
        # Setup the mock
        mock_client = MagicMock()
        mock_table = MagicMock()
        mock_delete = MagicMock()
        mock_eq = MagicMock()

        mock_create_client.return_value = mock_client
        mock_client.table.return_value = mock_table
        mock_table.delete.return_value = mock_delete
        mock_delete.eq.return_value = mock_eq
        mock_eq.execute.return_value = self.mock_response

        # Test delete
        client = SupabaseClient()
        result = client.delete(Contact, 1)

        mock_client.table.assert_called_with("contacts")
        mock_table.delete.assert_called_once()
        mock_delete.eq.assert_called_with("id", 1)
        mock_eq.execute.assert_called_once()
        self.assertTrue(result)
