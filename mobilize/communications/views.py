import logging

from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView,
    FormView,
)
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.core.mail import EmailMultiAlternatives
from django.utils.html import strip_tags
from django.conf import settings
from django.contrib import messages
from django.views import View
from django.core.exceptions import PermissionDenied
from django.db import models

from .models import EmailTemplate, EmailSignature, Communication
from .forms import (
    EmailTemplateForm,
    EmailSignatureForm,
    CommunicationForm,
    ComposeEmailForm,
)
from .gmail_service import GmailService
from .google_contacts_service import GoogleContactsService
from mobilize.authentication.decorators import office_data_filter

logger = logging.getLogger(__name__)


# Email Template Views
class EmailTemplateListView(LoginRequiredMixin, ListView):
    model = EmailTemplate
    template_name = "communications/email_template_list.html"
    context_object_name = "email_templates"
    paginate_by = 10

    def dispatch(self, request, *args, **kwargs):
        # Check office assignment
        from mobilize.admin_panel.models import UserOffice

        if (
            request.user.role != "super_admin"
            and not UserOffice.objects.filter(user_id=str(request.user.id)).exists()
        ):
            raise PermissionDenied("Access denied. User not assigned to any office.")
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        # Only fetch fields that exist in database - exclude 'body' field temporarily due to schema mismatch
        queryset = EmailTemplate.objects.all().only(
            "id",
            "name",
            "subject",
            "is_active",
            "category",
            "created_by",
            "created_at",
            "updated_at",
        )

        # Super admins see all templates
        if self.request.user.role == "super_admin":
            return queryset

        # Other users see templates from their offices or created by them
        try:
            from mobilize.admin_panel.models import UserOffice

            user_offices = list(
                UserOffice.objects.filter(
                    user_id=str(self.request.user.id)
                ).values_list("office_id", flat=True)
            )

            if user_offices:
                # Templates are shared within offices
                return queryset.filter(
                    models.Q(created_by=self.request.user)
                    | models.Q(created_by__useroffice__office__in=user_offices)
                ).distinct()
            else:
                # If user has no office assignments, only show their own templates
                return queryset.filter(created_by=self.request.user)
        except Exception:
            # If there's any error with office filtering, fall back to user's own templates
            return queryset.filter(created_by=self.request.user)


class EmailTemplateDetailView(LoginRequiredMixin, DetailView):
    model = EmailTemplate
    template_name = "communications/email_template_detail.html"
    context_object_name = "email_template"


class EmailTemplateCreateView(LoginRequiredMixin, CreateView):
    model = EmailTemplate
    form_class = EmailTemplateForm
    template_name = "communications/email_template_form.html"
    success_url = reverse_lazy("communications:email_template_list")

    def dispatch(self, request, *args, **kwargs):
        # Prevent limited users from creating
        if request.user.role == "limited_user":
            raise PermissionDenied("Limited users cannot create email templates")

        # Check office assignment
        from mobilize.admin_panel.models import UserOffice

        if (
            request.user.role != "super_admin"
            and not UserOffice.objects.filter(user_id=str(request.user.id)).exists()
        ):
            raise PermissionDenied("Access denied. User not assigned to any office.")

        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)


class EmailTemplateUpdateView(LoginRequiredMixin, UpdateView):
    model = EmailTemplate
    form_class = EmailTemplateForm
    template_name = "communications/email_template_form.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_success_url(self):
        return reverse(
            "communications:email_template_detail", kwargs={"pk": self.object.pk}
        )


class EmailTemplateDeleteView(LoginRequiredMixin, DeleteView):
    model = EmailTemplate
    template_name = "communications/email_template_confirm_delete.html"
    success_url = reverse_lazy("communications:email_template_list")


# Email Signature Views
class EmailSignatureListView(LoginRequiredMixin, ListView):
    model = EmailSignature
    template_name = "communications/email_signature_list.html"
    context_object_name = "email_signatures"

    def get_queryset(self):
        # Users can only see their own signatures
        return EmailSignature.objects.filter(user=self.request.user)


class EmailSignatureDetailView(LoginRequiredMixin, DetailView):
    model = EmailSignature
    template_name = "communications/email_signature_detail.html"
    context_object_name = "email_signature"


class EmailSignatureCreateView(LoginRequiredMixin, CreateView):
    model = EmailSignature
    form_class = EmailSignatureForm
    template_name = "communications/email_signature_form.html"
    success_url = reverse_lazy("communications:email_signature_list")

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs


class EmailSignatureUpdateView(LoginRequiredMixin, UpdateView):
    model = EmailSignature
    form_class = EmailSignatureForm
    template_name = "communications/email_signature_form.html"

    def get_success_url(self):
        return reverse("communications:email_signature_list")

    def get_queryset(self):
        # Users can only edit their own signatures
        return EmailSignature.objects.filter(user=self.request.user)

    def form_valid(self, form):
        # Add logging to see if form is valid
        print(f"Form is valid, saving signature: {form.cleaned_data}")
        return super().form_valid(form)

    def form_invalid(self, form):
        # Add logging to see form errors
        print(f"Form is invalid, errors: {form.errors}")
        return super().form_invalid(form)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs


class EmailSignatureDeleteView(LoginRequiredMixin, DeleteView):
    model = EmailSignature
    template_name = "communications/email_signature_confirm_delete.html"
    success_url = reverse_lazy("communications:email_signature_list")

    def get_queryset(self):
        # Users can only delete their own signatures
        return EmailSignature.objects.filter(user=self.request.user)


# Communication Views
class CommunicationListView(LoginRequiredMixin, ListView):
    model = Communication
    template_name = "communications/communication_list.html"
    context_object_name = "communications"
    paginate_by = 20

    def dispatch(self, request, *args, **kwargs):
        # Check office assignment - temporarily disable strict checking for debugging
        # if request.user.role != 'super_admin' and not request.user.useroffice_set.exists():
        #     raise PermissionDenied("Access denied. User not assigned to any office.")
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        # Filter communications by user - each user sees only their own communications
        try:
            # Super admins see all communications, everyone else sees only their own
            if self.request.user.role == "super_admin":
                queryset = Communication.objects.all()
            else:
                queryset = Communication.objects.filter(user=self.request.user)

            # Apply basic filters from GET parameters
            type_filter = self.request.GET.get("type")
            if type_filter:
                queryset = queryset.filter(type=type_filter)

            direction_filter = self.request.GET.get("direction")
            if direction_filter:
                queryset = queryset.filter(direction=direction_filter)

            date_from = self.request.GET.get("date_from")
            if date_from:
                queryset = queryset.filter(date__gte=date_from)

            search_query = self.request.GET.get("search")
            if search_query:
                from django.db.models import Q

                # Build search query for communications with proper field lookups
                search_conditions = Q(
                    # Search in basic communication fields
                    Q(subject__icontains=search_query)
                    | Q(sender__icontains=search_query)
                    | Q(message__icontains=search_query)
                    | Q(content__icontains=search_query)
                    |
                    # Search in person contact fields
                    Q(person__contact__first_name__icontains=search_query)
                    | Q(person__contact__last_name__icontains=search_query)
                    | Q(person__contact__email__icontains=search_query)
                    |
                    # Search in church contact fields
                    Q(church__contact__church_name__icontains=search_query)
                    | Q(church__contact__email__icontains=search_query)
                    | Q(church__name__icontains=search_query)  # Church's own name field
                )

                queryset = queryset.filter(search_conditions)

            # Filter by contact_id or person_id if provided (for "View All" button functionality)
            contact_id = self.request.GET.get("contact_id")
            person_id = self.request.GET.get("person_id")

            if person_id:
                # Direct person ID filtering is more precise
                queryset = queryset.filter(person_id=person_id)
            elif contact_id:
                from django.db.models import Q

                queryset = queryset.filter(
                    Q(person__contact_id=contact_id) | Q(church__contact_id=contact_id)
                )

            # Sort by actual sent/received date, not import date
            from django.db.models import Case, When, F

            return queryset.annotate(
                effective_date=Case(
                    When(date_sent__isnull=False, then=F("date_sent")),
                    When(date__isnull=False, then=F("date")),
                    default=F("created_at"),
                )
            ).order_by("-effective_date")

        except Exception as e:
            # If there's any database error, return empty queryset
            import logging

            logging.error(f"Error in CommunicationListView.get_queryset: {e}")
            return Communication.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["type_choices"] = Communication.TYPE_CHOICES
        context["direction_choices"] = Communication.DIRECTION_CHOICES

        # Add context for bulk operations
        from django.contrib.auth import get_user_model

        User = get_user_model()

        # Get users for bulk assignment
        if self.request.user.role == "super_admin":
            context["users"] = User.objects.filter(is_active=True).order_by(
                "first_name", "last_name"
            )
        else:
            # Get users from same offices
            from mobilize.admin_panel.models import UserOffice

            user_offices = UserOffice.objects.filter(
                user_id=str(self.request.user.id)
            ).values_list("office_id", flat=True)

            office_user_ids = UserOffice.objects.filter(
                office_id__in=user_offices
            ).values_list("user_id", flat=True)

            context["users"] = User.objects.filter(
                id__in=office_user_ids, is_active=True
            ).order_by("first_name", "last_name")

        # Status choices for bulk operations
        context["status_choices"] = [
            ("pending", "Pending"),
            ("processing", "Processing"),
            ("sent", "Sent"),
            ("delivered", "Delivered"),
            ("failed", "Failed"),
        ]

        return context


