from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from mobilize.communications.gmail_service import GmailService
from mobilize.communications.models import Communication
import time
import logging

User = get_user_model()


class Command(BaseCommand):
    help = "One-time comprehensive Gmail sync of ALL historical emails to/from contacts in the app"

    def add_arguments(self, parser):
        parser.add_argument(
            "--user-id", type=int, help="Sync emails for specific user ID only"
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=100,
            help="Number of emails to process per batch (default: 100)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be synced without actually syncing",
        )
        parser.add_argument(
            "--max-results",
            type=int,
            default=2000,
            help="Maximum number of emails to fetch per query (default: 2000)",
        )
        parser.add_argument(
            "--delay",
            type=float,
            default=0.1,
            help="Delay in seconds between API calls to avoid rate limiting (default: 0.1)",
        )

    def handle(self, *args, **options):
        user_id = options.get("user_id")
        batch_size = options["batch_size"]
        dry_run = options["dry_run"]
        max_results = options["max_results"]
        delay = options["delay"]

        # Setup logging
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger(__name__)

        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    "[DRY RUN] Gmail comprehensive historical sync (contacts only)"
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    "Starting Gmail comprehensive historical sync (contacts only)..."
                )
            )
            self.stdout.write(
                self.style.WARNING("This may take a while for large email histories...")
            )

        # Get users to sync
        if user_id:
            users = User.objects.filter(id=user_id)
        else:
            # Get all users who have Gmail tokens
            try:
                from mobilize.authentication.models import GoogleToken

                user_ids_with_tokens = GoogleToken.objects.filter(
                    access_token__isnull=False
                ).values_list("user_id", flat=True)
                users = User.objects.filter(id__in=user_ids_with_tokens)
            except Exception:
                users = User.objects.filter(is_active=True)

        total_synced = 0
        users_processed = 0

        for user in users:
            try:
                self.stdout.write(
                    f"\n--- Processing user: {user.username} ({user.id}) ---"
                )

                gmail_service = GmailService(user)

                if not gmail_service.is_authenticated():
                    self.stdout.write(
                        self.style.WARNING(
                            f"User {user.username} - Gmail not authenticated, skipping"
                        )
                    )
                    continue

                if dry_run:
                    # For dry run, estimate emails to sync
                    self.stdout.write(
                        f"User {user.username} - Ready for full historical sync"
                    )
                    users_processed += 1
                    continue

                # Get existing synced message IDs to avoid duplicates
                existing_message_ids = set(
                    Communication.objects.filter(
                        user=user, gmail_message_id__isnull=False
                    ).values_list("gmail_message_id", flat=True)
                )

                self.stdout.write(
                    f"Found {len(existing_message_ids)} already synced emails for this user"
                )

                # Sync comprehensive email history
                user_synced = self.sync_user_full_history(
                    gmail_service,
                    user,
                    existing_message_ids,
                    batch_size,
                    max_results,
                    delay,
                )

                total_synced += user_synced
                users_processed += 1

                self.stdout.write(
                    self.style.SUCCESS(
                        f"User {user.username} - Synced {user_synced} new emails"
                    )
                )

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"User {user.username} - Error: {str(e)}")
                )
                logger.exception(f"Error syncing user {user.username}")

        # Summary
        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f"\n[DRY RUN] {users_processed} users ready for comprehensive Gmail sync"
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"\nComprehensive Gmail sync completed: {total_synced} emails synced for {users_processed} users"
                )
            )

    def sync_user_full_history(
        self, gmail_service, user, existing_message_ids, batch_size, max_results, delay
    ):
        """Sync all historical emails for a user with known contacts"""
        from datetime import datetime, timedelta
        from mobilize.contacts.models import Person
        from mobilize.churches.models import Church

        synced_count = 0

        # Get all known contact emails
        known_emails = set()
        try:
            person_emails = (
                Person.objects.filter(contact__email__isnull=False)
                .exclude(contact__email="")
                .values_list("contact__email", flat=True)
            )
            known_emails.update(person_emails)

            church_emails = (
                Church.objects.filter(contact__email__isnull=False)
                .exclude(contact__email="")
                .values_list("contact__email", flat=True)
            )
            known_emails.update(church_emails)

            self.stdout.write(f"Found {len(known_emails)} known contact emails")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error getting known emails: {e}"))
            return 0

        # Process in batches for memory efficiency
        processed_emails = 0

        # Get all emails (no date restriction for full history)
        for folder in ["inbox", "sent"]:
            self.stdout.write(f"Processing {folder} folder...")

            try:
                # Query with larger result set for historical sync
                query = f"in:{folder}"

                # Get messages in batches with error handling
                try:
                    all_messages = gmail_service.get_messages(
                        query=query, max_results=max_results
                    )
                    self.stdout.write(f"Found {len(all_messages)} messages in {folder}")

                    # Process in smaller batches to avoid memory issues
                    for i in range(0, len(all_messages), batch_size):
                        batch = all_messages[i : i + batch_size]
                        try:
                            batch_synced = self.process_message_batch(
                                gmail_service,
                                user,
                                batch,
                                known_emails,
                                existing_message_ids,
                                folder,
                            )
                            synced_count += batch_synced
                            processed_emails += len(batch)

                            self.stdout.write(
                                f"  Processed {processed_emails}/{len(all_messages)} messages, "
                                f"synced {synced_count} total"
                            )
                        except Exception as batch_error:
                            self.stdout.write(
                                f"  Error processing batch {i//batch_size + 1}: {batch_error}"
                            )
                            processed_emails += len(batch)  # Still count as processed
                            continue

                        # Rate limiting delay
                        if delay > 0:
                            time.sleep(delay)
                except Exception as query_error:
                    self.stdout.write(f"Error querying {folder}: {query_error}")
                    continue

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error processing {folder}: {e}"))
                continue

        return synced_count

    def process_message_batch(
        self, gmail_service, user, messages, known_emails, existing_message_ids, folder
    ):
        """Process a batch of messages"""
        batch_synced = 0

        for message in messages:
            try:
                # Skip if already synced
                if message["id"] in existing_message_ids:
                    continue

                # Check if this email is relevant (to/from known contacts)
                if self.should_sync_message(message, user, known_emails, folder):
                    # Use the existing sync logic
                    if self.sync_single_message(
                        gmail_service, user, message, known_emails
                    ):
                        batch_synced += 1
                        existing_message_ids.add(
                            message["id"]
                        )  # Track to avoid duplicates

            except Exception as e:
                self.stdout.write(
                    f"Error processing message {message.get('id', 'unknown')}: {e}"
                )
                continue

        return batch_synced

    def should_sync_message(self, message, user, known_emails, folder):
        """Check if a message should be synced based on sender/recipients"""
        import re

        sender_full = message.get("sender", "")
        # Parse email from "Name <email>" format
        sender_match = re.search(r"<([^>]+)>", sender_full)
        if sender_match:
            sender_email = sender_match.group(1).lower().strip()
        else:
            sender_email = sender_full.lower().strip()

        # Check if this is a sent email
        is_sent_email = sender_email == user.email.lower().strip()

        if is_sent_email:
            # For sent emails, check if any recipient is a known contact
            to_field = message.get("to", "")
            recipients = [
                email.strip() for email in to_field.split(",") if email.strip()
            ]

            for recipient_email in recipients:
                # Extract email from "Name <email>" format
                email_match = re.search(r"<([^>]+)>", recipient_email)
                if email_match:
                    recipient_email = email_match.group(1)
                recipient_email = recipient_email.lower().strip()

                if recipient_email in known_emails:
                    return True
            return False
        else:
            # For received emails, check if sender is a known contact
            return sender_email in known_emails

    def sync_single_message(self, gmail_service, user, message, known_emails):
        """Sync a single message using the existing logic"""
        import re
        from django.utils import timezone
        from mobilize.communications.models import Communication

        try:
            # Extract sender email for matching
            sender_full = message.get("sender", "")
            sender_match = re.search(r"<([^>]+)>", sender_full)
            if sender_match:
                sender_email = sender_match.group(1).lower().strip()
            else:
                sender_email = sender_full.lower().strip()

            # Check if this is a sent email
            is_sent_email = sender_email == user.email.lower().strip()

            person = None
            church = None
            direction = "inbound"

            if is_sent_email:
                # This is a sent email - find recipient contact
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
                # This is a received email
                person = gmail_service._find_person_by_email(sender_email)
                church = gmail_service._find_church_by_email(sender_email)

                if not person and not church:
                    return False

            # Create the communication record
            person_id = person.pk if person else None

            # Safely get message content
            subject = (message.get("subject") or "")[:200]
            body_text = (message.get("body") or message.get("snippet", ""))[:250]
            sender_text = (message.get("sender") or "")[:200]
            thread_id = message.get("thread_id", "")

            Communication.objects.create(
                type="email",
                subject=subject,
                message=body_text,
                direction=direction,
                date=timezone.now().date(),
                person_id=person_id,
                church=church,
                gmail_message_id=message["id"],
                gmail_thread_id=thread_id,
                email_status="sent" if is_sent_email else "received",
                sender=sender_text,
                user=user,
            )

            return True

        except Exception as e:
            # Log error but don't fail the whole sync
            print(f"Error syncing message {message.get('id', 'unknown')}: {e}")
            return False
