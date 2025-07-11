from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, View
from django.urls import reverse_lazy, reverse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.utils import timezone
from django.db import models
from django.contrib import messages
from django.core.exceptions import PermissionDenied

from .models import Task
from .forms import TaskForm
from mobilize.authentication.decorators import office_data_filter


class TaskListView(LoginRequiredMixin, ListView):
    model = Task
    template_name = 'tasks/task_list.html'
    context_object_name = 'tasks'
    paginate_by = 15

    def dispatch(self, request, *args, **kwargs):
        # Check if user has office assignment (except super_admin) - temporarily disable for debugging
        # if request.user.role != 'super_admin' and not request.user.useroffice_set.exists():
        #     raise PermissionDenied("Access denied. User not assigned to any office.")
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        try:
            # Start with basic queryset
            queryset = Task.objects.select_related(
                'created_by', 'assigned_to', 'person', 'church', 'office'
            )
            
            # Apply simplified office-level filtering with error handling
            if self.request.user.role != 'super_admin':
                try:
                    # Import UserOffice here to avoid circular imports
                    from mobilize.admin_panel.models import UserOffice
                    
                    # Get user offices using the correct approach
                    user_offices = list(UserOffice.objects.filter(
                        user_id=str(self.request.user.id)
                    ).values_list('office_id', flat=True))
                    
                    if user_offices:
                        # Filter tasks based on user access - only show assigned tasks
                        queryset = queryset.filter(
                            models.Q(assigned_to=self.request.user) |
                            models.Q(person__contact__office__in=user_offices) |
                            models.Q(church__contact__office__in=user_offices) |
                            models.Q(office__in=user_offices)
                        ).distinct()
                    else:
                        # If user has no office assignments, show only their assigned tasks
                        queryset = queryset.filter(
                            models.Q(assigned_to=self.request.user)
                        ).distinct()
                except Exception as e:
                    # If office filtering fails, fall back to user's assigned tasks only
                    queryset = queryset.filter(
                        models.Q(assigned_to=self.request.user)
                    ).distinct()
            
            # Apply filters from GET parameters
            status_filter = self.request.GET.get('status')
            if status_filter:
                queryset = queryset.filter(status=status_filter)
            
            priority_filter = self.request.GET.get('priority')
            if priority_filter:
                queryset = queryset.filter(priority=priority_filter)
            
            assigned_filter = self.request.GET.get('assigned_to')
            if assigned_filter:
                if assigned_filter == 'me':
                    queryset = queryset.filter(assigned_to=self.request.user)
                elif assigned_filter == 'unassigned':
                    queryset = queryset.filter(assigned_to__isnull=True)
            
            due_filter = self.request.GET.get('due')
            if due_filter:
                from datetime import date, timedelta
                today = date.today()
                if due_filter == 'overdue':
                    queryset = queryset.filter(due_date__lt=today, status__in=['pending', 'in_progress'])
                elif due_filter == 'today':
                    queryset = queryset.filter(due_date=today)
                elif due_filter == 'week':
                    queryset = queryset.filter(due_date__gte=today, due_date__lte=today + timedelta(days=7))
                elif due_filter == 'month':
                    queryset = queryset.filter(due_date__gte=today, due_date__lte=today + timedelta(days=30))
            
            # General search
            search_query = self.request.GET.get('search')
            if search_query:
                from django.db.models import Q
                queryset = queryset.filter(
                    Q(title__icontains=search_query) |
                    Q(description__icontains=search_query) |
                    Q(person__contact__first_name__icontains=search_query) |
                    Q(person__contact__last_name__icontains=search_query) |
                    Q(church__contact__church_name__icontains=search_query) |
                    Q(church__name__icontains=search_query)
                )
            
            # Custom sort: incomplete tasks first, then completed tasks.
            # Within incomplete, sort by due_date (nulls last), then priority.
            # Within completed, sort by completed_at descending.
            queryset = queryset.annotate(
                is_completed_val=models.Case(
                    models.When(status='completed', then=models.Value(1)),
                    default=models.Value(0),
                    output_field=models.IntegerField()
                )
            ).order_by('is_completed_val', models.F('due_date').asc(nulls_last=True), 'priority', models.F('completed_at').desc(nulls_last=True))
            return queryset
            
        except Exception as e:
            # If there's any error, return empty queryset to prevent 500 errors
            import logging
            logging.error(f"Error in TaskListView.get_queryset: {e}")
            return Task.objects.none()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Pass filter values to template
        context['current_status'] = self.request.GET.get('status', '')
        context['current_priority'] = self.request.GET.get('priority', '')
        context['current_assigned'] = self.request.GET.get('assigned_to', '')
        context['current_due'] = self.request.GET.get('due', '')
        context['search_query'] = self.request.GET.get('search', '')
        
        # Add users and offices for bulk operations
        from django.contrib.auth import get_user_model
        from mobilize.admin_panel.models import Office
        User = get_user_model()
        
        context['users'] = User.objects.filter(is_active=True).order_by('first_name', 'last_name', 'email')
        context['offices'] = Office.objects.filter(is_active=True).order_by('name')
        
        return context


