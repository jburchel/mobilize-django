"""
Simple duplicate contact cleanup command

This command deletes obvious duplicate contacts based on exact email matches.
It keeps the oldest contact and deletes newer duplicates.
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Count
from mobilize.contacts.models import Contact


class Command(BaseCommand):
    help = "Clean up obvious duplicate contacts (same email)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be deleted without making changes",
        )

    def handle(self, *args, **options):
        self.dry_run = options["dry_run"]

        if self.dry_run:
            self.stdout.write(
                self.style.WARNING("DRY RUN MODE - No changes will be made")
            )

        self.cleanup_email_duplicates()

    def cleanup_email_duplicates(self):
        """Find and clean up contacts with duplicate emails"""
        self.stdout.write("=== CLEANING UP EMAIL DUPLICATES ===")

        # Find emails that have multiple contacts
        duplicate_emails = (
            Contact.objects.values("email")
            .annotate(count=Count("id"))
            .filter(count__gt=1, email__isnull=False)
            .exclude(email="")
        )

        total_deleted = 0

        for dup in duplicate_emails:
            email = dup["email"]
            contacts = list(Contact.objects.filter(email=email).order_by("id"))

            if len(contacts) > 1:
                primary = contacts[0]  # Keep the oldest (lowest ID)
                duplicates = contacts[1:]  # Delete the rest

                self.stdout.write(f"\\nEmail: {email}")
                self.stdout.write(f"  Keeping: ID {primary.id} - {primary}")

                for dup_contact in duplicates:
                    self.stdout.write(
                        f"  Deleting: ID {dup_contact.id} - {dup_contact}"
                    )

                    if not self.dry_run:
                        try:
                            # Simple delete without complex merging
                            self.safe_delete_contact(dup_contact)
                            total_deleted += 1
                        except Exception as e:
                            self.stdout.write(f"    ✗ Error deleting contact: {e}")
                    else:
                        total_deleted += 1

        action = "Would delete" if self.dry_run else "Deleted"
        self.stdout.write(
            self.style.SUCCESS(f"\\n{action} {total_deleted} duplicate contacts")
        )

    def safe_delete_contact(self, contact):
        """Safely delete a contact without triggering database issues"""
        # Just delete the contact - let Django handle cascading
        contact.delete()


if __name__ == "__main__":
    import django
    import os

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mobilize.settings")
    django.setup()
