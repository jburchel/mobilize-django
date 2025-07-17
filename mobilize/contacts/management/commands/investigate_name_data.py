"""
Management command to investigate where name data might be stored for people showing as "No name listed".

This command checks for alternative name data sources.
"""

from django.core.management.base import BaseCommand
from django.db import models
from mobilize.contacts.models import Contact, Person


class Command(BaseCommand):
    help = "Investigate name data sources for people with missing names"

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("=== Investigating Name Data Sources ==="))

        # Find contacts with empty names
        empty_name_contacts = Contact.objects.filter(
            models.Q(first_name__isnull=True)
            | models.Q(first_name="")
            | models.Q(last_name__isnull=True)
            | models.Q(last_name="")
        ).filter(type="person")

        total_empty = empty_name_contacts.count()
        self.stdout.write(
            f"Found {total_empty} people with missing names in contacts table"
        )

        if total_empty == 0:
            self.stdout.write(self.style.SUCCESS("No people with missing names found!"))
            return

        # Check for alternative name sources
        recovery_sources = {
            "preferred_name": 0,
            "title": 0,
            "email_prefix": 0,
            "spouse_names": 0,
            "partial_names": 0,
        }

        self.stdout.write("\\nAnalyzing first 20 examples:")
        self.stdout.write("=" * 80)

        for i, contact in enumerate(empty_name_contacts[:20]):
            try:
                person = Person.objects.get(contact=contact)

                self.stdout.write(f"\\n--- Person {i+1}: Contact ID {contact.id} ---")
                self.stdout.write(
                    f'Contact first_name: "{contact.first_name or "EMPTY"}"'
                )
                self.stdout.write(
                    f'Contact last_name: "{contact.last_name or "EMPTY"}"'
                )

                # Check Person table fields for potential name data
                potential_names = []

                if person.preferred_name:
                    potential_names.append(f'preferred_name: "{person.preferred_name}"')
                    recovery_sources["preferred_name"] += 1

                if person.title:
                    potential_names.append(f'title: "{person.title}"')
                    recovery_sources["title"] += 1

                if contact.email:
                    email_prefix = contact.email.split("@")[0]
                    potential_names.append(f'email_prefix: "{email_prefix}"')
                    recovery_sources["email_prefix"] += 1

                if person.spouse_first_name or person.spouse_last_name:
                    spouse_name = f"{person.spouse_first_name or ''} {person.spouse_last_name or ''}".strip()
                    potential_names.append(f'spouse_name: "{spouse_name}"')
                    recovery_sources["spouse_names"] += 1

                # Check if we have partial name data
                if contact.first_name and not contact.last_name:
                    potential_names.append(
                        f'partial: first_name only "{contact.first_name}"'
                    )
                    recovery_sources["partial_names"] += 1
                elif contact.last_name and not contact.first_name:
                    potential_names.append(
                        f'partial: last_name only "{contact.last_name}"'
                    )
                    recovery_sources["partial_names"] += 1

                if potential_names:
                    self.stdout.write("POTENTIAL NAME SOURCES:")
                    for name_source in potential_names:
                        self.stdout.write(f"  - {name_source}")
                else:
                    self.stdout.write("NO ALTERNATIVE NAME SOURCES FOUND")

                # Show other identifying info
                other_info = []
                if contact.email:
                    other_info.append(f"email: {contact.email}")
                if contact.phone:
                    other_info.append(f"phone: {contact.phone}")
                if contact.street_address:
                    other_info.append(f"address: {contact.street_address[:50]}...")

                if other_info:
                    self.stdout.write("OTHER INFO: " + " | ".join(other_info))
                else:
                    self.stdout.write("NO OTHER IDENTIFYING INFO")

            except Person.DoesNotExist:
                self.stdout.write(
                    f"Contact {contact.id} has no corresponding Person record"
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Error processing Contact {contact.id}: {e}")
                )

        # Summary of recovery potential
        self.stdout.write("\\n" + "=" * 80)
        self.stdout.write("RECOVERY POTENTIAL SUMMARY:")
        self.stdout.write(f"Total people with missing names: {total_empty}")
        self.stdout.write(
            f'Could recover from preferred_name: {recovery_sources["preferred_name"]}'
        )
        self.stdout.write(f'Could recover from title: {recovery_sources["title"]}')
        self.stdout.write(
            f'Could recover from email: {recovery_sources["email_prefix"]}'
        )
        self.stdout.write(
            f'Have spouse names (reference): {recovery_sources["spouse_names"]}'
        )
        self.stdout.write(f'Have partial names: {recovery_sources["partial_names"]}')

        # Calculate potential recovery rate
        recoverable = (
            recovery_sources["preferred_name"]
            + recovery_sources["email_prefix"]
            + recovery_sources["partial_names"]
        )
        if total_empty > 0:
            recovery_rate = (recoverable / total_empty) * 100
            self.stdout.write(
                f"\\nPotential recovery rate: {recovery_rate:.1f}% ({recoverable}/{total_empty})"
            )

        # Check if there are any People with preferred_name but empty contact names
        self.stdout.write("\\n" + "=" * 80)
        self.stdout.write("CHECKING FOR PREFERRED_NAME DATA...")

        people_with_preferred = (
            Person.objects.exclude(preferred_name__isnull=True)
            .exclude(preferred_name="")
            .filter(
                models.Q(contact__first_name__isnull=True)
                | models.Q(contact__first_name="")
                | models.Q(contact__last_name__isnull=True)
                | models.Q(contact__last_name="")
            )
        )

        preferred_count = people_with_preferred.count()
        self.stdout.write(
            f"Found {preferred_count} people with preferred_name but missing contact names:"
        )

        for person in people_with_preferred[:10]:
            self.stdout.write(
                f'  Contact {person.contact.id}: preferred_name="{person.preferred_name}"'
            )

        if preferred_count > 10:
            self.stdout.write(f"  ... and {preferred_count - 10} more")

        self.stdout.write("\\n" + self.style.SUCCESS("Investigation complete!"))
