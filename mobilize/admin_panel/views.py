from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView,
    View,
)
from django.urls import reverse_lazy, reverse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from django.views.decorators.http import require_POST
from django.utils.decorators import method_decorator

from mobilize.authentication.decorators import super_admin_required
from mobilize.authentication.models import User
from mobilize.authentication.forms import CreateUserForm
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
    template_name = "admin_panel/office_list.html"
    context_object_name = "offices"

    def get_queryset(self):
        # Super admins can see all offices
        if self.request.user.role == "super_admin":
            return Office.objects.all()

        # Other users can only see offices they're assigned to
        return Office.objects.filter(useroffice__user=self.request.user).distinct()


class OfficeDetailView(LoginRequiredMixin, DetailView):
    model = Office
    template_name = "admin_panel/office_detail.html"
    context_object_name = "office"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get users for this office by querying UserOffice and then getting User objects
        user_ids = UserOffice.objects.filter(office=self.object).values_list(
            "user_id", flat=True
        )
        # Convert string user_ids to integers and get User objects
        try:
            int_user_ids = [int(uid) for uid in user_ids if uid]
            context["users"] = User.objects.filter(id__in=int_user_ids)
        except (ValueError, TypeError):
            context["users"] = User.objects.none()
        return context


class OfficeCreateView(SuperAdminRequiredMixin, CreateView):
    model = Office
    form_class = OfficeForm
    template_name = "admin_panel/office_form.html"
    success_url = reverse_lazy("admin_panel:office_list")

    def form_valid(self, form):
        # Save the office first
        response = super().form_valid(form)

        # Automatically assign the super admin who created the office
        if self.request.user.role == "super_admin":
            UserOffice.objects.create(
                user_id=str(self.request.user.id),
                office=self.object,
                is_primary=False,  # Don't automatically make it primary
                assigned_at=timezone.now(),
            )

            messages.success(
                self.request,
                f"Office '{self.object.name}' has been created and you have "
                "been automatically assigned to it.",
            )

        return response


class OfficeUpdateView(SuperAdminRequiredMixin, UpdateView):
    model = Office
    form_class = OfficeForm
    template_name = "admin_panel/office_form.html"

    def get_success_url(self):
        return reverse("admin_panel:office_detail", kwargs={"pk": self.object.pk})


class OfficeDeleteView(SuperAdminRequiredMixin, DeleteView):
    model = Office
    template_name = "admin_panel/office_confirm_delete.html"
    success_url = reverse_lazy("admin_panel:office_list")


class OfficeUserListView(LoginRequiredMixin, ListView):
    template_name = "admin_panel/office_users.html"
    context_object_name = "office_users"

    def get_queryset(self):
        self.office = get_object_or_404(Office, pk=self.kwargs["office_id"])

        # Check if user has permission to view this office's users
        if not (
            self.request.user.role == "super_admin"
            or (
                self.request.user.role == "office_admin"
                and UserOffice.objects.filter(
                    user_id=str(self.request.user.id), office=self.office
                ).exists()
            )
        ):
            return []

        # Get UserOffice objects and manually load User objects
        user_offices = UserOffice.objects.filter(office=self.office)

        # Load User objects for each UserOffice
        office_users_with_users = []
        for user_office in user_offices:
            try:
                # Convert VARCHAR user_id to int to get User object
                user_id_int = int(user_office.user_id) if user_office.user_id else None
                if user_id_int:
                    user = User.objects.get(id=user_id_int)
                    # Create a custom object with both user_office and user data
                    office_user = type(
                        "OfficeUser",
                        (),
                        {
                            "user_office": user_office,
                            "user": user,
                            "office": self.office,
                            "is_primary": user_office.is_primary,
                            "assigned_at": user_office.assigned_at,
                            "permissions": user_office.permissions,
                        },
                    )()
                    office_users_with_users.append(office_user)
            except (ValueError, User.DoesNotExist):
                # Skip invalid user_ids or missing users
                continue

        return office_users_with_users

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["office"] = self.office
        return context


