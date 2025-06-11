from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, FormView
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.core.mail import EmailMultiAlternatives
from django.utils.html import strip_tags
from django.conf import settings
from django.contrib import messages
from django.views import View

from .models import EmailTemplate, EmailSignature, Communication, EmailAttachment
from .forms import EmailTemplateForm, EmailSignatureForm, CommunicationForm, ComposeEmailForm
from .gmail_service import GmailService
from .google_contacts_service import GoogleContactsService


# Email Template Views
class EmailTemplateListView(LoginRequiredMixin, ListView):
    model = EmailTemplate
    template_name = 'communications/email_template_list.html'
    context_object_name = 'email_templates'
    paginate_by = 10
    
    def get_queryset(self):
        # Filter templates by user's office if not super_admin
        if self.request.user.role == 'super_admin':
            return EmailTemplate.objects.all()
        return EmailTemplate.objects.filter(office__in=self.request.user.offices.all())


class EmailTemplateDetailView(LoginRequiredMixin, DetailView):
    model = EmailTemplate
    template_name = 'communications/email_template_detail.html'
    context_object_name = 'email_template'


class EmailTemplateCreateView(LoginRequiredMixin, CreateView):
    model = EmailTemplate
    form_class = EmailTemplateForm
    template_name = 'communications/email_template_form.html'
    success_url = reverse_lazy('communications:email_template_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)


class EmailTemplateUpdateView(LoginRequiredMixin, UpdateView):
    model = EmailTemplate
    form_class = EmailTemplateForm
    template_name = 'communications/email_template_form.html'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def get_success_url(self):
        return reverse('communications:email_template_detail', kwargs={'pk': self.object.pk})


class EmailTemplateDeleteView(LoginRequiredMixin, DeleteView):
    model = EmailTemplate
    template_name = 'communications/email_template_confirm_delete.html'
    success_url = reverse_lazy('communications:email_template_list')


# Email Signature Views
class EmailSignatureListView(LoginRequiredMixin, ListView):
    model = EmailSignature
    template_name = 'communications/email_signature_list.html'
    context_object_name = 'email_signatures'
    
    def get_queryset(self):
        # Users can only see their own signatures or shared ones
        return EmailSignature.objects.filter(
            created_by=self.request.user
        ) | EmailSignature.objects.filter(is_shared=True)


class EmailSignatureDetailView(LoginRequiredMixin, DetailView):
    model = EmailSignature
    template_name = 'communications/email_signature_detail.html'
    context_object_name = 'email_signature'


class EmailSignatureCreateView(LoginRequiredMixin, CreateView):
    model = EmailSignature
    form_class = EmailSignatureForm
    template_name = 'communications/email_signature_form.html'
    success_url = reverse_lazy('communications:email_signature_list')
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)


class EmailSignatureUpdateView(LoginRequiredMixin, UpdateView):
    model = EmailSignature
    form_class = EmailSignatureForm
    template_name = 'communications/email_signature_form.html'
    
    def get_success_url(self):
        return reverse('communications:email_signature_detail', kwargs={'pk': self.object.pk})
    
    def get_queryset(self):
        # Users can only edit their own signatures
        return EmailSignature.objects.filter(created_by=self.request.user)


class EmailSignatureDeleteView(LoginRequiredMixin, DeleteView):
    model = EmailSignature
    template_name = 'communications/email_signature_confirm_delete.html'
    success_url = reverse_lazy('communications:email_signature_list')
    
    def get_queryset(self):
        # Users can only delete their own signatures
        return EmailSignature.objects.filter(created_by=self.request.user)


# Communication Views
class CommunicationListView(LoginRequiredMixin, ListView):
    model = Communication
    template_name = 'communications/communication_list.html'
    context_object_name = 'communications'
    paginate_by = 20
    
    def get_queryset(self):
        # Filter by user's access
        if self.request.user.role == 'super_admin':
            return Communication.objects.all()
        return Communication.objects.filter(
            created_by=self.request.user
        ) | Communication.objects.filter(
            office__in=self.request.user.offices.all()
        )


class CommunicationDetailView(LoginRequiredMixin, DetailView):
    model = Communication
    template_name = 'communications/communication_detail.html'
    context_object_name = 'communication'


class CommunicationCreateView(LoginRequiredMixin, CreateView):
    model = Communication
    form_class = CommunicationForm
    template_name = 'communications/communication_form.html'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('communications:communication_detail', kwargs={'pk': self.object.pk})


class CommunicationUpdateView(LoginRequiredMixin, UpdateView):
    model = Communication
    form_class = CommunicationForm
    template_name = 'communications/communication_form.html'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def get_success_url(self):
        return reverse('communications:communication_detail', kwargs={'pk': self.object.pk})


class CommunicationDeleteView(LoginRequiredMixin, DeleteView):
    model = Communication
    template_name = 'communications/communication_confirm_delete.html'
    success_url = reverse_lazy('communications:communication_list')


