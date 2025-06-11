from functools import wraps
from django.shortcuts import redirect
from django.http import HttpResponseForbidden
from django.contrib.auth.decorators import user_passes_test
from django.urls import reverse


def role_required(required_role):
    """
    Decorator to restrict access based on user role.
    
    Args:
        required_role: The minimum role required (super_admin, office_admin, standard_user, limited_user)
        
    Role hierarchy:
    - super_admin (highest)
    - office_admin
    - standard_user
    - limited_user (lowest)
    """
    role_hierarchy = {
        'super_admin': 4,
        'office_admin': 3,
        'standard_user': 2,
        'limited_user': 1
    }
    
    required_level = role_hierarchy.get(required_role, 0)
    
    def check_role(user):
        if not user.is_authenticated:
            return False
        user_level = role_hierarchy.get(user.role, 0)
        return user_level >= required_level
    
    return user_passes_test(check_role, login_url=reverse('authentication:login'))


def office_admin_required(view_func):
    """
    Decorator to restrict access to office admins and super admins.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('authentication:login')
        
        if request.user.role in ['super_admin', 'office_admin']:
            return view_func(request, *args, **kwargs)
        
        return HttpResponseForbidden("You don't have permission to access this page.")
    
    return _wrapped_view


def super_admin_required(view_func):
    """
    Decorator to restrict access to super admins only.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('authentication:login')
        
        if request.user.role == 'super_admin':
            return view_func(request, *args, **kwargs)
        
        return HttpResponseForbidden("You don't have permission to access this page.")
    
    return _wrapped_view


def office_permission_required(permission_type='view'):
    """
    Decorator to check if user has permission for a specific office.
    
    Args:
        permission_type: Type of permission required (view, manage, admin)
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('authentication:login')
            
            # Get office_id from URL parameters
            office_id = kwargs.get('office_id')
            if not office_id:
                return HttpResponseForbidden("Office ID is required.")
            
            # Super admins always have access
            if request.user.role == 'super_admin':
                return view_func(request, *args, **kwargs)
            
            # Map permission types to required roles
            permission_map = {
                'view': None,  # Any role assigned to the office
                'manage': 'standard_user',  # At least standard_user
                'admin': 'office_admin'  # Must be office_admin
            }
            
            required_role = permission_map.get(permission_type)
            
            # Check if user has permission for this office
            if request.user.has_office_permission(office_id, required_role):
                return view_func(request, *args, **kwargs)
            
            return HttpResponseForbidden("You don't have permission to access this office.")
        
        return _wrapped_view
    
    return decorator
