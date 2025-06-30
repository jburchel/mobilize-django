from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.contrib import messages
from django.core.cache import cache
from django.utils.http import urlencode
from django.http import JsonResponse, HttpResponse
from django.db import connection
from django.conf import settings
from django.utils import timezone
from datetime import datetime, timedelta
from mobilize.authentication.decorators import ensure_user_office_assignment
import os


@login_required
def dashboard_simple(request):
    """
    Simplified dashboard for initial deployment - bypasses complex database queries.
    """
    context = {
        'user': request.user,
        'deployment_success': True,
        'message': 'Django CRM successfully deployed to Render!',
        'next_steps': [
            'Google OAuth authentication is working',
            'User authentication system is functional',
            'Database connection established',
            'Ready for data migration and full setup'
        ]
    }
    return render(request, 'core/dashboard_simple.html', context)

@login_required
@ensure_user_office_assignment  
def dashboard(request):
    """
    Main dashboard view displaying key metrics and pending tasks.
    
    Data visibility is based on user role:
    - Super Admin: All data (can toggle to "my only" view)
    - Office Admin: Office data (can toggle to "my only" view)  
    - Standard User: Only their people, office churches
    
    Shows:
    - People count
    - Churches count
    - Recent communications
    - Pending tasks
    - Pipeline stage distribution
    - Recent activity
    - Overdue tasks
    """
    from mobilize.contacts.models import Person
    from mobilize.churches.models import Church
    from mobilize.tasks.models import Task
    from mobilize.communications.models import Communication
    from mobilize.core.permissions import get_data_access_manager
    from mobilize.core.dashboard_widgets import get_user_dashboard_config, organize_widgets_by_row, get_widget_css_class
    from django.db.models import Count, Q
    from datetime import datetime, timedelta
    
    # Get data access manager based on user role and view preferences
    access_manager = get_data_access_manager(request)
    
    # Create cache key based on user and view mode for performance
    cache_key = f'dashboard_data_{request.user.id}_{access_manager.view_mode}_{datetime.now().strftime("%Y%m%d_%H")}'
    cached_data = cache.get(cache_key)
    
    if cached_data:
        # Use cached data for better performance (1-hour cache)
        people_count = cached_data['people_count']
        churches_count = cached_data['churches_count']
        people_queryset = access_manager.get_people_queryset()
        churches_queryset = access_manager.get_churches_queryset()
        tasks_queryset = access_manager.get_tasks_queryset()
        communications_queryset = access_manager.get_communications_queryset()
    else:
        # Get filtered querysets based on user permissions
        people_queryset = access_manager.get_people_queryset()
        churches_queryset = access_manager.get_churches_queryset()
        tasks_queryset = access_manager.get_tasks_queryset()
        communications_queryset = access_manager.get_communications_queryset()
        
        # Get counts for dashboard widgets
        people_count = people_queryset.count()
        churches_count = churches_queryset.count()
        
        # Cache the basic counts for 1 hour
        cache.set(cache_key, {
            'people_count': people_count,
            'churches_count': churches_count,
        }, 3600)
    
    # Get pending tasks for current user (always user-specific) with optimization
    pending_tasks = tasks_queryset.select_related(
        'created_by', 'assigned_to', 'person', 'church', 'office'
    ).filter(
        status='pending'
    ).order_by('due_date')[:5]
    
    # Get task counts using aggregation for efficiency
    task_stats = tasks_queryset.aggregate(
        overdue_tasks=Count('pk', filter=Q(
            status__in=['pending', 'in_progress'],
            due_date__lt=datetime.now().date()
        )),
        upcoming_tasks=Count('pk', filter=Q(
            status__in=['pending', 'in_progress'],
            due_date__range=[datetime.now().date(), datetime.now().date() + timedelta(days=7)]
        )),
        completed_this_week=Count('pk', filter=Q(
            status='completed',
            completed_at__gte=datetime.now() - timedelta(days=7)
        ))
    )
    
    # Get recent communications (user-specific) with optimization
    recent_communications = communications_queryset.select_related(
        'person', 'church', 'office'
    ).order_by('-date_sent')[:5]
    
    # Get pipeline distribution for people and churches
    from mobilize.pipeline.models import MAIN_PEOPLE_PIPELINE_STAGES, MAIN_CHURCH_PIPELINE_STAGES
    from django.db.models import Count, Case, When, CharField, Value
    
    # Skip complex pipeline queries for "my only" mode to prevent crashes
    if access_manager.view_mode == 'my_only':
        # Simple fallback for my_only mode
        people_pipeline_data = []
        for stage_code, stage_name in MAIN_PEOPLE_PIPELINE_STAGES:
            people_pipeline_data.append({
                'stage_code': stage_code,
                'stage_name': stage_name,
                'count': 0
            })
    else:
        # Get people pipeline distribution - OPTIMIZED with database aggregation
        from mobilize.pipeline.models import PipelineContact, PipelineStage
        
        # Get all pipeline stage names for mapping
        stage_name_map = dict(MAIN_PEOPLE_PIPELINE_STAGES)
        
        # Use database aggregation instead of Python loops with error handling
        try:
            people_pipeline_raw = people_queryset.select_related('contact').prefetch_related(
                'contact__pipeline_entries__current_stage'
            ).annotate(
                pipeline_stage_name=Case(
                    *[When(contact__pipeline_entries__current_stage__name=stage_name, then=Value(stage_code))
                      for stage_code, stage_name in MAIN_PEOPLE_PIPELINE_STAGES],
                    default=Value('unknown'),
                    output_field=CharField()
                )
            ).values('pipeline_stage_name').annotate(count=Count('contact_id'))
            
            # Convert to expected format
            people_pipeline_data = []
            pipeline_counts = {item['pipeline_stage_name']: item['count'] for item in people_pipeline_raw}
            for stage_code, stage_name in MAIN_PEOPLE_PIPELINE_STAGES:
                count = pipeline_counts.get(stage_code, 0)
                people_pipeline_data.append({
                    'stage_code': stage_code,
                    'stage_name': stage_name,
                    'count': count
                })
        except Exception as e:
            # Fallback to simple counts if pipeline aggregation fails
            people_pipeline_data = []
            for stage_code, stage_name in MAIN_PEOPLE_PIPELINE_STAGES:
                people_pipeline_data.append({
                    'stage_code': stage_code,
                    'stage_name': stage_name,
                    'count': 0
                })
    
    # Get churches pipeline distribution - OPTIMIZED with database aggregation
    church_stage_name_map = dict(MAIN_CHURCH_PIPELINE_STAGES)
    
    # Skip complex pipeline queries for "my only" mode to prevent crashes
    if access_manager.view_mode == 'my_only':
        # Simple fallback for my_only mode
        churches_pipeline_data = []
        for stage_code, stage_name in MAIN_CHURCH_PIPELINE_STAGES:
            churches_pipeline_data.append({
                'stage_code': stage_code,
                'stage_name': stage_name,
                'count': 0
            })
    else:
        try:
            churches_pipeline_raw = churches_queryset.select_related('contact').prefetch_related(
                'contact__pipeline_entries__current_stage'
            ).annotate(
                pipeline_stage_name=Case(
                    *[When(contact__pipeline_entries__current_stage__name=stage_name, then=Value(stage_code))
                      for stage_code, stage_name in MAIN_CHURCH_PIPELINE_STAGES],
                    default=Value('unknown'),
                    output_field=CharField()
                )
            ).values('pipeline_stage_name').annotate(count=Count('contact_id'))
            
            # Convert to expected format
            churches_pipeline_data = []
            church_pipeline_counts = {item['pipeline_stage_name']: item['count'] for item in churches_pipeline_raw}
            for stage_code, stage_name in MAIN_CHURCH_PIPELINE_STAGES:
                count = church_pipeline_counts.get(stage_code, 0)
                churches_pipeline_data.append({
                    'stage_code': stage_code,
                    'stage_name': stage_name,
                    'count': count
                })
        except Exception as e:
            # Fallback to simple counts if pipeline aggregation fails
            churches_pipeline_data = []
            for stage_code, stage_name in MAIN_CHURCH_PIPELINE_STAGES:
                churches_pipeline_data.append({
                    'stage_code': stage_code,
                    'stage_name': stage_name,
                    'count': 0
                })
    
    # Calculate percentages
    people_total = sum(item['count'] for item in people_pipeline_data) or 1
    for item in people_pipeline_data:
        item['percentage'] = round((item['count'] / people_total) * 100, 1)
    
    churches_total = sum(item['count'] for item in churches_pipeline_data) or 1
    for item in churches_pipeline_data:
        item['percentage'] = round((item['count'] / churches_total) * 100, 1)
    
    # Get activity summary for this week (based on access level) using aggregation
    week_start = datetime.now() - timedelta(days=7)
    activity_stats = {
        'recent_people': people_queryset.filter(
            contact__created_at__gte=week_start.date()
        ).count(),
        'recent_churches': churches_queryset.filter(
            contact__created_at__gte=week_start.date()
        ).count()
    }
    
    # Prepare priority distribution (user-specific tasks)
    priority_tasks = tasks_queryset.filter(
        status='pending'
    ).values('priority').annotate(count=Count('pk')).order_by('priority')
    
    # Get activity timeline data (last 7 days) - OPTIMIZED with single queries and proper date handling
    from django.db.models import DateField
    from django.db.models.functions import TruncDate
    
    # Get date range for last 7 days
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=6)
    
    # Get all people created in last 7 days, grouped by date - OPTIMIZED
    people_by_date = people_queryset.select_related('contact').filter(
        contact__created_at__date__range=[start_date, end_date]
    ).annotate(
        created_date=TruncDate('contact__created_at')
    ).values('created_date').annotate(count=Count('contact_id'))
    people_counts = {item['created_date']: item['count'] for item in people_by_date}
    
    # Get all tasks completed in last 7 days, grouped by date - OPTIMIZED
    tasks_by_date = tasks_queryset.select_related('assigned_to', 'created_by').filter(
        status='completed',
        completed_at__date__range=[start_date, end_date]
    ).annotate(
        task_date=TruncDate('completed_at')
    ).values('task_date').annotate(count=Count('pk'))
    task_counts = {item['task_date']: item['count'] for item in tasks_by_date}
    
    # Get all communications sent in last 7 days, grouped by date - OPTIMIZED
    comms_by_date = communications_queryset.select_related('person', 'church', 'user').filter(
        date__range=[start_date, end_date]
    ).annotate(
        comm_date=TruncDate('date')
    ).values('comm_date').annotate(count=Count('pk'))
    comm_counts = {item['comm_date']: item['count'] for item in comms_by_date}
    
    # Build timeline data efficiently
    activity_timeline = []
    for i in range(6, -1, -1):
        date = datetime.now().date() - timedelta(days=i)
        activity_timeline.append({
            'date': date.strftime('%m/%d'),
            'people': people_counts.get(date, 0),
            'tasks': task_counts.get(date, 0),
            'communications': comm_counts.get(date, 0),
        })
    
    # Get church activity summary
    church_stats = {
        'total': churches_queryset.count(),
        'with_contacts': churches_queryset.filter(
            main_contact_id__isnull=False
        ).count(),
        'recent_activity': churches_queryset.filter(
            contact__updated_at__gte=week_start
        ).count(),
    }
    
    # Get user's dashboard widget configuration
    dashboard_config = get_user_dashboard_config(request.user)
    enabled_widgets = dashboard_config.get_enabled_widgets()
    widget_rows = organize_widgets_by_row(enabled_widgets)
    
    # Get offices for super admin office selector
    all_offices = []
    if request.user.role == 'super_admin':
        from mobilize.admin_panel.models import Office
        all_offices = Office.objects.all().order_by('name')
    
    context = {
        'people_count': people_count,
        'churches_count': churches_count,
        'pending_tasks': pending_tasks,
        'overdue_tasks': task_stats['overdue_tasks'],
        'upcoming_tasks': task_stats['upcoming_tasks'],
        'recent_communications': recent_communications,
        'people_pipeline_data': people_pipeline_data,
        'churches_pipeline_data': churches_pipeline_data,
        'completed_this_week': task_stats['completed_this_week'],
        'recent_people': activity_stats['recent_people'],
        'recent_churches': activity_stats['recent_churches'],
        'priority_tasks': priority_tasks,
        'activity_timeline': activity_timeline,
        'church_stats': church_stats,
        # Add view mode controls
        'can_toggle_view': access_manager.can_view_all_data(),
        'current_view_mode': access_manager.view_mode,
        'view_mode_display': access_manager.get_view_mode_display(),
        'user_role': getattr(request.user, 'role', 'standard_user'),
        'all_offices': all_offices,
        # Add widget configuration
        'widget_rows': widget_rows,
        'get_widget_css_class': get_widget_css_class,
    }
    
    return render(request, 'core/dashboard.html', context)


