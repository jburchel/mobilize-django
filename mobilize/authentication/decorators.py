from functools import wraps
from django.shortcuts import redirect, get_object_or_404
from django.http import HttpResponseForbidden, Http404
from django.contrib.auth.decorators import user_passes_test, login_required
from django.core.exceptions import PermissionDenied
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


def office_data_filter(queryset, user, office_field='office'):
    """
    Filter queryset based on user's office permissions.
    
    Args:
        queryset: The queryset to filter
        user: The user to check permissions for
        office_field: The field name for office filtering
    
    Returns:
        Filtered queryset based on user's office access
    """
    # Super admins see everything
    if user.role == 'super_admin':
        return queryset
    
    # Get user's office assignments (cast user_id to string to match database type)
    from mobilize.admin_panel.models import UserOffice
    user_offices = UserOffice.objects.extra(
        where=["user_id = %s"],
        params=[str(user.id)]
    ).values_list('office_id', flat=True)
    
    if not user_offices:
        # User not assigned to any office - return empty queryset
        return queryset.none()
    
    # Filter to only objects in user's offices
    filter_kwargs = {f'{office_field}__in': user_offices}
    return queryset.filter(**filter_kwargs)


def office_object_permission_required(model_class, lookup_field='office'):
    """
    Decorator to check office-level permissions for specific object access.
    
    Args:
        model_class: The model class to check
        lookup_field: The field to use for office lookup (default: 'office')
    
    Usage:
        @office_object_permission_required(Contact, 'office')
        def contact_detail(request, pk):
            pass
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            # Super admins have access to everything
            if request.user.role == 'super_admin':
                return view_func(request, *args, **kwargs)
            
            # Get user's office assignments (cast user_id to string to match database type)
            from mobilize.admin_panel.models import UserOffice
            user_offices = UserOffice.objects.extra(
                where=["user_id = %s"],
                params=[str(request.user.id)]
            ).values_list('office_id', flat=True)
            
            if not user_offices:
                raise PermissionDenied("User not assigned to any office")
            
            # Check object-level permissions if pk is provided
            if 'pk' in kwargs:
                try:
                    obj = get_object_or_404(model_class, pk=kwargs['pk'])
                    
                    # Handle nested field lookups (e.g., 'contact__office')
                    office_value = obj
                    for field in lookup_field.split('__'):
                        office_value = getattr(office_value, field, None)
                        if office_value is None:
                            break
                    
                    # Handle different office field types
                    if hasattr(office_value, 'id'):
                        office_id = office_value.id
                    elif office_value:
                        office_id = office_value
                    else:
                        # No office assigned - only super_admin can access
                        raise Http404("Object not found")
                    
                    if office_id not in user_offices:
                        raise Http404("Object not found")  # Hide existence from other offices
                        
                except model_class.DoesNotExist:
                    raise Http404("Object not found")
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


def limited_user_check(action='view'):
    """
    Decorator to prevent limited users from performing unauthorized actions.
    
    Args:
        action: The action being attempted ('view', 'create', 'edit', 'delete')
    
    Usage:
        @limited_user_check('create')
        def create_contact(request):
            pass
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            if request.user.role == 'limited_user' and action != 'view':
                raise PermissionDenied("Limited users can only view data, not modify it")
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


def can_create_edit_delete(view_func):
    """
    Decorator to prevent limited users from creating, editing, or deleting.
    
    Usage:
        @can_create_edit_delete
        def create_contact(request):
            pass
    """
    @wraps(view_func)
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        if request.user.role == 'limited_user':
            raise PermissionDenied("Limited users cannot create, edit, or delete data")
        
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def ensure_user_office_assignment(view_func):
    """
    Decorator to ensure user has at least one office assignment.
    
    Usage:
        @ensure_user_office_assignment
        def dashboard_view(request):
            pass
    """
    @wraps(view_func)
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        # Super admins don't need office assignments
        if request.user.role == 'super_admin':
            return view_func(request, *args, **kwargs)
        
        # Check if user has office assignments (cast user_id to string to match database type)
        from mobilize.admin_panel.models import UserOffice
        if not UserOffice.objects.extra(
            where=["user_id = %s"],
            params=[str(request.user.id)]
        ).exists():
            raise PermissionDenied("Access denied. User not assigned to any office. Please contact an administrator.")
        
        return view_func(request, *args, **kwargs)
    return _wrapped_view
