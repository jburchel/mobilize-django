from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, View
from django.urls import reverse_lazy, reverse
from django.contrib.auth.mixins import LoginRequiredMixin
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
        # Check if user has office assignment (except super_admin)
        if request.user.role != 'super_admin' and not request.user.useroffice_set.exists():
            raise PermissionDenied("Access denied. User not assigned to any office.")
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        # Order by due date (nulls last), then priority
        queryset = Task.objects.select_related(
            'created_by', 'assigned_to', 'person', 'church', 'office'
        ).prefetch_related('contact')
        
        # Apply office-level filtering based on person/church office or task office
        if self.request.user.role != 'super_admin':
            user_offices = self.request.user.useroffice_set.values_list('office_id', flat=True)
            
            # Filter tasks based on:
            # 1. Tasks assigned to user
            # 2. Tasks created by user
            # 3. Tasks where person/church belongs to user's office
            # 4. Tasks directly assigned to user's office
            queryset = queryset.filter(
                models.Q(assigned_to=self.request.user) |
                models.Q(created_by=self.request.user) |
                models.Q(person__contact__office__in=user_offices) |
                models.Q(church__contact__office__in=user_offices) |
                models.Q(office__in=user_offices)
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
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Pass filter values to template
        context['current_status'] = self.request.GET.get('status', '')
        context['current_priority'] = self.request.GET.get('priority', '')
        context['current_assigned'] = self.request.GET.get('assigned_to', '')
        context['current_due'] = self.request.GET.get('due', '')
        context['search_query'] = self.request.GET.get('search', '')
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
            user_offices = self.request.user.useroffice_set.values_list('office_id', flat=True)
            
            queryset = queryset.filter(
                models.Q(assigned_to=self.request.user) |
                models.Q(created_by=self.request.user) |
                models.Q(person__contact__office__in=user_offices) |
                models.Q(church__contact__office__in=user_offices) |
                models.Q(office__in=user_offices)
            ).distinct()
        
        return queryset


class TaskCreateView(LoginRequiredMixin, CreateView):
    
    def dispatch(self, request, *args, **kwargs):
        # Prevent limited users from creating
        if request.user.role == 'limited_user':
            raise PermissionDenied("Limited users cannot create tasks")
        
        # Check office assignment
        if request.user.role != 'super_admin' and not request.user.useroffice_set.exists():
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
        if request.user.role != 'super_admin' and not request.user.useroffice_set.exists():
            raise PermissionDenied("Access denied. User not assigned to any office.")
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        """Filter tasks based on office permissions"""
        queryset = Task.objects.select_related(
            'created_by', 'assigned_to', 'person', 'church', 'office'
        )
        
        # Apply office-level filtering
        if self.request.user.role != 'super_admin':
            user_offices = self.request.user.useroffice_set.values_list('office_id', flat=True)
            
            queryset = queryset.filter(
                models.Q(assigned_to=self.request.user) |
                models.Q(created_by=self.request.user) |
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
        if request.user.role != 'super_admin' and not request.user.useroffice_set.exists():
            raise PermissionDenied("Access denied. User not assigned to any office.")
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        """Filter tasks based on office permissions"""
        queryset = Task.objects.select_related(
            'created_by', 'assigned_to', 'person', 'church', 'office'
        )
        
        # Apply office-level filtering
        if self.request.user.role != 'super_admin':
            user_offices = self.request.user.useroffice_set.values_list('office_id', flat=True)
            
            queryset = queryset.filter(
                models.Q(assigned_to=self.request.user) |
                models.Q(created_by=self.request.user) |
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