class CommunicationDetailView(LoginRequiredMixin, DetailView):
    model = Communication
    template_name = "communications/communication_detail.html"
    context_object_name = "communication"

    def get_queryset(self):
        queryset = Communication.objects.select_related(
            "person", "church", "office", "user"
        )

        # Apply office-level filtering
        if self.request.user.role != "super_admin":
            try:
                from mobilize.admin_panel.models import UserOffice

                user_offices = list(
                    UserOffice.objects.filter(
                        user_id=str(self.request.user.id)
                    ).values_list("office_id", flat=True)
                )

                if user_offices:
                    queryset = queryset.filter(
                        models.Q(user=self.request.user)
                        | models.Q(person__contact__office__in=user_offices)
                        | models.Q(church__contact__office__in=user_offices)
                        | models.Q(office__in=user_offices)
                    ).distinct()
                else:
                    # If user has no office assignments, only show their own communications
                    queryset = queryset.filter(user=self.request.user)
            except Exception:
                # If there's any error with office filtering, fall back to user's own communications
                queryset = queryset.filter(user=self.request.user)

        return queryset


class CommunicationCreateView(LoginRequiredMixin, CreateView):
    model = Communication
    form_class = CommunicationForm
    template_name = "communications/communication_form.html"

    def dispatch(self, request, *args, **kwargs):
        # Prevent limited users from creating
        if request.user.role == "limited_user":
            raise PermissionDenied("Limited users cannot create communications")

        # Check office assignment - temporarily disable strict checking for debugging
        # if request.user.role != 'super_admin' and not request.user.useroffice_set.exists():
        #     raise PermissionDenied("Access denied. User not assigned to any office.")

        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.user_id = str(self.request.user.id)
        return super().form_valid(form)

    def get_success_url(self):
        # Check for redirect_to parameter first
        redirect_to = self.request.POST.get("redirect_to")
        if redirect_to:
            return redirect_to
        return reverse(
            "communications:communication_detail", kwargs={"pk": self.object.pk}
        )

    def post(self, request, *args, **kwargs):
        # Handle JSON requests for API calls
        if request.content_type == "application/json":
            import json
            from django.http import JsonResponse

            try:
                data = json.loads(request.body)

                # Get the contact
                contact_id = data.get("contact_id")
                if not contact_id:
                    return JsonResponse(
                        {"success": False, "error": "Contact ID is required"}
                    )

                from mobilize.contacts.models import Contact

                try:
                    contact = Contact.objects.get(id=contact_id)
                except Contact.DoesNotExist:
                    return JsonResponse(
                        {"success": False, "error": "Contact not found"}
                    )

                # Create the communication
                communication = Communication.objects.create(
                    contact=contact,
                    person=(
                        getattr(contact, "person_details", None)
                        if contact.type == "person"
                        else None
                    ),
                    church=(
                        getattr(contact, "church_details", None)
                        if contact.type == "church"
                        else None
                    ),
                    type=data.get("type", "other"),
                    subject=data.get("subject", ""),
                    message=data.get("message", ""),
                    date=data.get("date"),
                    user=request.user,
                    direction="outbound",  # Default to outbound for logged communications
                )

                return JsonResponse(
                    {
                        "success": True,
                        "message": "Communication logged successfully",
                        "communication_id": communication.id,
                    }
                )

            except json.JSONDecodeError:
                return JsonResponse({"success": False, "error": "Invalid JSON data"})
            except Exception as e:
                return JsonResponse({"success": False, "error": str(e)})

        # Handle regular form submission
        return super().post(request, *args, **kwargs)


class CommunicationUpdateView(LoginRequiredMixin, UpdateView):
    model = Communication
    form_class = CommunicationForm
    template_name = "communications/communication_form.html"

    def dispatch(self, request, *args, **kwargs):
        # Prevent limited users from editing
        if request.user.role == "limited_user":
            raise PermissionDenied("Limited users cannot edit communications")

        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        queryset = Communication.objects.select_related(
            "person", "church", "office", "user"
        )

        # Apply office-level filtering
        if self.request.user.role != "super_admin":
            try:
                from mobilize.admin_panel.models import UserOffice

                user_offices = list(
                    UserOffice.objects.filter(
                        user_id=str(self.request.user.id)
                    ).values_list("office_id", flat=True)
                )

                if user_offices:
                    queryset = queryset.filter(
                        models.Q(user=self.request.user)
                        | models.Q(person__contact__office__in=user_offices)
                        | models.Q(church__contact__office__in=user_offices)
                        | models.Q(office__in=user_offices)
                    ).distinct()
                else:
                    # If user has no office assignments, only show their own communications
                    queryset = queryset.filter(user=self.request.user)
            except Exception:
                # If there's any error with office filtering, fall back to user's own communications
                queryset = queryset.filter(user=self.request.user)

        return queryset

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        # Add logging to see if form is valid
        print(f"Communication form is valid, saving: {form.cleaned_data}")
        try:
            return super().form_valid(form)
        except Exception as e:
            print(f"Error in form_valid: {e}")
            raise

    def form_invalid(self, form):
        # Add logging to see form errors
        print(f"Communication form is invalid, errors: {form.errors}")
        return super().form_invalid(form)

    def get_success_url(self):
        try:
            return reverse(
                "communications:communication_detail", kwargs={"pk": self.object.pk}
            )
        except Exception as e:
            print(f"Error getting success URL: {e}")
            # Fallback to communication list if detail view fails
            return reverse("communications:communication_list")


