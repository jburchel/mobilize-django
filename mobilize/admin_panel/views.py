from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, View
from django.urls import reverse_lazy, reverse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.contrib import messages
from django.utils import timezone

from mobilize.authentication.decorators import super_admin_required, office_admin_required
from mobilize.authentication.models import User
from .models import Office, UserOffice
from .forms import OfficeForm


# Apply the super_admin_required decorator to class-based views
class SuperAdminRequiredMixin:
    @classmethod
    def as_view(cls, **kwargs):
        view = super().as_view(**kwargs)
        return super_admin_required(view)


class OfficeListView(LoginRequiredMixin, ListView):
    model = Office
    template_name = 'admin_panel/office_list.html'
    context_object_name = 'offices'
    
    def get_queryset(self):
        # Super admins can see all offices
        if self.request.user.role == 'super_admin':
            return Office.objects.all()
        
        # Other users can only see offices they're assigned to
        return Office.objects.filter(
            useroffice__user=self.request.user
        ).distinct()


class OfficeDetailView(LoginRequiredMixin, DetailView):
    model = Office
    template_name = 'admin_panel/office_detail.html'
    context_object_name = 'office'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['users'] = User.objects.filter(
            useroffice__office=self.object
        )
        return context


class OfficeCreateView(SuperAdminRequiredMixin, CreateView):
    model = Office
    form_class = OfficeForm
    template_name = 'admin_panel/office_form.html'
    success_url = reverse_lazy('admin_panel:office_list')


class OfficeUpdateView(SuperAdminRequiredMixin, UpdateView):
    model = Office
    form_class = OfficeForm
    template_name = 'admin_panel/office_form.html'
    
    def get_success_url(self):
        return reverse('admin_panel:office_detail', kwargs={'pk': self.object.pk})


class OfficeDeleteView(SuperAdminRequiredMixin, DeleteView):
    model = Office
    template_name = 'admin_panel/office_confirm_delete.html'
    success_url = reverse_lazy('admin_panel:office_list')


class OfficeUserListView(LoginRequiredMixin, ListView):
    template_name = 'admin_panel/office_users.html'
    context_object_name = 'office_users'
    
    def get_queryset(self):
        self.office = get_object_or_404(Office, pk=self.kwargs['office_id'])
        
        # Check if user has permission to view this office's users
        if not (self.request.user.role == 'super_admin' or 
                (self.request.user.role == 'office_admin' and 
                 UserOffice.objects.filter(user_id=str(self.request.user.id), office=self.office).exists())):
            return UserOffice.objects.none()
        
        return UserOffice.objects.filter(office=self.office)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['office'] = self.office
        return context


class AddUserToOfficeView(LoginRequiredMixin, View):
    def get(self, request, office_id):
        office = get_object_or_404(Office, pk=office_id)
        
        # Check if user has permission to add users to this office
        if not (request.user.role == 'super_admin' or 
                (request.user.role == 'office_admin' and 
                 UserOffice.objects.filter(user_id=str(request.user.id), office=office).exists())):
            messages.error(request, "You don't have permission to add users to this office.")
            return redirect('admin_panel:office_detail', pk=office_id)
        
        # Get users not already in this office
        existing_users = UserOffice.objects.filter(office=office).values_list('user_id', flat=True)
        available_users = User.objects.exclude(id__in=existing_users)
        
        return render(request, 'admin_panel/add_user_to_office.html', {
            'office': office,
            'available_users': available_users,
        })
    
    def post(self, request, office_id):
        office = get_object_or_404(Office, pk=office_id)
        
        # Check if user has permission to add users to this office
        if not (request.user.role == 'super_admin' or 
                (request.user.role == 'office_admin' and 
                 UserOffice.objects.filter(user_id=str(request.user.id), office=office).exists())):
            messages.error(request, "You don't have permission to add users to this office.")
            return redirect('admin_panel:office_detail', pk=office_id)
        
        user_id = request.POST.get('user_id')
        is_primary = request.POST.get('is_primary') == 'on'
        
        if not user_id:
            messages.error(request, "Please select a user.")
            return redirect('admin_panel:add_user_to_office', office_id=office_id)
        
        user = get_object_or_404(User, pk=user_id)
        
        # Create the UserOffice relationship
        UserOffice.objects.create(
            user_id=str(user.id),
            office=office,
            is_primary=is_primary,
            assigned_at=timezone.now()
        )
        
        messages.success(request, f"{user.get_full_name()} has been added to {office.name}.")
        return redirect('admin_panel:office_users', office_id=office_id)