class TaskDetailView(LoginRequiredMixin, DetailView):
    model = Task
    template_name = 'tasks/task_detail.html'
    context_object_name = 'task'
    
    def get_queryset(self):
        queryset = Task.objects.select_related(
            'created_by', 'assigned_to', 'person', 'church', 'office', 'contact'
        )
        
        # Apply office-level filtering
        if self.request.user.role != 'super_admin':
            from mobilize.admin_panel.models import UserOffice
            user_offices = UserOffice.objects.filter(
                user_id=str(self.request.user.id)
            ).values_list('office_id', flat=True)
            
            queryset = queryset.filter(
                models.Q(assigned_to=self.request.user) |
                models.Q(person__contact__office__in=user_offices) |
                models.Q(church__contact__office__in=user_offices) |
                models.Q(office__in=user_offices)
            ).distinct()
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        task = self.object
        
        # Collect all associated people from different relationships
        associated_people = []
        
        # 1. Direct person relationship
        if task.person:
            associated_people.append({
                'person': task.person,
                'relationship_type': 'Direct Assignment',
                'description': 'Task directly assigned to this person'
            })
        
        # 2. If task has a church, get church contacts (people associated with the church)
        if task.church:
            # Get people who are members or contacts of this church
            church_people = task.church.members.select_related('contact').all()
            for person in church_people:
                associated_people.append({
                    'person': person,
                    'relationship_type': 'Church Member',
                    'description': f'Member of {task.church.name}'
                })
        
        # 3. If task has a generic contact that's a person
        if task.contact and task.contact.type == 'person':
            try:
                person = task.contact.person
                # Only add if not already in the list (avoid duplicates)
                if not any(ap['person'].pk == person.pk for ap in associated_people):
                    associated_people.append({
                        'person': person,
                        'relationship_type': 'Contact Reference',
                        'description': 'Referenced through contact field'
                    })
            except:
                pass  # Handle case where person doesn't exist for contact
        
        context['associated_people'] = associated_people
        
        return context