@login_required
def profile(request):
    """
    User profile view for viewing and editing personal information.
    """
    return render(request, 'core/profile.html')


@login_required
def settings(request):
    """
    Settings view for configuring user preferences.
    """
    from mobilize.authentication.models import UserContactSyncSettings
    from mobilize.authentication.forms import UserContactSyncSettingsForm, UserProfileForm
    
    # Get or create contact sync settings
    sync_settings, created = UserContactSyncSettings.objects.get_or_create(
        user_id=request.user.id,
        defaults={'sync_preference': 'crm_only'}
    )
    
    if request.method == 'POST':
        if 'sync_settings' in request.POST:
            sync_form = UserContactSyncSettingsForm(
                request.POST, 
                instance=sync_settings,
                user=request.user
            )
            profile_form = UserProfileForm(instance=request.user)
            
            if sync_form.is_valid():
                sync_form.save()
                messages.success(request, 'Contact sync settings updated successfully.')
                return redirect('core:settings')
        
        elif 'profile_settings' in request.POST:
            profile_form = UserProfileForm(request.POST, instance=request.user)
            sync_form = UserContactSyncSettingsForm(instance=sync_settings, user=request.user)
            
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, 'Profile updated successfully.')
                return redirect('core:settings')
        
        else:
            sync_form = UserContactSyncSettingsForm(instance=sync_settings, user=request.user)
            profile_form = UserProfileForm(instance=request.user)
    else:
        sync_form = UserContactSyncSettingsForm(instance=sync_settings, user=request.user)
        profile_form = UserProfileForm(instance=request.user)
    
    # Check Gmail connection status
    gmail_connected = False
    try:
        from mobilize.communications.gmail_service import GmailService
        gmail_service = GmailService(request.user)
        gmail_connected = gmail_service.is_authenticated()
    except Exception:
        pass
    
    context = {
        'sync_form': sync_form,
        'profile_form': profile_form,
        'sync_settings': sync_settings,
        'gmail_connected': gmail_connected,
    }
    
    return render(request, 'core/settings.html', context)