class CommunicationDeleteView(LoginRequiredMixin, DeleteView):
    model = Communication
    template_name = "communications/communication_confirm_delete.html"
    success_url = reverse_lazy("communications:communication_list")

    def dispatch(self, request, *args, **kwargs):
        # Prevent limited users from deleting
        if request.user.role == "limited_user":
            raise PermissionDenied("Limited users cannot delete communications")

        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        try:
            # Use basic queryset without complex select_related to avoid foreign key issues
            queryset = Communication.objects.all()

            # Apply office-level filtering
            if self.request.user.role != "super_admin":
                try:
                    from mobilize.admin_panel.models import UserOffice

                    user_offices = list(
                        UserOffice.objects.filter(
                            user_id=str(self.request.user.id)
                        ).values_list("office_id", flat=True)
                    )

                    if user_offices:
                        # Simplified filtering to avoid complex joins that might fail
                        queryset = queryset.filter(
                            models.Q(user=self.request.user)
                            | models.Q(office__in=user_offices)
                        ).distinct()
                    else:
                        # If user has no office assignments, only show their own communications
                        queryset = queryset.filter(user=self.request.user)
                except Exception:
                    # If there's any error with office filtering, fall back to user's own communications
                    queryset = queryset.filter(user=self.request.user)

            return queryset
        except Exception as e:
            # If any error occurs, return basic queryset filtered by user
            print(f"Error in CommunicationDeleteView.get_queryset: {e}")
            return Communication.objects.filter(user=self.request.user)

    def delete(self, request, *args, **kwargs):
        """Override delete method with error handling"""
        try:
            print(f"CommunicationDeleteView.delete called with pk: {kwargs.get('pk')}")
            obj = self.get_object()
            print(f"Found object: {obj.id} - {obj.subject}")
            result = super().delete(request, *args, **kwargs)
            print("Delete successful")
            return result
        except Exception as e:
            print(f"Error deleting communication: {e}")
            import traceback

            traceback.print_exc()
            messages.error(request, f"Error deleting communication: {str(e)}")
            return redirect("communications:communication_list")


# Email Composition
class ComposeEmailView(LoginRequiredMixin, FormView):
    template_name = "communications/compose_email.html"
    form_class = ComposeEmailForm
    success_url = reverse_lazy("communications:communication_list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["email_templates"] = EmailTemplate.objects.filter(
            created_by=self.request.user
        ).only("id", "name", "subject", "is_active", "category")
        context["email_signatures"] = EmailSignature.objects.filter(
            user=self.request.user
        ).only("id", "name", "content", "is_default", "user")
        return context


@login_required
def send_email(request):
    if request.method == "POST":
        form = ComposeEmailForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            # Process form data
            subject = form.cleaned_data["subject"]
            recipient_list = form.cleaned_data["recipients"].split(",")
            template_content = form.cleaned_data["content"]
            signature = form.cleaned_data.get("signature")

            # Combine content with signature if provided
            html_content = template_content
            if signature:
                html_content += f"<br><br>{signature.content}"

            # Create plain text version
            text_content = strip_tags(html_content)

            # Create email
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=recipient_list,
            )
            email.attach_alternative(html_content, "text/html")

            # Attach files if any
            for file in request.FILES.getlist("attachments"):
                email.attach(file.name, file.read(), file.content_type)

            # Send email
            email.send()

            # Create communication record
            communication = Communication.objects.create(
                subject=subject,
                content=html_content,
                communication_type="email",
                created_by=request.user,
                office=form.cleaned_data.get("office"),
            )

            # Save attachments - temporarily disabled due to missing EmailAttachment table
            # for file in request.FILES.getlist('attachments'):
            #     EmailAttachment.objects.create(
            #         communication=communication,
            #         file=file,
            #         name=file.name
            #     )

            return redirect("communications:communication_detail", pk=communication.pk)
    else:
        form = ComposeEmailForm(user=request.user)

    return render(request, "communications/compose_email.html", {"form": form})


@login_required
def preview_email_template(request, template_id):
    template = get_object_or_404(EmailTemplate, pk=template_id)

    # Check if user has access to this template
    if not (template.is_global or template.office in request.user.offices.all()):
        return JsonResponse({"error": "Access denied"}, status=403)

    return JsonResponse({"subject": template.subject, "content": template.content})


# Gmail Integration Views
class GmailAuthView(LoginRequiredMixin, View):
    """Initiate Gmail OAuth flow"""

    def get(self, request):
        try:
            gmail_service = GmailService(request.user)
            redirect_uri = request.build_absolute_uri(
                reverse("communications:gmail_callback")
            )

            if gmail_service.is_authenticated():
                messages.info(request, "Gmail is already connected for your account.")
                return redirect("communications:communication_list")

            auth_url = gmail_service.get_authorization_url(redirect_uri)
            return redirect(auth_url)
        except Exception as e:
            messages.error(
                request,
                f"Gmail authentication error: {str(e)}. Please check your Google OAuth settings.",
            )
            return redirect("communications:communication_list")


class GmailCallbackView(LoginRequiredMixin, View):
    """Handle Gmail OAuth callback"""

    def get(self, request):
        code = request.GET.get("code")
        error = request.GET.get("error")

        if error:
            messages.error(request, f"Gmail authorization failed: {error}")
            return redirect("communications:communication_list")

        if not code:
            messages.error(request, "Authorization code not received.")
            return redirect("communications:communication_list")

        try:
            gmail_service = GmailService(request.user)
            redirect_uri = request.build_absolute_uri(
                reverse("communications:gmail_callback")
            )
            gmail_service.handle_oauth_callback(code, redirect_uri)

            messages.success(
                request,
                "Gmail successfully connected! You can now send emails through Gmail.",
            )
            return redirect("communications:communication_list")

        except Exception as e:
            messages.error(request, f"Failed to connect Gmail: {str(e)}")
            return redirect("communications:communication_list")


class GmailComposeView(LoginRequiredMixin, FormView):
    """Compose and send email via Gmail"""

    template_name = "communications/gmail_compose.html"
    form_class = ComposeEmailForm

    def dispatch(self, request, *args, **kwargs):
        try:
            return super().dispatch(request, *args, **kwargs)
        except Exception as e:
            # If there's any error in dispatch, show error message and redirect
            messages.error(
                request,
                f"Email compose error: {str(e)}. Gmail may not be properly configured.",
            )
            return redirect("communications:communication_list")

    def get_form_kwargs(self):
        try:
            kwargs = super().get_form_kwargs()
            kwargs["user"] = self.request.user
            return kwargs
        except Exception as e:
            # If form kwargs fail, provide minimal kwargs
            return {"user": self.request.user}

    def get_context_data(self, **kwargs):
        try:
            context = super().get_context_data(**kwargs)
        except Exception as e:
            # If context data fails, create minimal context with basic form
            from django import forms

            class SimpleEmailForm(forms.Form):
                recipients = forms.CharField(widget=forms.Textarea(attrs={"rows": 2}))
                subject = forms.CharField()
                body = forms.CharField(widget=forms.Textarea(attrs={"rows": 10}))

            simple_form = SimpleEmailForm()
            context = {"form": simple_form, "view": self, "form_error": str(e)}

        try:
            gmail_service = GmailService(self.request.user)
            context["gmail_authenticated"] = gmail_service.is_authenticated()
        except Exception as e:
            # If Gmail service initialization fails, assume not authenticated
            context["gmail_authenticated"] = False
            context["gmail_error"] = str(e)

        try:
            # Only fetch fields that exist in database - exclude 'body' field temporarily due to schema mismatch
            context["email_templates"] = EmailTemplate.objects.filter(
                is_active=True
            ).only("id", "name", "subject", "is_active", "category")
            context["email_signatures"] = EmailSignature.objects.filter(
                user=self.request.user
            ).only("id", "name", "content", "is_default", "user")
        except Exception:
            context["email_templates"] = []
            context["email_signatures"] = []

        # Pre-populate recipient if specified
        recipient = self.request.GET.get("recipient")
        name = self.request.GET.get("name")
        contact_id = self.request.GET.get("contact_id")

        if recipient:
            context["preselected_recipient"] = recipient
            context["preselected_name"] = name
            context["preselected_contact_id"] = contact_id

        return context

    def form_valid(self, form):
        try:
            gmail_service = GmailService(self.request.user)

            if not gmail_service.is_authenticated():
                messages.error(
                    self.request,
                    "Gmail is not connected. Please authorize Gmail access first.",
                )
                return redirect("communications:gmail_auth")
        except Exception as e:
            messages.error(
                self.request, f"Gmail service error: {str(e)}. Please try again later."
            )
            return self.form_invalid(form)

        # Extract form data
        to_emails = [
            email.strip() for email in form.cleaned_data["recipients"].split(",")
        ]
        cc_emails = [
            email.strip()
            for email in form.cleaned_data.get("cc", "").split(",")
            if email.strip()
        ]
        bcc_emails = [
            email.strip()
            for email in form.cleaned_data.get("bcc", "").split(",")
            if email.strip()
        ]
        subject = form.cleaned_data["subject"]
        body = form.cleaned_data["body"]
        is_html = form.cleaned_data.get("is_html", True)
        template_id = form.cleaned_data.get("template")
        signature_id = form.cleaned_data.get("signature")

        # Send email
        result = gmail_service.send_email(
            to_emails=to_emails,
            cc_emails=cc_emails if cc_emails != [""] else None,
            bcc_emails=bcc_emails if bcc_emails != [""] else None,
            subject=subject,
            body=body,
            is_html=is_html,
            template_id=template_id.id if template_id else None,
            signature_id=signature_id.id if signature_id else None,
            related_person_id=form.cleaned_data.get("related_person_id"),
            related_church_id=form.cleaned_data.get("related_church_id"),
        )

        if result["success"]:
            messages.success(
                self.request, f'Email sent successfully to {", ".join(to_emails)}'
            )
            return redirect("communications:communication_list")
        else:
            messages.error(self.request, f'Failed to send email: {result["error"]}')
            return self.form_invalid(form)