class TaskCreateView(LoginRequiredMixin, CreateView):
    
    def dispatch(self, request, *args, **kwargs):
        # Prevent limited users from creating
        if request.user.role == 'limited_user':
            raise PermissionDenied("Limited users cannot create tasks")
        
        # Check office assignment
        if request.user.role != 'super_admin':
            from mobilize.admin_panel.models import UserOffice
            if not UserOffice.objects.filter(user_id=str(request.user.id)).exists():
                raise PermissionDenied("Access denied. User not assigned to any office.")
        
        return super().dispatch(request, *args, **kwargs)
    model = Task
    form_class = TaskForm
    template_name = 'tasks/task_form.html'

    def get_form_kwargs(self):
        """Pass the request object to the form's keyword arguments."""
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        """If the form is valid, save the associated model and set created_by."""
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        
        # If this is a recurring template, set up the next occurrence date
        if form.instance.is_recurring_template:
            form.instance.next_occurrence_date = form.instance.calculate_next_occurrence()
            form.instance.save(update_fields=['next_occurrence_date'])
            messages.success(self.request, f'Recurring task template "{form.instance.title}" created successfully.')
        else:
            messages.success(self.request, f'Task "{form.instance.title}" created successfully.')
        
        # Handle Google Calendar sync if enabled
        if form.instance.google_calendar_sync_enabled:
            self._sync_task_to_calendar(form.instance)
            
        return response
    
    def _sync_task_to_calendar(self, task):
        """Sync the task to Google Calendar if user is authenticated"""
        try:
            from mobilize.communications.google_calendar_service import GoogleCalendarService
            
            # Debug: Check if task has due_date
            if not task.due_date:
                messages.warning(
                    self.request,
                    'Task created but calendar sync skipped: Task must have a due date for calendar sync.'
                )
                return
            
            calendar_service = GoogleCalendarService(self.request.user)
            
            # Debug: Check if user has Google tokens
            from mobilize.authentication.models import GoogleToken
            try:
                google_token = GoogleToken.objects.get(user=self.request.user)
                print(f"DEBUG: User {self.request.user.username} has Google token, expires: {google_token.expires_at}")
            except GoogleToken.DoesNotExist:
                print(f"DEBUG: User {self.request.user.username} has NO Google token")
                messages.warning(
                    self.request,
                    f'Task created but Google Calendar sync requires Google authentication. '
                    f'<a href="/auth/google-auth/">Click here to authenticate with Google</a>',
                    extra_tags='safe'
                )
                return
            
            # Debug: More detailed authentication check
            if calendar_service.is_authenticated():
                result = calendar_service.create_event_from_task(task)
                if result['success']:
                    messages.success(
                        self.request, 
                        f'Task synced to Google Calendar successfully! '
                        f'<a href="{result["event_link"]}" target="_blank">View in Calendar</a>',
                        extra_tags='safe'
                    )
                else:
                    messages.warning(
                        self.request,
                        f'Task created but calendar sync failed: {result["error"]}'
                    )
            else:
                messages.warning(
                    self.request,
                    f'Task created but Google Calendar sync is not set up for user {self.request.user.username}. '
                    'Please authenticate with Google Calendar in your settings.'
                )
        except Exception as e:
            messages.warning(
                self.request,
                f'Task created but calendar sync failed: {str(e)}'
            )

    def get_success_url(self):
        return reverse('tasks:task_list')


