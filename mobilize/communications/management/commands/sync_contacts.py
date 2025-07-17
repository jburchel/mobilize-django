from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from mobilize.communications.google_contacts_service import GoogleContactsService
from mobilize.authentication.models import UserContactSyncSettings

User = get_user_model()


class Command(BaseCommand):
    help = "Sync Google contacts for all users based on their preferences"

    def add_arguments(self, parser):
        parser.add_argument(
            "--user-id", type=int, help="Sync contacts for specific user ID only"
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Force sync even if not scheduled (ignore frequency settings)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be synced without actually syncing",
        )

    def handle(self, *args, **options):
        user_id = options.get("user_id")
        force_sync = options["force"]
        dry_run = options["dry_run"]

        if dry_run:
            self.stdout.write(self.style.SUCCESS("[DRY RUN] Google Contacts sync"))
        else:
            self.stdout.write(self.style.SUCCESS("Starting Google Contacts sync..."))

        # Get users to sync
        if user_id:
            users = User.objects.filter(id=user_id)
        else:
            # Get all users who have contact sync enabled
            sync_settings = UserContactSyncSettings.objects.exclude(
                sync_preference="disabled"
            )

            if not force_sync:
                # Filter to only users who need sync now
                sync_settings = sync_settings.filter(auto_sync_enabled=True)
                user_ids_to_sync = [
                    setting.user_id
                    for setting in sync_settings
                    if setting.should_sync_now()
                ]
            else:
                user_ids_to_sync = [setting.user_id for setting in sync_settings]

            users = User.objects.filter(id__in=user_ids_to_sync)

        total_synced = 0
        users_processed = 0

        for user in users:
            try:
                sync_settings = UserContactSyncSettings.objects.filter(
                    user=user
                ).first()

                if not sync_settings or sync_settings.sync_preference == "disabled":
                    self.stdout.write(
                        self.style.WARNING(
                            f"User {user.username} ({user.id}) - Contact sync disabled"
                        )
                    )
                    continue

                contacts_service = GoogleContactsService(user)

                if not contacts_service.is_authenticated():
                    self.stdout.write(
                        self.style.WARNING(
                            f"User {user.username} ({user.id}) - Google Contacts not authenticated"
                        )
                    )
                    continue

                if dry_run:
                    # For dry run, just check what would be synced
                    if sync_settings.sync_preference == "crm_only":
                        mode = "Update existing CRM contacts only"
                    elif sync_settings.sync_preference == "all_contacts":
                        mode = "Import all Google contacts"
                    else:
                        mode = "Unknown sync mode"

                    self.stdout.write(
                        self.style.SUCCESS(
                            f"User {user.username} ({user.id}) - Ready for sync: {mode}"
                        )
                    )
                    users_processed += 1
                else:
                    # Actually sync contacts
                    result = contacts_service.sync_contacts_based_on_preference()

                    if result["success"]:
                        synced_count = result["synced_count"]
                        total_synced += synced_count
                        users_processed += 1

                        self.stdout.write(
                            self.style.SUCCESS(
                                f'User {user.username} ({user.id}) - {result["message"]} ({synced_count} contacts)'
                            )
                        )

                        # Show any warnings
                        if "errors" in result and result["errors"]:
                            for error in result["errors"][:3]:  # Show first 3 errors
                                self.stdout.write(
                                    self.style.WARNING(f"  Warning: {error}")
                                )
                            if len(result["errors"]) > 3:
                                self.stdout.write(
                                    self.style.WARNING(
                                        f'  ... and {len(result["errors"]) - 3} more warnings'
                                    )
                                )
                    else:
                        self.stdout.write(
                            self.style.ERROR(
                                f'User {user.username} ({user.id}) - Sync failed: {result["error"]}'
                            )
                        )

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f"User {user.username} ({user.id}) - Error: {str(e)}"
                    )
                )

        # Summary
        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f"[DRY RUN] {users_processed} users ready for contact sync"
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Contact sync completed: {total_synced} contacts synced for {users_processed} users"
                )
            )

            # Show sync frequency info
            if not force_sync:
                self.stdout.write(
                    "Note: Only users with auto-sync enabled and due for sync were processed. "
                    "Use --force to sync all users regardless of schedule."
                )
