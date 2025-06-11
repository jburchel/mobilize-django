"""
Tests for the SupabaseSync utility.

These tests verify that the SupabaseSync utility correctly handles
synchronization between Django models and Supabase.
"""

from unittest.mock import patch, MagicMock
from django.test import TestCase

from mobilize.utils.supabase_sync import SupabaseSync


class SupabaseSyncTestCase(TestCase):
    """Test cases for the SupabaseSync utility."""

    def setUp(self):
        """Set up test data."""
        # Test data for Django format
        self.django_data = {
            'id': 1,
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john.doe@example.com',
            'phone': '123-456-7890',
            'user_id': 42,
            'office_id': 5,
            'has_conflict': False
        }
        
        # Test data for Supabase format
        self.supabase_data = {
            'id': 1,
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john.doe@example.com',
            'phone': '123-456-7890',
            'user_id': '42',  # String in Supabase
            'office_id': '5',  # String in Supabase
            'has_conflict': False
        }
        
        # Mock model class
        self.mock_model = MagicMock()
        self.mock_model.__name__ = 'Contact'
        
        # Mock model instance
        self.mock_instance = MagicMock()
        self.mock_instance.__class__ = self.mock_model
        for field, value in self.django_data.items():
            setattr(self.mock_instance, field, value)

    @patch('mobilize.utils.supabase_sync.SupabaseMapper.to_supabase')
    def test_sync_to_supabase(self, mock_to_supabase):
        """Test synchronizing a Django model instance to Supabase."""
        # Setup the mock
        mock_to_supabase.return_value = self.supabase_data.copy()
        
        # Call the method
        result = SupabaseSync.sync_to_supabase(self.mock_instance)
        
        # Verify the result
        self.assertIn('last_synced_at', result)
        self.assertEqual(result['first_name'], 'John')
        self.assertEqual(result['last_name'], 'Doe')
        self.assertEqual(result['user_id'], '42')
        
        # Verify the mock was called correctly
        mock_to_supabase.assert_called_once_with(self.mock_instance)

    @patch('mobilize.utils.supabase_sync.SupabaseMapper.from_supabase')
    def test_sync_from_supabase_create(self, mock_from_supabase):
        """Test creating a Django model instance from Supabase data."""
        # Setup the mock
        mock_from_supabase.return_value = self.django_data.copy()
        
        # Create a proper DoesNotExist exception
        self.mock_model.DoesNotExist = type('DoesNotExist', (Exception,), {})
        
        # Mock the model's objects manager
        self.mock_model.objects.get.side_effect = self.mock_model.DoesNotExist()
        self.mock_model.objects.create.return_value = self.mock_instance
        
        # Call the method
        result = SupabaseSync.sync_from_supabase(self.supabase_data, self.mock_model)
        
        # Verify the result
        self.assertEqual(result, self.mock_instance)
        
        # Verify the mock was called correctly
        mock_from_supabase.assert_called_once_with(self.supabase_data, self.mock_model)
        self.mock_model.objects.create.assert_called_once()

    @patch('mobilize.utils.supabase_sync.SupabaseMapper.from_supabase')
    def test_sync_from_supabase_update(self, mock_from_supabase):
        """Test updating a Django model instance from Supabase data."""
        # Setup the mock
        mock_from_supabase.return_value = self.django_data.copy()
        
        # Mock the model's objects manager
        self.mock_model.objects.get.return_value = self.mock_instance
        
        # Call the method
        result = SupabaseSync.sync_from_supabase(self.supabase_data, self.mock_model)
        
        # Verify the result
        self.assertEqual(result, self.mock_instance)
        
        # Verify the mock was called correctly
        mock_from_supabase.assert_called_once_with(self.supabase_data, self.mock_model)
        self.mock_instance.save.assert_called_once()

    @patch('mobilize.utils.supabase_sync.SupabaseSync.sync_to_supabase')
    def test_bulk_sync_to_supabase(self, mock_sync_to_supabase):
        """Test bulk synchronizing Django model instances to Supabase."""
        # Setup the mock
        mock_sync_to_supabase.return_value = self.supabase_data.copy()
        
        # Create a list of mock instances
        instances = [self.mock_instance, self.mock_instance]
        
        # Call the method
        result = SupabaseSync.bulk_sync_to_supabase(instances)
        
        # Verify the result
        self.assertEqual(len(result), 2)
        
        # Verify the mock was called correctly
        self.assertEqual(mock_sync_to_supabase.call_count, 2)

    @patch('mobilize.utils.supabase_sync.SupabaseSync.sync_from_supabase')
    def test_bulk_sync_from_supabase(self, mock_sync_from_supabase):
        """Test bulk synchronizing data from Supabase to Django models."""
        # Setup the mock
        mock_sync_from_supabase.return_value = self.mock_instance
        
        # Create a list of Supabase data
        supabase_data_list = [self.supabase_data, self.supabase_data]
        
        # Call the method
        result = SupabaseSync.bulk_sync_from_supabase(supabase_data_list, self.mock_model)
        
        # Verify the result
        self.assertEqual(len(result), 2)
        
        # Verify the mock was called correctly
        self.assertEqual(mock_sync_from_supabase.call_count, 2)

    @patch('mobilize.utils.supabase_sync.SupabaseMapper.to_supabase')
    @patch('mobilize.utils.supabase_sync.SupabaseMapper.from_supabase')
    def test_detect_conflicts(self, mock_from_supabase, mock_to_supabase):
        """Test detecting conflicts between Django and Supabase data."""
        # Setup the mocks
        mock_to_supabase.return_value = self.supabase_data.copy()
        
        # Create conflicting data
        conflicting_data = self.supabase_data.copy()
        conflicting_data['first_name'] = 'Jane'
        conflicting_data['email'] = 'jane.doe@example.com'
        
        django_conflicting_data = self.django_data.copy()
        django_conflicting_data['first_name'] = 'Jane'
        django_conflicting_data['email'] = 'jane.doe@example.com'
        
        mock_from_supabase.return_value = django_conflicting_data
        
        # Call the method
        conflicts = SupabaseSync.detect_conflicts(self.mock_instance, conflicting_data)
        
        # Verify the result
        self.assertEqual(len(conflicts), 2)
        self.assertIn('first_name', conflicts)
        self.assertIn('email', conflicts)
        self.assertEqual(conflicts['first_name']['django_value'], 'John')
        self.assertEqual(conflicts['first_name']['supabase_value'], 'Jane')

    def test_resolve_conflicts_django_strategy(self):
        """Test resolving conflicts using the Django strategy."""
        # Create conflict data
        conflicts = {
            'first_name': {
                'django_value': 'John',
                'supabase_value': 'Jane'
            },
            'email': {
                'django_value': 'john.doe@example.com',
                'supabase_value': 'jane.doe@example.com'
            }
        }
        
        # Set conflict flags on the instance
        self.mock_instance.has_conflict = True
        self.mock_instance.conflict_data = conflicts
        
        # Call the method
        result = SupabaseSync.resolve_conflicts(self.mock_instance, conflicts, 'django')
        
        # Verify the result
        self.assertEqual(result, self.mock_instance)
        self.assertFalse(result.has_conflict)
        self.assertIsNone(result.conflict_data)
        
        # Verify the Django values were kept
        self.assertEqual(result.first_name, 'John')
        self.assertEqual(result.email, 'john.doe@example.com')
        
        # Verify the instance was saved
        self.mock_instance.save.assert_called_once()

    def test_resolve_conflicts_supabase_strategy(self):
        """Test resolving conflicts using the Supabase strategy."""
        # Create conflict data
        conflicts = {
            'first_name': {
                'django_value': 'John',
                'supabase_value': 'Jane'
            },
            'email': {
                'django_value': 'john.doe@example.com',
                'supabase_value': 'jane.doe@example.com'
            }
        }
        
        # Set conflict flags on the instance
        self.mock_instance.has_conflict = True
        self.mock_instance.conflict_data = conflicts
        
        # Call the method
        result = SupabaseSync.resolve_conflicts(self.mock_instance, conflicts, 'supabase')
        
        # Verify the result
        self.assertEqual(result, self.mock_instance)
        self.assertFalse(result.has_conflict)
        self.assertIsNone(result.conflict_data)
        
        # Verify the Supabase values were used
        self.assertEqual(result.first_name, 'Jane')
        self.assertEqual(result.email, 'jane.doe@example.com')
        
        # Verify the instance was saved
        self.mock_instance.save.assert_called_once()
