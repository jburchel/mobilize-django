"""
Tests for the SupabaseSync utility with actual Django models.

These tests verify that the SupabaseSync utility correctly handles
synchronization between our Django models (Contact, Person, Church) and Supabase.
"""

from unittest.mock import patch, MagicMock
from django.test import TestCase

from mobilize.contacts.models import Contact, Person
from mobilize.churches.models import Church
from mobilize.utils.supabase_sync import SupabaseSync


class SupabaseSyncModelsTestCase(TestCase):
    """Test cases for the SupabaseSync utility with actual models."""

    def setUp(self):
        """Set up test data."""
        # Test data for Contact
        self.contact_django_data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "phone": "123-456-7890",
            "type": "person",
            "user_id": 42,
            "office_id": 5,
        }

        self.contact_supabase_data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "phone": "123-456-7890",
            "type": "person",
            "user_id": "42",  # String in Supabase
            "office_id": "5",  # String in Supabase
        }

        # Test data for Person
        self.person_django_data = {
            "first_name": "Jane",
            "last_name": "Smith",
            "email": "jane.smith@example.com",
            "phone": "987-654-3210",
            "type": "person",
            "user_id": 43,
            "office_id": 5,
            "title": "Ms.",
            "birthday": "1990-01-01",
            "occupation": "Engineer",
            "church_role": "Member",
        }

        self.person_supabase_data = {
            "first_name": "Jane",
            "last_name": "Smith",
            "email": "jane.smith@example.com",
            "phone": "987-654-3210",
            "type": "person",
            "user_id": "43",
            "office_id": "5",
            "title": "Ms.",
            "birthday": "1990-01-01",
            "occupation": "Engineer",
            "church_role": "Member",
        }

        # Test data for Church
        self.church_django_data = {
            "church_name": "Community Church",
            "email": "info@communitychurch.org",
            "phone": "555-123-4567",
            "type": "church",
            "user_id": 44,
            "office_id": 5,
            "location": "Downtown",
            "denomination": "Non-denominational",
            "congregation_size": 500,
            "weekly_attendance": 350,
        }

        self.church_supabase_data = {
            "name": "Community Church",  # Different field name in Supabase
            "email": "info@communitychurch.org",
            "phone": "555-123-4567",
            "type": "church",
            "user_id": "44",
            "office_id": "5",
            "location": "Downtown",
            "denomination": "Non-denominational",
            "congregation_size": 500,
            "weekly_attendance": 350,
        }

    @patch("mobilize.utils.supabase_sync.SupabaseMapper.to_supabase")
    def test_sync_contact_to_supabase(self, mock_to_supabase):
        """Test synchronizing a Contact model instance to Supabase."""
        # Setup the mock
        mock_to_supabase.return_value = self.contact_supabase_data.copy()

        # Create a mock Contact instance
        contact = MagicMock(spec=Contact)
        for field, value in self.contact_django_data.items():
            setattr(contact, field, value)

        # Call the method
        result = SupabaseSync.sync_to_supabase(contact)

        # Verify the result
        self.assertIn("last_synced_at", result)
        self.assertEqual(result["first_name"], "John")
        self.assertEqual(result["last_name"], "Doe")
        self.assertEqual(result["user_id"], "42")

        # Verify the mock was called correctly
        mock_to_supabase.assert_called_once_with(contact)

    @patch("mobilize.utils.supabase_sync.SupabaseMapper.to_supabase")
    def test_sync_person_to_supabase(self, mock_to_supabase):
        """Test synchronizing a Person model instance to Supabase."""
        # Setup the mock
        mock_to_supabase.return_value = self.person_supabase_data.copy()

        # Create a mock Person instance
        person = MagicMock(spec=Person)
        for field, value in self.person_django_data.items():
            setattr(person, field, value)

        # Call the method
        result = SupabaseSync.sync_to_supabase(person)

        # Verify the result
        self.assertIn("last_synced_at", result)
        self.assertEqual(result["first_name"], "Jane")
        self.assertEqual(result["last_name"], "Smith")
        self.assertEqual(result["user_id"], "43")
        self.assertEqual(result["title"], "Ms.")
        self.assertEqual(result["occupation"], "Engineer")

        # Verify the mock was called correctly
        mock_to_supabase.assert_called_once_with(person)

    @patch("mobilize.utils.supabase_sync.SupabaseMapper.to_supabase")
    def test_sync_church_to_supabase(self, mock_to_supabase):
        """Test synchronizing a Church model instance to Supabase."""
        # Setup the mock
        mock_to_supabase.return_value = self.church_supabase_data.copy()

        # Create a mock Church instance
        church = MagicMock(spec=Church)
        for field, value in self.church_django_data.items():
            setattr(church, field, value)

        # Call the method
        result = SupabaseSync.sync_to_supabase(church)

        # Verify the result
        self.assertIn("last_synced_at", result)
        self.assertEqual(result["name"], "Community Church")  # Field name mapping
        self.assertEqual(result["email"], "info@communitychurch.org")
        self.assertEqual(result["user_id"], "44")
        self.assertEqual(result["location"], "Downtown")
        self.assertEqual(result["denomination"], "Non-denominational")

        # Verify the mock was called correctly
        mock_to_supabase.assert_called_once_with(church)

    @patch("mobilize.utils.supabase_sync.SupabaseMapper.from_supabase")
    def test_sync_contact_from_supabase(self, mock_from_supabase):
        """Test synchronizing a Contact from Supabase data."""
        # Setup the mock
        django_data = self.contact_django_data.copy()
        django_data["id"] = 1  # Add ID for existing record
        mock_from_supabase.return_value = django_data

        # Create a mock Contact instance
        contact = MagicMock(spec=Contact)
        for field, value in django_data.items():
            setattr(contact, field, value)

        # Mock the Contact.objects.get method
        Contact.objects.get = MagicMock(return_value=contact)

        # Add ID to Supabase data
        supabase_data = self.contact_supabase_data.copy()
        supabase_data["id"] = 1

        # Call the method
        with patch("django.db.transaction.atomic", return_value=MagicMock()):
            result = SupabaseSync.sync_from_supabase(supabase_data, Contact)

        # Verify the result
        self.assertEqual(result, contact)
        self.assertTrue(hasattr(result, "last_synced_at"))

        # Verify the mock was called correctly
        mock_from_supabase.assert_called_once_with(supabase_data, Contact)

    @patch("mobilize.utils.supabase_sync.SupabaseMapper.from_supabase")
    def test_sync_person_from_supabase(self, mock_from_supabase):
        """Test synchronizing a Person from Supabase data."""
        # Setup the mock
        django_data = self.person_django_data.copy()
        django_data["id"] = 2  # Add ID for existing record
        mock_from_supabase.return_value = django_data

        # Create a mock Person instance
        person = MagicMock(spec=Person)
        for field, value in django_data.items():
            setattr(person, field, value)

        # Mock the Person.objects.get method
        Person.objects.get = MagicMock(return_value=person)

        # Add ID to Supabase data
        supabase_data = self.person_supabase_data.copy()
        supabase_data["id"] = 2

        # Call the method
        with patch("django.db.transaction.atomic", return_value=MagicMock()):
            result = SupabaseSync.sync_from_supabase(supabase_data, Person)

        # Verify the result
        self.assertEqual(result, person)
        self.assertTrue(hasattr(result, "last_synced_at"))

        # Verify the mock was called correctly
        mock_from_supabase.assert_called_once_with(supabase_data, Person)

    @patch("mobilize.utils.supabase_sync.SupabaseMapper.from_supabase")
    def test_sync_church_from_supabase(self, mock_from_supabase):
        """Test synchronizing a Church from Supabase data."""
        # Setup the mock
        django_data = self.church_django_data.copy()
        django_data["id"] = 3  # Add ID for existing record
        mock_from_supabase.return_value = django_data

        # Create a mock Church instance
        church = MagicMock(spec=Church)
        for field, value in django_data.items():
            setattr(church, field, value)

        # Mock the Church.objects.get method
        Church.objects.get = MagicMock(return_value=church)

        # Add ID to Supabase data
        supabase_data = self.church_supabase_data.copy()
        supabase_data["id"] = 3

        # Call the method
        with patch("django.db.transaction.atomic", return_value=MagicMock()):
            result = SupabaseSync.sync_from_supabase(supabase_data, Church)

        # Verify the result
        self.assertEqual(result, church)
        self.assertTrue(hasattr(result, "last_synced_at"))

        # Verify the mock was called correctly
        mock_from_supabase.assert_called_once_with(supabase_data, Church)

    @patch("mobilize.utils.supabase_sync.SupabaseMapper.from_supabase")
    def test_detect_conflicts_church(self, mock_from_supabase):
        """Test detecting conflicts between a Church instance and Supabase data."""
        # Setup the mock
        django_data = self.church_django_data.copy()
        django_data["church_name"] = "Updated Church Name"  # Different from original
        mock_from_supabase.return_value = django_data

        # Create a mock Church instance with original data
        church = MagicMock(spec=Church)
        for field, value in self.church_django_data.items():
            setattr(church, field, value)

        # Create Supabase data with different values
        supabase_data = self.church_supabase_data.copy()
        supabase_data["name"] = "Updated Church Name"  # Different from original

        # Call the method
        conflicts = SupabaseSync.detect_conflicts(church, supabase_data)

        # Verify the result
        self.assertEqual(len(conflicts), 1)
        self.assertIn("church_name", conflicts)
        self.assertEqual(conflicts["church_name"]["django_value"], "Community Church")
        self.assertEqual(
            conflicts["church_name"]["supabase_value"], "Updated Church Name"
        )