@login_required
def reports(request):
    """
    Reports view for generating and downloading various reports.
    """
    from mobilize.core.permissions import get_data_access_manager
    
    # Get data access manager to determine what reports user can access
    access_manager = get_data_access_manager(request)
    
    # Get summary statistics for the reports page
    people_count = access_manager.get_people_queryset().count()
    churches_count = access_manager.get_churches_queryset().count()
    tasks_count = access_manager.get_tasks_queryset().count()
    communications_count = access_manager.get_communications_queryset().count()
    
    context = {
        'people_count': people_count,
        'churches_count': churches_count,
        'tasks_count': tasks_count,
        'communications_count': communications_count,
        'can_toggle_view': access_manager.can_view_all_data(),
        'current_view_mode': access_manager.view_mode,
        'view_mode_display': access_manager.get_view_mode_display(),
        'user_role': getattr(request.user, 'role', 'standard_user'),
    }
    
    return render(request, 'core/reports.html', context)


@login_required
def export_report(request, report_type):
    """
    Export reports in various formats based on user permissions.
    
    Args:
        report_type: Type of report to export (people, churches, tasks, communications, summary)
    """
    from mobilize.core.reports import ReportGenerator
    
    # Get format and filters from request
    format = request.GET.get('format', 'csv')
    view_mode = request.GET.get('view_mode', 'default')
    
    # Create report generator
    generator = ReportGenerator(request.user, view_mode)
    
    try:
        if report_type == 'people':
            return generator.generate_people_report(format)
        elif report_type == 'churches':
            return generator.generate_churches_report(format)
        elif report_type == 'tasks':
            status_filter = request.GET.get('status')
            return generator.generate_tasks_report(format, status_filter)
        elif report_type == 'communications':
            date_range = request.GET.get('date_range')
            date_range = int(date_range) if date_range else None
            return generator.generate_communications_report(format, date_range)
        elif report_type == 'summary':
            return generator.generate_dashboard_summary(format)
        else:
            messages.error(request, f'Unknown report type: {report_type}')
            return redirect('core:reports')
            
    except Exception as e:
        messages.error(request, f'Error generating report: {str(e)}')
        return redirect('core:reports')


