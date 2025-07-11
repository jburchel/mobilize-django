from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q
from django.views.decorators.http import require_POST
from django.urls import reverse
import csv
from datetime import datetime

from .models import Person, Contact
from .forms import PersonForm, ImportContactsForm
from mobilize.authentication.decorators import (
    office_data_filter,
    office_object_permission_required,
    can_create_edit_delete,
    ensure_user_office_assignment
)


@login_required
@ensure_user_office_assignment
def person_list(request):
    """
    Display a list of people with filtering and pagination.
    Uses lazy loading for better performance.
    Only shows contacts from user's assigned offices.
    """
    # Get query parameters for filtering
    query = request.GET.get('q', '')
    priority = request.GET.get('priority', '')
    pipeline_stage = request.GET.get('pipeline_stage', '')
    
    # Check if lazy loading is disabled (for backwards compatibility)
    use_lazy_loading = request.GET.get('lazy', 'true').lower() == 'true'
    
    # Get pipeline stages for the dropdown
    from mobilize.pipeline.models import MAIN_PEOPLE_PIPELINE_STAGES
    
    if use_lazy_loading:
        # Use lazy loading template
        context = {
            'query': query,
            'priority': priority,
            'pipeline_stage': pipeline_stage,
            'priorities': Contact.PRIORITY_CHOICES,
            'pipeline_stages': MAIN_PEOPLE_PIPELINE_STAGES,
        }
        return render(request, 'contacts/person_list_lazy.html', context)
    else:
        # Fallback to traditional pagination
        # Start with all people - use select_related to optimize queries
        people = Person.objects.select_related('contact', 'contact__office').all()
        
        # Apply office-level filtering
        people = office_data_filter(people, request.user, 'contact__office')
        
        # Apply filters if provided
        if query:
            people = people.filter(
                Q(contact__first_name__icontains=query) | 
                Q(contact__last_name__icontains=query) | 
                Q(contact__email__icontains=query) | 
                Q(contact__phone__icontains=query)
            )
        
        if priority:
            people = people.filter(contact__priority=priority)
        
        if pipeline_stage:
            # Filter by pipeline stage
            from mobilize.pipeline.models import PipelineContact, Pipeline
            main_pipeline = Pipeline.get_main_people_pipeline()
            if main_pipeline:
                # Get all contacts in the specified stage
                pipeline_contacts = PipelineContact.objects.filter(
                    pipeline=main_pipeline,
                    current_stage__name__iexact=pipeline_stage.replace('_', ' ').title()
                ).values_list('contact_id', flat=True)
                people = people.filter(contact__id__in=pipeline_contacts)
        
        # Get items per page from request
        per_page = int(request.GET.get('per_page', 25))
        
        # Pagination
        paginator = Paginator(people, per_page)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)
        
        # Get priorities for filter dropdowns
        priorities = Contact.PRIORITY_CHOICES
        
        context = {
            'page_obj': page_obj,
            'query': query,
            'priority': priority,
            'pipeline_stage': pipeline_stage,
            'priorities': priorities,
            'pipeline_stages': MAIN_PEOPLE_PIPELINE_STAGES,
            'per_page': per_page,
        }
        
        return render(request, 'contacts/person_list.html', context)


@login_required
@office_object_permission_required(Person, 'contact__office')
def person_detail(request, pk):
    """
    Display detailed information about a person.
    Only accessible if user has office permission.
    """
    # Get the person (office filtering is handled by decorator)
    person = get_object_or_404(Person.objects.select_related('contact', 'contact__office'), pk=pk)
    # Get recent communications for this person
    from mobilize.communications.models import Communication
    recent_communications = Communication.objects.filter(
        person=person
    ).order_by('-date_sent', '-created_at')[:5]
    
    # Get related tasks for this person
    related_tasks = person.person_tasks.all().order_by('-due_date', '-created_at')[:10]
    
    context = {
        'person': person,
        'recent_communications': recent_communications,
        'related_tasks': related_tasks,
    }
    
    return render(request, 'contacts/person_detail.html', context)


@login_required
@can_create_edit_delete
@ensure_user_office_assignment
def person_create(request):
    """
    Create a new person.
    Only accessible for users with create permissions.
    """
    if request.method == 'POST':
        form = PersonForm(request.POST)
        if form.is_valid():
            person = form.save()
            messages.success(request, f"Successfully created {person.name}")
            return redirect('contacts:person_detail', pk=person.pk)
    else:
        form = PersonForm()
    
    return render(request, 'contacts/person_form.html', {
        'form': form,
        'title': 'Create Person',
    })


