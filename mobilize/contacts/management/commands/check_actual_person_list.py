"""
Management command to check what the person list API is actually returning.
"""

from django.core.management.base import BaseCommand
from django.db import models
from mobilize.contacts.models import Contact, Person
from mobilize.core.permissions import DataAccessManager
from mobilize.authentication.models import User


class Command(BaseCommand):
    help = "Check what the person list API is actually returning"

    def add_arguments(self, parser):
        parser.add_argument(
            "--user-id",
            type=int,
            help="Check for specific user ID (default: first super admin)",
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS("=== Checking Actual Person List API Results ===")
        )

        # Get user to test with
        if options["user_id"]:
            try:
                user = User.objects.get(id=options["user_id"])
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'User {options["user_id"]} not found')
                )
                return
        else:
            # Get first super admin
            user = User.objects.filter(role="super_admin").first()
            if not user:
                self.stdout.write(self.style.ERROR("No super admin found"))
                return

        self.stdout.write(
            f"Testing with user: {user.username} (ID: {user.id}, Role: {user.role})"
        )

        # Test the DataAccessManager
        access_manager = DataAccessManager(user, "default")
        people_queryset = access_manager.get_people_queryset()

        total_people = people_queryset.count()
        self.stdout.write(f"Total people accessible: {total_people}")

        # Check for people that might be showing as "Person ###"
        self.stdout.write("\\nChecking all accessible people for name issues:")

        problem_people = []

        for person in people_queryset[:20]:  # Check first 20
            # Simulate the API name logic
            first_name = person.contact.first_name or ""
            last_name = person.contact.last_name or ""

            # Clean up names
            first_name = first_name.strip()
            last_name = last_name.strip()

            # Build full name
            full_name = f"{first_name} {last_name}".strip()

            # Check for "No name listed" condition
            if not full_name:
                api_result = "No name listed"
                problem_people.append(person)
            else:
                api_result = full_name

            # Check if this would show as "Person ###"
            person_str = str(person)

            self.stdout.write(f"  Person {person.contact.id}:")
            self.stdout.write(f'    - API name: "{api_result}"')
            self.stdout.write(f'    - Django str: "{person_str}"')
            self.stdout.write(f'    - Contact names: "{first_name}" "{last_name}"')
            self.stdout.write(f"    - Email: {person.contact.email}")

            if api_result == "No name listed" or person_str.startswith("Person "):
                self.stdout.write(
                    f'    - ⚠️  PROBLEM: Shows as "{api_result}" or "{person_str}"'
                )

        if problem_people:
            self.stdout.write(
                f"\\nFound {len(problem_people)} people with name display issues"
            )
        else:
            self.stdout.write(
                "\\nNo people found with name display issues in first 20 records"
            )

        # Check if there are specific person IDs you mentioned
        test_ids = [699, 728, 685]
        self.stdout.write(f"\\nChecking specific person IDs: {test_ids}")

        for person_id in test_ids:
            # Check if person exists and is accessible
            accessible = people_queryset.filter(contact_id=person_id).exists()

            if accessible:
                person = people_queryset.get(contact_id=person_id)

                # Simulate API logic
                first_name = (person.contact.first_name or "").strip()
                last_name = (person.contact.last_name or "").strip()
                full_name = f"{first_name} {last_name}".strip()
                api_result = full_name if full_name else "No name listed"

                self.stdout.write(f"  Person {person_id}: ACCESSIBLE")
                self.stdout.write(f'    - API would show: "{api_result}"')
                self.stdout.write(f'    - Django str: "{str(person)}"')
                self.stdout.write(f'    - Actual names: "{first_name}" "{last_name}"')
                self.stdout.write(f"    - Email: {person.contact.email}")

            else:
                # Check if person exists at all
                try:
                    person = Person.objects.get(contact_id=person_id)
                    self.stdout.write(
                        f"  Person {person_id}: EXISTS but NOT ACCESSIBLE to this user"
                    )
                    self.stdout.write(
                        f"    - Assigned to user: {person.contact.user_id}"
                    )
                    self.stdout.write(f"    - Office: {person.contact.office_id}")
                    self.stdout.write(
                        f'    - Names: "{person.contact.first_name}" "{person.contact.last_name}"'
                    )
                except Person.DoesNotExist:
                    self.stdout.write(f"  Person {person_id}: DOES NOT EXIST")

        # Test with different view modes for super admin
        if user.role == "super_admin":
            self.stdout.write("\\n=== Testing Super Admin View Modes ===")

            for view_mode in ["default", "my_only"]:
                access_manager = DataAccessManager(user, view_mode)
                people_queryset = access_manager.get_people_queryset()
                count = people_queryset.count()
                self.stdout.write(f"  {view_mode} mode: {count} people visible")

                # Check if our test people are visible in this mode
                for person_id in test_ids:
                    visible = people_queryset.filter(contact_id=person_id).exists()
                    self.stdout.write(
                        f'    - Person {person_id}: {"✓" if visible else "✗"}'
                    )

        self.stdout.write("\\n" + self.style.SUCCESS("Person list check complete!"))