class AddUserToOfficeView(LoginRequiredMixin, View):
    def get(self, request, office_id):
        office = get_object_or_404(Office, pk=office_id)

        # Check if user has permission to add users to this office
        if not (
            request.user.role == "super_admin"
            or (
                request.user.role == "office_admin"
                and UserOffice.objects.filter(
                    user_id=str(request.user.id), office=office
                ).exists()
            )
        ):
            messages.error(
                request, "You don't have permission to add users to this office."
            )
            return redirect("admin_panel:office_detail", pk=office_id)

        # Get users not already in this office
        existing_users = UserOffice.objects.filter(office=office).values_list(
            "user_id", flat=True
        )
        # Convert existing user_ids to integers, filtering out invalid ones
        valid_existing_user_ids = []
        for user_id in existing_users:
            try:
                valid_existing_user_ids.append(int(user_id))
            except (ValueError, TypeError):
                # Skip invalid user_ids (like Firebase UIDs)
                continue

        available_users = User.objects.exclude(id__in=valid_existing_user_ids)

        # Create user form for new user creation
        create_user_form = CreateUserForm(created_by=request.user)

        return render(
            request,
            "admin_panel/add_user_to_office.html",
            {
                "office": office,
                "available_users": available_users,
                "create_user_form": create_user_form,
            },
        )

    def post(self, request, office_id):
        office = get_object_or_404(Office, pk=office_id)

        # Check if user has permission to add users to this office
        if not (
            request.user.role == "super_admin"
            or (
                request.user.role == "office_admin"
                and UserOffice.objects.filter(
                    user_id=str(request.user.id), office=office
                ).exists()
            )
        ):
            messages.error(
                request, "You don't have permission to add users to this office."
            )
            return redirect("admin_panel:office_detail", pk=office_id)

        # Check if this is a "create new user" request
        if "create_user" in request.POST or "create_and_assign" in request.POST:
            return self._handle_create_user(request, office)

        # Handle existing user assignment
        user_id = request.POST.get("user_id")
        is_primary = request.POST.get("is_primary") == "on"

        if not user_id:
            messages.error(request, "Please select a user.")
            return redirect("admin_panel:add_user_to_office", office_id=office_id)

        user = get_object_or_404(User, pk=user_id)

        # Create the UserOffice relationship
        UserOffice.objects.create(
            user_id=str(user.id),
            office=office,
            is_primary=is_primary,
            assigned_at=timezone.now(),
        )

        messages.success(
            request, f"{user.get_full_name()} has been added to {office.name}."
        )
        return redirect("admin_panel:office_users", office_id=office.id)

    def _handle_create_user(self, request, office):
        """Handle creation of new user and optional assignment to office."""
        create_user_form = CreateUserForm(request.POST, created_by=request.user)

        if create_user_form.is_valid():
            # Create the user
            user = create_user_form.save()

            # Determine if we should assign to office
            assign_to_office = "create_and_assign" in request.POST
            is_primary = request.POST.get("is_primary") == "on"

            if assign_to_office:
                # Create the UserOffice relationship
                UserOffice.objects.create(
                    user_id=str(user.id),
                    office=office,
                    is_primary=is_primary,
                    assigned_at=timezone.now(),
                )

                messages.success(
                    request,
                    f"User {user.get_full_name()} has been created and "
                    f"assigned to {office.name}.",
                )
                return redirect("admin_panel:office_users", office_id=office.id)
            else:
                messages.success(
                    request,
                    f"User {user.get_full_name()} has been created successfully.",
                )
                return redirect("admin_panel:office_users", office_id=office.id)
        else:
            # Form has errors, re-render with form errors
            # Get available users for the existing user dropdown
            existing_users = UserOffice.objects.filter(office=office).values_list(
                "user_id", flat=True
            )
            valid_existing_user_ids = []
            for user_id in existing_users:
                try:
                    valid_existing_user_ids.append(int(user_id))
                except (ValueError, TypeError):
                    continue

            available_users = User.objects.exclude(id__in=valid_existing_user_ids)

            return render(
                request,
                "admin_panel/add_user_to_office.html",
                {
                    "office": office,
                    "available_users": available_users,
                    "create_user_form": create_user_form,
                },
            )


class RemoveUserFromOfficeView(LoginRequiredMixin, View):
    def post(self, request, office_id, user_id):
        office = get_object_or_404(Office, pk=office_id)
        user = get_object_or_404(User, pk=user_id)

        # Check if user has permission to remove users from this office
        if not (
            request.user.role == "super_admin"
            or (
                request.user.role == "office_admin"
                and UserOffice.objects.filter(
                    user_id=str(request.user.id), office=office
                ).exists()
                and user_id != request.user.id
            )
        ):  # Can't remove yourself
            messages.error(request, "You don't have permission to remove this user.")
            return redirect("admin_panel:office_users", office_id=office_id)

        # Delete the UserOffice relationship
        user_office = get_object_or_404(UserOffice, user_id=str(user_id), office=office)
        user_office.delete()

        messages.success(
            request, f"{user.get_full_name()} has been removed from {office.name}."
        )
        return redirect("admin_panel:office_users", office_id=office_id)