class TaskUpdateView(LoginRequiredMixin, UpdateView):
    model = Task
    form_class = TaskForm
    template_name = 'tasks/task_form.html'
    
    def dispatch(self, request, *args, **kwargs):
        # Prevent limited users from editing
        if request.user.role == 'limited_user':
            raise PermissionDenied("Limited users cannot edit tasks")
        
        # Check office assignment
        if request.user.role != 'super_admin':
            from mobilize.admin_panel.models import UserOffice
            if not UserOffice.objects.filter(user_id=str(request.user.id)).exists():
                raise PermissionDenied("Access denied. User not assigned to any office.")
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        """Filter tasks based on office permissions"""
        queryset = Task.objects.select_related(
            'created_by', 'assigned_to', 'person', 'church', 'office'
        )
        
        # Apply office-level filtering
        if self.request.user.role != 'super_admin':
            from mobilize.admin_panel.models import UserOffice
            user_offices = UserOffice.objects.filter(
                user_id=str(self.request.user.id)
            ).values_list('office_id', flat=True)
            
            queryset = queryset.filter(
                models.Q(assigned_to=self.request.user) |
                models.Q(person__contact__office__in=user_offices) |
                models.Q(church__contact__office__in=user_offices) |
                models.Q(office__in=user_offices)
            ).distinct()
        
        return queryset

    def get_form_kwargs(self):
        """Pass the request object to the form's keyword arguments."""
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        task = form.instance 
        original_task = get_object_or_404(Task, pk=self.object.pk)

        if form.cleaned_data.get('status') == 'completed' and original_task.status != 'completed':
            task.completed_at = timezone.now()
        elif form.cleaned_data.get('status') != 'completed' and original_task.status == 'completed':
            task.completed_at = None
            task.completion_notes = "" # Clear completion notes if marked incomplete
            
        response = super().form_valid(form)
        
        # Update next occurrence date if this is a recurring template and relevant fields changed
        if (task.is_recurring_template and 
            (original_task.recurring_pattern != task.recurring_pattern or 
             original_task.due_date != task.due_date)):
            task.next_occurrence_date = task.calculate_next_occurrence()
            task.save(update_fields=['next_occurrence_date'])
        
        # Handle Google Calendar sync if enabled and not already synced
        if (task.google_calendar_sync_enabled and 
            not task.google_calendar_event_id and 
            not original_task.google_calendar_sync_enabled):
            self._sync_task_to_calendar(task)
            
        messages.success(self.request, f'Task "{task.title}" updated successfully.')
        return response
    
    def _sync_task_to_calendar(self, task):
        """Sync the task to Google Calendar if user is authenticated"""
        try:
            from mobilize.communications.google_calendar_service import GoogleCalendarService
            
            # Debug: Check if task has due_date
            if not task.due_date:
                messages.warning(
                    self.request,
                    'Task updated but calendar sync skipped: Task must have a due date for calendar sync.'
                )
                return
            
            calendar_service = GoogleCalendarService(self.request.user)
            if calendar_service.is_authenticated():
                result = calendar_service.create_event_from_task(task)
                if result['success']:
                    messages.success(
                        self.request, 
                        f'Task synced to Google Calendar successfully! '
                        f'<a href="{result["event_link"]}" target="_blank">View in Calendar</a>',
                        extra_tags='safe'
                    )
                else:
                    messages.warning(
                        self.request,
                        f'Task updated but calendar sync failed: {result["error"]}'
                    )
            else:
                messages.warning(
                    self.request,
                    f'Task updated but Google Calendar sync is not set up for user {self.request.user.username}. '
                    'Please authenticate with Google Calendar in your settings.'
                )
        except Exception as e:
            messages.warning(
                self.request,
                f'Task updated but calendar sync failed: {str(e)}'
            )

    def get_success_url(self):
        return reverse('tasks:task_detail', kwargs={'pk': self.object.pk})

class TaskDeleteView(LoginRequiredMixin, DeleteView):
    model = Task
    template_name = 'tasks/task_confirm_delete.html'
    success_url = reverse_lazy('tasks:task_list')
    context_object_name = 'task'
    
    def dispatch(self, request, *args, **kwargs):
        # Prevent limited users from deleting
        if request.user.role == 'limited_user':
            raise PermissionDenied("Limited users cannot delete tasks")
        
        # Check office assignment
        if request.user.role != 'super_admin':
            from mobilize.admin_panel.models import UserOffice
            if not UserOffice.objects.filter(user_id=str(request.user.id)).exists():
                raise PermissionDenied("Access denied. User not assigned to any office.")
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        """Filter tasks based on office permissions"""
        queryset = Task.objects.select_related(
            'created_by', 'assigned_to', 'person', 'church', 'office'
        )
        
        # Apply office-level filtering
        if self.request.user.role != 'super_admin':
            from mobilize.admin_panel.models import UserOffice
            user_offices = UserOffice.objects.filter(
                user_id=str(self.request.user.id)
            ).values_list('office_id', flat=True)
            
            queryset = queryset.filter(
                models.Q(assigned_to=self.request.user) |
                models.Q(person__contact__office__in=user_offices) |
                models.Q(church__contact__office__in=user_offices) |
                models.Q(office__in=user_offices)
            ).distinct()
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        task = self.get_object()
        
        # Add context for recurring task deletion
        if task.is_recurring_template:
            context['occurrence_count'] = task.occurrences.count()
        elif task.parent_task:
            context['is_recurring_instance'] = True
            context['parent_task'] = task.parent_task
            
        return context
        
    def delete(self, request, *args, **kwargs):
        task = self.get_object()
        
        if task.is_recurring_template:
            # Deleting a recurring template
            occurrence_count = task.occurrences.count()
            if occurrence_count > 0:
                messages.warning(
                    request, 
                    f'Deleted recurring template "{task.title}" and {occurrence_count} generated instances.'
                )
            else:
                messages.success(request, f'Deleted recurring template "{task.title}".')
        else:
            messages.success(request, f'Deleted task "{task.title}".')
            
        return super().delete(request, *args, **kwargs)


class TaskCompleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        task = get_object_or_404(Task, pk=pk)
        if task.status != 'completed':
            task.status = 'completed'
            task.completed_at = timezone.now()
            task.save(update_fields=['status', 'completed_at', 'updated_at'])
            return JsonResponse({
                'success': True, 
                'status': task.get_status_display(), 
                'completed_at_formatted': task.completed_at.strftime('%Y-%m-%d') if task.completed_at else None
            })
        return JsonResponse({'success': False, 'message': 'Task already completed or no change.'}, status=400)


class TaskCategoryListView(LoginRequiredMixin, ListView):
    template_name = 'tasks/category_list.html'
    context_object_name = 'categories'
    
    def get_queryset(self):
        # This will be implemented with actual TaskCategory model
        return []


class TaskCategoryDetailView(LoginRequiredMixin, DetailView):
    template_name = 'tasks/category_detail.html'
    context_object_name = 'category'
    
    def get_queryset(self):
        # This will be implemented with actual TaskCategory model
        return []


class TaskCategoryCreateView(LoginRequiredMixin, CreateView):
    template_name = 'tasks/category_form.html'
    fields = ['name', 'description']
    
    def get_success_url(self):
        return reverse('tasks:category_list')


class TaskCategoryUpdateView(LoginRequiredMixin, UpdateView):
    template_name = 'tasks/category_form.html'
    fields = ['name', 'description']
    
    def get_queryset(self):
        # This will be implemented with actual TaskCategory model
        return []
    
    def get_success_url(self):
        return reverse('tasks:category_detail', kwargs={'pk': self.object.pk})


class TaskCategoryDeleteView(LoginRequiredMixin, DeleteView):
    template_name = 'tasks/category_confirm_delete.html'
    success_url = reverse_lazy('tasks:category_list')
    
    def get_queryset(self):
        # This will be implemented with actual TaskCategory model
        return []


# Bulk Operations Views
@login_required
@require_POST
def bulk_delete_tasks(request):
    """Delete selected tasks"""
    task_ids = request.POST.get('task_ids', '').split(',')
    task_ids = [id.strip() for id in task_ids if id.strip()]
    
    if not task_ids:
        messages.error(request, 'No tasks selected for deletion.')
        return redirect('tasks:task_list')
    
    try:
        # Get tasks that user has permission to delete
        if request.user.role == 'super_admin':
            tasks = Task.objects.filter(id__in=task_ids)
        else:
            from mobilize.admin_panel.models import UserOffice
            user_offices = UserOffice.objects.filter(
                user_id=str(request.user.id)
            ).values_list('office_id', flat=True)
            
            tasks = Task.objects.filter(
                id__in=task_ids
            ).filter(
                models.Q(assigned_to=request.user) |
                models.Q(person__contact__office__in=user_offices) |
                models.Q(church__contact__office__in=user_offices) |
                models.Q(office__in=user_offices)
            ).distinct()
        
        count = tasks.count()
        tasks.delete()
        messages.success(request, f'Successfully deleted {count} tasks.')
        
    except Exception as e:
        messages.error(request, f'Error deleting tasks: {str(e)}')
    
    return redirect('tasks:task_list')


