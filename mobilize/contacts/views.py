from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.core.paginator import Paginator
from django.db.models import Q
import csv
from datetime import datetime

from .models import Person
from .forms import PersonForm, ImportContactsForm


@login_required
def person_list(request):
    """
    Display a list of people with filtering and pagination.
    """
    # Get query parameters for filtering
    query = request.GET.get('q', '')
    pipeline_stage = request.GET.get('pipeline_stage', '')
    priority = request.GET.get('priority', '')
    
    # Start with all people - use select_related to optimize queries
    people = Person.objects.select_related('contact').all()
    
    # Apply filters if provided
    if query:
        people = people.filter(
            Q(contact__first_name__icontains=query) | 
            Q(contact__last_name__icontains=query) | 
            Q(contact__email__icontains=query) | 
            Q(contact__phone__icontains=query)
        )
    
    if pipeline_stage:
        people = people.filter(contact__pipeline_stage=pipeline_stage)
    
    if priority:
        people = people.filter(contact__priority=priority)
    
    # Pagination
    paginator = Paginator(people, 25)  # Show 25 people per page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Get pipeline stages and priorities for filter dropdowns
    pipeline_stages = [
        ('new', 'New Contact'),
        ('contacted', 'Contacted'),
        ('meeting_scheduled', 'Meeting Scheduled'),
        ('proposal', 'Proposal'),
        ('committed', 'Committed'),
        ('partnership', 'Partnership'),
        ('inactive', 'Inactive'),
    ]
    
    priorities = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]
    
    context = {
        'page_obj': page_obj,
        'query': query,
        'pipeline_stage': pipeline_stage,
        'priority': priority,
        'pipeline_stages': pipeline_stages,
        'priorities': priorities,
    }
    
    return render(request, 'contacts/person_list.html', context)


@login_required
def person_detail(request, pk):
    """
    Display detailed information about a person.
    """
    person = get_object_or_404(Person, pk=pk)
    interactions = person.interactions.all()[:5]  # Get the 5 most recent interactions
    
    context = {
        'person': person,
        'interactions': interactions,
    }
    
    return render(request, 'contacts/person_detail.html', context)


@login_required
def person_create(request):
    """
    Create a new person.
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
def person_edit(request, pk):
    """
    Edit an existing person.
    """
    person = get_object_or_404(Person, pk=pk)
    
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
def person_delete(request, pk):
    """
    Delete a person.
    """
    person = get_object_or_404(Person, pk=pk)
    
    if request.method == 'POST':
        name = person.name
        person.delete()
        messages.success(request, f"Successfully deleted {name}")
        return redirect('contacts:person_list')
    
    return render(request, 'contacts/person_confirm_delete.html', {
        'person': person,
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
                messages.error(request, f"Error processing CSV: {str(e)}")
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
    pipeline_stage = request.GET.get('pipeline_stage', '')
    priority = request.GET.get('priority', '')
    
    # Start with all people - use select_related to optimize queries
    people = Person.objects.select_related('contact').all()
    
    # Apply filters if provided
    if query:
        people = people.filter(
            Q(contact__first_name__icontains=query) | 
            Q(contact__last_name__icontains=query) | 
            Q(contact__email__icontains=query) | 
            Q(contact__phone__icontains=query)
        )
    
    if pipeline_stage:
        people = people.filter(contact__pipeline_stage=pipeline_stage)
    
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
        'Pipeline Stage', 'Priority', 'Status', 'Notes', 
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
            person.contact.pipeline_stage or '',
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
