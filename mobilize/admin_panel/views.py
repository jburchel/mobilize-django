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
        ).select_related('useroffice')
        return context


class OfficeCreateView(SuperAdminRequiredMixin, CreateView):
    model = Office
    template_name = 'admin_panel/office_form.html'
    fields = ['name', 'code', 'address', 'city', 'state', 'country', 
              'postal_code', 'phone', 'email', 'timezone_name', 'settings']
    success_url = reverse_lazy('admin_panel:office_list')


class OfficeUpdateView(SuperAdminRequiredMixin, UpdateView):
    model = Office
    template_name = 'admin_panel/office_form.html'
    fields = ['name', 'code', 'address', 'city', 'state', 'country', 
              'postal_code', 'phone', 'email', 'timezone_name', 'settings', 'is_active']
    
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
                UserOffice.objects.filter(user=self.request.user, office=self.office, 
                                         role__in=['office_admin']).exists()):
            return UserOffice.objects.none()
        
        return UserOffice.objects.filter(office=self.office).select_related('user')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['office'] = self.office
        return context


class AddUserToOfficeView(LoginRequiredMixin, View):
    def get(self, request, office_id):
        office = get_object_or_404(Office, pk=office_id)
        
        # Check if user has permission to add users to this office
        if not (request.user.role == 'super_admin' or 
                UserOffice.objects.filter(user=request.user, office=office, 
                                         role='office_admin').exists()):
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
                UserOffice.objects.filter(user=request.user, office=office, 
                                         role='office_admin').exists()):
            messages.error(request, "You don't have permission to add users to this office.")
            return redirect('admin_panel:office_detail', pk=office_id)
        
        user_id = request.POST.get('user_id')
        role = request.POST.get('role', 'standard_user')
        is_primary = request.POST.get('is_primary') == 'on'
        
        if not user_id:
            messages.error(request, "Please select a user.")
            return redirect('admin_panel:add_user_to_office', office_id=office_id)
        
        user = get_object_or_404(User, pk=user_id)
        
        # Create the UserOffice relationship
        UserOffice.objects.create(
            user=user,
            office=office,
            role=role,
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
                (UserOffice.objects.filter(user=request.user, office=office, 
                                          role='office_admin').exists() and 
                 user_id != request.user.id)):  # Can't remove yourself
            messages.error(request, "You don't have permission to remove this user.")
            return redirect('admin_panel:office_users', office_id=office_id)
        
        # Delete the UserOffice relationship
        user_office = get_object_or_404(UserOffice, user=user, office=office)
        user_office.delete()
        
        messages.success(request, f"{user.get_full_name()} has been removed from {office.name}.")
        return redirect('admin_panel:office_users', office_id=office_id)


class UpdateUserOfficeRoleView(LoginRequiredMixin, View):
    def post(self, request, office_id, user_id):
        office = get_object_or_404(Office, pk=office_id)
        user = get_object_or_404(User, pk=user_id)
        
        # Check if user has permission to update roles in this office
        if not (request.user.role == 'super_admin' or 
                (UserOffice.objects.filter(user=request.user, office=office, 
                                          role='office_admin').exists() and 
                 user_id != request.user.id)):  # Can't change your own role
            messages.error(request, "You don't have permission to update this user's role.")
            return redirect('admin_panel:office_users', office_id=office_id)
        
        role = request.POST.get('role')
        is_primary = request.POST.get('is_primary') == 'on'
        
        # Update the UserOffice relationship
        user_office = get_object_or_404(UserOffice, user=user, office=office)
        user_office.role = role
        
        if is_primary:
            # Set all other offices for this user as non-primary
            UserOffice.objects.filter(user=user, is_primary=True).update(is_primary=False)
            user_office.is_primary = True
        
        user_office.save()
        
        messages.success(request, f"{user.get_full_name()}'s role has been updated.")
        return redirect('admin_panel:office_users', office_id=office_id)
