from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from mobilize.communications.gmail_service import GmailService
from mobilize.communications.models import Communication
from datetime import datetime, timedelta
import time

User = get_user_model()


class Command(BaseCommand):
    help = "Multi-year historical Gmail sync using date-chunked queries for maximum coverage"

    def add_arguments(self, parser):
        parser.add_argument(
            "--user-id", type=int, help="Sync emails for specific user ID only"
        )
        parser.add_argument(
            "--years-back",
            type=int,
            default=3,
            help="Number of years back to sync (default: 3)",
        )
        parser.add_argument(
            "--chunk-months",
            type=int,
            default=3,
            help="Number of months per query chunk (default: 3)",
        )
        parser.add_argument(
            "--max-per-chunk",
            type=int,
            default=500,
            help="Maximum emails per chunk query (default: 500)",
        )
        parser.add_argument(
            "--delay",
            type=float,
            default=0.5,
            help="Delay between chunks in seconds (default: 0.5)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be synced without actually syncing",
        )
        parser.add_argument(
            "--start-date",
            type=str,
            help="Start date in YYYY-MM-DD format (overrides --years-back)",
        )

    def handle(self, *args, **options):
        user_id = options.get("user_id")
        years_back = options["years_back"]
        chunk_months = options["chunk_months"]
        max_per_chunk = options["max_per_chunk"]
        delay = options["delay"]
        dry_run = options["dry_run"]
        start_date_str = options.get("start_date")

        # Calculate date range
        end_date = datetime.now()
        if start_date_str:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
        else:
            start_date = end_date - timedelta(days=years_back * 365)

        self.stdout.write(
            self.style.SUCCESS(
                f'{"[DRY RUN] " if dry_run else ""}Multi-year Gmail historical sync'
            )
        )
        self.stdout.write(
            f'Date range: {start_date.strftime("%Y-%m-%d")} to {end_date.strftime("%Y-%m-%d")}'
        )
        self.stdout.write(
            f"Chunk size: {chunk_months} months, Max per chunk: {max_per_chunk}"
        )

        # Get user
        if user_id:
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"User with ID {user_id} not found"))
                return
        else:
            # Get authenticated Gmail users
            try:
                from mobilize.authentication.models import GoogleToken

                user_ids_with_tokens = GoogleToken.objects.filter(
                    access_token__isnull=False
                ).values_list("user_id", flat=True)
                users = User.objects.filter(id__in=user_ids_with_tokens)
                if users.count() == 1:
                    user = users.first()
                else:
                    self.stdout.write(
                        self.style.ERROR(
                            "Multiple users found. Please specify --user-id"
                        )
                    )
                    return
            except Exception:
                self.stdout.write(
                    self.style.ERROR("Could not find Gmail authenticated user")
                )
                return

        self.stdout.write(f"Processing user: {user.username} ({user.id})")

        # Check Gmail authentication
        gmail_service = GmailService(user)
        if not gmail_service.is_authenticated():
            self.stdout.write(
                self.style.ERROR(f"User {user.username} - Gmail not authenticated")
            )
            return

        if dry_run:
            self.stdout.write(
                self.style.SUCCESS("User ready for multi-year historical sync")
            )
            return

        # Get known contacts
        known_emails = self.get_known_contact_emails()
        self.stdout.write(f"Found {len(known_emails)} known contact emails")

        # Get existing synced message IDs
        existing_message_ids = set(
            Communication.objects.filter(
                user=user, gmail_message_id__isnull=False
            ).values_list("gmail_message_id", flat=True)
        )
        self.stdout.write(f"Found {len(existing_message_ids)} already synced emails")

        # Process in date chunks
        total_synced = self.sync_date_chunks(
            gmail_service,
            user,
            known_emails,
            existing_message_ids,
            start_date,
            end_date,
            chunk_months,
            max_per_chunk,
            delay,
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Multi-year historical sync completed: {total_synced} emails synced"
            )
        )

    def get_known_contact_emails(self):
        """Get all known contact emails"""
        from mobilize.contacts.models import Person
        from mobilize.churches.models import Church

        known_emails = set()

        # Person emails
        person_emails = (
            Person.objects.filter(contact__email__isnull=False)
            .exclude(contact__email="")
            .values_list("contact__email", flat=True)
        )
        known_emails.update(person_emails)

        # Church emails
        church_emails = (
            Church.objects.filter(contact__email__isnull=False)
            .exclude(contact__email="")
            .values_list("contact__email", flat=True)
        )
        known_emails.update(church_emails)

        return known_emails

    def sync_date_chunks(
        self,
        gmail_service,
        user,
        known_emails,
        existing_message_ids,
        start_date,
        end_date,
        chunk_months,
        max_per_chunk,
        delay,
    ):
        """Sync emails in date chunks"""
        total_synced = 0
        current_date = start_date
        chunk_num = 1

        while current_date < end_date:
            # Calculate chunk end date
            chunk_end = min(current_date + timedelta(days=chunk_months * 30), end_date)

            self.stdout.write(
                f'\n--- Chunk {chunk_num}: {current_date.strftime("%Y-%m-%d")} to {chunk_end.strftime("%Y-%m-%d")} ---'
            )

            chunk_synced = self.sync_date_range(
                gmail_service,
                user,
                known_emails,
                existing_message_ids,
                current_date,
                chunk_end,
                max_per_chunk,
            )

            total_synced += chunk_synced
            self.stdout.write(
                f"Chunk {chunk_num} synced: {chunk_synced} emails (total: {total_synced})"
            )

            # Rate limiting delay
            if delay > 0:
                time.sleep(delay)

            current_date = chunk_end
            chunk_num += 1

        return total_synced

    def sync_date_range(
        self,
        gmail_service,
        user,
        known_emails,
        existing_message_ids,
        start_date,
        end_date,
        max_per_chunk,
    ):
        """Sync emails for a specific date range"""
        from django.utils import timezone
        import re

        synced_count = 0

        # Format dates for Gmail query
        start_str = start_date.strftime("%Y/%m/%d")
        end_str = end_date.strftime("%Y/%m/%d")

        # Query both inbox and sent for this date range
        for folder in ["inbox", "sent"]:
            try:
                query = f"in:{folder} after:{start_str} before:{end_str}"
                messages = gmail_service.get_messages(
                    query=query, max_results=max_per_chunk
                )

                self.stdout.write(f"  {folder}: Found {len(messages)} messages")

                for message in messages:
                    # Skip if already synced
                    if message["id"] in existing_message_ids:
                        continue

                    # Check if should sync this message
                    if self.should_sync_message(message, user, known_emails):
                        if self.sync_single_message(
                            gmail_service, user, message, known_emails
                        ):
                            synced_count += 1
                            existing_message_ids.add(
                                message["id"]
                            )  # Track to avoid duplicates

            except Exception as e:
                self.stdout.write(f"  Error processing {folder} for date range: {e}")
                continue

        return synced_count

    def should_sync_message(self, message, user, known_emails):
        """Check if message should be synced"""
        import re

        # Extract sender email
        sender_full = message.get("sender", "")
        sender_match = re.search(r"<([^>]+)>", sender_full)
        if sender_match:
            sender_email = sender_match.group(1).lower().strip()
        else:
            sender_email = sender_full.lower().strip()

        # Check if sent email
        is_sent_email = sender_email == user.email.lower().strip()

        if is_sent_email:
            # For sent emails, check if any recipient is a known contact
            to_field = message.get("to", "")
            recipients = [
                email.strip() for email in to_field.split(",") if email.strip()
            ]

            for recipient_email in recipients:
                email_match = re.search(r"<([^>]+)>", recipient_email)
                if email_match:
                    recipient_email = email_match.group(1)
                recipient_email = recipient_email.lower().strip()

                if recipient_email in known_emails:
                    return True
            return False
        else:
            # For received emails, check if sender is known contact
            return sender_email in known_emails

    def sync_single_message(self, gmail_service, user, message, known_emails):
        """Sync a single message"""
        import re
        from django.utils import timezone

        try:
            # Extract sender email
            sender_full = message.get("sender", "")
            sender_match = re.search(r"<([^>]+)>", sender_full)
            if sender_match:
                sender_email = sender_match.group(1).lower().strip()
            else:
                sender_email = sender_full.lower().strip()

            # Check if sent email
            is_sent_email = sender_email == user.email.lower().strip()

            person = None
            church = None
            direction = "inbound"

            if is_sent_email:
                # Find recipient contact
                to_field = message.get("to", "")
                recipients = [
                    email.strip() for email in to_field.split(",") if email.strip()
                ]

                for recipient_email in recipients:
                    email_match = re.search(r"<([^>]+)>", recipient_email)
                    if email_match:
                        recipient_email = email_match.group(1)
                    recipient_email = recipient_email.lower().strip()

                    if recipient_email in known_emails:
                        person = gmail_service._find_person_by_email(recipient_email)
                        church = gmail_service._find_church_by_email(recipient_email)
                        if person or church:
                            direction = "outbound"
                            break

                if not person and not church:
                    return False
            else:
                # Find sender contact
                person = gmail_service._find_person_by_email(sender_email)
                church = gmail_service._find_church_by_email(sender_email)

                if not person and not church:
                    return False

            # Create communication record
            person_id = person.pk if person else None

            Communication.objects.create(
                type="email",
                subject=(message.get("subject") or "")[:200],
                message=(message.get("body") or message.get("snippet", ""))[:250],
                direction=direction,
                date=timezone.now().date(),  # Using current date as Gmail doesn't give parsed dates
                person_id=person_id,
                church=church,
                gmail_message_id=message["id"],
                gmail_thread_id=message.get("thread_id", ""),
                email_status="sent" if is_sent_email else "received",
                sender=(message.get("sender") or "")[:200],
                user=user,
            )

            return True

        except Exception as e:
            print(f"Error syncing message {message.get('id', 'unknown')}: {e}")
            return False
