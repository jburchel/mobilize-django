from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db.models import Q
from datetime import datetime, timedelta
from mobilize.contacts.models import Person, Contact
from mobilize.communications.tasks import sync_gmail_emails
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Sync last 2 years of Gmail emails for specific targeted contacts"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be synced without actually syncing",
        )
        parser.add_argument(
            "--days",
            type=int,
            default=730,  # 2 years
            help="Number of days back to sync (default: 730 for 2 years)",
        )
        parser.add_argument(
            "--user-email",
            type=str,
            help="Specific user email to sync for (if not provided, will try to find appropriate user)",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        days_back = options["days"]
        user_email = options["user_email"]

        # Target contact names (combined list)
        target_names = [
            # Original list - corrected spellings
            "Niranjan Madhavan",  # Fixed spelling: Madhavan not Madhaven
            "Beka Ahlstrom",
            "Ellie Montgomery",
            "Austin Riggs",
            "Gracie Taylor",
            "Teresa McAfee",
            "Paul Wilkins",
            "Ben Cimorelli",
            "Scott And Chrissy Wallace",  # This is how it appears in the database
            "Scott Simmons",
            # Additional list
            "Barb Jackowski",
            "Chris Vernon",
            "Chuck Hill",
            "Edith Parks",
            "Efran Klund",
            "Erich Schultz",
            "Heather Pastva",
            "Janette Brown",
            "Jenny Tarpley",
            "Jim Turnage",
            "Jimmy Currence",
            "Jimmy Kniss",
            "Jonathan St Clair",
            "Joshua Knott",
            "Judy Davis",
            "Kendall Hicks",
            "Kenny And Nikki Coker",  # Standardized format
            "Kent Fancher",
            "Kyle Donn",
            "Laura Roe Jones",
            "Marc Rattray",
            "Mark Stanley",
            "Matt Rhodes",
            "Michael Hull",
            "David Bunn",  # Database has no "Rev." prefix
            "Richard Thomas",
            "Rob Campbell",
            "Ruthanne Lynch",
            "Savannah Simpson",
        ]

        self.stdout.write(f"Searching for {len(target_names)} target contacts...")

        # Find matching contacts using flexible name matching
        found_contacts = []
        missing_contacts = []

        for target_name in target_names:
            # Try multiple search strategies
            contact_found = False

            # Strategy 1: Full name match (first + last)
            name_parts = target_name.split()
            if len(name_parts) >= 2:
                first_name = name_parts[0]
                last_name = " ".join(name_parts[1:])  # Handle multi-word last names

                contact = Contact.objects.filter(
                    first_name__icontains=first_name,
                    last_name__icontains=last_name,
                    type="person",
                ).first()

                if contact and hasattr(contact, "person_details"):
                    found_contacts.append((contact, target_name))
                    contact_found = True

            # Strategy 2: Search in full name concatenation
            if not contact_found:
                contacts = Contact.objects.filter(type="person").exclude(
                    Q(first_name__isnull=True) & Q(last_name__isnull=True)
                )

                for contact in contacts:
                    full_name = (
                        f"{contact.first_name or ''} {contact.last_name or ''}".strip()
                    )
                    if (
                        target_name.lower() in full_name.lower()
                        or full_name.lower() in target_name.lower()
                    ):
                        if hasattr(contact, "person_details"):
                            found_contacts.append((contact, target_name))
                            contact_found = True
                            break

            # Strategy 3: Partial name matching
            if not contact_found:
                for name_part in target_name.split():
                    if len(name_part) > 2:  # Skip short words
                        contact = Contact.objects.filter(
                            Q(first_name__icontains=name_part)
                            | Q(last_name__icontains=name_part),
                            type="person",
                        ).first()

                        if contact and hasattr(contact, "person_details"):
                            found_contacts.append((contact, target_name))
                            contact_found = True
                            break

            if not contact_found:
                missing_contacts.append(target_name)

        self.stdout.write(
            self.style.SUCCESS(f"Found {len(found_contacts)} matching contacts:")
        )
        for contact, target_name in found_contacts:
            full_name = f"{contact.first_name or ''} {contact.last_name or ''}".strip()
            self.stdout.write(
                f'  ✓ {target_name} -> {full_name} ({contact.email or "no email"})'
            )

        if missing_contacts:
            self.stdout.write(
                self.style.WARNING(f"\nMissing {len(missing_contacts)} contacts:")
            )
            for name in missing_contacts:
                self.stdout.write(f"  ✗ {name}")

        if not found_contacts:
            self.stdout.write(self.style.ERROR("No contacts found to sync!"))
            return

        # Get or determine user for Gmail sync
        sync_user = None
        if user_email:
            try:
                sync_user = User.objects.get(email=user_email)
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f"User with email {user_email} not found")
                )
                return
        else:
            # Try to find a user with Gmail credentials
            # This is a simplified approach - in practice you might want to be more specific
            sync_user = User.objects.filter(is_staff=True, is_active=True).first()
            if sync_user:
                self.stdout.write(f"Using user: {sync_user.email} for Gmail sync")

        if not sync_user:
            self.stdout.write(
                self.style.ERROR(
                    "No user found for Gmail sync. Use --user-email to specify."
                )
            )
            return

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f"\nDRY RUN - Would sync last {days_back} days of emails for {len(found_contacts)} contacts"
                )
            )
            return

        # Perform the actual sync
        self.stdout.write(
            f"\nStarting Gmail sync for {len(found_contacts)} contacts..."
        )
        self.stdout.write(
            f"Syncing last {days_back} days of emails using user: {sync_user.email}"
        )

        # Extract email addresses for sync
        contact_emails = []
        for contact, target_name in found_contacts:
            if contact.email:
                contact_emails.append(contact.email)

        if contact_emails:
            try:
                # Try to use Celery first, fall back to direct execution
                try:
                    # Trigger Gmail sync task
                    result = sync_gmail_emails.delay(
                        user_id=sync_user.id,
                        days_back=days_back,
                        specific_emails=contact_emails,  # Pass specific emails to sync
                    )

                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Gmail sync task queued with ID: {result.id}"
                        )
                    )
                    self.stdout.write(
                        f"Syncing emails for {len(contact_emails)} email addresses"
                    )
                    self.stdout.write("Monitor the task progress in your Celery logs")

                except Exception as celery_error:
                    self.stdout.write(
                        self.style.WARNING(
                            f"Celery not available ({celery_error}), running sync directly..."
                        )
                    )

                    # Run sync directly without Celery
                    from mobilize.communications.gmail_service import GmailService

                    gmail_service = GmailService(sync_user)
                    if not gmail_service.is_authenticated():
                        self.stdout.write(
                            self.style.ERROR("Gmail not authenticated for user")
                        )
                        return

                    self.stdout.write(
                        f"Starting direct Gmail sync for {len(contact_emails)} email addresses..."
                    )

                    # Run the sync directly
                    result = gmail_service.sync_emails_to_communications(
                        days_back=days_back,
                        contacts_only=False,
                        specific_emails=contact_emails,
                    )

                    if result["success"]:
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'Successfully synced {result["synced_count"]} emails'
                            )
                        )
                    else:
                        self.stdout.write(
                            self.style.ERROR(
                                f'Sync failed: {result.get("error", "Unknown error")}'
                            )
                        )

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Failed to sync emails: {e}"))
        else:
            self.stdout.write(
                self.style.WARNING("No email addresses found for the matched contacts")
            )

        self.stdout.write(
            self.style.SUCCESS("\nTargeted email sync command completed!")
        )
