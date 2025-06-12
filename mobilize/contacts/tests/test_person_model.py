from django.test import TestCase
from mobilize.contacts.models import Person
from mobilize.utils.supabase_mapper import SupabaseMapper


class PersonModelTest(TestCase):
    """Test cases for the Person model and its compatibility with SupabaseMapper."""

    def setUp(self):
        """Set up test data."""
        self.person_data = {
            'first_name': 'Jane',
            'last_name': 'Smith',
            'email': 'jane.smith@example.com',
            'phone': '123-456-7890',
            'street_address': '123 Main St',
            'city': 'Anytown',
            'state': 'CA',
            'zip_code': '12345',
            'country': 'USA',
            'user_id': 1,  # This is inherited from Contact (integer)
            'notes': 'Test notes',
            'status': 'Active',
            'title': 'Ms.',
            'birthday': '1990-01-01',
            'spouse_first_name': 'John',
            'spouse_last_name': 'Smith',
            'facebook': 'janesmith',
            'twitter': '@janesmith',
            'linkedin': 'jane-smith',
            'instagram': 'janesmith',
            'assigned_to': 'Manager',
            'source': 'Referral',
        }
        
        self.person = Person.objects.create(**self.person_data)
        
        # Supabase representation (with field name differences)
        # Note: In Supabase, people.user_id is character varying while Contact.user_id is integer
        self.supabase_data = {
            'id': self.person.id,
            'first_name': 'Jane',
            'last_name': 'Smith',
            'email': 'jane.smith@example.com',
            'phone': '123-456-7890',
            'street_address': '123 Main St',
            'city': 'Anytown',
            'state': 'CA',
            'zip_code': '12345',
            'country': 'USA',
            'user_id': '1',  # String in people table
            'notes': 'Test notes',
            'status': 'Active',
            'title': 'Ms.',
            'birthday': '1990-01-01',
            'spouse_first_name': 'John',
            'spouse_last_name': 'Smith',
            'facebook': 'janesmith',
            'twitter': '@janesmith',
            'linkedin': 'jane-smith',
            'instagram': 'janesmith',
            'assigned_to': 'Manager',
            'source': 'Referral',
            'created_at': '2025-06-05',
            'updated_at': '2025-06-05',
        }

    def test_person_creation(self):
        """Test that a person can be created with the expected fields."""
        self.assertEqual(self.person.first_name, 'Jane')
        self.assertEqual(self.person.last_name, 'Smith')
        self.assertEqual(self.person.email, 'jane.smith@example.com')
        self.assertEqual(self.person.phone, '123-456-7890')
        self.assertEqual(self.person.title, 'Ms.')
        self.assertEqual(str(self.person.birthday), '1990-01-01')
        self.assertEqual(self.person.spouse_first_name, 'John')
        self.assertEqual(self.person.spouse_last_name, 'Smith')
        self.assertEqual(self.person.facebook, 'janesmith')
        self.assertEqual(self.person.twitter, '@janesmith')
        self.assertEqual(self.person.linkedin, 'jane-smith')
        self.assertEqual(self.person.instagram, 'janesmith')
        self.assertEqual(self.person.assigned_to, 'Manager')
        self.assertEqual(self.person.source, 'Referral')
    
    def test_person_to_supabase_conversion(self):
        """Test converting a Person model instance to Supabase format."""
        supabase_dict = SupabaseMapper.to_supabase(self.person)
        
        # Check that key fields are correctly mapped
        self.assertEqual(supabase_dict['id'], self.person.id)
        self.assertEqual(supabase_dict['first_name'], self.person.first_name)
        self.assertEqual(supabase_dict['last_name'], self.person.last_name)
        self.assertEqual(supabase_dict['email'], self.person.email)
        self.assertEqual(supabase_dict['phone'], self.person.phone)
        self.assertEqual(supabase_dict['title'], self.person.title)
        
        # Check that user_id is converted to string for Supabase
        self.assertEqual(supabase_dict['user_id'], str(self.person.user_id))
        self.assertIsInstance(supabase_dict['user_id'], str)
        
    def test_person_from_supabase_conversion(self):
        """Test converting Supabase data to Person model format."""
        django_dict = SupabaseMapper.from_supabase(self.supabase_data, Person)
        
        # Check that key fields are correctly mapped
        self.assertEqual(django_dict['id'], self.supabase_data['id'])
        self.assertEqual(django_dict['first_name'], self.supabase_data['first_name'])
        self.assertEqual(django_dict['last_name'], self.supabase_data['last_name'])
        self.assertEqual(django_dict['email'], self.supabase_data['email'])
        self.assertEqual(django_dict['phone'], self.supabase_data['phone'])
        self.assertEqual(django_dict['title'], self.supabase_data['title'])
        
        # Check that user_id is converted to integer for Django
        self.assertEqual(django_dict['user_id'], int(self.supabase_data['user_id']))
        self.assertIsInstance(django_dict['user_id'], int)
        
    def test_person_create_from_supabase(self):
        """Test creating a new Person instance from Supabase data."""
        # Delete the existing person to avoid conflicts
        self.person.delete()
        
        # Create a new person from Supabase data
        new_person = SupabaseMapper.create_from_supabase(self.supabase_data, Person)
        
        # Check that the person was created with the correct data
        self.assertEqual(new_person.first_name, self.supabase_data['first_name'])
        self.assertEqual(new_person.last_name, self.supabase_data['last_name'])
        self.assertEqual(new_person.email, self.supabase_data['email'])
        self.assertEqual(new_person.phone, self.supabase_data['phone'])
        self.assertEqual(new_person.title, self.supabase_data['title'])
        
        # Check that user_id was converted correctly
        self.assertEqual(new_person.user_id, int(self.supabase_data['user_id']))
        
    def test_person_update_from_supabase(self):
        """Test updating an existing Person instance from Supabase data."""
        # Modify the Supabase data
        updated_data = self.supabase_data.copy()
        updated_data['first_name'] = 'Janet'
        updated_data['title'] = 'Dr.'
        updated_data['user_id'] = '2'  # String in Supabase
        
        # Update the person
        updated_person = SupabaseMapper.update_from_supabase(self.person, updated_data)
        
        # Check that the person was updated with the correct data
        self.assertEqual(updated_person.first_name, 'Janet')
        self.assertEqual(updated_person.title, 'Dr.')
        self.assertEqual(updated_person.last_name, self.person.last_name)  # Unchanged
        
        # Check that user_id was converted correctly
        self.assertEqual(updated_person.user_id, 2)  # Integer in Django
