from django.core.management.base import BaseCommand
from mobilize.tasks.notifications import send_due_date_notifications

class Command(BaseCommand):
    help = 'Checks for tasks with upcoming due dates and sends reminder notifications.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('Starting to check and send task reminders...'))
        try:
            count = send_due_date_notifications()
            self.stdout.write(self.style.SUCCESS(f'Successfully processed reminders. {count} notification(s) sent/simulated.'))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'An error occurred: {e}'))