class UpdateUserOfficePrimaryView(LoginRequiredMixin, View):
    def post(self, request, office_id, user_id):
        office = get_object_or_404(Office, pk=office_id)
        user = get_object_or_404(User, pk=user_id)

        # Check if user has permission to update office assignments
        if not (
            request.user.role == "super_admin"
            or (
                request.user.role == "office_admin"
                and UserOffice.objects.filter(
                    user_id=str(request.user.id), office=office
                ).exists()
                and user_id != request.user.id
            )
        ):  # Can't change your own primary office
            messages.error(
                request,
                "You don't have permission to update this user's office assignment.",
            )
            return redirect("admin_panel:office_users", office_id=office_id)

        is_primary = request.POST.get("is_primary") == "on"

        # Update the UserOffice relationship
        user_office = get_object_or_404(UserOffice, user_id=str(user_id), office=office)

        if is_primary:
            # Set all other offices for this user as non-primary
            UserOffice.objects.filter(user_id=str(user_id), is_primary=True).update(
                is_primary=False
            )

        user_office.is_primary = is_primary
        user_office.save()

        messages.success(
            request, f"{user.get_full_name()}'s primary office has been updated."
        )
        return redirect("admin_panel:office_users", office_id=office_id)


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
        if request.user.role != "super_admin":
            messages.error(
                request, "You don't have permission to view cross-office reports."
            )
            return redirect("admin_panel:office_list")

        from mobilize.contacts.models import Person
        from mobilize.churches.models import Church
        from mobilize.tasks.models import Task
        from django.db.models import Count, Q

        # Get all offices with statistics
        offices = Office.objects.annotate(
            user_count_db=Count("useroffice", distinct=True),
            admin_count_db=Count(
                "useroffice",
                filter=Q(useroffice__user__role__in=["super_admin", "office_admin"]),
                distinct=True,
            ),
        ).order_by("name")

        # Calculate additional metrics for each office
        office_data = []
        for office in offices:
            # Get contact counts for this office
            people_count = (
                Person.objects.filter(
                    Q(contact__office_id=office.id)
                    | Q(
                        contact__user__in=UserOffice.objects.filter(
                            office=office
                        ).values_list("user_id", flat=True)
                    )
                )
                .distinct()
                .count()
            )

            churches_count = Church.objects.filter(contact__office_id=office.id).count()

            # Get task counts for this office
            office_users = UserOffice.objects.filter(office=office).values_list(
                "user", flat=True
            )
            pending_tasks = (
                Task.objects.filter(
                    Q(assigned_to__in=office_users) | Q(created_by__in=office_users),
                    status="pending",
                )
                .distinct()
                .count()
            )

            office_data.append(
                {
                    "office": office,
                    "people_count": people_count,
                    "churches_count": churches_count,
                    "pending_tasks": pending_tasks,
                    "total_contacts": people_count + churches_count,
                }
            )

        # Overall statistics
        total_stats = {
            "total_offices": offices.count(),
            "active_offices": offices.filter(is_active=True).count(),
            "total_users": User.objects.count(),
            "total_people": Person.objects.count(),
            "total_churches": Church.objects.count(),
            "total_tasks": Task.objects.count(),
        }

        return render(
            request,
            "admin_panel/cross_office_report.html",
            {
                "office_data": office_data,
                "total_stats": total_stats,
            },
        )


