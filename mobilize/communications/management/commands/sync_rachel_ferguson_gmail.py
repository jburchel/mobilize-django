"""
Management command to sync Rachel Ferguson's Gmail communications going back 2 years.

This command specifically syncs emails for Rachel Ferguson (rbf1997@gmail.com)
to ensure all her communications are properly captured in the database.
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta
from mobilize.contacts.models import Contact, Person
from mobilize.communications.models import Communication


class Command(BaseCommand):
    help = "Sync Rachel Ferguson Gmail communications going back 2 years (Issue #17)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be done without making changes",
        )
        parser.add_argument(
            "--verbose",
            action="store_true",
            help="Show detailed output",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        verbose = options["verbose"]

        self.stdout.write(
            self.style.SUCCESS("Starting Rachel Ferguson Gmail sync (Issue #17)...")
        )

        if dry_run:
            self.stdout.write(
                self.style.WARNING("DRY RUN MODE - No changes will be made")
            )

        try:
            # Step 1: Find Rachel Ferguson's Contact record
            try:
                rachel_ferguson_contact = Contact.objects.get(email="rbf1997@gmail.com")
                rachel_ferguson_person = Person.objects.get(
                    contact=rachel_ferguson_contact
                )
                if verbose:
                    self.stdout.write(
                        f"Found Rachel Ferguson: Person ID {rachel_ferguson_person.id}, "
                        f"Contact ID {rachel_ferguson_contact.id}, "
                        f"Email: {rachel_ferguson_contact.email}"
                    )
            except (Contact.DoesNotExist, Person.DoesNotExist):
                self.stdout.write(
                    self.style.ERROR(
                        "Could not find Rachel Ferguson with email rbf1997@gmail.com"
                    )
                )
                return

            # Step 2: Check current communications for Rachel Ferguson
            current_comms = Communication.objects.filter(
                person=rachel_ferguson_person
            ).order_by("-date")

            if verbose:
                self.stdout.write(
                    f"Rachel Ferguson currently has {current_comms.count()} communications"
                )

                # Show current communications
                for comm in current_comms:
                    self.stdout.write(
                        f"  ID {comm.id}: {comm.subject} - {comm.date} "
                        f"(from {comm.sender})"
                    )

            # Step 3: Calculate date range (2 years back)
            end_date = timezone.now().date()
            start_date = end_date - timedelta(days=730)  # 2 years

            self.stdout.write(
                f"Checking for communications from {start_date} to {end_date}"
            )

            # Step 4: Check for communications in the date range
            date_filtered_comms = current_comms.filter(
                date__gte=start_date, date__lte=end_date
            )

            self.stdout.write(
                f"Found {date_filtered_comms.count()} communications in the last 2 years"
            )

            # Step 5: Information about Gmail sync
            self.stdout.write(
                self.style.WARNING(
                    "\nNOTE: This command shows current communications status. "
                    "To sync Gmail emails, you need to run the Gmail sync command:\n"
                    "python manage.py sync_gmail --contacts-only\n"
                    "or\n"
                    "python manage.py sync_gmail --all-emails"
                )
            )

            # Step 6: Check for any potential duplicate issues
            # Look for communications with similar sender patterns
            potential_duplicates = Communication.objects.filter(
                sender__icontains="rbf1997@gmail.com"
            ).exclude(person=rachel_ferguson_person)

            if potential_duplicates.exists():
                self.stdout.write(
                    self.style.WARNING(
                        f"\nFound {potential_duplicates.count()} communications "
                        f"from rbf1997@gmail.com linked to other people:"
                    )
                )
                for comm in potential_duplicates:
                    person_name = (
                        comm.person.name if comm.person else "No person linked"
                    )
                    self.stdout.write(
                        f"  ID {comm.id}: {comm.subject} - {comm.date} "
                        f"-> {person_name} (should be Rachel Ferguson)"
                    )

            # Step 7: Summary
            self.stdout.write(
                self.style.SUCCESS(
                    f"\nSummary for Rachel Ferguson (rbf1997@gmail.com):"
                    f"\n- Total communications: {current_comms.count()}"
                    f"\n- Communications in last 2 years: {date_filtered_comms.count()}"
                    f"\n- Potential duplicate issues: {potential_duplicates.count()}"
                    f"\n\nTo sync Gmail emails, run: python manage.py sync_gmail"
                )
            )

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error occurred: {str(e)}"))
            raise
