from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, View
from django.urls import reverse_lazy, reverse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.utils import timezone

from .models import Task
from .forms import TaskForm


class TaskListView(LoginRequiredMixin, ListView):
    model = Task
    template_name = 'tasks/task_list.html'
    context_object_name = 'tasks'
    paginate_by = 15

    def get_queryset(self):
        # Order by due date (nulls last), then priority
        queryset = Task.objects.all()
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


class TaskDetailView(LoginRequiredMixin, DetailView):
    model = Task
    template_name = 'tasks/task_detail.html'
    context_object_name = 'task'


class TaskCreateView(LoginRequiredMixin, CreateView):
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
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('tasks:task_list')


class TaskUpdateView(LoginRequiredMixin, UpdateView):
    model = Task
    form_class = TaskForm
    template_name = 'tasks/task_form.html'

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
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('tasks:task_detail', kwargs={'pk': self.object.pk})

class TaskDeleteView(LoginRequiredMixin, DeleteView):
    model = Task
    template_name = 'tasks/task_confirm_delete.html'
    success_url = reverse_lazy('tasks:task_list')
    context_object_name = 'task'


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
