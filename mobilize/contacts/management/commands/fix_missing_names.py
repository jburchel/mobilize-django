"""
Management command to fix people with missing names.

This command identifies and fixes Contact records with empty first_name and last_name,
which cause "No name listed" or "Person {id}" display issues.
"""

from django.core.management.base import BaseCommand
from django.db import models, transaction
from mobilize.contacts.models import Contact, Person


class Command(BaseCommand):
    help = (
        "Fix people with missing names by prompting for names or removing empty records"
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--auto-fix",
            action="store_true",
            help='Automatically set missing names to "Unknown" instead of prompting',
        )
        parser.add_argument(
            "--delete-empty",
            action="store_true",
            help="Delete contacts with no name and no other identifying information",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be changed without making actual changes",
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS("=== Fixing People with Missing Names ===")
        )

        # Find contacts with empty names
        empty_names = Contact.objects.filter(
            models.Q(first_name__isnull=True)
            | models.Q(first_name="")
            | models.Q(last_name__isnull=True)
            | models.Q(last_name="")
        ).filter(type="person")

        total_found = empty_names.count()
        self.stdout.write(f"Found {total_found} people with missing names")

        if total_found == 0:
            self.stdout.write(self.style.SUCCESS("No people with missing names found!"))
            return

        if options["dry_run"]:
            self.stdout.write(
                self.style.WARNING("DRY RUN MODE - No changes will be made")
            )

        fixed_count = 0
        deleted_count = 0

        for contact in empty_names:
            try:
                person = Person.objects.get(contact=contact)

                # Show current status
                self.stdout.write(f"\n--- Contact ID: {contact.id} ---")
                self.stdout.write(
                    f'Current first_name: "{contact.first_name or "NULL"}"'
                )
                self.stdout.write(f'Current last_name: "{contact.last_name or "NULL"}"')
                self.stdout.write(f'Email: "{contact.email or "None"}"')
                self.stdout.write(f'Phone: "{contact.phone or "None"}"')
                self.stdout.write(f'Person display: "{str(person)}"')

                # Determine what to do
                should_delete = False
                new_first_name = contact.first_name or ""
                new_last_name = contact.last_name or ""

                if options["delete_empty"]:
                    # Delete if no identifying information
                    if (
                        not contact.email
                        and not contact.phone
                        and not contact.street_address
                    ):
                        should_delete = True
                        self.stdout.write(
                            self.style.WARNING(
                                f"Will DELETE Contact {contact.id} - no name, email, phone, or address"
                            )
                        )

                if not should_delete:
                    if options["auto_fix"]:
                        # Auto-fix mode
                        if not new_first_name and not new_last_name:
                            if contact.email:
                                # Try to extract name from email
                                email_prefix = contact.email.split("@")[0]
                                if "." in email_prefix:
                                    parts = email_prefix.split(".")
                                    new_first_name = parts[0].capitalize()
                                    new_last_name = parts[1].capitalize()
                                else:
                                    new_first_name = email_prefix.capitalize()
                            else:
                                new_first_name = "Unknown"

                        self.stdout.write(
                            self.style.SUCCESS(
                                f'Will UPDATE Contact {contact.id}: "{new_first_name}" "{new_last_name}"'
                            )
                        )
                    else:
                        # Interactive mode
                        if not options["dry_run"]:
                            self.stdout.write("What would you like to do?")
                            self.stdout.write("1. Enter a name")
                            self.stdout.write('2. Set to "Unknown"')
                            self.stdout.write("3. Delete this contact")
                            self.stdout.write("4. Skip")

                            choice = input("Choice (1-4): ").strip()

                            if choice == "1":
                                new_first_name = input("First name: ").strip()
                                new_last_name = input("Last name: ").strip()
                                if not new_first_name and not new_last_name:
                                    new_first_name = "Unknown"
                            elif choice == "2":
                                new_first_name = "Unknown"
                                new_last_name = ""
                            elif choice == "3":
                                should_delete = True
                            else:
                                continue

                # Apply the changes
                if not options["dry_run"]:
                    with transaction.atomic():
                        if should_delete:
                            person.delete()  # This will also delete the contact due to CASCADE
                            deleted_count += 1
                            self.stdout.write(
                                self.style.ERROR(f"DELETED Contact {contact.id}")
                            )
                        else:
                            contact.first_name = new_first_name
                            contact.last_name = new_last_name
                            contact.save(update_fields=["first_name", "last_name"])
                            fixed_count += 1
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f'UPDATED Contact {contact.id}: "{new_first_name}" "{new_last_name}"'
                                )
                            )
                else:
                    if should_delete:
                        self.stdout.write(
                            self.style.ERROR(f"WOULD DELETE Contact {contact.id}")
                        )
                        deleted_count += 1
                    else:
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'WOULD UPDATE Contact {contact.id}: "{new_first_name}" "{new_last_name}"'
                            )
                        )
                        fixed_count += 1

            except Person.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(
                        f"Contact {contact.id} has no corresponding Person record - skipping"
                    )
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Error processing Contact {contact.id}: {e}")
                )

        # Summary
        self.stdout.write(f"\n=== SUMMARY ===")
        if options["dry_run"]:
            self.stdout.write(f"WOULD FIX: {fixed_count} contacts")
            self.stdout.write(f"WOULD DELETE: {deleted_count} contacts")
            self.stdout.write("Run without --dry-run to apply changes")
        else:
            self.stdout.write(f"FIXED: {fixed_count} contacts")
            self.stdout.write(f"DELETED: {deleted_count} contacts")
            self.stdout.write(self.style.SUCCESS("Data cleanup completed!"))