class UserManagementView(SuperAdminRequiredMixin, ListView):
    """
    Comprehensive user management view for super admins.

    Provides centralized management of all users across all offices.
    """

    model = User
    template_name = "admin_panel/user_management.html"
    context_object_name = "users"
    paginate_by = 25

    def get_queryset(self):
        try:
            queryset = User.objects.select_related("person").order_by("username")

            # Filter by role if specified
            role_filter = self.request.GET.get("role")
            if role_filter:
                queryset = queryset.filter(role=role_filter)

            # Filter by active status
            active_filter = self.request.GET.get("active")
            if active_filter == "true":
                queryset = queryset.filter(is_active=True)
            elif active_filter == "false":
                queryset = queryset.filter(is_active=False)

            # Search functionality
            search_query = self.request.GET.get("search")
            if search_query:
                queryset = queryset.filter(
                    Q(username__icontains=search_query)
                    | Q(email__icontains=search_query)
                    | Q(first_name__icontains=search_query)
                    | Q(last_name__icontains=search_query)
                )

            return queryset
        except Exception as e:
            # Log the error for debugging
            import logging

            logger = logging.getLogger(__name__)
            logger.error(
                f"Error in UserManagementView.get_queryset: {e}", exc_info=True
            )
            # Return empty queryset to prevent 500 error
            return User.objects.none()

    def get_context_data(self, **kwargs):
        try:
            # Ensure required attributes are set before calling super()
            if not hasattr(self, "object_list"):
                self.object_list = self.get_queryset()
            if not hasattr(self, "kwargs"):
                self.kwargs = {}
            context = super().get_context_data(**kwargs)

            # Add filter options
            context["role_choices"] = User._meta.get_field("role").choices
            context["current_role"] = self.request.GET.get("role", "")
            context["current_active"] = self.request.GET.get("active", "")
            context["current_search"] = self.request.GET.get("search", "")

            # Add statistics
            context["stats"] = {
                "total_users": User.objects.count(),
                "active_users": User.objects.filter(is_active=True).count(),
                "super_admins": User.objects.filter(role="super_admin").count(),
                "office_admins": User.objects.filter(role="office_admin").count(),
                "standard_users": User.objects.filter(role="standard_user").count(),
                "limited_users": User.objects.filter(role="limited_user").count(),
            }

            # Get first office for create user link
            context["first_office"] = Office.objects.first()

            # Get all offices for batch operations
            context["all_offices"] = Office.objects.all().order_by("name")

            # Add office assignments to each user object
            for user in context["users"]:
                user_offices = UserOffice.objects.filter(
                    user_id=str(user.id)
                ).select_related("office")
                user.office_assignments = user_offices

            return context
        except Exception as e:
            # Log the error for debugging
            import logging

            logger = logging.getLogger(__name__)
            logger.error(
                f"Error in UserManagementView.get_context_data: {e}", exc_info=True
            )
            # Return minimal context to prevent 500 error
            empty_users = User.objects.none()
            for user in empty_users:
                user.office_assignments = []
            return {
                "users": empty_users,
                "role_choices": [],
                "current_role": "",
                "current_active": "",
                "current_search": "",
                "stats": {
                    "total_users": 0,
                    "active_users": 0,
                    "super_admins": 0,
                    "office_admins": 0,
                    "standard_users": 0,
                    "limited_users": 0,
                },
                "first_office": None,
                "all_offices": [],
            }


class UserDetailView(SuperAdminRequiredMixin, DetailView):
    """
    Detailed view of a specific user for super admins.

    Shows user information, office assignments, and management options.
    """

    model = User
    template_name = "admin_panel/user_detail.html"
    context_object_name = "user_detail"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get user's office assignments
        user_offices = UserOffice.objects.filter(
            user_id=str(self.object.id)
        ).select_related("office")
        context["user_offices"] = user_offices

        # Get offices not assigned to this user
        assigned_office_ids = user_offices.values_list("office_id", flat=True)
        context["available_offices"] = Office.objects.filter(is_active=True).exclude(
            id__in=assigned_office_ids
        )

        return context


class UserUpdateView(SuperAdminRequiredMixin, UpdateView):
    """
    Update user information for super admins.
    """

    model = User
    template_name = "admin_panel/user_form.html"
    fields = ["username", "email", "first_name", "last_name", "role", "is_active"]

    def get_success_url(self):
        return reverse("admin_panel:user_detail", kwargs={"pk": self.object.pk})

    def form_valid(self, form):
        messages.success(
            self.request,
            f"User {form.instance.username} has been updated successfully.",
        )
        return super().form_valid(form)


class UserToggleActiveView(SuperAdminRequiredMixin, View):
    """
    Toggle user active status.
    """

    def post(self, request, pk):
        user = get_object_or_404(User, pk=pk)

        # Don't allow disabling yourself
        if user == request.user:
            messages.error(request, "You cannot disable your own account.")
            return redirect("admin_panel:user_detail", pk=pk)

        user.is_active = not user.is_active
        user.save()

        status_text = "activated" if user.is_active else "deactivated"
        messages.success(request, f"User {user.username} has been {status_text}.")

        return redirect("admin_panel:user_detail", pk=pk)


