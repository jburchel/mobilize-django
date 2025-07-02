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
            view_mode: 'default', 'my_only', or 'office_<office_id>' - controls viewing scope for admins
        """
        self.user = user
        self.view_mode = view_mode
        self.user_role = getattr(user, 'role', 'standard_user')
        
        # Parse office-specific view mode for super admins
        self.selected_office_id = None
        if view_mode.startswith('office_'):
            try:
                self.selected_office_id = int(view_mode.split('_')[1])
            except (ValueError, IndexError):
                self.selected_office_id = None
        
    def get_people_queryset(self):
        """
        Get the appropriate People queryset based on user role and view mode.
        
        Returns:
            QuerySet filtered for the user's access level
        """
        from mobilize.contacts.models import Person
        
        # Get user ID safely to handle custom authentication middleware
        user_id = getattr(self.user, 'id', None)
        
        if self.user_role == 'super_admin':
            if self.view_mode == 'my_only':
                # Super admin viewing only their assigned people
                return Person.objects.filter(contact__user_id=user_id)
            elif self.selected_office_id:
                # Super admin viewing people from a specific office
                return Person.objects.filter(contact__office_id=self.selected_office_id)
            else:
                # Super admin viewing all people across all offices
                return Person.objects.all()
                
        elif self.user_role == 'office_admin':
            if self.view_mode == 'my_only':
                # Office admin viewing only their assigned people
                return Person.objects.filter(contact__user_id=user_id)
            else:
                # Office admin viewing all people in their office(s)
                user_offices = self._get_user_offices()
                return Person.objects.filter(
                    Q(contact__office_id__in=user_offices) |
                    Q(contact__user_id=user_id)
                ).distinct()
                
        else:  # standard_user or limited_user
            # Standard/limited users see only their assigned people
            return Person.objects.filter(contact__user_id=user_id)
    
    def get_churches_queryset(self):
        """
        Get the appropriate Churches queryset based on user role.
        
        Returns:
            QuerySet filtered for the user's access level
        """
        from mobilize.churches.models import Church
        
        if self.user_role == 'super_admin':
            if self.selected_office_id:
                # Super admin viewing churches from a specific office
                return Church.objects.filter(contact__office_id=self.selected_office_id)
            else:
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
        Get tasks queryset based on user role and view mode.
        
        Returns:
            QuerySet filtered for the user's access
        """
        from mobilize.tasks.models import Task
        
        # Get user ID safely to handle custom authentication middleware
        user_id = getattr(self.user, 'id', None)
        
        if self.user_role == 'super_admin':
            if self.view_mode == 'my_only':
                # Super admin viewing only their own tasks
                return Task.objects.filter(Q(assigned_to_id=user_id) | Q(created_by_id=user_id))
            elif self.selected_office_id:
                # Super admin viewing tasks related to a specific office
                return Task.objects.filter(
                    Q(office_id=self.selected_office_id) |
                    Q(person__contact__office_id=self.selected_office_id) |
                    Q(church__contact__office_id=self.selected_office_id)
                )
            else:
                # Super admin viewing all tasks
                return Task.objects.all()
        else:
            # All other users only see their own tasks (assigned to them or created by them)
            return Task.objects.filter(
                Q(assigned_to_id=user_id) | Q(created_by_id=user_id)
            )
    
    def get_communications_queryset(self):
        """
        Get communications queryset based on user role and view mode.
        
        Returns:
            QuerySet filtered for the user's access
        """
        from mobilize.communications.models import Communication
        
        # Get user ID safely to handle custom authentication middleware
        user_id = getattr(self.user, 'id', None)
        
        if self.user_role == 'super_admin':
            if self.view_mode == 'my_only':
                # Super admin viewing only their own communications
                return Communication.objects.filter(user_id=str(user_id))
            elif self.selected_office_id:
                # Super admin viewing communications related to a specific office
                return Communication.objects.filter(
                    Q(office_id=self.selected_office_id) |
                    Q(person__contact__office_id=self.selected_office_id) |
                    Q(church__contact__office_id=self.selected_office_id)
                )
            else:
                # Super admin viewing all communications
                return Communication.objects.all()
        else:
            # All other users only see their own communications
            return Communication.objects.filter(user_id=str(user_id))
    
    def _get_user_offices(self):
        """
        Get the office IDs for the current user.
        
        Returns:
            List of office IDs the user is assigned to
        """
        from mobilize.admin_panel.models import UserOffice
        
        # Get user ID safely to handle custom authentication middleware
        user_id = getattr(self.user, 'id', None)
        
        try:
            # Cast user.id to string to match VARCHAR column type in database
            # Use extra() to force database-level string casting
            user_offices = UserOffice.objects.extra(
                where=["user_id = %s"],
                params=[str(user_id)]
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
        elif self.selected_office_id:
            # Get office name for display
            try:
                from mobilize.admin_panel.models import Office
                office = Office.objects.get(id=self.selected_office_id)
                return f"{office.name} Office"
            except:
                return "Selected Office"
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