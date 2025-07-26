from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from mobilize.admin_panel.models import Office, UserOffice

User = get_user_model()

class Command(BaseCommand):
    help = 'Assigns a user to an office'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str, help='Email address of the user')
        parser.add_argument('--office-name', type=str, help='Name of the office (creates if not exists)')
        parser.add_argument('--role', type=str, default='standard_user', 
                          choices=['office_admin', 'standard_user', 'limited_user'],
                          help='Role in the office')

    def handle(self, *args, **options):
        email = options['email']
        office_name = options.get('office_name', 'Default Office')
        role = options['role']
        
        try:
            user = User.objects.get(email=email)
            
            # Get or create the office
            office, created = Office.objects.get_or_create(
                name=office_name,
                defaults={'is_active': True}
            )
            
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Created new office: {office_name}')
                )
            
            # Assign user to office
            user_office, created = UserOffice.objects.get_or_create(
                user_id=str(user.id),  # Cast to string to match database type
                office=office,
                defaults={'is_active': True}
            )
            
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully assigned {email} to {office_name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'{email} is already assigned to {office_name}')
                )
                
            # Update user role if needed
            if user.role != role and user.role != 'super_admin':
                user.role = role
                user.save()
                self.stdout.write(
                    self.style.SUCCESS(f'Updated {email} role to {role}')
                )
                
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'User with email {email} does not exist')
            )