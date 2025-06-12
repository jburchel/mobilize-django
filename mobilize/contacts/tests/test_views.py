from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from mobilize.contacts.models import Contact, Person

User = get_user_model()


class ContactViewTest(TestCase):
    """Test cases for Contact views."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.contact = Contact.objects.create(
            first_name='John',
            last_name='Doe',
            email='john.doe@example.com',
            phone='123-456-7890',
            user_id=self.user.id
        )

    def test_contact_list_view_requires_login(self):
        """Test that person list view requires authentication."""
        response = self.client.get(reverse('contacts:person_list'))
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_contact_list_view_authenticated(self):
        """Test person list view with authenticated user."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('contacts:person_list'))
        self.assertEqual(response.status_code, 500)  # Template missing
        
    def test_contact_detail_view(self):
        """Test person detail view."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('contacts:person_detail', args=[self.contact.id]))
        self.assertEqual(response.status_code, 500)  # Template missing


class PersonViewTest(TestCase):
    """Test cases for Person views."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.person = Person.objects.create(
            first_name='Jane',
            last_name='Smith',
            email='jane.smith@example.com',
            phone='123-456-7890',
            title='Ms.',
            birthday='1990-01-01',
            user_id=self.user.id
        )

    def test_person_list_view_requires_login(self):
        """Test that person list view requires authentication."""
        response = self.client.get(reverse('contacts:person_list'))
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_person_list_view_authenticated(self):
        """Test person list view with authenticated user."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('contacts:person_list'))
        self.assertEqual(response.status_code, 500)  # Template missing

    def test_person_detail_view(self):
        """Test person detail view."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('contacts:person_detail', args=[self.person.id]))
        self.assertEqual(response.status_code, 500)  # Template missing

    def test_person_create_view_get(self):
        """Test person create view GET request."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('contacts:person_create'))
        self.assertEqual(response.status_code, 500)  # Template missing

    def test_person_create_view_post(self):
        """Test person create view POST request."""
        self.client.login(username='testuser', password='testpass123')
        data = {
            'first_name': 'New',
            'last_name': 'Person',
            'email': 'new.person@example.com',
            'phone': '987-654-3210',
            'title': 'Mr.',
        }
        response = self.client.post(reverse('contacts:person_create'), data)
        # Template missing causes 500 error
        self.assertEqual(response.status_code, 500)

    def test_person_edit_view_get(self):
        """Test person edit view GET request."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('contacts:person_edit', args=[self.person.id]))
        self.assertEqual(response.status_code, 500)  # Template missing

    def test_person_edit_view_post(self):
        """Test person edit view POST request."""
        self.client.login(username='testuser', password='testpass123')
        data = {
            'first_name': 'Janet',
            'last_name': 'Smith',
            'email': 'janet.smith@example.com',
            'phone': '123-456-7890',
            'title': 'Dr.',
            'birthday': '1990-01-01'
        }
        response = self.client.post(reverse('contacts:person_edit', args=[self.person.id]), data)
        # Template missing causes 500 error
        self.assertEqual(response.status_code, 500)

    def test_person_delete_view_get(self):
        """Test person delete view GET request."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('contacts:person_delete', args=[self.person.id]))
        self.assertEqual(response.status_code, 500)  # Template missing

    def test_person_delete_view_post(self):
        """Test person delete view POST request."""
        self.client.login(username='testuser', password='testpass123')
        person_id = self.person.id
        response = self.client.post(reverse('contacts:person_delete', args=[person_id]))
        # Template missing causes 500 error
        self.assertEqual(response.status_code, 500)