"""
Management command to fix communication dates by re-fetching actual dates from Gmail.

This command will:
1. Find all communications with Gmail message IDs but incorrect dates
2. Re-fetch the actual email dates from Gmail API
3. Update the date and date_sent fields with correct values
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from mobilize.communications.models import Communication
from mobilize.communications.gmail_service import GmailService
from email.utils import parsedate_to_datetime

User = get_user_model()


class Command(BaseCommand):
    help = "Fix communication dates by re-fetching actual dates from Gmail"

    def add_arguments(self, parser):
        parser.add_argument(
            "--user-email",
            type=str,
            help="Email of user to fix communications for (if not provided, will fix for all users)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be updated without making changes",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=100,
            help="Maximum number of communications to process (default: 100)",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        user_email = options["user_email"]
        limit = options["limit"]

        if dry_run:
            self.stdout.write(
                self.style.WARNING("DRY RUN MODE - No changes will be made")
            )

        # Get users to process
        if user_email:
            try:
                users = [User.objects.get(email=user_email)]
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f"User with email {user_email} not found")
                )
                return
        else:
            # Get all users who have communications with Gmail message IDs
            user_ids = (
                Communication.objects.filter(gmail_message_id__isnull=False)
                .exclude(gmail_message_id="")
                .values_list("user_id", flat=True)
                .distinct()
            )
            users = User.objects.filter(id__in=user_ids)

        self.stdout.write(f"Processing {users.count()} users...")

        total_updated = 0
        total_processed = 0
        total_errors = 0

        for user in users:
            self.stdout.write(f"\nProcessing user: {user.email}")

            # Get communications that need fixing for this user
            # Look for communications where date_sent matches created_at (indicating sync time was used)
            # or where date_sent is null, or where date_sent is from July 11, 2025 (the sync date)
            from django.db.models import Q
            from datetime import date

            sync_date = date(2025, 7, 11)  # The date when the major sync happened

            communications = (
                Communication.objects.filter(user=user, gmail_message_id__isnull=False)
                .exclude(gmail_message_id="")
                .filter(
                    Q(date_sent__isnull=True)
                    | Q(date_sent__date=sync_date)  # Missing date_sent
                    | Q(  # Set to sync date
                        date__gte=sync_date, date_sent__date__gte=sync_date
                    )  # Both date and date_sent are recent (likely sync artifacts)
                )[:limit]
            )

            if not communications:
                self.stdout.write("  No communications to fix for this user")
                continue

            self.stdout.write(f"  Found {communications.count()} communications to fix")

            # Initialize Gmail service for this user
            gmail_service = GmailService(user)
            if not gmail_service.service:
                self.stdout.write(
                    self.style.WARNING(
                        f"  Gmail not authenticated for {user.email}, skipping"
                    )
                )
                continue

            updated_count = 0
            error_count = 0

            for comm in communications:
                try:
                    # Fetch the message from Gmail to get the actual date
                    message_detail = (
                        gmail_service.service.users()
                        .messages()
                        .get(userId="me", id=comm.gmail_message_id)
                        .execute()
                    )

                    # Parse the message to get the date
                    parsed_message = gmail_service._parse_message(message_detail)
                    email_date_str = parsed_message.get("date", "")

                    if email_date_str:
                        try:
                            # Parse the email date
                            email_datetime = parsedate_to_datetime(email_date_str)
                            email_date = email_datetime.date()

                            if not dry_run:
                                # Update the communication
                                comm.date = email_date
                                comm.date_sent = email_datetime
                                comm.save(update_fields=["date", "date_sent"])

                            self.stdout.write(
                                f"    ✓ {comm.subject[:50]}... | "
                                f"Old: {comm.date} | New: {email_date} ({email_datetime})"
                            )
                            updated_count += 1

                        except Exception as e:
                            self.stdout.write(
                                self.style.WARNING(
                                    f'    ✗ Error parsing date "{email_date_str}": {e}'
                                )
                            )
                            error_count += 1
                    else:
                        self.stdout.write(
                            self.style.WARNING(
                                f"    ✗ No date found for: {comm.subject[:50]}..."
                            )
                        )
                        error_count += 1

                    total_processed += 1

                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(
                            f"    ✗ Error fetching message {comm.gmail_message_id}: {e}"
                        )
                    )
                    error_count += 1
                    total_processed += 1

            self.stdout.write(
                f"  User {user.email}: Updated {updated_count}, Errors {error_count}"
            )
            total_updated += updated_count
            total_errors += error_count

        self.stdout.write(
            self.style.SUCCESS(
                f"\n✅ Complete! Processed {total_processed} communications. "
                f"Updated {total_updated}, Errors {total_errors}"
            )
        )

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    "This was a dry run. Use without --dry-run to apply changes."
                )
            )
