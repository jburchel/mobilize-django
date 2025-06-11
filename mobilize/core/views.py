from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.contrib import messages
from datetime import datetime, timedelta


@login_required
def dashboard(request):
    """
    Main dashboard view displaying key metrics and pending tasks.
    
    Shows:
    - People count
    - Churches count
    - Recent communications
    - Pending tasks
    - Pipeline stage distribution
    """
    # These imports are placed here to avoid circular imports
    # Will be properly implemented when models are created
    """
    from mobilize.contacts.models import Person
    from mobilize.churches.models import Church
    from mobilize.tasks.models import Task
    from mobilize.communications.models import Communication
    
    # Get counts for dashboard widgets
    people_count = Person.objects.count()
    churches_count = Church.objects.count()
    
    # Get pending tasks
    pending_tasks = Task.objects.filter(
        status='pending',
        due_date__lte=datetime.now() + timedelta(days=7)
    ).order_by('due_date')[:5]
    
    # Get recent communications
    recent_communications = Communication.objects.all().order_by('-sent_at')[:5]
    
    # Get pipeline distribution
    pipeline_stages = Person.objects.values('pipeline_stage').annotate(
        count=Count('id')
    ).order_by('pipeline_stage')
    """
    
    # Placeholder data until models are implemented
    people_count = 0
    churches_count = 0
    pending_tasks = []
    recent_communications = []
    pipeline_stages = []
    
    context = {
        'people_count': people_count,
        'churches_count': churches_count,
        'pending_tasks': pending_tasks,
        'recent_communications': recent_communications,
        'pipeline_stages': pipeline_stages,
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
