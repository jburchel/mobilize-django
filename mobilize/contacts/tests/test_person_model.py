from django.test import TestCase
from django.contrib.auth import get_user_model
from mobilize.contacts.models import Person, Contact
from mobilize.utils.supabase_mapper import SupabaseMapper

User = get_user_model()


class PersonModelTest(TestCase):
    """Test cases for the Person model and its compatibility with SupabaseMapper."""

    def setUp(self):
        """Set up test data."""
        # Create a test user first
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )

        # Create Contact data (what goes on the Contact model)
        self.contact_data = {
            "type": "person",
            "first_name": "Jane",
            "last_name": "Smith",
            "email": "jane.smith@example.com",
            "phone": "123-456-7890",
            "street_address": "123 Main St",
            "city": "Anytown",
            "state": "CA",
            "zip_code": "12345",
            "country": "USA",
            "user": self.user,
            "notes": "Test notes",
            "status": "active",
        }

        # Create Person-specific data
        self.person_data = {
            "title": "Ms.",
            "birthday": "1990-01-01",
            "spouse_first_name": "John",
            "spouse_last_name": "Smith",
            "facebook_url": "https://facebook.com/janesmith",
            "twitter_url": "https://twitter.com/janesmith",
            "linkedin_url": "https://linkedin.com/in/jane-smith",
            "instagram_url": "https://instagram.com/janesmith",
        }

        # Create Contact first, then Person
        self.contact = Contact.objects.create(**self.contact_data)
        self.person = Person.objects.create(contact=self.contact, **self.person_data)

        # Supabase representation (with field name differences)
        # Note: In Supabase, people.user_id is character varying while Contact.user_id is integer
        self.supabase_data = {
            "id": self.person.contact.id,
            "first_name": "Jane",
            "last_name": "Smith",
            "email": "jane.smith@example.com",
            "phone": "123-456-7890",
            "street_address": "123 Main St",
            "city": "Anytown",
            "state": "CA",
            "zip_code": "12345",
            "country": "USA",
            "user_id": "1",  # String in people table
            "notes": "Test notes",
            "status": "Active",
            "title": "Ms.",
            "birthday": "1990-01-01",
            "spouse_first_name": "John",
            "spouse_last_name": "Smith",
            "facebook": "janesmith",
            "twitter": "@janesmith",
            "linkedin": "jane-smith",
            "instagram": "janesmith",
            "assigned_to": "Manager",
            "source": "Referral",
            "created_at": "2025-06-05",
            "updated_at": "2025-06-05",
        }

    def test_person_creation(self):
        """Test that a person can be created with the expected fields."""
        # Test Contact fields (accessed through relationship)
        self.assertEqual(self.person.contact.first_name, "Jane")
        self.assertEqual(self.person.contact.last_name, "Smith")
        self.assertEqual(self.person.contact.email, "jane.smith@example.com")
        self.assertEqual(self.person.contact.phone, "123-456-7890")
        self.assertEqual(self.person.contact.type, "person")

        # Test Person-specific fields
        self.assertEqual(self.person.title, "Ms.")
        self.assertEqual(str(self.person.birthday), "1990-01-01")
        self.assertEqual(self.person.spouse_first_name, "John")
        self.assertEqual(self.person.spouse_last_name, "Smith")
        self.assertEqual(self.person.facebook_url, "https://facebook.com/janesmith")
        self.assertEqual(self.person.twitter_url, "https://twitter.com/janesmith")
        self.assertEqual(self.person.linkedin_url, "https://linkedin.com/in/jane-smith")
        self.assertEqual(self.person.instagram_url, "https://instagram.com/janesmith")

        # Test the name property
        self.assertEqual(self.person.name, "Jane Smith")

    def test_person_to_supabase_conversion(self):
        """Test converting a Person model instance to Supabase format."""
        supabase_dict = SupabaseMapper.to_supabase(self.person)

        # Check that key fields are correctly mapped
        self.assertEqual(supabase_dict["contact_id"], self.person.contact_id)
        self.assertEqual(supabase_dict["title"], self.person.title)

        # Note: Person model no longer has direct access to Contact fields
        # Contact fields would need to be accessed through self.person.contact
        # This test validates that Person-specific fields are converted correctly

    def test_person_from_supabase_conversion(self):
        """Test converting Supabase data to Person model format."""
        django_dict = SupabaseMapper.from_supabase(self.supabase_data, Person)

        # Check that Person-specific fields are correctly mapped
        # Note: Person model now only contains person-specific fields
        # Contact fields are handled separately through the Contact model
        self.assertEqual(django_dict["title"], self.supabase_data["title"])
        self.assertEqual(django_dict["birthday"], self.supabase_data["birthday"])
        self.assertEqual(
            django_dict["spouse_first_name"], self.supabase_data["spouse_first_name"]
        )
        self.assertEqual(
            django_dict["spouse_last_name"], self.supabase_data["spouse_last_name"]
        )

    def test_person_create_from_supabase(self):
        """Test creating a new Person instance from Supabase data."""
        # Delete the existing person to avoid conflicts
        self.person.delete()

        # Create a Contact first since Person requires a contact_id
        new_contact = Contact.objects.create(
            type="person",
            first_name=self.supabase_data["first_name"],
            last_name=self.supabase_data["last_name"],
            email="new.person@example.com",  # Use different email to avoid unique constraint
            user=self.user,
        )

        # Create Person-specific data for SupabaseMapper
        person_data = {
            "contact_id": new_contact.id,
            "title": self.supabase_data["title"],
            "birthday": self.supabase_data["birthday"],
            "spouse_first_name": self.supabase_data["spouse_first_name"],
            "spouse_last_name": self.supabase_data["spouse_last_name"],
        }

        # Create a new person from Person-specific Supabase data
        new_person = SupabaseMapper.create_from_supabase(person_data, Person)

        # Check that the person was created with the correct data
        self.assertEqual(
            new_person.contact.first_name, self.supabase_data["first_name"]
        )
        self.assertEqual(new_person.contact.last_name, self.supabase_data["last_name"])
        self.assertEqual(new_person.title, self.supabase_data["title"])

    def test_person_update_from_supabase(self):
        """Test updating an existing Person instance from Supabase data."""
        # Create Person-specific update data
        updated_data = {
            "title": "Dr.",
            "spouse_first_name": "Janet",
        }

        # Update the person
        updated_person = SupabaseMapper.update_from_supabase(self.person, updated_data)

        # Check that the person was updated with the correct data
        self.assertEqual(updated_person.title, "Dr.")
        self.assertEqual(updated_person.spouse_first_name, "Janet")
        # Other fields should remain unchanged
        self.assertEqual(updated_person.spouse_last_name, self.person.spouse_last_name)