@login_required
@can_create_edit_delete
@office_object_permission_required(Person, 'contact__office')
def person_edit(request, pk):
    """
    Edit an existing person.
    Only accessible for users with edit permissions and office access.
    """
    # Get the person (office filtering is handled by decorator)
    person = get_object_or_404(Person.objects.select_related('contact', 'contact__office'), pk=pk)
    
    if request.method == 'POST':
        form = PersonForm(request.POST, instance=person)
        if form.is_valid():
            form.save()
            messages.success(request, f"Successfully updated {person.name}")
            return redirect('contacts:person_detail', pk=person.pk)
    else:
        form = PersonForm(instance=person)
    
    return render(request, 'contacts/person_form.html', {
        'form': form,
        'person': person,
        'title': f'Edit {person.name}',
    })


@login_required
@can_create_edit_delete
@office_object_permission_required(Person, 'contact__office')
def person_delete(request, pk):
    """
    Delete a person.
    Only accessible for users with delete permissions and office access.
    """
    # Get the person (office filtering is handled by decorator)
    person = get_object_or_404(Person.objects.select_related('contact', 'contact__office'), pk=pk)
    
    if request.method == 'POST':
        name = person.name
        person.delete()
        messages.success(request, f"Successfully deleted {name}")
        return redirect('contacts:person_list')
    
    return render(request, 'contacts/person_confirm_delete.html', {
        'person': person,
    })


@login_required
def person_list_api(request):
    """
    JSON API endpoint for lazy loading person list data.
    """
    # Get query parameters
    query = request.GET.get('q', '')
    priority = request.GET.get('priority', '')
    pipeline_stage = request.GET.get('pipeline_stage', '')
    page = int(request.GET.get('page', 1))
    per_page = int(request.GET.get('per_page', 25))
    
    # Build queryset with optimizations
    people = Person.objects.select_related(
        'contact', 
        'contact__office',
        'primary_church'
    ).prefetch_related(
        'contact__pipeline_entries__current_stage'
    )
    
    # Apply filters
    if query:
        people = people.filter(
            Q(contact__first_name__icontains=query) | 
            Q(contact__last_name__icontains=query) | 
            Q(contact__email__icontains=query) | 
            Q(contact__phone__icontains=query)
        )
    
    if priority:
        people = people.filter(contact__priority=priority)
    
    if pipeline_stage:
        # Filter by pipeline stage
        from mobilize.pipeline.models import PipelineContact, Pipeline
        main_pipeline = Pipeline.get_main_people_pipeline()
        if main_pipeline:
            # Get all contacts in the specified stage
            pipeline_contacts = PipelineContact.objects.filter(
                pipeline=main_pipeline,
                current_stage__name__iexact=pipeline_stage.replace('_', ' ').title()
            ).values_list('contact_id', flat=True)
            people = people.filter(contact__id__in=pipeline_contacts)
    
    # Order by most recently updated
    people = people.order_by('-contact__updated_at')
    
    # Paginate
    paginator = Paginator(people, per_page)
    page_obj = paginator.get_page(page)
    
    # Build JSON response
    results = []
    for person in page_obj:
        results.append({
            'id': person.contact.id,
            'name': f"{person.contact.first_name} {person.contact.last_name}",
            'email': person.contact.email,
            'phone': person.contact.phone,
            'priority': person.contact.priority,
            'priority_display': person.contact.get_priority_display(),
            'pipeline_stage': person.contact.get_pipeline_stage_code(),
            'detail_url': reverse('contacts:person_detail', args=[person.pk]),
            'edit_url': reverse('contacts:person_edit', args=[person.pk]),
            'delete_url': reverse('contacts:person_delete', args=[person.pk]),
        })
    
    return JsonResponse({
        'results': results,
        'page': page,
        'per_page': per_page,
        'total': paginator.count,
        'has_next': page_obj.has_next(),
        'has_previous': page_obj.has_previous(),
    })


# interaction_list view has been removed as the ContactInteraction model no longer exists


# Interaction-related functions have been removed as the ContactInteraction model no longer exists


