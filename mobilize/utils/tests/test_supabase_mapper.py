"""
Tests for the Supabase Mapper utility.
"""

from django.test import TestCase
from mobilize.utils.supabase_mapper import SupabaseMapper


class SupabaseMapperTestCase(TestCase):
    """Test case for the SupabaseMapper utility."""

    def setUp(self):
        """Set up test data for testing."""
        # No setup needed as we're testing the actual field mappings
        pass

    def tearDown(self):
        """Clean up after tests."""
        # No cleanup needed
        pass

    def test_type_conversion_to_supabase(self):
        """Test type conversion when converting to Supabase format."""
        # Test Person.user_id and office_id conversion from int to string
        self.assertEqual(SupabaseMapper.TYPE_MAPPING['Person.user_id']['to_supabase'](5), '5')
        self.assertEqual(SupabaseMapper.TYPE_MAPPING['office_id']['to_supabase'](10), '10')
        
        # Test handling None values
        self.assertIsNone(SupabaseMapper.TYPE_MAPPING['Person.user_id']['to_supabase'](None))
        self.assertIsNone(SupabaseMapper.TYPE_MAPPING['office_id']['to_supabase'](None))

    def test_field_mapping_church(self):
        """Test field name mapping for Church model."""
        # Based on the actual implementation, Church has no field mappings
        # so the data should pass through unchanged
        supabase_data = {'name': 'Test Church', 'email': 'test@example.com'}
        django_data = SupabaseMapper.from_supabase(supabase_data, 'Church')
        
        # Verify fields pass through unchanged (no field mapping)
        self.assertEqual(django_data['name'], 'Test Church')
        self.assertEqual(django_data['email'], 'test@example.com')

    def test_type_conversion_from_supabase(self):
        """Test type conversion when converting from Supabase format."""
        # Test Person.user_id and office_id conversion from string to int
        self.assertEqual(SupabaseMapper.TYPE_MAPPING['Person.user_id']['from_supabase']('5'), 5)
        self.assertEqual(SupabaseMapper.TYPE_MAPPING['office_id']['from_supabase']('10'), 10)
        
        # Test handling None values
        self.assertIsNone(SupabaseMapper.TYPE_MAPPING['Person.user_id']['from_supabase'](None))
        self.assertIsNone(SupabaseMapper.TYPE_MAPPING['office_id']['from_supabase'](None))
        
        # Test handling empty string values
        self.assertIsNone(SupabaseMapper.TYPE_MAPPING['Person.user_id']['from_supabase'](''))
        self.assertIsNone(SupabaseMapper.TYPE_MAPPING['office_id']['from_supabase'](''))

    def test_from_supabase_contact(self):
        """Test converting Supabase data to Contact format."""
        supabase_data = {
            'first_name': 'Alice',
            'last_name': 'Johnson',
            'email': 'alice.johnson@example.com',
            'phone': '111-222-3333',
            'office_id': '4'
        }
        
        django_data = SupabaseMapper.from_supabase(supabase_data, 'Contact')
        
        # Check field values
        self.assertEqual(django_data['first_name'], 'Alice')
        self.assertEqual(django_data['last_name'], 'Johnson')
        self.assertEqual(django_data['email'], 'alice.johnson@example.com')
        self.assertEqual(django_data['phone'], '111-222-3333')
        
        # Check type conversions
        self.assertEqual(django_data['office_id'], 4)

    def test_from_supabase_church(self):
        """Test converting Supabase data to Church format."""
        supabase_data = {
            'name': 'Community Church',
            'email': 'community@example.com',
            'location': 'Downtown',
            'office_id': '6'
        }
        
        django_data = SupabaseMapper.from_supabase(supabase_data, 'Church')
        
        # Check fields pass through unchanged (no field mapping for Church)
        self.assertEqual(django_data['name'], 'Community Church')
        self.assertEqual(django_data['email'], 'community@example.com')
        self.assertEqual(django_data['location'], 'Downtown')
        
        # Check type conversions
        self.assertEqual(django_data['office_id'], 6)

    def test_bulk_to_supabase(self):
        """Test bulk conversion to Supabase format."""
        # Create test data with office_id which has a type mapping
        django_data = [
            {'first_name': 'Bob', 'last_name': 'Brown', 'office_id': 7},
            {'first_name': 'Alice', 'last_name': 'Smith', 'office_id': 8}
        ]
        
        # Test the bulk_to_supabase method
        supabase_data = SupabaseMapper.bulk_to_supabase(django_data)
        
        # Check the results
        self.assertEqual(len(supabase_data), 2)
        self.assertEqual(supabase_data[0]['first_name'], 'Bob')
        self.assertEqual(supabase_data[0]['office_id'], '7')
        self.assertEqual(supabase_data[1]['first_name'], 'Alice')
        self.assertEqual(supabase_data[1]['office_id'], '8')

    def test_bulk_from_supabase(self):
        """Test bulk conversion from Supabase format."""
        # Create test data with office_id which has a type mapping
        supabase_data = [
            {'first_name': 'Bob', 'last_name': 'Brown', 'office_id': '7'},
            {'first_name': 'Alice', 'last_name': 'Smith', 'office_id': '8'}
        ]
        
        # Test the bulk_from_supabase method
        django_data = SupabaseMapper.bulk_from_supabase(supabase_data, 'Contact')
        
        # Check the results
        self.assertEqual(len(django_data), 2)
        self.assertEqual(django_data[0]['first_name'], 'Bob')
        self.assertEqual(django_data[0]['office_id'], 7)
        self.assertEqual(django_data[1]['first_name'], 'Alice')
        self.assertEqual(django_data[1]['office_id'], 8)