@login_required
@require_POST  
def bulk_update_task_status(request):
    """Update status for selected tasks"""
    task_ids = request.POST.get('task_ids', '').split(',')
    task_ids = [id.strip() for id in task_ids if id.strip()]
    status = request.POST.get('status', '').strip()
    
    if not task_ids:
        messages.error(request, 'No tasks selected.')
        return redirect('tasks:task_list')
        
    if not status:
        messages.error(request, 'No status selected.')
        return redirect('tasks:task_list')
    
    try:
        # Get tasks that user has permission to update
        if request.user.role == 'super_admin':
            tasks = Task.objects.filter(id__in=task_ids)
        else:
            from mobilize.admin_panel.models import UserOffice
            user_offices = UserOffice.objects.filter(
                user_id=str(request.user.id)
            ).values_list('office_id', flat=True)
            
            tasks = Task.objects.filter(
                id__in=task_ids
            ).filter(
                models.Q(assigned_to=request.user) |
                models.Q(person__contact__office__in=user_offices) |
                models.Q(church__contact__office__in=user_offices) |
                models.Q(office__in=user_offices)
            ).distinct()
        
        count = tasks.count()
        
        # Update status and handle completion timestamp
        for task in tasks:
            task.status = status
            if status == 'completed':
                task.completed_at = timezone.now()
            elif task.status == 'completed' and status != 'completed':
                task.completed_at = None
            task.save()
        
        status_display = dict(Task.STATUS_CHOICES).get(status, status)
        messages.success(request, f'Successfully updated {count} tasks to {status_display}.')
        
    except Exception as e:
        messages.error(request, f'Error updating task status: {str(e)}')
    
    return redirect('tasks:task_list')


@login_required
@require_POST
def bulk_update_task_priority(request):
    """Update priority for selected tasks"""
    task_ids = request.POST.get('task_ids', '').split(',')
    task_ids = [id.strip() for id in task_ids if id.strip()]
    priority = request.POST.get('priority', '').strip()
    
    if not task_ids:
        messages.error(request, 'No tasks selected.')
        return redirect('tasks:task_list')
        
    if not priority:
        messages.error(request, 'No priority selected.')
        return redirect('tasks:task_list')
    
    try:
        # Get tasks that user has permission to update
        if request.user.role == 'super_admin':
            tasks = Task.objects.filter(id__in=task_ids)
        else:
            from mobilize.admin_panel.models import UserOffice
            user_offices = UserOffice.objects.filter(
                user_id=str(request.user.id)
            ).values_list('office_id', flat=True)
            
            tasks = Task.objects.filter(
                id__in=task_ids
            ).filter(
                models.Q(assigned_to=request.user) |
                models.Q(person__contact__office__in=user_offices) |
                models.Q(church__contact__office__in=user_offices) |
                models.Q(office__in=user_offices)
            ).distinct()
        
        count = tasks.update(priority=priority)
        priority_display = dict(Task.PRIORITY_CHOICES).get(priority, priority)
        messages.success(request, f'Successfully updated {count} tasks to {priority_display} priority.')
        
    except Exception as e:
        messages.error(request, f'Error updating task priority: {str(e)}')
    
    return redirect('tasks:task_list')