# Email Composition
class ComposeEmailView(LoginRequiredMixin, FormView):
    template_name = 'communications/compose_email.html'
    form_class = ComposeEmailForm
    success_url = reverse_lazy('communications:communication_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['email_templates'] = EmailTemplate.objects.filter(
            office__in=self.request.user.offices.all()
        ) | EmailTemplate.objects.filter(is_global=True)
        context['email_signatures'] = EmailSignature.objects.filter(
            created_by=self.request.user
        ) | EmailSignature.objects.filter(is_shared=True)
        return context


@login_required
def send_email(request):
    if request.method == 'POST':
        form = ComposeEmailForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            # Process form data
            subject = form.cleaned_data['subject']
            recipient_list = form.cleaned_data['recipients'].split(',')
            template_content = form.cleaned_data['content']
            signature = form.cleaned_data.get('signature')
            
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
                to=recipient_list
            )
            email.attach_alternative(html_content, "text/html")
            
            # Attach files if any
            for file in request.FILES.getlist('attachments'):
                email.attach(file.name, file.read(), file.content_type)
            
            # Send email
            email.send()
            
            # Create communication record
            communication = Communication.objects.create(
                subject=subject,
                content=html_content,
                communication_type='email',
                created_by=request.user,
                office=form.cleaned_data.get('office'),
            )
            
            # Save attachments
            for file in request.FILES.getlist('attachments'):
                EmailAttachment.objects.create(
                    communication=communication,
                    file=file,
                    name=file.name
                )
            
            return redirect('communications:communication_detail', pk=communication.pk)
    else:
        form = ComposeEmailForm(user=request.user)
    
    return render(request, 'communications/compose_email.html', {'form': form})


@login_required
def preview_email_template(request, template_id):
    template = get_object_or_404(EmailTemplate, pk=template_id)
    
    # Check if user has access to this template
    if not (template.is_global or template.office in request.user.offices.all()):
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    return JsonResponse({
        'subject': template.subject,
        'content': template.content
    })


# Gmail Integration Views
class GmailAuthView(LoginRequiredMixin, View):
    """Initiate Gmail OAuth flow"""
    
    def get(self, request):
        gmail_service = GmailService(request.user)
        redirect_uri = request.build_absolute_uri(reverse('communications:gmail_callback'))
        
        if gmail_service.is_authenticated():
            messages.info(request, 'Gmail is already connected for your account.')
            return redirect('communications:communication_list')
        
        auth_url = gmail_service.get_authorization_url(redirect_uri)
        return redirect(auth_url)


class GmailCallbackView(LoginRequiredMixin, View):
    """Handle Gmail OAuth callback"""
    
    def get(self, request):
        code = request.GET.get('code')
        error = request.GET.get('error')
        
        if error:
            messages.error(request, f'Gmail authorization failed: {error}')
            return redirect('communications:communication_list')
        
        if not code:
            messages.error(request, 'Authorization code not received.')
            return redirect('communications:communication_list')
        
        try:
            gmail_service = GmailService(request.user)
            redirect_uri = request.build_absolute_uri(reverse('communications:gmail_callback'))
            gmail_service.handle_oauth_callback(code, redirect_uri)
            
            messages.success(request, 'Gmail successfully connected! You can now send emails through Gmail.')
            return redirect('communications:communication_list')
            
        except Exception as e:
            messages.error(request, f'Failed to connect Gmail: {str(e)}')
            return redirect('communications:communication_list')


class GmailComposeView(LoginRequiredMixin, FormView):
    """Compose and send email via Gmail"""
    template_name = 'communications/gmail_compose.html'
    form_class = ComposeEmailForm
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        gmail_service = GmailService(self.request.user)
        
        context['gmail_authenticated'] = gmail_service.is_authenticated()
        context['email_templates'] = EmailTemplate.objects.filter(is_active=True)
        context['email_signatures'] = EmailSignature.objects.filter(user=self.request.user)
        
        # Pre-populate recipient if specified
        contact_type = self.request.GET.get('contact_type')
        contact_id = self.request.GET.get('contact_id')
        
        if contact_type and contact_id:
            context['preselected_contact'] = {
                'type': contact_type,
                'id': contact_id
            }
        
        return context
    
    def form_valid(self, form):
        gmail_service = GmailService(self.request.user)
        
        if not gmail_service.is_authenticated():
            messages.error(self.request, 'Gmail is not connected. Please authorize Gmail access first.')
            return redirect('communications:gmail_auth')
        
        # Extract form data
        to_emails = [email.strip() for email in form.cleaned_data['recipients'].split(',')]
        cc_emails = [email.strip() for email in form.cleaned_data.get('cc', '').split(',') if email.strip()]
        bcc_emails = [email.strip() for email in form.cleaned_data.get('bcc', '').split(',') if email.strip()]
        subject = form.cleaned_data['subject']
        body = form.cleaned_data['body']
        is_html = form.cleaned_data.get('is_html', True)
        template_id = form.cleaned_data.get('template')
        signature_id = form.cleaned_data.get('signature')
        
        # Send email
        result = gmail_service.send_email(
            to_emails=to_emails,
            cc_emails=cc_emails if cc_emails != [''] else None,
            bcc_emails=bcc_emails if bcc_emails != [''] else None,
            subject=subject,
            body=body,
            is_html=is_html,
            template_id=template_id.id if template_id else None,
            signature_id=signature_id.id if signature_id else None,
            related_person_id=form.cleaned_data.get('related_person_id'),
            related_church_id=form.cleaned_data.get('related_church_id')
        )
        
        if result['success']:
            messages.success(
                self.request, 
                f'Email sent successfully to {", ".join(to_emails)}'
            )
            return redirect('communications:communication_list')
        else:
            messages.error(self.request, f'Failed to send email: {result["error"]}')
            return self.form_invalid(form)