class GmailSyncView(LoginRequiredMixin, View):
    """Sync Gmail messages to communications"""

    def post(self, request):
        gmail_service = GmailService(request.user)

        if not gmail_service.is_authenticated():
            return JsonResponse(
                {"success": False, "error": "Gmail not authenticated"}, status=400
            )

        days_back = int(request.POST.get("days_back", 7))
        result = gmail_service.sync_emails_to_communications(days_back)

        if result["success"]:
            messages.success(
                request,
                f'Synced {result["synced_count"]} emails from the last {days_back} days.',
            )
        else:
            messages.error(request, f'Sync failed: {result["error"]}')

        return JsonResponse(result)


@login_required
def gmail_status(request):
    """Check Gmail authentication status"""
    gmail_service = GmailService(request.user)
    return JsonResponse(
        {
            "authenticated": gmail_service.is_authenticated(),
            "user_email": request.user.email,
        }
    )


@login_required
def gmail_disconnect(request):
    """Disconnect Gmail for user"""
    if request.method == "POST":
        try:
            from mobilize.authentication.models import GoogleToken

            GoogleToken.objects.filter(user=request.user).delete()
            messages.success(request, "Gmail disconnected successfully.")
        except Exception as e:
            messages.error(request, f"Error disconnecting Gmail: {str(e)}")

    return redirect("communications:communication_list")


# Google Contacts Sync Views
class ContactSyncView(LoginRequiredMixin, View):
    """Sync Google contacts based on user preferences"""

    def post(self, request):
        contacts_service = GoogleContactsService(request.user)

        if not contacts_service.is_authenticated():
            return JsonResponse(
                {
                    "success": False,
                    "error": "Google Contacts not authenticated. Please connect Gmail first.",
                },
                status=400,
            )

        # Perform sync based on user preferences
        result = contacts_service.sync_contacts_based_on_preference()

        if result["success"]:
            messages.success(request, result["message"])
        else:
            messages.error(request, f'Contact sync failed: {result["error"]}')

        return JsonResponse(result)


@login_required
def contact_sync_status(request):
    """Get contact sync status for user"""
    try:
        from mobilize.authentication.models import UserContactSyncSettings

        sync_settings = UserContactSyncSettings.objects.filter(
            user=request.user
        ).first()
        contacts_service = GoogleContactsService(request.user)

        status = {
            "authenticated": contacts_service.is_authenticated(),
            "sync_preference": (
                sync_settings.sync_preference if sync_settings else "crm_only"
            ),
            "auto_sync_enabled": (
                sync_settings.auto_sync_enabled if sync_settings else False
            ),
            "last_sync_at": (
                sync_settings.last_sync_at.isoformat()
                if sync_settings and sync_settings.last_sync_at
                else None
            ),
            "has_errors": bool(sync_settings.sync_errors) if sync_settings else False,
            "should_sync_now": (
                sync_settings.should_sync_now() if sync_settings else False
            ),
        }

        return JsonResponse(status)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


class ContactSyncSettingsView(LoginRequiredMixin, View):
    """Handle contact sync settings updates"""

    def post(self, request):
        try:
            from mobilize.authentication.models import UserContactSyncSettings

            sync_preference = request.POST.get("sync_preference")
            auto_sync_enabled = request.POST.get("auto_sync_enabled") == "true"
            sync_frequency_hours = int(request.POST.get("sync_frequency_hours", 24))

            # Validate sync preference
            valid_preferences = [
                choice[0] for choice in UserContactSyncSettings.SYNC_CHOICES
            ]
            if sync_preference not in valid_preferences:
                return JsonResponse(
                    {"success": False, "error": "Invalid sync preference"}, status=400
                )

            # Get or create settings
            settings, created = UserContactSyncSettings.objects.get_or_create(
                user=request.user,
                defaults={
                    "sync_preference": sync_preference,
                    "auto_sync_enabled": auto_sync_enabled,
                    "sync_frequency_hours": sync_frequency_hours,
                },
            )

            if not created:
                settings.sync_preference = sync_preference
                settings.auto_sync_enabled = auto_sync_enabled
                settings.sync_frequency_hours = sync_frequency_hours
                settings.save()

            message = f"Contact sync settings updated: {settings.get_sync_preference_display()}"
            messages.success(request, message)

            return JsonResponse(
                {
                    "success": True,
                    "message": message,
                    "settings": {
                        "sync_preference": settings.sync_preference,
                        "auto_sync_enabled": settings.auto_sync_enabled,
                        "sync_frequency_hours": settings.sync_frequency_hours,
                    },
                }
            )

        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=500)


# Google Calendar Integration Views
class CalendarAuthView(LoginRequiredMixin, View):
    """Initiate Google Calendar OAuth flow"""

    def get(self, request):
        from .google_calendar_service import GoogleCalendarService

        calendar_service = GoogleCalendarService(request.user)
        redirect_uri = request.build_absolute_uri(
            reverse("communications:calendar_callback")
        )

        if calendar_service.is_authenticated():
            messages.info(
                request, "Google Calendar is already connected for your account."
            )
            return redirect("communications:calendar_list")

        auth_url = calendar_service.get_authorization_url(redirect_uri)
        return redirect(auth_url)


class CalendarCallbackView(LoginRequiredMixin, View):
    """Handle Google Calendar OAuth callback"""

    def get(self, request):
        from .google_calendar_service import GoogleCalendarService

        code = request.GET.get("code")
        error = request.GET.get("error")

        if error:
            messages.error(request, f"Calendar authorization failed: {error}")
            return redirect("communications:communication_list")

        if not code:
            messages.error(request, "Authorization code not received.")
            return redirect("communications:communication_list")

        try:
            calendar_service = GoogleCalendarService(request.user)
            redirect_uri = request.build_absolute_uri(
                reverse("communications:calendar_callback")
            )
            calendar_service.handle_oauth_callback(code, redirect_uri)

            messages.success(
                request,
                "Google Calendar successfully connected! You can now create and manage events.",
            )
            return redirect("communications:calendar_list")

        except Exception as e:
            messages.error(request, f"Failed to connect Calendar: {str(e)}")
            return redirect("communications:communication_list")


class CalendarListView(LoginRequiredMixin, View):
    """Display user's calendars and upcoming events"""

    def get(self, request):
        from .google_calendar_service import GoogleCalendarService
        from datetime import datetime, timedelta

        calendar_service = GoogleCalendarService(request.user)

        if not calendar_service.is_authenticated():
            return render(request, "communications/calendar_auth_required.html")

        # Get user's calendars
        calendars = calendar_service.get_calendars()

        # Get upcoming events from primary calendar
        upcoming_events = calendar_service.get_events(
            calendar_id="primary",
            time_min=datetime.now(),
            time_max=datetime.now() + timedelta(days=30),
            max_results=20,
        )

        context = {
            "calendars": calendars,
            "upcoming_events": upcoming_events,
            "calendar_authenticated": True,
        }

        return render(request, "communications/calendar_list.html", context)


