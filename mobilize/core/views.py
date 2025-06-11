from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
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
    return render(request, 'core/settings.html')
