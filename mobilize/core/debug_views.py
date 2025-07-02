"""
Debug views to help identify production issues
"""
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.db import connection
import traceback


@login_required
@require_http_methods(["GET"])
def debug_dashboard_toggle(request):
    """
    Debug endpoint to test the exact steps of the dashboard toggle
    """
    debug_info = {
        'user_info': {
            'id': request.user.id,
            'email': request.user.email,
            'role': getattr(request.user, 'role', 'unknown'),
        },
        'request_info': {
            'view_mode': request.GET.get('view_mode', 'default'),
            'method': request.method,
            'path': request.path,
        },
        'tests': {}
    }
    
    # Test 1: Office assignment check
    try:
        if request.user.role == 'super_admin':
            debug_info['tests']['office_assignment'] = 'super_admin_skip'
        else:
            from mobilize.admin_panel.models import UserOffice
            user_offices = UserOffice.objects.extra(
                where=["user_id = %s"],
                params=[str(request.user.id)]
            )
            count = user_offices.count()
            debug_info['tests']['office_assignment'] = f'found_{count}_offices'
            
            if count == 0:
                debug_info['tests']['office_assignment'] = 'ERROR_no_offices'
                
    except Exception as e:
        debug_info['tests']['office_assignment'] = f'ERROR: {str(e)}'
    
    # Test 2: DataAccessManager creation
    try:
        from mobilize.core.permissions import get_data_access_manager
        access_manager = get_data_access_manager(request)
        debug_info['tests']['data_access_manager'] = {
            'view_mode': access_manager.view_mode,
            'user_role': access_manager.user_role,
            'can_toggle': access_manager.can_view_all_data(),
            'display': access_manager.get_view_mode_display(),
        }
    except Exception as e:
        debug_info['tests']['data_access_manager'] = f'ERROR: {str(e)}'
        debug_info['tests']['data_access_manager_traceback'] = traceback.format_exc()
    
    # Test 3: Queryset access
    try:
        from mobilize.core.permissions import get_data_access_manager
        access_manager = get_data_access_manager(request)
        
        debug_info['tests']['querysets'] = {
            'people_count': access_manager.get_people_queryset().count(),
            'churches_count': access_manager.get_churches_queryset().count(),
            'tasks_count': access_manager.get_tasks_queryset().count(),
            'communications_count': access_manager.get_communications_queryset().count(),
        }
    except Exception as e:
        debug_info['tests']['querysets'] = f'ERROR: {str(e)}'
        debug_info['tests']['querysets_traceback'] = traceback.format_exc()
    
    # Test 4: Dashboard config
    try:
        from mobilize.core.dashboard_widgets import get_user_dashboard_config
        dashboard_config = get_user_dashboard_config(request.user)
        enabled_widgets = dashboard_config.get_enabled_widgets()
        
        debug_info['tests']['dashboard_config'] = {
            'config_type': str(type(dashboard_config)),
            'widget_count': len(enabled_widgets),
            'widgets': [w.get('id', 'unknown') for w in enabled_widgets]
        }
    except Exception as e:
        debug_info['tests']['dashboard_config'] = f'ERROR: {str(e)}'
        debug_info['tests']['dashboard_config_traceback'] = traceback.format_exc()
    
    # Test 5: Database connection
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT 1")
        debug_info['tests']['database'] = 'connected'
    except Exception as e:
        debug_info['tests']['database'] = f'ERROR: {str(e)}'
    
    return JsonResponse(debug_info, json_dumps_params={'indent': 2})


@login_required 
@require_http_methods(["GET"])
def debug_dashboard_minimal(request):
    """
    Minimal dashboard test - just the essential parts
    """
    try:
        # Import what the dashboard needs
        from mobilize.core.permissions import get_data_access_manager
        from mobilize.core.dashboard_widgets import get_user_dashboard_config
        
        # Create access manager
        access_manager = get_data_access_manager(request)
        
        # Get basic counts (what the dashboard does first)
        people_count = access_manager.get_people_queryset().count()
        churches_count = access_manager.get_churches_queryset().count()
        
        # Get dashboard config
        dashboard_config = get_user_dashboard_config(request.user)
        enabled_widgets = dashboard_config.get_enabled_widgets()
        
        return JsonResponse({
            'status': 'success',
            'view_mode': access_manager.view_mode,
            'people_count': people_count,
            'churches_count': churches_count,
            'widget_count': len(enabled_widgets),
            'user_role': request.user.role,
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'error': str(e),
            'traceback': traceback.format_exc()
        }, status=500)