class GmailSyncView(LoginRequiredMixin, View):
    """Sync Gmail messages to communications"""
    
    def post(self, request):
        gmail_service = GmailService(request.user)
        
        if not gmail_service.is_authenticated():
            return JsonResponse({
                'success': False, 
                'error': 'Gmail not authenticated'
            }, status=400)
        
        days_back = int(request.POST.get('days_back', 7))
        result = gmail_service.sync_emails_to_communications(days_back)
        
        if result['success']:
            messages.success(
                request, 
                f'Synced {result["synced_count"]} emails from the last {days_back} days.'
            )
        else:
            messages.error(request, f'Sync failed: {result["error"]}')
        
        return JsonResponse(result)


@login_required
def gmail_status(request):
    """Check Gmail authentication status"""
    gmail_service = GmailService(request.user)
    return JsonResponse({
        'authenticated': gmail_service.is_authenticated(),
        'user_email': request.user.email
    })


@login_required
def gmail_disconnect(request):
    """Disconnect Gmail for user"""
    if request.method == 'POST':
        try:
            from mobilize.authentication.models import GoogleToken
            GoogleToken.objects.filter(user=request.user).delete()
            messages.success(request, 'Gmail disconnected successfully.')
        except Exception as e:
            messages.error(request, f'Error disconnecting Gmail: {str(e)}')
    
    return redirect('communications:communication_list')


# Google Contacts Sync Views
class ContactSyncView(LoginRequiredMixin, View):
    """Sync Google contacts based on user preferences"""
    
    def post(self, request):
        contacts_service = GoogleContactsService(request.user)
        
        if not contacts_service.is_authenticated():
            return JsonResponse({
                'success': False, 
                'error': 'Google Contacts not authenticated. Please connect Gmail first.'
            }, status=400)
        
        # Perform sync based on user preferences
        result = contacts_service.sync_contacts_based_on_preference()
        
        if result['success']:
            messages.success(request, result['message'])
        else:
            messages.error(request, f'Contact sync failed: {result["error"]}')
        
        return JsonResponse(result)


@login_required
def contact_sync_status(request):
    """Get contact sync status for user"""
    try:
        from mobilize.authentication.models import UserContactSyncSettings
        
        sync_settings = UserContactSyncSettings.objects.filter(user=request.user).first()
        contacts_service = GoogleContactsService(request.user)
        
        status = {
            'authenticated': contacts_service.is_authenticated(),
            'sync_preference': sync_settings.sync_preference if sync_settings else 'crm_only',
            'auto_sync_enabled': sync_settings.auto_sync_enabled if sync_settings else False,
            'last_sync_at': sync_settings.last_sync_at.isoformat() if sync_settings and sync_settings.last_sync_at else None,
            'has_errors': bool(sync_settings.sync_errors) if sync_settings else False,
            'should_sync_now': sync_settings.should_sync_now() if sync_settings else False,
        }
        
        return JsonResponse(status)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


class ContactSyncSettingsView(LoginRequiredMixin, View):
    """Handle contact sync settings updates"""
    
    def post(self, request):
        try:
            from mobilize.authentication.models import UserContactSyncSettings
            
            sync_preference = request.POST.get('sync_preference')
            auto_sync_enabled = request.POST.get('auto_sync_enabled') == 'true'
            sync_frequency_hours = int(request.POST.get('sync_frequency_hours', 24))
            
            # Validate sync preference
            valid_preferences = [choice[0] for choice in UserContactSyncSettings.SYNC_CHOICES]
            if sync_preference not in valid_preferences:
                return JsonResponse({'success': False, 'error': 'Invalid sync preference'}, status=400)
            
            # Get or create settings
            settings, created = UserContactSyncSettings.objects.get_or_create(
                user=request.user,
                defaults={
                    'sync_preference': sync_preference,
                    'auto_sync_enabled': auto_sync_enabled,
                    'sync_frequency_hours': sync_frequency_hours,
                }
            )
            
            if not created:
                settings.sync_preference = sync_preference
                settings.auto_sync_enabled = auto_sync_enabled
                settings.sync_frequency_hours = sync_frequency_hours
                settings.save()
            
            message = f'Contact sync settings updated: {settings.get_sync_preference_display()}'
            messages.success(request, message)
            
            return JsonResponse({
                'success': True,
                'message': message,
                'settings': {
                    'sync_preference': settings.sync_preference,
                    'auto_sync_enabled': settings.auto_sync_enabled,
                    'sync_frequency_hours': settings.sync_frequency_hours,
                }
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
