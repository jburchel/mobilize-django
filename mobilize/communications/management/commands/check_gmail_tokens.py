from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from mobilize.authentication.models import GoogleToken

User = get_user_model()


class Command(BaseCommand):
    help = 'Check Google token status for all users'
    
    def handle(self, *args, **options):
        self.stdout.write('='*50)
        self.stdout.write('GOOGLE TOKEN STATUS CHECK')
        self.stdout.write('='*50)
        
        # Check all active users
        users = User.objects.filter(is_active=True)
        self.stdout.write(f'Found {users.count()} active users')
        
        for user in users:
            self.stdout.write(f'\nUser: {user.username} (ID: {user.id})')
            
            try:
                token = GoogleToken.objects.get(user=user)
                self.stdout.write(f'  ✅ Token exists')
                self.stdout.write(f'  Access token: {bool(token.access_token)}')
                self.stdout.write(f'  Refresh token: {bool(token.refresh_token)}')
                self.stdout.write(f'  Expires: {token.expires_at}')
                self.stdout.write(f'  Scopes: {token.scopes}')
                
                # Check if token is expired
                from django.utils import timezone
                if token.expires_at and token.expires_at < timezone.now():
                    self.stdout.write('  ⚠️  Token is EXPIRED')
                else:
                    self.stdout.write('  ✅ Token is valid')
                    
            except GoogleToken.DoesNotExist:
                self.stdout.write('  ❌ No Google token found')
        
        # Check which users would be found by the sync command
        self.stdout.write('\n' + '='*30)
        self.stdout.write('SYNC COMMAND USER SELECTION')
        self.stdout.write('='*30)
        
        authenticated_users = GoogleToken.objects.filter(
            access_token__isnull=False
        ).values_list('user_id', flat=True)
        
        sync_users = User.objects.filter(id__in=authenticated_users, is_active=True)
        
        self.stdout.write(f'Tokens with access_token: {len(authenticated_users)}')
        self.stdout.write(f'Users sync would process: {sync_users.count()}')
        self.stdout.write(f'User IDs: {list(authenticated_users)}')
        self.stdout.write(f'Usernames: {[u.username for u in sync_users]}')
        
        if not sync_users.exists():
            self.stdout.write('\n❌ This is why sync finds 0 users!')
            self.stdout.write('You need to log out and log back in via OAuth to create fresh tokens.')