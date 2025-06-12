"""
Permission utilities for role-based access control.

This module provides utilities for managing data visibility based on user roles
and viewing preferences throughout the application.
"""
from django.db.models import Q
from django.contrib.auth.models import User


class DataAccessManager:
    """
    Manages data access based on user roles and viewing preferences.
    """
    
    def __init__(self, user, view_mode='default'):
        """
        Initialize the data access manager.
        
        Args:
            user: The current user
            view_mode: 'default', 'my_only' - controls viewing scope for admins
        """
        self.user = user
        self.view_mode = view_mode
        self.user_role = getattr(user, 'role', 'standard_user')
        
    def get_people_queryset(self):
        """
        Get the appropriate People queryset based on user role and view mode.
        
        Returns:
            QuerySet filtered for the user's access level
        """
        from mobilize.contacts.models import Person
        
        if self.user_role == 'super_admin':
            if self.view_mode == 'my_only':
                # Super admin viewing only their assigned people
                return Person.objects.filter(assigned_to=str(self.user.id))
            else:
                # Super admin viewing all people across all offices
                return Person.objects.all()
                
        elif self.user_role == 'office_admin':
            if self.view_mode == 'my_only':
                # Office admin viewing only their assigned people
                return Person.objects.filter(assigned_to=str(self.user.id))
            else:
                # Office admin viewing all people in their office(s)
                user_offices = self._get_user_offices()
                return Person.objects.filter(
                    Q(contact__office_id__in=user_offices) |
                    Q(assigned_to=str(self.user.id))
                ).distinct()
                
        else:  # standard_user or limited_user
            # Standard/limited users see only their assigned people
            return Person.objects.filter(assigned_to=str(self.user.id))
    
    def get_churches_queryset(self):
        """
        Get the appropriate Churches queryset based on user role.
        
        Returns:
            QuerySet filtered for the user's access level
        """
        from mobilize.churches.models import Church
        
        if self.user_role == 'super_admin':
            # Super admin sees all churches
            return Church.objects.all()
            
        elif self.user_role in ['office_admin', 'standard_user', 'limited_user']:
            # Office admin and standard users see churches in their office(s)
            user_offices = self._get_user_offices()
            return Church.objects.filter(contact__office_id__in=user_offices)
            
        else:
            return Church.objects.none()
    
    def get_tasks_queryset(self):
        """
        Get tasks queryset - all users only see their own tasks.
        
        Returns:
            QuerySet filtered for the user's tasks
        """
        from mobilize.tasks.models import Task
        
        # All users only see their own tasks (assigned to them or created by them)
        return Task.objects.filter(
            Q(assigned_to=self.user) | Q(created_by=self.user)
        )
    
    def get_communications_queryset(self):
        """
        Get communications queryset - all users only see their own communications.
        
        Returns:
            QuerySet filtered for the user's communications
        """
        from mobilize.communications.models import Communication
        
        # All users only see their own communications
        return Communication.objects.filter(user_id=str(self.user.id))
    
    def _get_user_offices(self):
        """
        Get the office IDs for the current user.
        
        Returns:
            List of office IDs the user is assigned to
        """
        from mobilize.admin_panel.models import UserOffice
        
        try:
            user_offices = UserOffice.objects.filter(
                user_id=str(self.user.id)
            ).values_list('office_id', flat=True)
            return list(user_offices)
        except:
            # Fallback to user's primary office if UserOffice relationship fails
            if hasattr(self.user, 'office_id') and self.user.office_id:
                return [self.user.office_id]
            return []
    
    def can_view_all_data(self):
        """
        Check if user can toggle to view all data vs just their own.
        
        Returns:
            Boolean indicating if user can toggle views
        """
        return self.user_role in ['super_admin', 'office_admin']
    
    def get_view_mode_display(self):
        """
        Get human-readable display text for current view mode.
        
        Returns:
            String describing the current view mode
        """
        if not self.can_view_all_data():
            return "My Contacts"
            
        if self.view_mode == 'my_only':
            return "My Contacts Only"
        elif self.user_role == 'super_admin':
            return "All Offices"
        else:
            return "My Office"


def get_data_access_manager(request):
    """
    Factory function to create DataAccessManager from request.
    
    Args:
        request: Django request object
        
    Returns:
        DataAccessManager instance
    """
    view_mode = request.GET.get('view_mode', 'default')
    return DataAccessManager(request.user, view_mode)


def require_role(roles):
    """
    Decorator to require specific user roles.
    
    Args:
        roles: List of roles that can access the view
        
    Returns:
        Decorator function
    """
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            if not hasattr(request.user, 'role'):
                from django.http import HttpResponseForbidden
                return HttpResponseForbidden("Access denied")
                
            if request.user.role not in roles:
                from django.http import HttpResponseForbidden
                return HttpResponseForbidden("Insufficient permissions")
                
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator