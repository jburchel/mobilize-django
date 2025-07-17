"""
Interactive duplicate review command

This command helps you manually review and merge duplicate contacts
by presenting them in an organized way with merge recommendations.
"""

from django.core.management.base import BaseCommand
from django.db.models import Count
from mobilize.contacts.models import Contact


class Command(BaseCommand):
    help = "Interactive review of duplicate contacts"

    def add_arguments(self, parser):
        parser.add_argument(
            "--type",
            choices=["email", "name", "church"],
            default="name",
            help="Type of duplicates to review (default: name)",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=10,
            help="Number of duplicate groups to show (default: 10)",
        )
        parser.add_argument(
            "--auto-merge-obvious",
            action="store_true",
            help="Automatically merge obvious duplicates (one with data, one empty)",
        )

    def handle(self, *args, **options):
        duplicate_type = options["type"]
        limit = options["limit"]
        auto_merge = options["auto_merge_obvious"]

        if duplicate_type == "email":
            self.review_email_duplicates(limit, auto_merge)
        elif duplicate_type == "name":
            self.review_name_duplicates(limit, auto_merge)
        elif duplicate_type == "church":
            self.review_church_duplicates(limit, auto_merge)

    def review_email_duplicates(self, limit, auto_merge):
        """Review email duplicates"""
        self.stdout.write("=== EMAIL DUPLICATES REVIEW ===")

        email_duplicates = (
            Contact.objects.values("email")
            .annotate(count=Count("id"))
            .filter(count__gt=1, email__isnull=False)
            .exclude(email="")
        )

        for i, dup in enumerate(email_duplicates[:limit]):
            email = dup["email"]
            contacts = list(Contact.objects.filter(email=email).order_by("id"))

            self.stdout.write(
                f"\n--- Email Duplicate {i+1}/{min(limit, email_duplicates.count())} ---"
            )
            self.stdout.write(f"Email: {email}")

            for j, contact in enumerate(contacts):
                self.stdout.write(f"  {j+1}. ID {contact.id}: {contact}")
                self.stdout.write(f"     Type: {contact.type}")
                self.stdout.write(f"     Office: {contact.office}")
                self.stdout.write(f'     Phone: {contact.phone or "None"}')
                self.stdout.write(f'     Created: {contact.created_at or "Unknown"}')

            # Check if it's an obvious merge case
            if self.is_obvious_email_duplicate(contacts):
                self.stdout.write(
                    self.style.SUCCESS(
                        "     → OBVIOUS DUPLICATE (same email, similar data)"
                    )
                )
                if auto_merge:
                    self.auto_merge_contacts(contacts, f"email: {email}")
                else:
                    self.suggest_merge(contacts)
            else:
                self.stdout.write(self.style.WARNING("     → NEEDS MANUAL REVIEW"))

    def review_name_duplicates(self, limit, auto_merge):
        """Review name duplicates"""
        self.stdout.write("=== NAME DUPLICATES REVIEW ===")

        name_duplicates = (
            Contact.objects.filter(type="person")
            .values("first_name", "last_name")
            .annotate(count=Count("id"))
            .filter(count__gt=1, first_name__isnull=False, last_name__isnull=False)
            .exclude(first_name="")
            .exclude(last_name="")
        )

        for i, dup in enumerate(name_duplicates[:limit]):
            first, last = dup["first_name"], dup["last_name"]
            contacts = list(
                Contact.objects.filter(
                    type="person", first_name=first, last_name=last
                ).order_by("id")
            )

            self.stdout.write(
                f"\n--- Name Duplicate {i+1}/{min(limit, name_duplicates.count())} ---"
            )
            self.stdout.write(f"Name: {first} {last}")

            for j, contact in enumerate(contacts):
                self.stdout.write(f"  {j+1}. ID {contact.id}: {contact}")
                self.stdout.write(f'     Email: {contact.email or "None"}')
                self.stdout.write(f'     Phone: {contact.phone or "None"}')
                self.stdout.write(f"     Office: {contact.office}")
                self.stdout.write(
                    f'     Notes: {(contact.notes or "None")[:50]}{"..." if contact.notes and len(contact.notes) > 50 else ""}'
                )

            # Check if it's an obvious merge case
            recommendation = self.analyze_name_duplicates(contacts)
            if recommendation["obvious"]:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'     → OBVIOUS DUPLICATE: {recommendation["reason"]}'
                    )
                )
                if auto_merge:
                    self.auto_merge_contacts(contacts, f"name: {first} {last}")
                else:
                    self.suggest_merge(contacts, recommendation["keep_id"])
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f'     → NEEDS MANUAL REVIEW: {recommendation["reason"]}'
                    )
                )

    def review_church_duplicates(self, limit, auto_merge):
        """Review church duplicates"""
        self.stdout.write("=== CHURCH DUPLICATES REVIEW ===")

        church_duplicates = (
            Contact.objects.filter(type="church")
            .values("church_name")
            .annotate(count=Count("id"))
            .filter(count__gt=1, church_name__isnull=False)
            .exclude(church_name="")
        )

        for i, dup in enumerate(church_duplicates[:limit]):
            church_name = dup["church_name"]
            contacts = list(
                Contact.objects.filter(type="church", church_name=church_name).order_by(
                    "id"
                )
            )

            self.stdout.write(
                f"\n--- Church Duplicate {i+1}/{min(limit, church_duplicates.count())} ---"
            )
            self.stdout.write(f"Church: {church_name}")

            for j, contact in enumerate(contacts):
                self.stdout.write(f"  {j+1}. ID {contact.id}: {contact}")
                self.stdout.write(f'     Email: {contact.email or "None"}')
                self.stdout.write(f'     Phone: {contact.phone or "None"}')
                self.stdout.write(f'     Office: {contact.office or "None"}')
                self.stdout.write(
                    f'     Address: {contact.city or "None"}, {contact.state or "None"}'
                )

            # Check if it's an obvious merge case
            recommendation = self.analyze_church_duplicates(contacts)
            if recommendation["obvious"]:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'     → OBVIOUS DUPLICATE: {recommendation["reason"]}'
                    )
                )
                if auto_merge:
                    self.auto_merge_contacts(contacts, f"church: {church_name}")
                else:
                    self.suggest_merge(contacts, recommendation["keep_id"])
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f'     → NEEDS MANUAL REVIEW: {recommendation["reason"]}'
                    )
                )

    def is_obvious_email_duplicate(self, contacts):
        """Check if email duplicates are obvious (same person/organization)"""
        if len(contacts) != 2:
            return False

        # Same email means likely same entity
        return True

    def analyze_name_duplicates(self, contacts):
        """Analyze name duplicates and provide recommendation"""
        if len(contacts) != 2:
            return {"obvious": False, "reason": "More than 2 contacts with same name"}

        contact1, contact2 = contacts

        # Case 1: One has email, one doesn't (obvious duplicate)
        if contact1.email and not contact2.email:
            return {
                "obvious": True,
                "reason": "One has email, one is empty",
                "keep_id": contact1.id,
            }
        elif contact2.email and not contact1.email:
            return {
                "obvious": True,
                "reason": "One has email, one is empty",
                "keep_id": contact2.id,
            }

        # Case 2: Both have different emails (likely different people)
        elif contact1.email and contact2.email and contact1.email != contact2.email:
            return {
                "obvious": False,
                "reason": "Different emails - likely different people",
            }

        # Case 3: Neither has email (need more investigation)
        elif not contact1.email and not contact2.email:
            return {
                "obvious": False,
                "reason": "Both lack email - need more info to decide",
            }

        # Case 4: Same email (obvious duplicate)
        else:
            return {
                "obvious": True,
                "reason": "Same email address",
                "keep_id": contact1.id,  # Keep older one
            }

    def analyze_church_duplicates(self, contacts):
        """Analyze church duplicates and provide recommendation"""
        if len(contacts) != 2:
            return {"obvious": False, "reason": "More than 2 contacts with same name"}

        contact1, contact2 = contacts

        # Case 1: One in US office, one with no office (likely duplicate from migration)
        if contact1.office and contact1.office.name == "US" and not contact2.office:
            return {
                "obvious": True,
                "reason": "One in US office, one unassigned",
                "keep_id": contact1.id,
            }
        elif contact2.office and contact2.office.name == "US" and not contact1.office:
            return {
                "obvious": True,
                "reason": "One in US office, one unassigned",
                "keep_id": contact2.id,
            }

        # Case 2: Different offices (likely different locations)
        elif (
            contact1.office
            and contact2.office
            and contact1.office.name != contact2.office.name
        ):
            return {
                "obvious": False,
                "reason": "Different offices - might be different locations",
            }

        # Case 3: One has more data than the other
        elif self.has_more_data(contact1, contact2):
            return {
                "obvious": True,
                "reason": "One has more complete data",
                "keep_id": contact1.id,
            }
        elif self.has_more_data(contact2, contact1):
            return {
                "obvious": True,
                "reason": "One has more complete data",
                "keep_id": contact2.id,
            }

        return {"obvious": False, "reason": "Need manual review"}

    def has_more_data(self, contact1, contact2):
        """Check if contact1 has more data than contact2"""
        contact1_data = sum(
            [
                1 if contact1.email else 0,
                1 if contact1.phone else 0,
                1 if contact1.street_address else 0,
                1 if contact1.notes else 0,
            ]
        )

        contact2_data = sum(
            [
                1 if contact2.email else 0,
                1 if contact2.phone else 0,
                1 if contact2.street_address else 0,
                1 if contact2.notes else 0,
            ]
        )

        return contact1_data > contact2_data

    def suggest_merge(self, contacts, keep_id=None):
        """Suggest merge command for manual execution"""
        contact_ids = [str(c.id) for c in contacts]
        keep_id = keep_id or contacts[0].id

        merge_command = f'python manage.py merge_duplicates --merge-contact-ids="{",".join(contact_ids)}" --keep-contact-id={keep_id}'
        self.stdout.write(f"     💡 SUGGESTED MERGE: {merge_command}")

    def auto_merge_contacts(self, contacts, reason):
        """Automatically merge obvious duplicates"""
        if len(contacts) < 2:
            return

        from django.core.management import call_command
        from io import StringIO

        contact_ids = [str(c.id) for c in contacts]
        keep_id = contacts[0].id

        try:
            # Capture the output of the merge command
            out = StringIO()
            call_command(
                "merge_duplicates",
                merge_contact_ids=",".join(contact_ids),
                keep_contact_id=keep_id,
                stdout=out,
            )
            self.stdout.write(f"     ✅ AUTO-MERGED: Kept ID {keep_id}")
        except Exception as e:
            self.stdout.write(f"     ❌ AUTO-MERGE FAILED: {e}")
            self.suggest_merge(contacts, keep_id)