class CalendarEventCreateView(LoginRequiredMixin, View):
    """Create a new calendar event"""

    def get(self, request):
        from .google_calendar_service import GoogleCalendarService

        calendar_service = GoogleCalendarService(request.user)

        if not calendar_service.is_authenticated():
            messages.error(request, "Please connect your Google Calendar first.")
            return redirect("communications:calendar_auth")

        calendars = calendar_service.get_calendars()

        # Pre-populate if contact info provided
        context = {"calendars": calendars, "preselected_contact": {}}

        contact_type = request.GET.get("contact_type")
        contact_id = request.GET.get("contact_id")

        if contact_type and contact_id:
            context["preselected_contact"] = {"type": contact_type, "id": contact_id}

            # Get contact details for pre-population
            if contact_type == "person":
                from mobilize.contacts.models import Person

                try:
                    person = Person.objects.get(id=contact_id)
                    context["contact_email"] = person.contact.email
                    context["contact_name"] = (
                        f"{person.contact.first_name} {person.contact.last_name}"
                    )
                except Person.DoesNotExist:
                    pass
            elif contact_type == "church":
                from mobilize.churches.models import Church

                try:
                    church = Church.objects.get(id=contact_id)
                    context["contact_email"] = church.contact.email
                    context["contact_name"] = church.contact.name
                except Church.DoesNotExist:
                    pass

        return render(request, "communications/calendar_event_form.html", context)

    def post(self, request):
        from .google_calendar_service import GoogleCalendarService
        from datetime import datetime

        calendar_service = GoogleCalendarService(request.user)

        if not calendar_service.is_authenticated():
            messages.error(request, "Calendar not connected.")
            return redirect("communications:calendar_auth")

        try:
            # Extract form data
            calendar_id = request.POST.get("calendar_id", "primary")
            title = request.POST.get("title")
            description = request.POST.get("description", "")
            location = request.POST.get("location", "")

            # Parse dates and times
            start_date = request.POST.get("start_date")
            start_time = request.POST.get("start_time")
            end_date = request.POST.get("end_date")
            end_time = request.POST.get("end_time")
            timezone_name = request.POST.get("timezone", "UTC")
            all_day = request.POST.get("all_day") == "on"

            # Parse attendees
            attendees_str = request.POST.get("attendees", "")
            attendees = [
                email.strip() for email in attendees_str.split(",") if email.strip()
            ]

            # Create datetime objects
            if all_day:
                start_datetime = datetime.strptime(start_date, "%Y-%m-%d")
                end_datetime = datetime.strptime(end_date, "%Y-%m-%d")
            else:
                start_datetime = datetime.strptime(
                    f"{start_date} {start_time}", "%Y-%m-%d %H:%M"
                )
                end_datetime = datetime.strptime(
                    f"{end_date} {end_time}", "%Y-%m-%d %H:%M"
                )

            # Create the event
            result = calendar_service.create_event(
                calendar_id=calendar_id,
                title=title,
                description=description,
                start_datetime=start_datetime,
                end_datetime=end_datetime,
                attendees=attendees,
                location=location,
                timezone_name=timezone_name,
                all_day=all_day,
            )

            if result["success"]:
                messages.success(request, f'Event "{title}" created successfully!')
                return redirect("communications:calendar_list")
            else:
                messages.error(request, f'Failed to create event: {result["error"]}')
                return redirect("communications:calendar_event_create")

        except Exception as e:
            messages.error(request, f"Error creating event: {str(e)}")
            return redirect("communications:calendar_event_create")


class CalendarSyncView(LoginRequiredMixin, View):
    """Sync calendar events to tasks"""

    def post(self, request):
        from .google_calendar_service import GoogleCalendarService

        calendar_service = GoogleCalendarService(request.user)

        if not calendar_service.is_authenticated():
            return JsonResponse(
                {"success": False, "error": "Calendar not authenticated"}, status=400
            )

        days_ahead = int(request.POST.get("days_ahead", 30))
        result = calendar_service.sync_events_to_tasks(days_ahead)

        if result["success"]:
            messages.success(
                request, f'Synced {result["synced_count"]} calendar events to tasks.'
            )
        else:
            messages.error(request, f'Sync failed: {result["error"]}')

        return JsonResponse(result)


@login_required
def calendar_status(request):
    """Check Google Calendar authentication status"""
    from .google_calendar_service import GoogleCalendarService

    calendar_service = GoogleCalendarService(request.user)
    return JsonResponse(
        {
            "authenticated": calendar_service.is_authenticated(),
            "user_email": request.user.email,
        }
    )


@login_required
def calendar_disconnect(request):
    """Disconnect Google Calendar for user"""
    if request.method == "POST":
        try:
            # This would remove calendar-specific tokens if we stored them separately
            # For now, we'll use the same token as Gmail since they share OAuth scope
            messages.success(
                request,
                "Calendar access revoked. Note: This may also affect Gmail access.",
            )
        except Exception as e:
            messages.error(request, f"Error disconnecting Calendar: {str(e)}")

    return redirect("communications:communication_list")


@login_required
def get_contacts_json(request):
    """Get contacts (people and churches) as JSON for dropdowns"""
    from mobilize.contacts.models import Person
    from mobilize.churches.models import Church

    # Apply office-level filtering similar to other views
    if request.user.role == "super_admin":
        people = Person.objects.select_related("contact").all()
        churches = Church.objects.select_related("contact").all()
    else:
        try:
            from mobilize.admin_panel.models import UserOffice

            user_offices = list(
                UserOffice.objects.filter(user_id=str(request.user.id)).values_list(
                    "office_id", flat=True
                )
            )

            if user_offices:
                # Filter by office - contacts belong to offices
                people = Person.objects.select_related("contact").filter(
                    contact__office__in=user_offices
                )
                churches = Church.objects.select_related("contact").filter(
                    contact__office__in=user_offices
                )
            else:
                # If user has no office assignments, return empty querysets
                people = Person.objects.none()
                churches = Church.objects.none()
        except Exception:
            # If there's any error with office filtering, return empty querysets
            people = Person.objects.none()
            churches = Church.objects.none()

    people_data = [
        {
            "id": person.id,  # Use person.id instead of person.contact.id
            "name": f"{person.contact.first_name} {person.contact.last_name}".strip()
            or person.contact.email
            or f"Person {person.id}",
        }
        for person in people
    ]

    churches_data = [
        {
            "id": church.id,  # Use church.id instead of church.contact.id
            "name": church.contact.church_name
            or church.contact.email
            or f"Church {church.id}",
        }
        for church in churches
    ]

    return JsonResponse({"people": people_data, "churches": churches_data})


@login_required
def check_gmail_notifications(request):
    """Check for new Gmail notifications for the current user"""
    from django.core.cache import cache

    notification_key = f"gmail_notification_{request.user.id}"
    notification = cache.get(notification_key)

    if notification and not notification.get("read"):
        # Mark as read
        notification["read"] = True
        cache.set(notification_key, notification, timeout=86400)

        return JsonResponse(
            {
                "has_notification": True,
                "message": notification["message"],
                "timestamp": notification["timestamp"],
                "new_emails": notification["new_emails"],
            }
        )

    return JsonResponse({"has_notification": False})


