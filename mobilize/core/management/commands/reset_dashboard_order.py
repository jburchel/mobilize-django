from django.core.management.base import BaseCommand
from mobilize.core.models import DashboardPreference


class Command(BaseCommand):
    help = "Reset all user dashboard configurations to pick up new default widget order"

    def add_arguments(self, parser):
        parser.add_argument(
            "--confirm",
            action="store_true",
            help="Confirm that you want to reset all dashboard configurations",
        )

    def handle(self, *args, **options):
        if not options["confirm"]:
            self.stdout.write(
                self.style.WARNING(
                    "This will reset ALL user dashboard configurations to defaults.\n"
                    "Run with --confirm to proceed."
                )
            )
            return

        # Reset all dashboard preferences
        count = 0
        for pref in DashboardPreference.objects.all():
            pref.reset_to_defaults()
            count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully reset {count} dashboard configurations to new default order."
            )
        )
