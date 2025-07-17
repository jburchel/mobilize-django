from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta
from django.contrib.auth import get_user_model
from mobilize.communications.models import Communication
from mobilize.contacts.models import Contact, Person
from mobilize.admin_panel.models import Office
import random

User = get_user_model()


class Command(BaseCommand):
    help = 'Create test communication records of different types for testing the "View All" button functionality'

    def add_arguments(self, parser):
        parser.add_argument(
            "--person-id",
            type=int,
            help="ID of the person to create communications for",
        )
        parser.add_argument(
            "--person-name",
            type=str,
            help="Name of person to create communications for (will search by name)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be created without actually creating records",
        )
        parser.add_argument(
            "--count",
            type=int,
            default=2,
            help="Number of communications to create for each type (default: 2)",
        )
        parser.add_argument(
            "--cleanup",
            action="store_true",
            help="Remove all test communications created by this command",
        )

    def handle(self, *args, **options):
        if options["cleanup"]:
            self.cleanup_test_communications()
            return

        person = self.get_person(options)
        if not person:
            self.stderr.write(self.style.ERROR("Person not found"))
            return

        user = self.get_user()
        if not user:
            self.stderr.write(self.style.ERROR("No user found"))
            return

        if options["dry_run"]:
            self.stdout.write(
                self.style.WARNING("DRY RUN MODE - No records will be created")
            )
            self.show_what_would_be_created(person, options["count"])
            return

        self.create_test_communications(person, user, options["count"])

    def get_person(self, options):
        """Get person by ID or name"""
        if options["person_id"]:
            try:
                return Person.objects.get(id=options["person_id"])
            except Person.DoesNotExist:
                return None

        if options["person_name"]:
            # Search by name
            name_parts = options["person_name"].split()
            if len(name_parts) >= 2:
                try:
                    return Person.objects.filter(
                        contact__first_name__icontains=name_parts[0],
                        contact__last_name__icontains=name_parts[1],
                    ).first()
                except Person.DoesNotExist:
                    return None
            else:
                # Search by first name only
                try:
                    return Person.objects.filter(
                        contact__first_name__icontains=options["person_name"]
                    ).first()
                except Person.DoesNotExist:
                    return None

        # If no specific person, get the first person with an office
        return Person.objects.filter(contact__office__isnull=False).first()

    def get_user(self):
        """Get a user for the communications"""
        return User.objects.first()

    def show_what_would_be_created(self, person, count):
        """Show what would be created in dry run mode"""
        self.stdout.write(f"Would create test communications for: {person.name}")
        self.stdout.write(f"Contact ID: {person.contact.id}")
        self.stdout.write(f"Number of communications per type: {count}")

        comm_types = Communication.TYPE_CHOICES
        self.stdout.write(f"\nCommunication types to create:")
        for comm_type, display_name in comm_types:
            self.stdout.write(f"  - {display_name}: {count} records")

        total_count = len(comm_types) * count
        self.stdout.write(f"\nTotal communications to create: {total_count}")

    def create_test_communications(self, person, user, count):
        """Create test communications for the person"""
        office = person.contact.office
        if not office:
            self.stderr.write(self.style.ERROR("Person must have an office assigned"))
            return

        comm_types = Communication.TYPE_CHOICES
        directions = ["inbound", "outbound"]

        created_count = 0

        for comm_type, display_name in comm_types:
            for i in range(count):
                # Create varied dates over the past 30 days
                days_ago = random.randint(1, 30)
                comm_date = timezone.now() - timedelta(days=days_ago)

                # Create communication data based on type
                communication_data = self.get_communication_data(
                    comm_type, display_name, person, i + 1
                )

                communication = Communication.objects.create(
                    type=comm_type,
                    subject=communication_data["subject"],
                    message=communication_data["message"],
                    content=communication_data["content"],
                    direction=random.choice(directions),
                    date=comm_date.date(),
                    date_sent=comm_date,
                    person=person,
                    user=user,
                    office=office,
                    status="sent",
                    created_at=comm_date,
                    updated_at=comm_date,
                    # Add test marker for easy cleanup
                    external_id=f'test-communication-{comm_type.lower().replace(" ", "-")}-{i+1}',
                )

                created_count += 1

                self.stdout.write(
                    self.style.SUCCESS(
                        f"Created {display_name} communication: {communication.subject}"
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"\nSuccessfully created {created_count} test communications for {person.name}"
            )
        )

        # Display summary
        self.stdout.write(f"\nSummary:")
        self.stdout.write(f"Person: {person.name}")
        self.stdout.write(f"Contact ID: {person.contact.id}")
        self.stdout.write(f"Office: {office.name}")
        self.stdout.write(f"Communications created: {created_count}")
        self.stdout.write(
            f'\nTest the "View All" button at the person detail page to verify it shows all communication types.'
        )

    def get_communication_data(self, comm_type, display_name, person, index):
        """Generate appropriate test data for each communication type"""
        base_data = {
            "subject": f"Test {display_name} {index} - {person.name}",
            "message": f"This is a test {display_name.lower()} communication #{index} for {person.name}",
            "content": f'This is a test {display_name.lower()} communication #{index} for {person.name}. This record was created by the create_test_communications management command to test the "View All" button functionality.',
        }

        # Customize based on communication type
        if comm_type == "Email":
            base_data.update(
                {
                    "subject": f"Test Email: Meeting Request - {person.name}",
                    "message": f"Would you like to schedule a meeting to discuss your missions interest?",
                    "content": f"Hi {person.name},\n\nI hope this email finds you well. Would you like to schedule a meeting to discuss your missions interest? Let me know what works best for your schedule.\n\nBest regards,\nTest User",
                }
            )
        elif comm_type == "Phone Call":
            base_data.update(
                {
                    "subject": f"Phone Call: Follow-up Discussion",
                    "message": f"Called to discuss missions opportunities and next steps",
                    "content": f"Had a productive phone call with {person.name} about missions opportunities. Discussed their interests and potential next steps. Duration: 30 minutes. Follow-up needed in 2 weeks.",
                }
            )
        elif comm_type == "Text Message":
            base_data.update(
                {
                    "subject": f"Text: Event Reminder",
                    "message": f"Reminder about missions info session tomorrow at 7pm",
                    "content": f"Hi {person.name}! Just a friendly reminder about the missions info session tomorrow at 7pm. Looking forward to seeing you there!",
                }
            )
        elif comm_type == "Meeting":
            base_data.update(
                {
                    "subject": f"Meeting: Initial Consultation",
                    "message": f"Met to discuss missions calling and ministry opportunities",
                    "content": f"Had an initial consultation meeting with {person.name} at the church office. Discussed their missions calling, ministry background, and potential opportunities. Next steps: provide application materials and schedule follow-up in 2 weeks.",
                }
            )
        elif comm_type == "Video Call":
            base_data.update(
                {
                    "subject": f"Video Call: Missions Training Session",
                    "message": f"Conducted online training session via video call",
                    "content": f"Conducted a missions training session with {person.name} via video call. Covered cultural preparation, ministry strategies, and practical considerations. Session lasted 45 minutes. Follow-up materials sent via email.",
                }
            )

        return base_data

    def cleanup_test_communications(self):
        """Remove all test communications created by this command"""
        test_comms = Communication.objects.filter(
            external_id__startswith="test-communication-"
        )

        count = test_comms.count()
        if count == 0:
            self.stdout.write(
                self.style.WARNING("No test communications found to cleanup")
            )
            return

        self.stdout.write(f"Found {count} test communications to remove")

        # Show what will be deleted
        for comm in test_comms:
            self.stdout.write(f"  - {comm.type}: {comm.subject}")

        # Confirm deletion
        confirm = input(
            "\nAre you sure you want to delete these test communications? (y/N): "
        )
        if confirm.lower() in ["y", "yes"]:
            deleted_count = test_comms.delete()[0]
            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully deleted {deleted_count} test communications"
                )
            )
        else:
            self.stdout.write(self.style.WARNING("Cleanup cancelled"))