@login_required
def create_meet_link(request):
    """Create a Google Meet link for video calls"""
    if request.method == "POST":
        from .google_meet_service import GoogleMeetService
        from datetime import datetime, timedelta
        import json

        meet_service = GoogleMeetService(request.user)

        if not meet_service.is_authenticated():
            return JsonResponse(
                {
                    "success": False,
                    "error": "Google Calendar not connected. Please authorize Google access first.",
                }
            )

        try:
            data = json.loads(request.body)
            meet_option = data.get("meetOption", "none")
            title = data.get("title", "Video Call")

            if meet_option == "instant":
                # Create instant meet
                duration = data.get("duration", 60)
                result = meet_service.create_instant_meet_link(title, duration)

            elif meet_option == "scheduled":
                # Create scheduled meet
                start_datetime_str = data.get("start_datetime")
                duration = data.get("duration", 60)

                if not start_datetime_str:
                    return JsonResponse(
                        {
                            "success": False,
                            "error": "Start datetime is required for scheduled meetings",
                        }
                    )

                # Parse the datetime
                start_datetime = datetime.fromisoformat(
                    start_datetime_str.replace("Z", "+00:00")
                )
                end_datetime = start_datetime + timedelta(minutes=duration)

                # Get attendee emails from related contacts
                attendee_emails = []
                person_id = data.get("person_id")
                church_id = data.get("church_id")

                if person_id:
                    try:
                        from mobilize.contacts.models import Person

                        person = Person.objects.select_related("contact").get(
                            contact__id=person_id
                        )
                        if person.contact.email:
                            attendee_emails.append(person.contact.email)
                    except Person.DoesNotExist:
                        pass

                if church_id:
                    try:
                        from mobilize.churches.models import Church

                        church = Church.objects.select_related("contact").get(
                            contact__id=church_id
                        )
                        if church.contact.email:
                            attendee_emails.append(church.contact.email)
                    except Church.DoesNotExist:
                        pass

                result = meet_service.create_scheduled_meet(
                    title=title,
                    start_datetime=start_datetime,
                    end_datetime=end_datetime,
                    description=data.get("description", ""),
                    attendee_emails=attendee_emails,
                )

            else:
                return JsonResponse({"success": False, "error": "Invalid meet option"})

            return JsonResponse(result)

        except json.JSONDecodeError:
            return JsonResponse({"success": False, "error": "Invalid JSON data"})
        except Exception as e:
            return JsonResponse(
                {"success": False, "error": f"Error creating Meet link: {str(e)}"}
            )

    return JsonResponse({"success": False, "error": "Invalid request method"})


# Bulk Operations for Communications
@login_required
@require_POST
def bulk_delete_communications(request):
    """Delete selected communications"""
    communication_ids = request.POST.get("communication_ids", "").split(",")
    communication_ids = [id.strip() for id in communication_ids if id.strip()]

    if not communication_ids:
        messages.error(request, "No communications selected for deletion.")
        return redirect("communications:communication_list")

    try:
        # Get communications that user has permission to delete
        if request.user.role == "super_admin":
            communications = Communication.objects.filter(id__in=communication_ids)
        else:
            from mobilize.admin_panel.models import UserOffice

            user_offices = UserOffice.objects.filter(
                user_id=str(request.user.id)
            ).values_list("office_id", flat=True)

            communications = Communication.objects.filter(
                id__in=communication_ids
            ).filter(
                models.Q(user=request.user)
                | models.Q(person__contact__office__in=user_offices)
                | models.Q(church__contact__office__in=user_offices)
                | models.Q(office__in=user_offices)
            )

        deleted_count = communications.count()
        communications.delete()

        messages.success(
            request, f"Successfully deleted {deleted_count} communication(s)."
        )

    except Exception as e:
        messages.error(request, f"Error deleting communications: {str(e)}")

    return redirect("communications:communication_list")


@login_required
@require_POST
def bulk_archive_communications(request):
    """Archive/unarchive selected communications"""
    communication_ids = request.POST.get("communication_ids", "").split(",")
    communication_ids = [id.strip() for id in communication_ids if id.strip()]
    archive_action = request.POST.get(
        "archive_action", "archive"
    )  # 'archive' or 'unarchive'

    if not communication_ids:
        messages.error(request, "No communications selected.")
        return redirect("communications:communication_list")

    try:
        # Get communications that user has permission to modify
        if request.user.role == "super_admin":
            communications = Communication.objects.filter(id__in=communication_ids)
        else:
            from mobilize.admin_panel.models import UserOffice

            user_offices = UserOffice.objects.filter(
                user_id=str(request.user.id)
            ).values_list("office_id", flat=True)

            communications = Communication.objects.filter(
                id__in=communication_ids
            ).filter(
                models.Q(user=request.user)
                | models.Q(person__contact__office__in=user_offices)
                | models.Q(church__contact__office__in=user_offices)
                | models.Q(office__in=user_offices)
            )

        archived_value = archive_action == "archive"
        updated_count = communications.update(archived=archived_value)

        action_word = "archived" if archived_value else "unarchived"
        messages.success(
            request, f"Successfully {action_word} {updated_count} communication(s)."
        )

    except Exception as e:
        messages.error(request, f"Error updating communications: {str(e)}")

    return redirect("communications:communication_list")


@login_required
@require_POST
def bulk_update_communication_status(request):
    """Update status for selected communications"""
    communication_ids = request.POST.get("communication_ids", "").split(",")
    communication_ids = [id.strip() for id in communication_ids if id.strip()]
    status = request.POST.get("status", "").strip()

    if not communication_ids:
        messages.error(request, "No communications selected.")
        return redirect("communications:communication_list")

    if not status:
        messages.error(request, "No status selected.")
        return redirect("communications:communication_list")

    try:
        # Get communications that user has permission to modify
        if request.user.role == "super_admin":
            communications = Communication.objects.filter(id__in=communication_ids)
        else:
            from mobilize.admin_panel.models import UserOffice

            user_offices = UserOffice.objects.filter(
                user_id=str(request.user.id)
            ).values_list("office_id", flat=True)

            communications = Communication.objects.filter(
                id__in=communication_ids
            ).filter(
                models.Q(user=request.user)
                | models.Q(person__contact__office__in=user_offices)
                | models.Q(church__contact__office__in=user_offices)
                | models.Q(office__in=user_offices)
            )

        updated_count = communications.update(status=status)

        messages.success(
            request,
            f"Successfully updated status for {updated_count} communication(s).",
        )

    except Exception as e:
        messages.error(request, f"Error updating communication status: {str(e)}")

    return redirect("communications:communication_list")


@login_required
@require_POST
def bulk_update_communication_type(request):
    """Update type for selected communications"""
    communication_ids = request.POST.get("communication_ids", "").split(",")
    communication_ids = [id.strip() for id in communication_ids if id.strip()]
    comm_type = request.POST.get("type", "").strip()

    if not communication_ids:
        messages.error(request, "No communications selected.")
        return redirect("communications:communication_list")

    if not comm_type:
        messages.error(request, "No type selected.")
        return redirect("communications:communication_list")

    try:
        # Get communications that user has permission to modify
        if request.user.role == "super_admin":
            communications = Communication.objects.filter(id__in=communication_ids)
        else:
            from mobilize.admin_panel.models import UserOffice

            user_offices = UserOffice.objects.filter(
                user_id=str(request.user.id)
            ).values_list("office_id", flat=True)

            communications = Communication.objects.filter(
                id__in=communication_ids
            ).filter(
                models.Q(user=request.user)
                | models.Q(person__contact__office__in=user_offices)
                | models.Q(church__contact__office__in=user_offices)
                | models.Q(office__in=user_offices)
            )

        updated_count = communications.update(type=comm_type)

        messages.success(
            request, f"Successfully updated type for {updated_count} communication(s)."
        )

    except Exception as e:
        messages.error(request, f"Error updating communication type: {str(e)}")

    return redirect("communications:communication_list")


