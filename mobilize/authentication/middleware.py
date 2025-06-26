from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth.models import AnonymousUser


class CustomAuthMiddleware(MiddlewareMixin):
    """
    Custom middleware to handle authentication with manual session variables.
    This bridges our raw SQL user creation with Django's authentication system.
    """
    
    def process_request(self, request):
        # Check if user is authenticated via our manual session
        if request.session.get('authenticated') and request.session.get('user_id'):
            # Create a minimal user object that Django's auth system will accept
            class AuthenticatedUser:
                def __init__(self, user_id, email):
                    self.id = user_id
                    self.pk = user_id
                    self.email = email
                    self.username = email
                    self.is_authenticated = True
                    self.is_active = True
                    self.is_anonymous = False
                    self.is_staff = False
                    self.is_superuser = False
                    # Add missing attributes for CRM decorators
                    # Set role based on email - j.burchel@crossoverglobal.net is super admin
                    if email == 'j.burchel@crossoverglobal.net':
                        self.role = 'super_admin'
                        self.is_staff = True
                        self.is_superuser = True
                    else:
                        self.role = 'standard_user'  # Default for other users
                    self.first_name = ''
                    self.last_name = ''
                    self.preferences = {}
                    self.person = None
                    
                def get_username(self):
                    return self.email
                    
                def __str__(self):
                    return self.email
                    
                def has_perm(self, perm, obj=None):
                    return True  # Temporary - allow all permissions
                    
                def has_perms(self, perm_list, obj=None):
                    return True  # Temporary - allow all permissions
                    
                def has_module_perms(self, package_name):
                    return True  # Temporary - allow all permissions
                    
                def has_office_permission(self, office_id, required_role=None):
                    return True  # Temporary - allow all office access
                    
                def get_or_create_person(self):
                    return None  # Temporary - no person record
            
            # Set the user on the request
            request.user = AuthenticatedUser(
                request.session['user_id'],
                request.session['user_email']
            )
        else:
            # User is not authenticated
            request.user = AnonymousUser()