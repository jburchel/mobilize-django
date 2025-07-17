"""
Management command to sync Gmail emails for specific email addresses going back one year.

This command will sync emails for the specific church contacts and people
identified in the email scan request.
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta
from mobilize.contacts.models import Person, Contact
from mobilize.communications.models import Communication

# from mobilize.communications.gmail_sync import sync_gmail_for_user
from mobilize.authentication.models import User


class Command(BaseCommand):
    help = "Sync Gmail emails for specific contacts going back one year"

    def add_arguments(self, parser):
        parser.add_argument("--email", type=str, help="Specific email address to sync")
        parser.add_argument(
            "--all-target-emails",
            action="store_true",
            help="Sync all target church email addresses",
        )
        parser.add_argument(
            "--days-back",
            type=int,
            default=365,
            help="Number of days to go back (default: 365)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be done without syncing",
        )

    def handle(self, *args, **options):
        email = options.get("email")
        all_target_emails = options.get("all_target_emails")
        days_back = options.get("days_back", 365)
        dry_run = options.get("dry_run")

        # Target email addresses from the church scan
        target_emails = [
            "thiggins@thegracecity.com",
            "tjhiggins@thegracecity.com",
            "reparks94@aol.com",
            "cactuscreek44@gmail.com",
        ]

        if email:
            emails_to_sync = [email]
        elif all_target_emails:
            emails_to_sync = target_emails
        else:
            self.stdout.write(
                self.style.ERROR("Please specify --email or --all-target-emails")
            )
            return

        self.stdout.write(
            self.style.SUCCESS(
                f"Starting targeted email sync for {len(emails_to_sync)} addresses..."
            )
        )

        if dry_run:
            self.stdout.write(
                self.style.WARNING("DRY RUN MODE - No actual syncing will occur")
            )

        # Check date range
        start_date = timezone.now().date() - timedelta(days=days_back)
        end_date = timezone.now().date()

        self.stdout.write(f"Scanning emails from {start_date} to {end_date}")
        self.stdout.write("=" * 60)

        for email_addr in emails_to_sync:
            self.stdout.write(f"\\n📧 Processing: {email_addr}")

            # Find people with this email address
            people = Person.objects.filter(contact__email=email_addr)

            if people.exists():
                self.stdout.write(f"   Found {people.count()} people with this email:")
                for person in people:
                    self.stdout.write(f"     👤 {person.name} (ID: {person.id})")

                    # Check current communications
                    current_comms = Communication.objects.filter(
                        person=person, date__gte=start_date
                    ).count()

                    self.stdout.write(
                        f"        Current communications: {current_comms}"
                    )
            else:
                self.stdout.write(f"   ❌ No people found with email {email_addr}")

                # Check if there's a church contact with this email
                church_contacts = Contact.objects.filter(
                    email=email_addr, type="church"
                )

                if church_contacts.exists():
                    self.stdout.write(
                        f"   Found {church_contacts.count()} church contacts with this email:"
                    )
                    for contact in church_contacts:
                        self.stdout.write(
                            f"     🏛️ {contact.church_name} (Contact ID: {contact.id})"
                        )

            # Check existing communications with this email in sender
            existing_sender_comms = Communication.objects.filter(
                date__gte=start_date, sender__icontains=email_addr
            ).count()

            self.stdout.write(
                f"   Existing communications FROM this email: {existing_sender_comms}"
            )

            if not dry_run:
                # For actual Gmail sync, we need to run the general sync command
                # since Gmail sync works at the user level, not individual emails
                self.stdout.write(f"   💡 To sync emails for {email_addr}, run:")
                self.stdout.write(
                    f"      python manage.py sync_gmail --days-back {days_back} --all-emails"
                )
            else:
                self.stdout.write(f"   📋 Would sync Gmail for {email_addr}")

        self.stdout.write("\\n" + "=" * 60)

        if not dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    "Email sync analysis completed!\\n"
                    "To perform the actual Gmail sync, run:\\n"
                    f"python manage.py sync_gmail --days-back {days_back} --all-emails"
                )
            )
        else:
            self.stdout.write(
                self.style.WARNING("DRY RUN completed - No actual syncing performed")
            )