@login_required
@require_POST
def bulk_assign_communication_user(request):
    """Assign selected communications to a user"""
    communication_ids = request.POST.get("communication_ids", "").split(",")
    communication_ids = [id.strip() for id in communication_ids if id.strip()]
    user_id = request.POST.get("user_id", "").strip()

    if not communication_ids:
        messages.error(request, "No communications selected.")
        return redirect("communications:communication_list")

    if not user_id:
        messages.error(request, "No user selected.")
        return redirect("communications:communication_list")

    try:
        from django.contrib.auth import get_user_model

        User = get_user_model()
        assigned_user = get_object_or_404(User, id=user_id)

        # Get communications that user has permission to modify
        if request.user.role == "super_admin":
            communications = Communication.objects.filter(id__in=communication_ids)
        else:
            from mobilize.admin_panel.models import UserOffice

            user_offices = UserOffice.objects.filter(
                user_id=str(request.user.id)
            ).values_list("office_id", flat=True)

            communications = Communication.objects.filter(
                id__in=communication_ids
            ).filter(
                models.Q(user=request.user)
                | models.Q(person__contact__office__in=user_offices)
                | models.Q(church__contact__office__in=user_offices)
                | models.Q(office__in=user_offices)
            )

        updated_count = communications.update(user=assigned_user)

        messages.success(
            request,
            f"Successfully assigned {updated_count} communication(s) to {assigned_user.get_full_name()}.",
        )

    except Exception as e:
        messages.error(request, f"Error assigning communications: {str(e)}")

    return redirect("communications:communication_list")


@login_required
def send_sms_view(request):
    """
    Handle SMS sending requests
    """
    if request.method != "POST":
        return JsonResponse(
            {"success": False, "error": "Method not allowed"}, status=405
        )

    try:
        from .sms_service import sms_service

        # Get form data
        to_number = request.POST.get("to_number")
        message_body = request.POST.get("message")
        contact_id = request.POST.get("contact_id")
        contact_type = request.POST.get(
            "contact_type", "person"
        )  # 'person' or 'church'

        # Validate required fields
        if not to_number or not message_body:
            return JsonResponse(
                {"success": False, "error": "Phone number and message are required"},
                status=400,
            )

        # Get contact object
        contact = None
        if contact_id:
            try:
                if contact_type == "person":
                    from mobilize.contacts.models import Person

                    person = Person.objects.get(pk=contact_id)
                    contact = person.contact
                elif contact_type == "church":
                    from mobilize.churches.models import Church

                    church = Church.objects.get(pk=contact_id)
                    contact = church.contact
            except (Person.DoesNotExist, Church.DoesNotExist):
                logger.warning(f"Contact not found: {contact_type} {contact_id}")

        # Send SMS
        result = sms_service.send_sms(
            to_number=to_number,
            message_body=message_body,
            user=request.user,
            contact=contact,
        )

        if result["success"]:
            return JsonResponse(
                {
                    "success": True,
                    "message": "SMS sent successfully",
                    "message_sid": result.get("message_sid"),
                }
            )
        else:
            return JsonResponse(
                {"success": False, "error": result["error"]}, status=400
            )

    except Exception as e:
        logger.error(f"Error in send_sms_view: {e}")
        return JsonResponse(
            {"success": False, "error": "An unexpected error occurred"}, status=500
        )


@require_POST
def sms_webhook(request):
    """
    Handle incoming SMS webhooks from Twilio
    """
    try:
        from .sms_service import sms_service

        # Extract webhook data
        from_number = request.POST.get("From")
        body = request.POST.get("Body")
        message_sid = request.POST.get("MessageSid")

        if not all([from_number, body, message_sid]):
            return JsonResponse({"error": "Missing required fields"}, status=400)

        # Process incoming SMS
        result = sms_service.handle_incoming_sms(
            from_number=from_number, body=body, message_sid=message_sid
        )

        # Return TwiML response (empty response acknowledges receipt)
        from django.http import HttpResponse

        return HttpResponse(
            '<?xml version="1.0" encoding="UTF-8"?><Response></Response>',
            content_type="text/xml",
        )

    except Exception as e:
        logger.error(f"Error in sms_webhook: {e}")
        return JsonResponse({"error": "Internal server error"}, status=500)


# Native SMS Logging Views
@login_required
def native_sms_log_view(request):
    """View for manually logging SMS messages"""
    if request.method == "POST":
        try:
            from .native_sms_service import native_sms_service

            # Get form data
            phone_number = request.POST.get("phone_number", "").strip()
            message_body = request.POST.get("message_body", "").strip()
            direction = request.POST.get("direction", "inbound")

            if not phone_number or not message_body:
                return JsonResponse(
                    {
                        "success": False,
                        "error": "Phone number and message are required",
                    },
                    status=400,
                )

            # Log the SMS
            if direction == "inbound":
                result = native_sms_service.log_incoming_sms(
                    from_number=phone_number,
                    message_body=message_body,
                    user=request.user,
                )
            else:
                result = native_sms_service.log_outgoing_sms(
                    to_number=phone_number, message_body=message_body, user=request.user
                )

            if result["success"]:
                return JsonResponse(
                    {
                        "success": True,
                        "message": f"SMS logged successfully",
                        "contact_found": result["contact_found"],
                        "contact_name": result.get("contact_name"),
                        "normalized_phone": result.get("normalized_phone"),
                        "communication_id": result["communication"].id,
                    }
                )
            else:
                return JsonResponse(
                    {"success": False, "error": result["error"]}, status=400
                )

        except Exception as e:
            logger.error(f"Error in native_sms_log_view: {e}")
            return JsonResponse(
                {"success": False, "error": "An unexpected error occurred"}, status=500
            )

    # GET request - show the form
    return render(request, "communications/native_sms_log.html")


@login_required
def sms_quick_log_api(request):
    """API endpoint for quick SMS logging from mobile"""
    if request.method == "POST":
        try:
            from .native_sms_service import native_sms_service
            import json

            # Parse JSON data
            data = json.loads(request.body)

            phone_number = data.get("phone_number", "").strip()
            message_body = data.get("message_body", "").strip()
            direction = data.get("direction", "inbound")

            if not phone_number or not message_body:
                return JsonResponse(
                    {
                        "success": False,
                        "error": "Phone number and message are required",
                    },
                    status=400,
                )

            # Log the SMS
            if direction == "inbound":
                result = native_sms_service.log_incoming_sms(
                    from_number=phone_number,
                    message_body=message_body,
                    user=request.user,
                )
            else:
                result = native_sms_service.log_outgoing_sms(
                    to_number=phone_number, message_body=message_body, user=request.user
                )

            return JsonResponse(result)

        except Exception as e:
            logger.error(f"Error in sms_quick_log_api: {e}")
            return JsonResponse(
                {"success": False, "error": "An unexpected error occurred"}, status=500
            )

    return JsonResponse({"error": "Method not allowed"}, status=405)


@login_required
def sms_contact_search_api(request):
    """API endpoint for searching contacts by phone number"""
    try:
        from .native_sms_service import native_sms_service

        phone_number = request.GET.get("phone", "").strip()

        if not phone_number:
            return JsonResponse(
                {"success": False, "error": "Phone number is required"}, status=400
            )

        # Normalize and search for contact
        normalized_phone = native_sms_service.normalize_phone_number(phone_number)
        contact = native_sms_service._find_contact_by_phone(normalized_phone)

        if contact:
            contact_name = native_sms_service._get_contact_name(contact)
            contact_type = (
                "person"
                if hasattr(contact, "person_details") and contact.person_details
                else "church"
            )

            return JsonResponse(
                {
                    "success": True,
                    "contact_found": True,
                    "contact_name": contact_name,
                    "contact_type": contact_type,
                    "normalized_phone": normalized_phone,
                    "contact_id": contact.id,
                }
            )
        else:
            return JsonResponse(
                {
                    "success": True,
                    "contact_found": False,
                    "normalized_phone": normalized_phone,
                }
            )

    except Exception as e:
        logger.error(f"Error in sms_contact_search_api: {e}")
        return JsonResponse(
            {"success": False, "error": "An unexpected error occurred"}, status=500
        )


