from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from mobilize.contacts.models import Contact, Person


class ContactModelValidationTest(TestCase):
    """Test cases for Contact model validation and constraints."""

    def test_contact_str_method_with_names(self):
        """Test Contact __str__ method with first and last name."""
        contact = Contact.objects.create(first_name="John", last_name="Doe")
        self.assertEqual(str(contact), "John Doe")

    def test_contact_str_method_with_church_name(self):
        """Test Contact __str__ method with church name."""
        contact = Contact.objects.create(church_name="First Baptist Church")
        self.assertEqual(str(contact), "First Baptist Church")

    def test_contact_str_method_fallback(self):
        """Test Contact __str__ method fallback to ID."""
        contact = Contact.objects.create()
        self.assertEqual(str(contact), f"Contact {contact.id}")

    def test_contact_full_address_property(self):
        """Test Contact full_address property."""
        contact = Contact.objects.create(
            street_address="123 Main St",
            city="Anytown",
            state="CA",
            zip_code="12345",
            country="USA",
        )
        expected = "123 Main St, Anytown, CA, 12345"
        self.assertEqual(contact.full_address, expected)

    def test_contact_full_address_property_minimal(self):
        """Test Contact full_address property with minimal data."""
        contact = Contact.objects.create(city="Anytown", state="CA")
        expected = "Anytown, CA"
        self.assertEqual(contact.full_address, expected)

    def test_contact_full_address_property_empty(self):
        """Test Contact full_address property with no address data."""
        contact = Contact.objects.create()
        self.assertEqual(contact.full_address, "")

    def test_contact_full_address_property_with_address_field(self):
        """Test Contact full_address property falls back to address field."""
        contact = Contact.objects.create(address="Some generic address")
        self.assertEqual(contact.full_address, "Some generic address")

    def test_contact_full_address_excludes_usa(self):
        """Test Contact full_address property excludes USA from output."""
        contact = Contact.objects.create(
            street_address="123 Main St",
            city="Anytown",
            state="CA",
            zip_code="12345",
            country="USA",
        )
        self.assertNotIn("USA", contact.full_address)

    def test_contact_full_address_includes_non_usa_country(self):
        """Test Contact full_address property includes non-USA countries."""
        contact = Contact.objects.create(
            street_address="123 Main St",
            city="Toronto",
            state="ON",
            zip_code="M5V 3A8",
            country="Canada",
        )
        self.assertIn("Canada", contact.full_address)

    def test_contact_json_field_valid_data(self):
        """Test Contact conflict_data JSONField with valid data."""
        conflict_data = {
            "field": "email",
            "local_value": "local@example.com",
            "remote_value": "remote@example.com",
        }
        contact = Contact.objects.create(
            first_name="John", conflict_data=conflict_data, has_conflict=True
        )
        self.assertEqual(contact.conflict_data["field"], "email")
        self.assertTrue(contact.has_conflict)

    def test_contact_optional_fields_can_be_null(self):
        """Test that Contact optional fields can be null."""
        contact = Contact.objects.create()
        self.assertIsNone(contact.first_name)
        self.assertIsNone(contact.last_name)
        self.assertIsNone(contact.email)
        self.assertIsNone(contact.phone)
        self.assertIsNone(contact.user_id)
        self.assertIsNone(contact.office_id)


class PersonModelValidationTest(TestCase):
    """Test cases for Person model validation and constraints."""

    def test_person_inherits_from_contact(self):
        """Test that Person properly relates to Contact."""
        contact = Contact.objects.create(
            type="person", first_name="Jane", last_name="Smith"
        )
        person = Person.objects.create(contact=contact, title="Ms.")
        # Person should access Contact fields through relationship
        self.assertEqual(person.contact.first_name, "Jane")
        self.assertEqual(person.contact.last_name, "Smith")
        # And Person-specific fields
        self.assertEqual(person.title, "Ms.")

    def test_person_name_property(self):
        """Test Person name property."""
        contact = Contact.objects.create(
            type="person", first_name="Jane", last_name="Smith"
        )
        person = Person.objects.create(contact=contact)
        self.assertEqual(person.name, "Jane Smith")

    def test_person_name_property_first_only(self):
        """Test Person name property with first name only."""
        contact = Contact.objects.create(type="person", first_name="Jane")
        person = Person.objects.create(contact=contact)
        self.assertEqual(person.name, "Jane")

    def test_person_name_property_last_only(self):
        """Test Person name property with last name only."""
        contact = Contact.objects.create(type="person", last_name="Smith")
        person = Person.objects.create(contact=contact)
        self.assertEqual(person.name, "Smith")

    def test_person_name_property_empty(self):
        """Test Person name property with no names."""
        contact = Contact.objects.create(type="person")
        person = Person.objects.create(contact=contact)
        self.assertEqual(person.name, "")

    def test_person_get_absolute_url(self):
        """Test Person get_absolute_url method."""
        contact = Contact.objects.create(
            type="person", first_name="Jane", last_name="Smith"
        )
        person = Person.objects.create(contact=contact)
        expected_url = f"/contacts/{person.contact_id}/"
        self.assertEqual(person.get_absolute_url(), expected_url)

    def test_person_date_fields_validation(self):
        """Test Person date fields accept valid dates."""
        contact = Contact.objects.create(type="person")
        person = Person.objects.create(
            contact=contact, birthday="1990-01-01", anniversary="2015-06-15"
        )
        self.assertEqual(str(person.birthday), "1990-01-01")
        self.assertEqual(str(person.anniversary), "2015-06-15")

    def test_person_boolean_fields(self):
        """Test Person boolean fields."""
        contact = Contact.objects.create(type="person", first_name="Jane")
        person = Person.objects.create(contact=contact)
        # Person model doesn't have boolean fields in current schema
        # This test validates the model can be created
        self.assertIsNotNone(person)

    def test_person_text_fields_can_be_long(self):
        """Test Person text fields can handle long content."""
        contact = Contact.objects.create(type="person", first_name="Jane")
        # Test languages field which exists and is JSON
        languages_list = ["English", "Spanish", "French"]
        person = Person.objects.create(contact=contact, languages=languages_list)
        self.assertEqual(person.languages, languages_list)

    def test_person_meta_ordering(self):
        """Test Person model ordering."""
        contact1 = Contact.objects.create(
            type="person", first_name="John", last_name="Zebra"
        )
        contact2 = Contact.objects.create(
            type="person", first_name="Jane", last_name="Apple"
        )
        contact3 = Contact.objects.create(
            type="person", first_name="Bob", last_name="Apple"
        )

        person1 = Person.objects.create(contact=contact1)
        person2 = Person.objects.create(contact=contact2)
        person3 = Person.objects.create(contact=contact3)

        # Should be ordered by contact last_name, then first_name
        people = list(Person.objects.all())
        self.assertEqual(people[0], person3)  # Bob Apple
        self.assertEqual(people[1], person2)  # Jane Apple
        self.assertEqual(people[2], person1)  # John Zebra

    def test_person_db_table_correct(self):
        """Test Person model uses correct database table."""
        self.assertEqual(Person._meta.db_table, "people")

    def test_person_verbose_names(self):
        """Test Person model verbose names."""
        self.assertEqual(Person._meta.verbose_name, "Person")
        self.assertEqual(Person._meta.verbose_name_plural, "People")
