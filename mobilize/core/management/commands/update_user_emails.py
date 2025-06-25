from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction

User = get_user_model()

class Command(BaseCommand):
    help = 'Update existing user emails to use @crossoverglobal.net domain'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirm that you want to update user emails',
        )

    def handle(self, *args, **options):
        if not options['confirm']:
            self.stdout.write(
                self.style.WARNING(
                    'This will update existing user emails to use @crossoverglobal.net domain.\n'
                    'Run with --confirm to proceed.'
                )
            )
            return

        with transaction.atomic():
            self.stdout.write('Updating user emails...')
            
            # Update specific users to have crossoverglobal.net emails
            updates = [
                ('admin', 'admin@crossoverglobal.net'),
                ('admin_north_america_office', 'admin.na@crossoverglobal.net'),
                ('admin_europe_office', 'admin.eu@crossoverglobal.net'),
                ('admin_asia_pacific_office', 'admin.ap@crossoverglobal.net'),
                ('admin_latin_america_office', 'admin.la@crossoverglobal.net'),
                ('user1', 'john.smith@crossoverglobal.net'),
                ('user2', 'jane.doe@crossoverglobal.net'),
                ('user3', 'mike.johnson@crossoverglobal.net'),
                ('user4', 'sarah.wilson@crossoverglobal.net'),
                ('user5', 'david.brown@crossoverglobal.net'),
                ('user6', 'lisa.davis@crossoverglobal.net'),
                ('user7', 'chris.miller@crossoverglobal.net'),
                ('user8', 'amy.garcia@crossoverglobal.net'),
                ('user9', 'tom.martinez@crossoverglobal.net'),
                ('user10', 'emma.anderson@crossoverglobal.net'),
                ('user11', 'ryan.taylor@crossoverglobal.net'),
                ('user12', 'kate.thomas@crossoverglobal.net'),
            ]
            
            updated_count = 0
            for username, new_email in updates:
                try:
                    user = User.objects.get(username=username)
                    old_email = user.email
                    user.email = new_email
                    user.save()
                    self.stdout.write(f'Updated {username}: {old_email} -> {new_email}')
                    updated_count += 1
                except User.DoesNotExist:
                    self.stdout.write(f'User {username} not found, skipping...')

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully updated {updated_count} user emails.\n\n'
                'Test Accounts (all passwords remain the same):\n'
                '==============================================\n'
                'Super Admin: admin@crossoverglobal.net / admin123\n'
                'Office Admins:\n'
                '  - admin.na@crossoverglobal.net / admin123 (North America)\n'
                '  - admin.eu@crossoverglobal.net / admin123 (Europe)\n'
                '  - admin.ap@crossoverglobal.net / admin123 (Asia Pacific)\n'
                '  - admin.la@crossoverglobal.net / admin123 (Latin America)\n'
                'Standard Users:\n'
                '  - john.smith@crossoverglobal.net / user123\n'
                '  - jane.doe@crossoverglobal.net / user123\n'
                '  - mike.johnson@crossoverglobal.net / user123\n'
                '  - And others...\n'
            )
        )