class AssignUserToOfficeView(SuperAdminRequiredMixin, View):
    """
    Assign a user to an office from the user management page.
    """

    def post(self, request, user_id):
        user = get_object_or_404(User, pk=user_id)
        office_id = request.POST.get("office_id")
        is_primary = request.POST.get("is_primary") == "on"

        if not office_id:
            messages.error(request, "Please select an office.")
            return redirect("admin_panel:user_detail", pk=user_id)

        office = get_object_or_404(Office, pk=office_id)

        # Check if user is already assigned to this office
        if UserOffice.objects.filter(user_id=str(user.id), office=office).exists():
            messages.error(
                request, f"User {user.username} is already assigned to {office.name}."
            )
            return redirect("admin_panel:user_detail", pk=user_id)

        # Create the UserOffice relationship
        UserOffice.objects.create(
            user_id=str(user.id),
            office=office,
            is_primary=is_primary,
            assigned_at=timezone.now(),
        )

        messages.success(
            request, f"User {user.username} has been assigned to {office.name}."
        )
        return redirect("admin_panel:user_detail", pk=user_id)


class BatchUserDeleteView(SuperAdminRequiredMixin, View):
    """
    Batch delete users from the user management page.
    """

    @method_decorator(require_POST)
    def post(self, request):
        user_ids = request.POST.getlist("user_ids")

        # Handle comma-separated string from JavaScript
        if len(user_ids) == 1 and "," in user_ids[0]:
            user_ids = [uid.strip() for uid in user_ids[0].split(",") if uid.strip()]
        elif not user_ids:
            # Try to get as a single string
            user_ids_str = request.POST.get("user_ids", "")
            if user_ids_str:
                user_ids = [
                    uid.strip() for uid in user_ids_str.split(",") if uid.strip()
                ]

        if not user_ids:
            messages.error(request, "No users selected for deletion")
            return redirect("admin_panel:user_management")

        try:
            # Get the users to delete
            users_to_delete = User.objects.filter(id__in=user_ids)

            # Don't allow deletion of the current user
            if request.user.id in [int(uid) for uid in user_ids]:
                messages.error(request, "Cannot delete your own account")
                return redirect("admin_panel:user_management")

            count = users_to_delete.count()

            if count == 0:
                messages.error(request, "No valid users found to delete")
                return redirect("admin_panel:user_management")

            # Delete the users
            users_to_delete.delete()

            messages.success(request, f"Successfully deleted {count} user(s)")

        except Exception as e:
            messages.error(request, f"Error deleting users: {str(e)}")

        return redirect("admin_panel:user_management")


class BatchUserStatusView(SuperAdminRequiredMixin, View):
    """
    Batch activate/deactivate users from the user management page.
    """

    @method_decorator(require_POST)
    def post(self, request):
        user_ids = request.POST.getlist("user_ids")
        action = request.POST.get("action")

        # Handle comma-separated string from JavaScript
        if len(user_ids) == 1 and "," in user_ids[0]:
            user_ids = [uid.strip() for uid in user_ids[0].split(",") if uid.strip()]
        elif not user_ids:
            # Try to get as a single string
            user_ids_str = request.POST.get("user_ids", "")
            if user_ids_str:
                user_ids = [
                    uid.strip() for uid in user_ids_str.split(",") if uid.strip()
                ]

        if not user_ids:
            messages.error(request, "No users selected for status update")
            return redirect("admin_panel:user_management")

        if action not in ["activate", "deactivate"]:
            messages.error(request, "Invalid action selected")
            return redirect("admin_panel:user_management")

        try:
            # Get the users to update
            users_to_update = User.objects.filter(id__in=user_ids)

            # Don't allow deactivation of the current user
            if action == "deactivate" and request.user.id in [
                int(uid) for uid in user_ids
            ]:
                messages.error(request, "Cannot deactivate your own account")
                return redirect("admin_panel:user_management")

            count = users_to_update.count()

            if count == 0:
                messages.error(request, "No valid users found to update")
                return redirect("admin_panel:user_management")

            # Update the users
            is_active = action == "activate"
            users_to_update.update(is_active=is_active)

            action_text = "activated" if is_active else "deactivated"
            messages.success(request, f"Successfully {action_text} {count} user(s)")

        except Exception as e:
            messages.error(request, f"Error updating users: {str(e)}")

        return redirect("admin_panel:user_management")


