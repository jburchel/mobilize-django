from django.test import TestCase
from mobilize.contacts.models import Contact
from mobilize.utils.supabase_mapper import SupabaseMapper


class ContactModelTest(TestCase):
    """Test cases for the Contact model and its compatibility with SupabaseMapper."""

    def setUp(self):
        """Set up test data."""
        self.contact_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john.doe@example.com',
            'phone': '123-456-7890',
            'street_address': '123 Main St',
            'city': 'Anytown',
            'state': 'CA',
            'zip_code': '12345',
            'country': 'USA',
            'user_id': 1,  # Integer in Contact model
            'notes': 'Test notes',
            'type': 'Person',  # Contact has 'type' field, not 'status'
        }
        
        self.contact = Contact.objects.create(**self.contact_data)
        
        # Supabase representation (with field name differences)
        self.supabase_data = {
            'id': self.contact.id,
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john.doe@example.com',
            'phone': '123-456-7890',
            'street_address': '123 Main St',
            'city': 'Anytown',
            'state': 'CA',
            'zip_code': '12345',
            'country': 'USA',
            'user_id': 1,  # Integer in contacts table
            'notes': 'Test notes',
            'type': 'Person',
            'created_at': '2025-06-05T12:00:00',
            'updated_at': '2025-06-05T12:00:00',
        }

    def test_contact_creation(self):
        """Test that a contact can be created with the expected fields."""
        self.assertEqual(self.contact.first_name, 'John')
        self.assertEqual(self.contact.last_name, 'Doe')
        self.assertEqual(self.contact.email, 'john.doe@example.com')
        self.assertEqual(self.contact.phone, '123-456-7890')
        self.assertEqual(self.contact.street_address, '123 Main St')
        self.assertEqual(self.contact.city, 'Anytown')
        self.assertEqual(self.contact.state, 'CA')
        self.assertEqual(self.contact.zip_code, '12345')
        self.assertEqual(self.contact.country, 'USA')
        self.assertEqual(self.contact.user_id, 1)
        self.assertEqual(self.contact.notes, 'Test notes')
        self.assertEqual(self.contact.type, 'Person')
    
    def test_contact_to_supabase_conversion(self):
        """Test converting a Contact model instance to Supabase format."""
        supabase_dict = SupabaseMapper.to_supabase(self.contact)
        
        # Check that key fields are correctly mapped
        self.assertEqual(supabase_dict['id'], self.contact.id)
        self.assertEqual(supabase_dict['first_name'], self.contact.first_name)
        self.assertEqual(supabase_dict['last_name'], self.contact.last_name)
        self.assertEqual(supabase_dict['email'], self.contact.email)
        self.assertEqual(supabase_dict['phone'], self.contact.phone)
        self.assertEqual(supabase_dict['street_address'], self.contact.street_address)
        self.assertEqual(supabase_dict['user_id'], self.contact.user_id)
        
    def test_contact_from_supabase_conversion(self):
        """Test converting Supabase data to Contact model format."""
        django_dict = SupabaseMapper.from_supabase(self.supabase_data, Contact)
        
        # Check that key fields are correctly mapped
        self.assertEqual(django_dict['id'], self.supabase_data['id'])
        self.assertEqual(django_dict['first_name'], self.supabase_data['first_name'])
        self.assertEqual(django_dict['last_name'], self.supabase_data['last_name'])
        self.assertEqual(django_dict['email'], self.supabase_data['email'])
        self.assertEqual(django_dict['phone'], self.supabase_data['phone'])
        self.assertEqual(django_dict['street_address'], self.supabase_data['street_address'])
        self.assertEqual(django_dict['user_id'], self.supabase_data['user_id'])
        
    def test_contact_create_from_supabase(self):
        """Test creating a new Contact instance from Supabase data."""
        # Delete the existing contact to avoid conflicts
        self.contact.delete()
        
        # Create a new contact from Supabase data
        new_contact = SupabaseMapper.create_from_supabase(self.supabase_data, Contact)
        
        # Check that the contact was created with the correct data
        self.assertEqual(new_contact.first_name, self.supabase_data['first_name'])
        self.assertEqual(new_contact.last_name, self.supabase_data['last_name'])
        self.assertEqual(new_contact.email, self.supabase_data['email'])
        self.assertEqual(new_contact.phone, self.supabase_data['phone'])
        self.assertEqual(new_contact.street_address, self.supabase_data['street_address'])
        self.assertEqual(new_contact.user_id, self.supabase_data['user_id'])
        
    def test_contact_update_from_supabase(self):
        """Test updating an existing Contact instance from Supabase data."""
        # Modify the Supabase data
        updated_data = self.supabase_data.copy()
        updated_data['first_name'] = 'Jane'
        updated_data['email'] = 'jane.doe@example.com'
        
        # Update the contact
        updated_contact = SupabaseMapper.update_from_supabase(self.contact, updated_data)
        
        # Check that the contact was updated with the correct data
        self.assertEqual(updated_contact.first_name, 'Jane')
        self.assertEqual(updated_contact.email, 'jane.doe@example.com')
        self.assertEqual(updated_contact.last_name, self.contact.last_name)  # Unchanged
        self.assertEqual(updated_contact.phone, self.contact.phone)  # Unchanged