@login_required
def import_contacts(request):
    """
    Import contacts from CSV file.
    """
    if request.method == 'POST':
        form = ImportContactsForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = request.FILES['csv_file']
            
            # Check if file is CSV
            if not csv_file.name.endswith('.csv'):
                messages.error(request, 'Please upload a CSV file')
                return redirect('contacts:import_contacts')
            
            # Process CSV file
            try:
                decoded_file = csv_file.read().decode('utf-8').splitlines()
                reader = csv.DictReader(decoded_file)
                
                # Track import results
                created_count = 0
                updated_count = 0
                error_count = 0
                
                for row in reader:
                    try:
                        # Check if contact exists by email
                        email = row.get('email', '').strip()
                        
                        # First, handle the Contact creation/update
                        if email:
                            # Check if a contact with this email already exists
                            from .models import Contact
                            try:
                                contact = Contact.objects.get(email=email)
                                created = False
                                # Update contact fields
                                contact.first_name = row.get('first_name', '').strip()
                                contact.last_name = row.get('last_name', '').strip()
                                contact.phone = row.get('phone', '').strip()
                                contact.street_address = row.get('street_address', row.get('address_line1', '')).strip()
                                contact.city = row.get('city', '').strip()
                                contact.state = row.get('state', '').strip()
                                contact.zip_code = row.get('zip_code', row.get('postal_code', '')).strip()
                                contact.country = row.get('country', 'United States').strip()
                                contact.pipeline_stage = row.get('pipeline_stage', 'new').strip()
                                contact.priority = row.get('priority', 'medium').strip()
                                contact.notes = row.get('notes', '').strip()
                                contact.user = request.user
                                contact.save()
                            except Contact.DoesNotExist:
                                # Create new contact
                                contact = Contact.objects.create(
                                    type='person',
                                    email=email,
                                    first_name=row.get('first_name', '').strip(),
                                    last_name=row.get('last_name', '').strip(),
                                    phone=row.get('phone', '').strip(),
                                    street_address=row.get('street_address', row.get('address_line1', '')).strip(),
                                    city=row.get('city', '').strip(),
                                    state=row.get('state', '').strip(),
                                    zip_code=row.get('zip_code', row.get('postal_code', '')).strip(),
                                    country=row.get('country', 'United States').strip(),
                                    pipeline_stage=row.get('pipeline_stage', 'new').strip(),
                                    priority=row.get('priority', 'medium').strip(),
                                    notes=row.get('notes', '').strip(),
                                    user=request.user,
                                )
                                created = True
                        else:
                            # No email, create new contact
                            contact = Contact.objects.create(
                                type='person',
                                first_name=row.get('first_name', '').strip(),
                                last_name=row.get('last_name', '').strip(),
                                phone=row.get('phone', '').strip(),
                                street_address=row.get('street_address', row.get('address_line1', '')).strip(),
                                city=row.get('city', '').strip(),
                                state=row.get('state', '').strip(),
                                zip_code=row.get('zip_code', row.get('postal_code', '')).strip(),
                                country=row.get('country', 'United States').strip(),
                                pipeline_stage=row.get('pipeline_stage', 'new').strip(),
                                priority=row.get('priority', 'medium').strip(),
                                notes=row.get('notes', '').strip(),
                                user=request.user,
                            )
                            created = True
                        
                        # Now create or update the Person record
                        person, person_created = Person.objects.get_or_create(
                            contact=contact,
                            defaults={
                                # Add any person-specific fields from CSV if available
                                'title': row.get('title', '').strip(),
                                'profession': row.get('profession', row.get('occupation', '')).strip(),
                                'organization': row.get('organization', row.get('employer', '')).strip(),
                            }
                        )
                        
                        if created or person_created:
                            created_count += 1
                        else:
                            updated_count += 1
                            
                    except Exception as e:
                        error_count += 1
                        print(f"Error importing row: {e}")
                
                messages.success(
                    request, 
                    f"Import complete: {created_count} created, {updated_count} updated, {error_count} errors"
                )
                return redirect('contacts:person_list')
            
            except Exception as e:
                messages.error(request, f"Error processing CSV file: {str(e)}")
                return redirect('contacts:import_contacts')
    else:
        form = ImportContactsForm()
    
    return render(request, 'contacts/import_contacts.html', {'form': form})


