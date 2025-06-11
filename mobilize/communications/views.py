from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, FormView
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.core.mail import EmailMultiAlternatives
from django.utils.html import strip_tags
from django.conf import settings

from .models import EmailTemplate, EmailSignature, Communication, EmailAttachment
from .forms import EmailTemplateForm, EmailSignatureForm, CommunicationForm, ComposeEmailForm


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
