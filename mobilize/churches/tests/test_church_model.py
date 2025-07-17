from django.test import TestCase
from mobilize.churches.models import Church
from mobilize.utils.supabase_mapper import SupabaseMapper


class ChurchModelTest(TestCase):
    """Test cases for the Church model and its compatibility with SupabaseMapper."""

    def setUp(self):
        """Set up test data."""
        self.church_data = {
            "name": "First Baptist Church of Anytown",
            "location": "Downtown",
            "denomination": "Baptist",
            "website": "www.firstbaptist.org",
            "year_founded": 1950,
            "congregation_size": 500,
            "weekly_attendance": 350,
            "pastor_name": "Pastor John Smith",
            "senior_pastor_first_name": "John",
            "senior_pastor_last_name": "Smith",
            "pastor_phone": "123-456-7891",
            "pastor_email": "pastor@firstbaptist.org",
            "missions_pastor_first_name": "Jane",
            "missions_pastor_last_name": "Doe",
            "mission_pastor_phone": "123-456-7892",
            "mission_pastor_email": "missions@firstbaptist.org",
            "primary_contact_first_name": "Bob",
            "primary_contact_last_name": "Johnson",
            "primary_contact_phone": "123-456-7893",
            "primary_contact_email": "contact@firstbaptist.org",
            "main_contact_id": 1,
            "church_pipeline": "Active",
            "priority": "High",
            "assigned_to": "John Doe",
            "virtuous": True,
            "source": "Website",
            "referred_by": "Pastor Smith",
            "info_given": "Initial contact information",
            "reason_closed": None,
            "owner_id": 1,
            "office_id": 1,
        }

        self.church = Church.objects.create(**self.church_data)

        # Supabase representation (matches Church model fields)
        self.supabase_data = {
            "id": self.church.id,
            "name": "First Baptist Church of Anytown",
            "location": "Downtown",
            "denomination": "Baptist",
            "website": "www.firstbaptist.org",
            "year_founded": 1950,
            "congregation_size": 500,
            "weekly_attendance": 350,
            "pastor_name": "Pastor John Smith",
            "senior_pastor_first_name": "John",
            "senior_pastor_last_name": "Smith",
            "pastor_phone": "123-456-7891",
            "pastor_email": "pastor@firstbaptist.org",
            "missions_pastor_first_name": "Jane",
            "missions_pastor_last_name": "Doe",
            "mission_pastor_phone": "123-456-7892",
            "mission_pastor_email": "missions@firstbaptist.org",
            "primary_contact_first_name": "Bob",
            "primary_contact_last_name": "Johnson",
            "primary_contact_phone": "123-456-7893",
            "primary_contact_email": "contact@firstbaptist.org",
            "main_contact_id": 1,
            "church_pipeline": "Active",
            "priority": "High",
            "assigned_to": "John Doe",
            "virtuous": True,
            "source": "Website",
            "referred_by": "Pastor Smith",
            "info_given": "Initial contact information",
            "reason_closed": None,
            "owner_id": 1,
            "office_id": 1,
        }

    def test_church_creation(self):
        """Test that a church can be created with the expected fields."""
        self.assertEqual(self.church.name, "First Baptist Church of Anytown")
        self.assertEqual(self.church.location, "Downtown")
        self.assertEqual(self.church.denomination, "Baptist")
        self.assertEqual(self.church.year_founded, 1950)
        self.assertEqual(self.church.congregation_size, 500)
        self.assertEqual(self.church.weekly_attendance, 350)
        self.assertEqual(self.church.pastor_name, "Pastor John Smith")
        self.assertEqual(self.church.senior_pastor_first_name, "John")
        self.assertEqual(self.church.senior_pastor_last_name, "Smith")
        self.assertEqual(self.church.pastor_phone, "123-456-7891")
        self.assertEqual(self.church.pastor_email, "pastor@firstbaptist.org")
        self.assertEqual(self.church.website, "www.firstbaptist.org")
        self.assertEqual(self.church.church_pipeline, "Active")
        self.assertEqual(self.church.priority, "High")
        self.assertEqual(self.church.assigned_to, "John Doe")

    def test_church_to_supabase_conversion(self):
        """Test converting a Church model instance to Supabase format."""
        supabase_dict = SupabaseMapper.to_supabase(self.church)

        # Check that key fields are correctly mapped
        self.assertEqual(supabase_dict["id"], self.church.id)
        self.assertEqual(supabase_dict["name"], self.church.name)
        self.assertEqual(supabase_dict["location"], self.church.location)
        self.assertEqual(supabase_dict["denomination"], self.church.denomination)
        self.assertEqual(supabase_dict["year_founded"], self.church.year_founded)
        self.assertEqual(
            supabase_dict["congregation_size"], self.church.congregation_size
        )
        self.assertEqual(
            supabase_dict["weekly_attendance"], self.church.weekly_attendance
        )
        self.assertEqual(supabase_dict["pastor_name"], self.church.pastor_name)

    def test_church_from_supabase_conversion(self):
        """Test converting Supabase data to Church model format."""
        django_dict = SupabaseMapper.from_supabase(self.supabase_data, Church)

        # Check that key fields are correctly mapped
        self.assertEqual(django_dict["id"], self.supabase_data["id"])
        self.assertEqual(django_dict["name"], self.supabase_data["name"])
        self.assertEqual(django_dict["location"], self.supabase_data["location"])
        self.assertEqual(
            django_dict["denomination"], self.supabase_data["denomination"]
        )
        self.assertEqual(
            django_dict["year_founded"], self.supabase_data["year_founded"]
        )
        self.assertEqual(
            django_dict["congregation_size"], self.supabase_data["congregation_size"]
        )
        self.assertEqual(
            django_dict["weekly_attendance"], self.supabase_data["weekly_attendance"]
        )
        self.assertEqual(django_dict["pastor_name"], self.supabase_data["pastor_name"])

    def test_church_create_from_supabase(self):
        """Test creating a new Church instance from Supabase data."""
        # Delete the existing church to avoid conflicts
        self.church.delete()

        # Create a new church from Supabase data
        new_church = SupabaseMapper.create_from_supabase(self.supabase_data, Church)

        # Check that the church was created with the correct data
        self.assertEqual(new_church.name, self.supabase_data["name"])
        self.assertEqual(new_church.location, self.supabase_data["location"])
        self.assertEqual(new_church.denomination, self.supabase_data["denomination"])
        self.assertEqual(new_church.year_founded, self.supabase_data["year_founded"])
        self.assertEqual(
            new_church.congregation_size, self.supabase_data["congregation_size"]
        )
        self.assertEqual(
            new_church.weekly_attendance, self.supabase_data["weekly_attendance"]
        )
        self.assertEqual(new_church.pastor_name, self.supabase_data["pastor_name"])

    def test_church_update_from_supabase(self):
        """Test updating an existing Church instance from Supabase data."""
        # Modify the Supabase data
        updated_data = self.supabase_data.copy()
        updated_data["name"] = "First Baptist Church of Anytown (Updated)"
        updated_data["congregation_size"] = 600
        updated_data["weekly_attendance"] = 450

        # Update the church
        updated_church = SupabaseMapper.update_from_supabase(self.church, updated_data)

        # Check that the church was updated with the correct data
        self.assertEqual(
            updated_church.name, "First Baptist Church of Anytown (Updated)"
        )
        self.assertEqual(updated_church.congregation_size, 600)
        self.assertEqual(updated_church.weekly_attendance, 450)
        self.assertEqual(updated_church.location, self.church.location)  # Unchanged
        self.assertEqual(
            updated_church.denomination, self.church.denomination
        )  # Unchanged