class RemoveUserFromOfficeView(LoginRequiredMixin, View):
    def post(self, request, office_id, user_id):
        office = get_object_or_404(Office, pk=office_id)
        user = get_object_or_404(User, pk=user_id)
        
        # Check if user has permission to remove users from this office
        if not (request.user.role == 'super_admin' or 
                (request.user.role == 'office_admin' and 
                 UserOffice.objects.filter(user_id=str(request.user.id), office=office).exists() and 
                 user_id != request.user.id)):  # Can't remove yourself
            messages.error(request, "You don't have permission to remove this user.")
            return redirect('admin_panel:office_users', office_id=office_id)
        
        # Delete the UserOffice relationship
        user_office = get_object_or_404(UserOffice, user_id=str(user_id), office=office)
        user_office.delete()
        
        messages.success(request, f"{user.get_full_name()} has been removed from {office.name}.")
        return redirect('admin_panel:office_users', office_id=office_id)


class UpdateUserOfficePrimaryView(LoginRequiredMixin, View):
    def post(self, request, office_id, user_id):
        office = get_object_or_404(Office, pk=office_id)
        user = get_object_or_404(User, pk=user_id)
        
        # Check if user has permission to update office assignments
        if not (request.user.role == 'super_admin' or 
                (request.user.role == 'office_admin' and 
                 UserOffice.objects.filter(user_id=str(request.user.id), office=office).exists() and 
                 user_id != request.user.id)):  # Can't change your own primary office
            messages.error(request, "You don't have permission to update this user's office assignment.")
            return redirect('admin_panel:office_users', office_id=office_id)
        
        is_primary = request.POST.get('is_primary') == 'on'
        
        # Update the UserOffice relationship
        user_office = get_object_or_404(UserOffice, user_id=str(user_id), office=office)
        
        if is_primary:
            # Set all other offices for this user as non-primary
            UserOffice.objects.filter(user_id=str(user_id), is_primary=True).update(is_primary=False)
        
        user_office.is_primary = is_primary
        user_office.save()
        
        messages.success(request, f"{user.get_full_name()}'s primary office has been updated.")
        return redirect('admin_panel:office_users', office_id=office_id)


class CrossOfficeReportView(LoginRequiredMixin, View):
    """
    Cross-office reporting view for super admins.
    
    Provides insights across all offices including:
    - User distribution by office
    - Contact counts by office  
    - Performance metrics
    """
    
    def get(self, request):
        # Only super admins can access cross-office reports
        if request.user.role != 'super_admin':
            messages.error(request, "You don't have permission to view cross-office reports.")
            return redirect('admin_panel:office_list')
        
        from mobilize.contacts.models import Person
        from mobilize.churches.models import Church
        from mobilize.tasks.models import Task
        from django.db.models import Count, Q
        
        # Get all offices with statistics
        offices = Office.objects.annotate(
            user_count_db=Count('useroffice', distinct=True),
            admin_count_db=Count('useroffice', filter=Q(useroffice__user__role__in=['super_admin', 'office_admin']), distinct=True)
        ).order_by('name')
        
        # Calculate additional metrics for each office
        office_data = []
        for office in offices:
            # Get contact counts for this office
            people_count = Person.objects.filter(
                Q(contact__office_id=office.id) | 
                Q(contact__user__in=UserOffice.objects.filter(office=office).values_list('user_id', flat=True))
            ).distinct().count()
            
            churches_count = Church.objects.filter(contact__office_id=office.id).count()
            
            # Get task counts for this office
            office_users = UserOffice.objects.filter(office=office).values_list('user', flat=True)
            pending_tasks = Task.objects.filter(
                Q(assigned_to__in=office_users) | Q(created_by__in=office_users),
                status='pending'
            ).distinct().count()
            
            office_data.append({
                'office': office,
                'people_count': people_count,
                'churches_count': churches_count,
                'pending_tasks': pending_tasks,
                'total_contacts': people_count + churches_count
            })
        
        # Overall statistics
        total_stats = {
            'total_offices': offices.count(),
            'active_offices': offices.filter(is_active=True).count(),
            'total_users': User.objects.count(),
            'total_people': Person.objects.count(),
            'total_churches': Church.objects.count(),
            'total_tasks': Task.objects.count(),
        }
        
        return render(request, 'admin_panel/cross_office_report.html', {
            'office_data': office_data,
            'total_stats': total_stats,
        })