class BatchUserRoleView(SuperAdminRequiredMixin, View):
    """
    Batch update user roles from the user management page.
    """

    @method_decorator(require_POST)
    def post(self, request):
        user_ids = request.POST.getlist("user_ids")
        new_role = request.POST.get("role")

        # Handle comma-separated string from JavaScript
        if len(user_ids) == 1 and "," in user_ids[0]:
            user_ids = [uid.strip() for uid in user_ids[0].split(",") if uid.strip()]
        elif not user_ids:
            # Try to get as a single string
            user_ids_str = request.POST.get("user_ids", "")
            if user_ids_str:
                user_ids = [
                    uid.strip() for uid in user_ids_str.split(",") if uid.strip()
                ]

        if not user_ids:
            messages.error(request, "No users selected for role update")
            return redirect("admin_panel:user_management")

        if not new_role:
            messages.error(request, "Please select a role")
            return redirect("admin_panel:user_management")

        # Validate role choice
        valid_roles = [choice[0] for choice in User._meta.get_field("role").choices]
        if new_role not in valid_roles:
            messages.error(request, "Invalid role selected")
            return redirect("admin_panel:user_management")

        try:
            # Get the users to update
            users_to_update = User.objects.filter(id__in=user_ids)

            # Don't allow changing the current user's role
            if request.user.id in [int(uid) for uid in user_ids]:
                messages.error(request, "Cannot change your own role")
                return redirect("admin_panel:user_management")

            count = users_to_update.count()

            if count == 0:
                messages.error(request, "No valid users found to update")
                return redirect("admin_panel:user_management")

            # Update the users
            users_to_update.update(role=new_role)

            role_display = dict(User._meta.get_field("role").choices).get(
                new_role, new_role
            )
            messages.success(
                request, f"Successfully updated {count} user(s) to {role_display} role"
            )

        except Exception as e:
            messages.error(request, f"Error updating users: {str(e)}")

        return redirect("admin_panel:user_management")


class RemoveUserFromOfficeDirectView(SuperAdminRequiredMixin, View):
    """
    Remove a user from an office from the user management page.
    """

    def post(self, request, user_id, office_id):
        user = get_object_or_404(User, pk=user_id)
        office = get_object_or_404(Office, pk=office_id)

        # Delete the UserOffice relationship
        user_office = get_object_or_404(UserOffice, user_id=str(user_id), office=office)
        user_office.delete()

        messages.success(
            request, f"User {user.username} has been removed from {office.name}."
        )
        return redirect("admin_panel:user_detail", pk=user_id)


class BatchUserOfficeView(SuperAdminRequiredMixin, View):
    """
    Batch assign users to an office from the user management page.
    """

    @method_decorator(require_POST)
    def post(self, request):
        user_ids = request.POST.getlist("user_ids")
        office_id = request.POST.get("office_id")

        # Handle comma-separated string from JavaScript
        if len(user_ids) == 1 and "," in user_ids[0]:
            user_ids = [uid.strip() for uid in user_ids[0].split(",") if uid.strip()]
        elif not user_ids:
            # Try to get as a single string
            user_ids_str = request.POST.get("user_ids", "")
            if user_ids_str:
                user_ids = [
                    uid.strip() for uid in user_ids_str.split(",") if uid.strip()
                ]

        if not user_ids:
            messages.error(request, "No users selected for office assignment")
            return redirect("admin_panel:user_management")

        if not office_id:
            messages.error(request, "Please select an office")
            return redirect("admin_panel:user_management")

        try:
            office = get_object_or_404(Office, pk=office_id)

            # Get the users to assign
            users_to_assign = User.objects.filter(id__in=user_ids)

            count = users_to_assign.count()

            if count == 0:
                messages.error(request, "No valid users found to assign")
                return redirect("admin_panel:user_management")

            # Assign users to the office
            assigned_count = 0
            for user in users_to_assign:
                # Check if user is already assigned to this office
                if not UserOffice.objects.filter(
                    user_id=str(user.id), office=office
                ).exists():
                    UserOffice.objects.create(
                        user_id=str(user.id),
                        office=office,
                        is_primary=False,
                        assigned_at=timezone.now(),
                    )
                    assigned_count += 1

            if assigned_count > 0:
                messages.success(
                    request,
                    f"Successfully assigned {assigned_count} user(s) to {office.name}",
                )
            else:
                messages.warning(
                    request, "All selected users are already assigned to this office"
                )

        except Exception as e:
            messages.error(request, f"Error assigning users: {str(e)}")

        return redirect("admin_panel:user_management")