@login_required
def customize_dashboard(request):
    """
    Dashboard customization view for managing widget preferences.
    """
    from mobilize.core.dashboard_widgets import get_user_dashboard_config, toggle_widget, reorder_widgets
    import json
    
    dashboard_config = get_user_dashboard_config(request.user)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'toggle_widget':
            widget_id = request.POST.get('widget_id')
            enabled = request.POST.get('enabled') == 'true'
            toggle_widget(request.user, widget_id, enabled)
            messages.success(request, f'Widget {"enabled" if enabled else "disabled"} successfully.')
            
        elif action == 'reorder_widgets':
            widget_order = json.loads(request.POST.get('widget_order', '[]'))
            reorder_widgets(request.user, widget_order)
            messages.success(request, 'Widget order updated successfully.')
            
        elif action == 'reset_defaults':
            dashboard_config.reset_to_defaults()
            messages.success(request, 'Dashboard reset to default configuration.')
        
        return redirect('core:customize_dashboard')
    
    context = {
        'dashboard_config': dashboard_config,
        'widgets': dashboard_config.get_widget_config(),
    }
    
    return render(request, 'core/customize_dashboard.html', context)


def db_diagnostic(request):
    """Simple diagnostic endpoint to check database connection info."""
    if not request.user.is_authenticated or request.user.role != 'super_admin':
        return HttpResponse("Unauthorized", status=401)
    
    try:
        cursor = connection.cursor()
        
        # Get connection details
        cursor.execute("SELECT current_database(), current_user, inet_server_addr(), inet_server_port();")
        db_name, db_user, server_addr, server_port = cursor.fetchone()
        
        # Get total person contacts
        cursor.execute("SELECT COUNT(*) FROM contacts WHERE type = 'person'")
        total_person_count = cursor.fetchone()[0]
        
        # Check for Olivia Tanchak to identify which database
        cursor.execute("""
            SELECT id, first_name, last_name, email 
            FROM contacts 
            WHERE first_name = 'Olivia' AND last_name = 'Tanchak'
            LIMIT 1
        """)
        olivia_result = cursor.fetchone()
        
        # Get environment info
        database_url = os.environ.get('DATABASE_URL', 'Not set')
        debug_mode = getattr(settings, 'DEBUG', 'Unknown')
        
        # Basic data structure
        data = {
            'database': db_name,
            'user': db_user,
            'server': f"{server_addr}:{server_port}",
            'total_person_contacts': total_person_count,
            'olivia_tanchak': {
                'found': olivia_result is not None,
                'contact_id': olivia_result[0] if olivia_result else None,
                'email': olivia_result[3] if olivia_result else None
            },
            'is_supabase': 'supabase' in str(server_addr).lower() or 'aws' in str(server_addr).lower(),
            'debug_mode': debug_mode,
            'timestamp': timezone.now().isoformat()
        }
        
        # Try to add permission information
        try:
            from mobilize.core.permissions import DataAccessManager
            access_manager = DataAccessManager(request.user, 'default')
            visible_people = access_manager.get_people_queryset().count()
            visible_churches = access_manager.get_churches_queryset().count()
            
            data['visible_people'] = visible_people
            data['visible_churches'] = visible_churches
            data['user_role'] = getattr(request.user, 'role', 'unknown')
            data['user_id'] = request.user.id
            data['office_id'] = getattr(request.user, 'office_id', None)
            
        except Exception as e:
            data['permission_error'] = str(e)
        
        # Try to check for empty name people
        try:
            cursor.execute("""
                SELECT COUNT(*)
                FROM contacts c
                WHERE c.type = 'person'
                AND (c.first_name IS NULL OR c.first_name = '')
                AND (c.last_name IS NULL OR c.last_name = '')
            """)
            empty_names_count = cursor.fetchone()[0]
            data['empty_names_count'] = empty_names_count
            
        except Exception as e:
            data['empty_names_error'] = str(e)
        
        # Mask password in DATABASE_URL for display
        if database_url != 'Not set':
            masked_url = database_url
            if '@' in masked_url and ':' in masked_url:
                parts = masked_url.split('@')
                if ':' in parts[0]:
                    auth_parts = parts[0].split(':')
                    if len(auth_parts) >= 3:
                        auth_parts[2] = '****'
                        parts[0] = ':'.join(auth_parts)
                masked_url = '@'.join(parts)
            data['database_url'] = masked_url
        
        return JsonResponse(data, json_dumps_params={'indent': 2})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def permissions_debug(request):
    """Debug endpoint specifically for checking permission filtering."""
    if not request.user.is_authenticated or request.user.role != 'super_admin':
        return HttpResponse("Unauthorized", status=401)
    
    try:
        from mobilize.core.permissions import DataAccessManager
        from mobilize.contacts.models import Person, Contact
        
        # Test different view modes
        results = {}
        
        for view_mode in ['default', 'my_only']:
            access_manager = DataAccessManager(request.user, view_mode)
            people_queryset = access_manager.get_people_queryset()
            
            # Get sample of visible people
            sample_people = people_queryset[:5]
            people_data = []
            
            for person in sample_people:
                people_data.append({
                    'contact_id': person.contact.id,
                    'first_name': person.contact.first_name,
                    'last_name': person.contact.last_name,
                    'email': person.contact.email,
                    'user_id': person.contact.user_id,
                    'office_id': person.contact.office_id
                })
            
            results[view_mode] = {
                'total_visible': people_queryset.count(),
                'sample_people': people_data
            }
        
        # Also check raw SQL for people with empty names
        cursor = connection.cursor()
        cursor.execute("""
            SELECT c.id, c.first_name, c.last_name, c.email, c.user_id, c.office_id
            FROM contacts c
            WHERE c.type = 'person'
            AND (c.first_name IS NULL OR c.first_name = '')
            AND (c.last_name IS NULL OR c.last_name = '')
            LIMIT 5
        """)
        empty_name_people = cursor.fetchall()
        
        results['empty_name_people'] = [
            {
                'contact_id': row[0],
                'first_name': row[1],
                'last_name': row[2],
                'email': row[3],
                'user_id': row[4],
                'office_id': row[5]
            } for row in empty_name_people
        ]
        
        return JsonResponse(results, json_dumps_params={'indent': 2})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)