from django.test import TestCase
from django.contrib.auth import get_user_model
from mobilize.contacts.models import Contact, Person
from mobilize.contacts.forms import PersonForm

User = get_user_model()



class PersonFormTest(TestCase):
    """Test cases for PersonForm."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_person_form_valid_data(self):
        """Test PersonForm with valid data."""
        form_data = {
            'first_name': 'Jane',
            'last_name': 'Smith',
            'email': 'jane.smith@example.com',
            'phone': '123-456-7890',
            'title': 'Ms.',
            'birthday': '1990-01-01',
            'spouse_first_name': 'John',
            'spouse_last_name': 'Smith',
            'profession': 'Engineer',
            'organization': 'Tech Corp',
            'street_address': '456 Oak Ave',
            'city': 'Somewhere',
            'state': 'NY',
            'zip_code': '54321',
            'status': 'active',
        }
        form = PersonForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_person_form_empty_data(self):
        """Test PersonForm with empty data."""
        form = PersonForm(data={})
        # PersonForm should be valid even with empty data since most fields are optional
        self.assertTrue(form.is_valid())

    def test_person_form_save(self):
        """Test PersonForm save method."""
        form_data = {
            'first_name': 'Jane',
            'last_name': 'Smith',
            'email': 'jane.smith@example.com',
            'phone': '123-456-7890',
            'birthday': '1990-01-01',
            'status': 'active'
        }
        form = PersonForm(data=form_data)
        self.assertTrue(form.is_valid())
        
        person = form.save()
        # Access Contact fields through relationship
        self.assertEqual(person.contact.first_name, 'Jane')
        self.assertEqual(person.contact.last_name, 'Smith')
        self.assertEqual(person.contact.email, 'jane.smith@example.com')
        self.assertEqual(str(person.birthday), '1990-01-01')
        self.assertEqual(person.contact.status, 'active')

    def test_person_form_invalid_birthday(self):
        """Test PersonForm with invalid birthday format."""
        form_data = {
            'first_name': 'Jane',
            'last_name': 'Smith',
            'birthday': 'invalid-date',
        }
        form = PersonForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('birthday', form.errors)

    def test_person_form_update_existing(self):
        """Test PersonForm updating an existing person."""
        # Create Contact first, then Person
        contact_data = {
            'type': 'person',
            'first_name': 'Original',
            'last_name': 'Name',
            'email': 'original@example.com',
            'user': self.user,
        }
        contact = Contact.objects.create(**contact_data)
        person = Person.objects.create(contact=contact)
        
        # Update with form
        form_data = {
            'first_name': 'Updated',
            'last_name': 'Name',
            'email': 'updated@example.com',
        }
        form = PersonForm(data=form_data, instance=person)
        self.assertTrue(form.is_valid())
        
        updated_person = form.save()
        self.assertEqual(updated_person.contact_id, person.contact_id)  # Same instance
        self.assertEqual(updated_person.contact.first_name, 'Updated')
        self.assertEqual(updated_person.contact.email, 'updated@example.com')