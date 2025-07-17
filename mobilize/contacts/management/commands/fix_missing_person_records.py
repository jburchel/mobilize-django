from django.core.management.base import BaseCommand
from django.db import transaction
from mobilize.contacts.models import Contact, Person


class Command(BaseCommand):
    help = 'Creates missing Person records for contacts with type="person"'

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be created without actually creating records",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]

        # Find contacts of type 'person' without Person records
        contacts_without_person = Contact.objects.filter(type="person").exclude(
            id__in=Person.objects.values_list("contact_id", flat=True)
        )

        total_count = contacts_without_person.count()
        self.stdout.write(f"Found {total_count} contacts without Person records")

        if total_count == 0:
            self.stdout.write(
                self.style.SUCCESS("All person contacts have Person records!")
            )
            return

        if dry_run:
            self.stdout.write(
                self.style.WARNING("DRY RUN - No records will be created")
            )
            for contact in contacts_without_person[:20]:  # Show first 20
                self.stdout.write(
                    f"  Would create Person for: {contact.first_name} {contact.last_name} ({contact.email})"
                )
            if total_count > 20:
                self.stdout.write(f"  ... and {total_count - 20} more")
            return

        created_count = 0
        errors = []

        with transaction.atomic():
            for contact in contacts_without_person:
                try:
                    person = Person.objects.create(contact=contact)
                    created_count += 1
                    self.stdout.write(
                        f"Created Person for: {contact.first_name} {contact.last_name} ({contact.email})"
                    )
                except Exception as e:
                    error_msg = f"Error creating Person for contact {contact.id} ({contact.email}): {e}"
                    errors.append(error_msg)
                    self.stdout.write(self.style.ERROR(error_msg))

        self.stdout.write(
            self.style.SUCCESS(f"\nSuccessfully created {created_count} Person records")
        )

        if errors:
            self.stdout.write(self.style.ERROR(f"Encountered {len(errors)} errors"))
