"""
Tests for the Supabase Mapper utility.
"""

from django.test import TestCase
from mobilize.utils.supabase_mapper import SupabaseMapper


class SupabaseMapperTestCase(TestCase):
    """Test case for the SupabaseMapper utility."""

    def setUp(self):
        """Set up test data and field mappings for testing."""
        # Store the original field mapping to restore later
        self.original_field_mapping = SupabaseMapper.FIELD_MAPPING.copy()
        
        # Define test field mappings
        SupabaseMapper.FIELD_MAPPING = {
            'Contact': {},
            'Church': {'church_name': 'name'},
            'Person': {}
        }

    def tearDown(self):
        """Restore original field mappings after tests."""
        SupabaseMapper.FIELD_MAPPING = self.original_field_mapping

    def test_type_conversion_to_supabase(self):
        """Test type conversion when converting to Supabase format."""
        # Test user_id and office_id conversion from int to string
        self.assertEqual(SupabaseMapper.TYPE_MAPPING['user_id']['to_supabase'](5), '5')
        self.assertEqual(SupabaseMapper.TYPE_MAPPING['office_id']['to_supabase'](10), '10')
        
        # Test handling None values
        self.assertIsNone(SupabaseMapper.TYPE_MAPPING['user_id']['to_supabase'](None))
        self.assertIsNone(SupabaseMapper.TYPE_MAPPING['office_id']['to_supabase'](None))

    def test_field_mapping_church(self):
        """Test field name mapping for Church model."""
        # Test that church_name maps to name
        self.assertEqual(SupabaseMapper.FIELD_MAPPING['Church'].get('church_name'), 'name')
        
        # Test that the reverse mapping works in from_supabase
        supabase_data = {'name': 'Test Church', 'email': 'test@example.com'}
        django_data = SupabaseMapper.from_supabase(supabase_data, 'Church')
        
        # Verify field mapping worked
        self.assertEqual(django_data['church_name'], 'Test Church')
        self.assertNotIn('name', django_data)

    def test_type_conversion_from_supabase(self):
        """Test type conversion when converting from Supabase format."""
        # Test user_id and office_id conversion from string to int
        self.assertEqual(SupabaseMapper.TYPE_MAPPING['user_id']['from_supabase']('5'), 5)
        self.assertEqual(SupabaseMapper.TYPE_MAPPING['office_id']['from_supabase']('10'), 10)
        
        # Test handling None values
        self.assertIsNone(SupabaseMapper.TYPE_MAPPING['user_id']['from_supabase'](None))
        self.assertIsNone(SupabaseMapper.TYPE_MAPPING['office_id']['from_supabase'](None))
        
        # Test handling empty string values
        self.assertIsNone(SupabaseMapper.TYPE_MAPPING['user_id']['from_supabase'](''))
        self.assertIsNone(SupabaseMapper.TYPE_MAPPING['office_id']['from_supabase'](''))

    def test_from_supabase_contact(self):
        """Test converting Supabase data to Contact format."""
        supabase_data = {
            'first_name': 'Alice',
            'last_name': 'Johnson',
            'email': 'alice.johnson@example.com',
            'phone': '111-222-3333',
            'user_id': '3',
            'office_id': '4'
        }
        
        django_data = SupabaseMapper.from_supabase(supabase_data, 'Contact')
        
        # Check field values
        self.assertEqual(django_data['first_name'], 'Alice')
        self.assertEqual(django_data['last_name'], 'Johnson')
        self.assertEqual(django_data['email'], 'alice.johnson@example.com')
        
        # Check type conversions
        self.assertEqual(django_data['user_id'], 3)
        self.assertEqual(django_data['office_id'], 4)

    def test_from_supabase_church(self):
        """Test converting Supabase data to Church format."""
        supabase_data = {
            'name': 'Community Church',
            'email': 'community@example.com',
            'location': 'Downtown',
            'user_id': '5',
            'office_id': '6'
        }
        
        django_data = SupabaseMapper.from_supabase(supabase_data, 'Church')
        
        # Check field name mapping
        self.assertEqual(django_data['church_name'], 'Community Church')
        self.assertNotIn('name', django_data)
        
        # Check other fields
        self.assertEqual(django_data['email'], 'community@example.com')
        self.assertEqual(django_data['location'], 'Downtown')
        
        # Check type conversions
        self.assertEqual(django_data['user_id'], 5)
        self.assertEqual(django_data['office_id'], 6)

    def test_bulk_to_supabase(self):
        """Test bulk conversion to Supabase format."""
        # Create test data
        django_data = [
            {'first_name': 'Bob', 'last_name': 'Brown', 'user_id': 7},
            {'first_name': 'Alice', 'last_name': 'Smith', 'user_id': 8}
        ]
        
        # Test the bulk_to_supabase method
        supabase_data = SupabaseMapper.bulk_to_supabase(django_data)
        
        # Check the results
        self.assertEqual(len(supabase_data), 2)
        self.assertEqual(supabase_data[0]['first_name'], 'Bob')
        self.assertEqual(supabase_data[0]['user_id'], '7')
        self.assertEqual(supabase_data[1]['first_name'], 'Alice')
        self.assertEqual(supabase_data[1]['user_id'], '8')

    def test_bulk_from_supabase(self):
        """Test bulk conversion from Supabase format."""
        # Create test data
        supabase_data = [
            {'first_name': 'Bob', 'last_name': 'Brown', 'user_id': '7'},
            {'first_name': 'Alice', 'last_name': 'Smith', 'user_id': '8'}
        ]
        
        # Test the bulk_from_supabase method
        django_data = SupabaseMapper.bulk_from_supabase(supabase_data, 'Contact')
        
        # Check the results
        self.assertEqual(len(django_data), 2)
        self.assertEqual(django_data[0]['first_name'], 'Bob')
        self.assertEqual(django_data[0]['user_id'], 7)
        self.assertEqual(django_data[1]['first_name'], 'Alice')
        self.assertEqual(django_data[1]['user_id'], 8)