@login_required
def export_contacts(request):
    """
    Export contacts to CSV file.
    """
    # Get query parameters for filtering
    query = request.GET.get('q', '')
    priority = request.GET.get('priority', '')
    
    # Start with all people - use select_related to optimize queries
    people = Person.objects.select_related('contact', 'contact__office').all()
    
    # Apply filters if provided
    if query:
        people = people.filter(
            Q(contact__first_name__icontains=query) | 
            Q(contact__last_name__icontains=query) | 
            Q(contact__email__icontains=query) | 
            Q(contact__phone__icontains=query)
        )
    
    if priority:
        people = people.filter(contact__priority=priority)
    
    # Create the HttpResponse object with CSV header
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="contacts_export_{timestamp}.csv"'
    
    # Create CSV writer
    writer = csv.writer(response)
    
    # Write header row
    writer.writerow([
        'First Name', 'Last Name', 'Email', 'Phone', 
        'Street Address', 'City', 'State', 'Zip Code', 'Country',
        'Priority', 'Status', 'Notes', 
        'Title', 'Profession', 'Organization',
        'Created At', 'Last Updated'
    ])
    
    # Write data rows
    for person in people:
        writer.writerow([
            person.contact.first_name or '',
            person.contact.last_name or '',
            person.contact.email or '',
            person.contact.phone or '',
            person.contact.street_address or '',
            person.contact.city or '',
            person.contact.state or '',
            person.contact.zip_code or '',
            person.contact.country or '',
            person.contact.priority or '',
            person.contact.status or '',
            person.contact.notes or '',
            person.title or '',
            person.profession or '',
            person.organization or '',
            person.contact.created_at.strftime('%Y-%m-%d %H:%M:%S') if person.contact.created_at else '',
            person.contact.updated_at.strftime('%Y-%m-%d %H:%M:%S') if person.contact.updated_at else ''
        ])
    
    return response


@login_required
def google_sync(request):
    """
    Synchronize contacts with Google Contacts API.
    
    This is a placeholder for the Google Contacts API integration.
    """
    if request.method == 'POST':
        # This would be implemented with the Google Contacts API
        messages.info(request, "Google Contacts sync is not yet implemented")
    
    return render(request, 'contacts/google_sync.html')


@login_required
@require_POST
def bulk_delete(request):
    """
    Delete multiple contacts at once.
    """
    contact_ids = request.POST.getlist('contact_ids')
    
    if not contact_ids:
        messages.error(request, "No contacts selected for deletion")
        return redirect('contacts:person_list')
    
    try:
        # Get the contacts to delete
        contacts = Contact.objects.filter(id__in=contact_ids, type='person')
        count = contacts.count()
        
        if count == 0:
            messages.error(request, "No valid contacts found to delete")
            return redirect('contacts:person_list')
        
        # Delete the contacts (this will cascade to delete Person records)
        contacts.delete()
        
        messages.success(request, f"Successfully deleted {count} contact(s)")
        
    except Exception as e:
        messages.error(request, f"Error deleting contacts: {str(e)}")
    
    return redirect('contacts:person_list')


@login_required
@require_POST
def bulk_update_priority(request):
    """
    Update priority for multiple contacts at once.
    """
    contact_ids = request.POST.getlist('contact_ids')
    new_priority = request.POST.get('priority')
    
    if not contact_ids:
        messages.error(request, "No contacts selected for update")
        return redirect('contacts:person_list')
    
    if not new_priority:
        messages.error(request, "Please select a priority")
        return redirect('contacts:person_list')
    
    try:
        # Get the contacts to update
        contacts = Contact.objects.filter(id__in=contact_ids, type='person')
        count = contacts.count()
        
        if count == 0:
            messages.error(request, "No valid contacts found to update")
            return redirect('contacts:person_list')
        
        # Update the priority
        contacts.update(priority=new_priority)
        
        priority_display = dict([
            ('low', 'Low'),
            ('medium', 'Medium'),
            ('high', 'High'),
        ]).get(new_priority, new_priority)
        
        messages.success(request, f"Successfully updated {count} contact(s) to {priority_display} priority")
        
    except Exception as e:
        messages.error(request, f"Error updating contacts: {str(e)}")
    
    return redirect('contacts:person_list')


@login_required
@require_POST
def bulk_assign_office(request):
    """
    Assign multiple contacts to an office at once.
    """
    contact_ids = request.POST.getlist('contact_ids')
    office_id = request.POST.get('office_id')
    
    if not contact_ids:
        messages.error(request, "No contacts selected for assignment")
        return redirect('contacts:person_list')
    
    if not office_id:
        messages.error(request, "Please select an office")
        return redirect('contacts:person_list')
    
    try:
        from mobilize.admin_panel.models import Office
        office = get_object_or_404(Office, id=office_id)
        
        # Get the contacts to update
        contacts = Contact.objects.filter(id__in=contact_ids, type='person')
        count = contacts.count()
        
        if count == 0:
            messages.error(request, "No valid contacts found to assign")
            return redirect('contacts:person_list')
        
        # Update the office assignment
        contacts.update(office=office)
        
        messages.success(request, f"Successfully assigned {count} contact(s) to {office.name}")
        
    except Exception as e:
        messages.error(request, f"Error assigning contacts: {str(e)}")
    
    return redirect('contacts:person_list')