@login_required
@require_POST
def bulk_assign_task_user(request):
    """Assign selected tasks to a user"""
    task_ids = request.POST.get('task_ids', '').split(',')
    task_ids = [id.strip() for id in task_ids if id.strip()]
    user_id = request.POST.get('user_id', '').strip()
    
    if not task_ids:
        messages.error(request, 'No tasks selected.')
        return redirect('tasks:task_list')
        
    if not user_id:
        messages.error(request, 'No user selected.')
        return redirect('tasks:task_list')
    
    try:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        assigned_user = get_object_or_404(User, id=user_id)
        
        # Get tasks that user has permission to update
        if request.user.role == 'super_admin':
            tasks = Task.objects.filter(id__in=task_ids)
        else:
            from mobilize.admin_panel.models import UserOffice
            user_offices = UserOffice.objects.filter(
                user_id=str(request.user.id)
            ).values_list('office_id', flat=True)
            
            tasks = Task.objects.filter(
                id__in=task_ids
            ).filter(
                models.Q(assigned_to=request.user) |
                models.Q(person__contact__office__in=user_offices) |
                models.Q(church__contact__office__in=user_offices) |
                models.Q(office__in=user_offices)
            ).distinct()
        
        count = tasks.update(assigned_to=assigned_user)
        user_name = assigned_user.get_full_name() or assigned_user.email
        messages.success(request, f'Successfully assigned {count} tasks to {user_name}.')
        
    except Exception as e:
        messages.error(request, f'Error assigning tasks: {str(e)}')
    
    return redirect('tasks:task_list')


@login_required
@require_POST
def bulk_assign_task_office(request):
    """Assign selected tasks to an office"""
    task_ids = request.POST.get('task_ids', '').split(',')
    task_ids = [id.strip() for id in task_ids if id.strip()]
    office_id = request.POST.get('office_id', '').strip()
    
    if not task_ids:
        messages.error(request, 'No tasks selected.')
        return redirect('tasks:task_list')
        
    if not office_id:
        messages.error(request, 'No office selected.')
        return redirect('tasks:task_list')
    
    try:
        from mobilize.admin_panel.models import Office
        office = get_object_or_404(Office, id=office_id)
        
        # Get tasks that user has permission to update
        if request.user.role == 'super_admin':
            tasks = Task.objects.filter(id__in=task_ids)
        else:
            from mobilize.admin_panel.models import UserOffice
            user_offices = UserOffice.objects.filter(
                user_id=str(request.user.id)
            ).values_list('office_id', flat=True)
            
            tasks = Task.objects.filter(
                id__in=task_ids
            ).filter(
                models.Q(assigned_to=request.user) |
                models.Q(person__contact__office__in=user_offices) |
                models.Q(church__contact__office__in=user_offices) |
                models.Q(office__in=user_offices)
            ).distinct()
        
        count = tasks.update(office=office)
        messages.success(request, f'Successfully assigned {count} tasks to {office.name}.')
        
    except Exception as e:
        messages.error(request, f'Error assigning tasks to office: {str(e)}')
    
    return redirect('tasks:task_list')


@login_required
@require_POST
def bulk_complete_tasks(request):
    """Mark selected tasks as completed"""
    task_ids = request.POST.get('task_ids', '').split(',')
    task_ids = [id.strip() for id in task_ids if id.strip()]
    
    if not task_ids:
        messages.error(request, 'No tasks selected.')
        return redirect('tasks:task_list')
    
    try:
        # Get tasks that user has permission to update
        if request.user.role == 'super_admin':
            tasks = Task.objects.filter(id__in=task_ids)
        else:
            from mobilize.admin_panel.models import UserOffice
            user_offices = UserOffice.objects.filter(
                user_id=str(request.user.id)
            ).values_list('office_id', flat=True)
            
            tasks = Task.objects.filter(
                id__in=task_ids
            ).filter(
                models.Q(assigned_to=request.user) |
                models.Q(person__contact__office__in=user_offices) |
                models.Q(church__contact__office__in=user_offices) |
                models.Q(office__in=user_offices)
            ).distinct()
        
        count = 0
        for task in tasks:
            if task.status != 'completed':
                task.status = 'completed'
                task.completed_at = timezone.now()
                task.save()
                count += 1
        
        messages.success(request, f'Successfully completed {count} tasks.')
        
    except Exception as e:
        messages.error(request, f'Error completing tasks: {str(e)}')
    
    return redirect('tasks:task_list')
