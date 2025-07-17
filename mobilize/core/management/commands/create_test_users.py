from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from mobilize.admin_panel.models import Office, UserOffice

User = get_user_model()


class Command(BaseCommand):
    help = "Create test users with @crossoverglobal.net email addresses"

    def add_arguments(self, parser):
        parser.add_argument(
            "--confirm",
            action="store_true",
            help="Confirm that you want to create test users",
        )

    def handle(self, *args, **options):
        if not options["confirm"]:
            self.stdout.write(
                self.style.WARNING(
                    "This will create test users with @crossoverglobal.net email addresses.\n"
                    "Run with --confirm to proceed."
                )
            )
            return

        with transaction.atomic():
            self.stdout.write("Creating test users...")

            # Get offices
            offices = list(Office.objects.all())
            if not offices:
                self.stdout.write(
                    self.style.ERROR(
                        "No offices found. Please run create_sample_data first."
                    )
                )
                return

            # Create super admin
            super_admin, created = User.objects.get_or_create(
                email="admin@crossoverglobal.net",
                defaults={
                    "username": "admin",
                    "first_name": "Super",
                    "last_name": "Admin",
                    "role": "super_admin",
                    "is_staff": True,
                    "is_superuser": True,
                },
            )
            if created:
                super_admin.set_password("admin123")
                super_admin.save()
                self.stdout.write(f"Created super admin: {super_admin.email}")

            # Assign super admin to first office
            UserOffice.objects.get_or_create(
                user=super_admin, office=offices[0], defaults={"is_primary": True}
            )

            # Create office admins
            office_admins = []
            for i, office in enumerate(offices):
                office_admin, created = User.objects.get_or_create(
                    email=f"admin.{office.code.lower()}@crossoverglobal.net",
                    defaults={
                        "username": f"admin_{office.code.lower()}",
                        "first_name": f"{office.name.split()[0]}",
                        "last_name": "Admin",
                        "role": "office_admin",
                        "is_staff": True,
                    },
                )
                if created:
                    office_admin.set_password("admin123")
                    office_admin.save()
                    self.stdout.write(f"Created office admin: {office_admin.email}")

                # Assign office admin to their office
                UserOffice.objects.get_or_create(
                    user=office_admin, office=office, defaults={"is_primary": True}
                )
                office_admins.append(office_admin)

            # Create standard users
            standard_users = []
            user_names = [
                ("John", "Smith"),
                ("Jane", "Doe"),
                ("Mike", "Johnson"),
                ("Sarah", "Wilson"),
                ("David", "Brown"),
                ("Lisa", "Davis"),
                ("Chris", "Miller"),
                ("Amy", "Garcia"),
                ("Tom", "Martinez"),
                ("Emma", "Anderson"),
                ("Ryan", "Taylor"),
                ("Kate", "Thomas"),
            ]

            for i, (first_name, last_name) in enumerate(user_names):
                office = offices[i % len(offices)]
                username = f"{first_name.lower()}.{last_name.lower()}"
                email = f"{username}@crossoverglobal.net"

                user, created = User.objects.get_or_create(
                    email=email,
                    defaults={
                        "username": username,
                        "first_name": first_name,
                        "last_name": last_name,
                        "role": "standard_user",
                    },
                )
                if created:
                    user.set_password("user123")
                    user.save()
                    self.stdout.write(f"Created user: {user.email}")

                # Assign user to their office
                UserOffice.objects.get_or_create(
                    user=user, office=office, defaults={"is_primary": True}
                )
                standard_users.append(user)

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully created test users:\n"
                f"- 1 super admin (admin@crossoverglobal.net)\n"
                f"- {len(office_admins)} office admins\n"
                f"- {len(standard_users)} standard users\n"
                f"All passwords are: admin123 (for admins) or user123 (for standard users)"
            )
        )

        self.stdout.write(
            self.style.WARNING(
                "\nTest Accounts:\n"
                "=============\n"
                "Super Admin: admin@crossoverglobal.net / admin123\n"
                "Office Admins:\n"
                f"  - admin.na@crossoverglobal.net / admin123 (North America)\n"
                f"  - admin.eu@crossoverglobal.net / admin123 (Europe)\n"
                f"  - admin.ap@crossoverglobal.net / admin123 (Asia Pacific)\n"
                f"  - admin.la@crossoverglobal.net / admin123 (Latin America)\n"
                "Standard Users: john.smith@crossoverglobal.net / user123 (and others)\n"
            )
        )
