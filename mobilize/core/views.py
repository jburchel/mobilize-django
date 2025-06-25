from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.contrib import messages
from django.core.cache import cache
from django.utils.http import urlencode
from datetime import datetime, timedelta
from mobilize.authentication.decorators import ensure_user_office_assignment


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
            status='pending',
            due_date__lt=datetime.now().date()
        )),
        upcoming_tasks=Count('pk', filter=Q(
            status='pending',
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
    
    # Get people pipeline distribution - OPTIMIZED with database aggregation
    from mobilize.pipeline.models import PipelineContact, PipelineStage
    
    # Get all pipeline stage names for mapping
    stage_name_map = dict(MAIN_PEOPLE_PIPELINE_STAGES)
    
    # Use database aggregation instead of Python loops
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
    
    # Get churches pipeline distribution - OPTIMIZED with database aggregation
    church_stage_name_map = dict(MAIN_CHURCH_PIPELINE_STAGES)
    
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
        user=request.user,
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
