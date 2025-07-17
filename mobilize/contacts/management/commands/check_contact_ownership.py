"""
Management command to check contact ownership and access permissions.
"""

from django.core.management.base import BaseCommand
from django.db import models
from mobilize.contacts.models import Contact, Person
from mobilize.authentication.models import User


class Command(BaseCommand):
    help = "Check contact ownership and access permissions"

    def add_arguments(self, parser):
        parser.add_argument(
            "--user-id",
            type=int,
            help="Check access for specific user ID",
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("=== Checking Contact Ownership ==="))

        # Check the contacts that have proper names
        test_contacts = [685, 699]

        for contact_id in test_contacts:
            try:
                contact = Contact.objects.get(id=contact_id)
                self.stdout.write(
                    f"\\n--- Contact {contact_id}: {contact.first_name} {contact.last_name} ---"
                )
                self.stdout.write(
                    f'  Assigned to user: {contact.user_id} ({contact.user.username if contact.user else "No user"})'
                )
                self.stdout.write(
                    f'  Office: {contact.office_id} ({contact.office.name if contact.office else "No office"})'
                )
                self.stdout.write(f"  Email: {contact.email}")
                self.stdout.write(f"  Type: {contact.type}")

            except Contact.DoesNotExist:
                self.stdout.write(f"Contact {contact_id} not found")

        # Get all users to see who might have access
        self.stdout.write("\\n=== ALL USERS IN SYSTEM ===")
        users = User.objects.all()
        for user in users:
            self.stdout.write(
                f"  User {user.id}: {user.username} ({user.first_name} {user.last_name}) - Role: {user.role}"
            )

        # Check what contacts each user can see with current permissions
        if options["user_id"]:
            user_id = options["user_id"]
            self.stdout.write(f"\\n=== ACCESS CHECK FOR USER {user_id} ===")

            try:
                user = User.objects.get(id=user_id)
                self.stdout.write(f"User: {user.username} - Role: {user.role}")

                # Test the security filtering
                from mobilize.core.permissions import DataAccessManager

                access_manager = DataAccessManager(user, "default")

                people_queryset = access_manager.get_people_queryset()
                visible_people = people_queryset.count()
                self.stdout.write(f"Can see {visible_people} people total")

                # Check specific test contacts
                for contact_id in test_contacts:
                    is_visible = people_queryset.filter(contact_id=contact_id).exists()
                    self.stdout.write(
                        f'  Contact {contact_id}: {"✓ VISIBLE" if is_visible else "✗ HIDDEN"}'
                    )

                # Show first few visible people
                self.stdout.write("\\nFirst 10 visible people:")
                for person in people_queryset[:10]:
                    self.stdout.write(
                        f"  {person.contact.id}: {person.name} (user: {person.contact.user_id})"
                    )

            except User.DoesNotExist:
                self.stdout.write(f"User {user_id} not found")
        else:
            # Check access for all users
            self.stdout.write("\\n=== ACCESS CHECK FOR ALL USERS ===")

            for user in users:
                from mobilize.core.permissions import DataAccessManager

                access_manager = DataAccessManager(user, "default")
                people_queryset = access_manager.get_people_queryset()
                visible_count = people_queryset.count()

                # Check if user can see our test contacts
                can_see_685 = people_queryset.filter(contact_id=685).exists()
                can_see_699 = people_queryset.filter(contact_id=699).exists()

                self.stdout.write(
                    f"  User {user.id} ({user.username}): sees {visible_count} people"
                )
                self.stdout.write(
                    f'    - Can see Olivia (685): {"Yes" if can_see_685 else "No"}'
                )
                self.stdout.write(
                    f'    - Can see Nate (699): {"Yes" if can_see_699 else "No"}'
                )

        self.stdout.write("\\n" + self.style.SUCCESS("Ownership check complete!"))