@login_required
def sms_history_api(request):
    """API endpoint for getting SMS history with a contact"""
    try:
        from .native_sms_service import native_sms_service

        phone_number = request.GET.get("phone", "").strip()

        if not phone_number:
            return JsonResponse(
                {"success": False, "error": "Phone number is required"}, status=400
            )

        # Find contact and get SMS history
        normalized_phone = native_sms_service.normalize_phone_number(phone_number)
        contact = native_sms_service._find_contact_by_phone(normalized_phone)

        if contact:
            recent_sms = native_sms_service.get_recent_sms_for_contact(
                contact, limit=20
            )

            sms_history = []
            for sms in recent_sms:
                sms_history.append(
                    {
                        "id": sms.id,
                        "direction": sms.direction,
                        "message": sms.message,
                        "date_sent": (
                            sms.date_sent.isoformat() if sms.date_sent else None
                        ),
                        "sender": sms.sender,
                        "user": sms.user.get_full_name() if sms.user else None,
                    }
                )

            return JsonResponse(
                {
                    "success": True,
                    "contact_found": True,
                    "contact_name": native_sms_service._get_contact_name(contact),
                    "sms_history": sms_history,
                }
            )
        else:
            return JsonResponse(
                {"success": True, "contact_found": False, "sms_history": []}
            )

    except Exception as e:
        logger.error(f"Error in sms_history_api: {e}")
        return JsonResponse(
            {"success": False, "error": "An unexpected error occurred"}, status=500
        )


@login_required
def communication_list_api(request):
    """
    JSON API endpoint for lazy loading communication list data.
    Supports search by people, church, subject, type, etc.
    """
    import logging
    from django.urls import reverse

    logger = logging.getLogger(__name__)

    try:
        # Filter communications by user - each user sees only their own communications
        if request.user.role == "super_admin":
            queryset = Communication.objects.all()
        else:
            queryset = Communication.objects.filter(user=request.user)

        # Get query parameters
        search_query = request.GET.get("search", "")
        type_filter = request.GET.get("type", "")
        direction_filter = request.GET.get("direction", "")
        status_filter = request.GET.get("status", "")
        contact_id = request.GET.get("contact_id", "")
        person_id = request.GET.get("person_id", "")
        page = int(request.GET.get("page", 1))
        per_page = int(request.GET.get("per_page", 25))

        # Apply filters from GET parameters
        if type_filter:
            queryset = queryset.filter(type=type_filter)

        if direction_filter:
            queryset = queryset.filter(direction=direction_filter)

        if status_filter:
            queryset = queryset.filter(status=status_filter)

        # Filter by contact_id or person_id if provided (for "View All" button functionality)
        if person_id:
            # Direct person ID filtering is more precise
            queryset = queryset.filter(person_id=person_id)
        elif contact_id:
            from django.db.models import Q

            queryset = queryset.filter(
                Q(person__contact_id=contact_id) | Q(church__contact_id=contact_id)
            )

        # General search across people, church, subject, type
        if search_query:
            from django.db.models import Q

            search_conditions = Q(
                # Search in basic communication fields
                Q(subject__icontains=search_query)
                | Q(sender__icontains=search_query)
                | Q(message__icontains=search_query)
                | Q(content__icontains=search_query)
                | Q(type__icontains=search_query)
                |
                # Search in person contact fields
                Q(person__contact__first_name__icontains=search_query)
                | Q(person__contact__last_name__icontains=search_query)
                | Q(person__contact__email__icontains=search_query)
                |
                # Search in church contact fields
                Q(church__contact__church_name__icontains=search_query)
                | Q(church__contact__email__icontains=search_query)
                | Q(church__name__icontains=search_query)
            )

            queryset = queryset.filter(search_conditions)

        # Apply sorting: most recent first
        queryset = queryset.order_by("-date", "-created_at")

        # Get total count
        total_count = queryset.count()

        # Apply pagination
        start = (page - 1) * per_page
        end = start + per_page
        communications = queryset[start:end]

        # Format results
        results = []
        for comm in communications:
            # Get contact info
            contact_name = None
            contact_url = None
            contact_icon = "fas fa-user"

            if comm.person:
                contact_name = f"{comm.person.contact.first_name} {comm.person.contact.last_name}".strip()
                contact_url = reverse("contacts:person_detail", args=[comm.person.id])
                contact_icon = "fas fa-user"
            elif comm.church:
                contact_name = comm.church.name or comm.church.contact.church_name
                contact_url = reverse("churches:church_detail", args=[comm.church.id])
                contact_icon = "fas fa-church"

            # Format date
            date_formatted = (
                comm.date.strftime("%b %d, %Y at %I:%M %p") if comm.date else "No date"
            )

            results.append(
                {
                    "id": comm.id,
                    "type": comm.type,
                    "subject": comm.subject or "No subject",
                    "sender": comm.sender or "",
                    "message": comm.message or comm.content or "",
                    "direction": comm.direction,
                    "date": date_formatted,
                    "contact_name": contact_name,
                    "contact_url": contact_url,
                    "contact_icon": contact_icon,
                    "detail_url": reverse(
                        "communications:communication_detail", args=[comm.id]
                    ),
                    "edit_url": reverse(
                        "communications:communication_update", args=[comm.id]
                    ),
                    "delete_url": reverse(
                        "communications:communication_delete", args=[comm.id]
                    ),
                }
            )

        # Calculate pagination info
        has_next = end < total_count
        has_previous = page > 1

        return JsonResponse(
            {
                "results": results,
                "page": page,
                "per_page": per_page,
                "total": total_count,
                "has_next": has_next,
                "has_previous": has_previous,
            }
        )

    except Exception as e:
        logger.error(f"Communication API error: {e}")
        return JsonResponse(
            {
                "results": [],
                "page": page,
                "per_page": per_page,
                "total": 0,
                "has_next": False,
                "has_previous": False,
                "error": str(e),
            }
        )


@login_required
@require_POST
def sync_person_emails(request):
    """Sync emails for a specific contact person"""
    import json

    try:
        # Parse JSON body
        data = json.loads(request.body)
        contact_id = data.get("contact_id")
        contact_email = data.get("contact_email")

        if not contact_id or not contact_email:
            return JsonResponse(
                {"success": False, "error": "Contact ID and email are required"},
                status=400,
            )

        # Verify the contact exists and user has permission
        from mobilize.contacts.models import Contact

        try:
            contact = Contact.objects.get(id=contact_id)
            # Check if user has permission to view this contact
            # Users can access contacts from offices they belong to
            if contact.office:
                # Get user's office assignments
                from mobilize.admin_panel.models import UserOffice

                user_offices = UserOffice.objects.filter(
                    user_id=str(request.user.id)
                ).values_list("office_id", flat=True)

                # Super admins can access all contacts
                if (
                    request.user.role != "super_admin"
                    and contact.office.id not in user_offices
                ):
                    return JsonResponse(
                        {
                            "success": False,
                            "error": "You don't have permission to sync emails for this contact",
                        },
                        status=403,
                    )
        except Contact.DoesNotExist:
            return JsonResponse(
                {"success": False, "error": "Contact not found"}, status=404
            )

        # Initialize Gmail service
        gmail_service = GmailService(request.user)

        if not gmail_service.is_authenticated():
            return JsonResponse(
                {
                    "success": False,
                    "error": "Gmail not authenticated. Please connect your Gmail account first.",
                },
                status=401,
            )

        # Sync emails for this specific contact
        # Using the sync_emails_to_communications method with specific_emails parameter
        result = gmail_service.sync_emails_to_communications(
            days_back=3650,  # 10 years back - effectively all history
            contacts_only=True,
            specific_emails=[contact_email],
        )

        if result["success"]:
            return JsonResponse(
                {
                    "success": True,
                    "synced_count": result.get("synced_count", 0),
                    "skipped_count": result.get("skipped_count", 0),
                    "message": f"Successfully synced {result.get('synced_count', 0)} emails with {contact_email}",
                }
            )
        else:
            return JsonResponse(
                {
                    "success": False,
                    "error": result.get("error", "Failed to sync emails"),
                },
                status=500,
            )

    except json.JSONDecodeError:
        return JsonResponse(
            {"success": False, "error": "Invalid JSON data"}, status=400
        )
    except Exception as e:
        logger.error(f"Error syncing person emails: {e}")
        return JsonResponse({"success": False, "error": str(e)}, status=500)
