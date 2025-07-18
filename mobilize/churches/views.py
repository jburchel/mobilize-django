from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q
from django.db import models
import csv
from datetime import datetime

from .models import Church, ChurchMembership
from .forms import ChurchForm, ImportChurchesForm
from mobilize.pipeline.models import MAIN_CHURCH_PIPELINE_STAGES

# ChurchContact and ChurchInteraction models have been removed as they don't exist in Supabase


@login_required
def church_list(request):
    """
    Display a list of churches with filtering and pagination.
    """
    # Get query parameters for filtering
    query = request.GET.get('q', '')
    pipeline_stage = request.GET.get('pipeline_stage', '')
    priority = request.GET.get('priority', '')
    
    # Start with all churches - use select_related to optimize queries
    churches = Church.objects.select_related('contact').all()
    
    # Apply filters if provided
    if query:
        churches = churches.filter(
            Q(name__icontains=query) | 
            Q(contact__church_name__icontains=query) |
            Q(location__icontains=query) | 
            Q(denomination__icontains=query) |
            Q(contact__email__icontains=query) |
            Q(contact__phone__icontains=query)
        )
    
    if pipeline_stage:
        # Filter by pipeline stage through the pipeline system
        from mobilize.pipeline.models import PipelineContact, PipelineStage
        try:
            # Get church contacts that have the specified pipeline stage
            stage_objects = PipelineStage.objects.filter(name__iexact=pipeline_stage.title())
            if stage_objects.exists():
                pipeline_contacts = PipelineContact.objects.filter(
                    current_stage__in=stage_objects,
                    contact_type='church'
                ).values_list('contact_id', flat=True)
                churches = churches.filter(contact_id__in=pipeline_contacts)
            else:
                # If no matching stage found, also check church_pipeline field
                churches = churches.filter(church_pipeline=pipeline_stage)
        except Exception:
            # Fallback to church_pipeline field
            churches = churches.filter(church_pipeline=pipeline_stage)
    
    if priority:
        churches = churches.filter(contact__priority=priority)
    
    # Pagination
    paginator = Paginator(churches, 25)  # Show 25 churches per page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Get pipeline stages and priorities for filter dropdowns
    pipeline_stages = MAIN_CHURCH_PIPELINE_STAGES
    
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
    
    return render(request, 'churches/church_list.html', context)


@login_required
def church_detail(request, pk):
    """
    Display detailed information about a church.
    """
    church = get_object_or_404(Church, pk=pk)
    
    # Get church memberships with related person data
    memberships = church.memberships.filter(status='active').select_related(
        'person__contact'
    ).order_by('-is_primary_contact', 'role', 'person__contact__last_name')
    
    # Get recent communications for this church
    try:
        from mobilize.communications.models import Communication
        recent_communications = Communication.objects.filter(
            models.Q(church=church) | models.Q(person__church_memberships__church=church)
        ).distinct().order_by('-created_at')[:5]
    except ImportError:
        recent_communications = []
    
    context = {
        'church': church,
        'memberships': memberships,
        'recent_communications': recent_communications,
    }
    
    return render(request, 'churches/church_detail.html', context)


@login_required
def church_create(request):
    """
    Create a new church.
    """
    if request.method == 'POST':
        form = ChurchForm(request.POST)
        if form.is_valid():
            # Get the user's first office assignment (or could be from form data)
            user_office = request.user.useroffice_set.first()
            office = user_office.office if user_office else None
            
            church = form.save(user=request.user, office=office)
            messages.success(request, f"Successfully created {church.name}")
            return redirect('churches:church_detail', pk=church.pk)
    else:
        form = ChurchForm()
    
    return render(request, 'churches/church_form.html', {
        'form': form,
        'title': 'Create Church',
    })


@login_required
def church_edit(request, pk):
    """
    Edit an existing church.
    """
    church = get_object_or_404(Church, pk=pk)
    
    if request.method == 'POST':
        form = ChurchForm(request.POST, instance=church)
        if form.is_valid():
            form.save()
            messages.success(request, f"Successfully updated {church.name}")
            return redirect('churches:church_detail', pk=church.pk)
    else:
        form = ChurchForm(instance=church)
    
    return render(request, 'churches/church_form.html', {
        'form': form,
        'church': church,
        'title': f'Edit {church.name}',
    })


@login_required
def church_delete(request, pk):
    """
    Delete a church.
    """
    church = get_object_or_404(Church, pk=pk)
    
    if request.method == 'POST':
        name = church.name
        church.delete()
        messages.success(request, f"Successfully deleted {name}")
        return redirect('churches:church_list')
    
    return render(request, 'churches/church_confirm_delete.html', {
        'church': church,
    })


@login_required
def church_contacts(request, pk):
    """
    Display a list of contacts for a church.
    """
    church = get_object_or_404(Church, pk=pk)
    
    context = {
        'church': church,
    }
    
    return render(request, 'churches/church_contacts_simple.html', context)


@login_required
def import_churches(request):
    """
    Import churches from CSV file.
    """
    if request.method == 'POST':
        form = ImportChurchesForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = request.FILES['csv_file']
            
            # Check if file is CSV
            if not csv_file.name.endswith('.csv'):
                messages.error(request, 'Please upload a CSV file')
                return redirect('churches:import_churches')
            
            # Check if file is empty
            if csv_file.size == 0:
                form.add_error('csv_file', 'The uploaded file is empty')
                return render(request, 'churches/import_churches.html', {'form': form})
            
            # Process CSV file
            try:
                decoded_file = csv_file.read().decode('utf-8').splitlines()
                if not decoded_file:
                    form.add_error('csv_file', 'The CSV file appears to be empty')
                    return render(request, 'churches/import_churches.html', {'form': form})
                    
                reader = csv.DictReader(decoded_file)
                
                # Check for required columns
                if 'name' not in reader.fieldnames:
                    form.add_error('csv_file', 'Required column "name" not found in CSV file')
                    return render(request, 'churches/import_churches.html', {'form': form})
                
                # Track import results
                created_count = 0
                updated_count = 0
                error_count = 0
                
                for row in reader:
                    try:
                        # Check if church exists by name and location
                        name = row.get('name', '').strip()
                        location = row.get('location', '').strip()
                        
                        if name:  # Only name is required
                            church, created = Church.objects.update_or_create(
                                name=name,
                                defaults={
                                    'location': location,
                                    'denomination': row.get('denomination', '').strip(),
                                    'website': row.get('website', '').strip(),
                                    'congregation_size': int(row.get('congregation_size', 0)) if row.get('congregation_size', '').strip() else None,
                                    'weekly_attendance': int(row.get('weekly_attendance', 0)) if row.get('weekly_attendance', '').strip() else None,
                                    'church_pipeline': row.get('church_pipeline', '').strip(),
                                    'priority': row.get('priority', '').strip(),
                                    'office_id': request.POST.get('office_id') or 1,  # Use office_id from form
                                }
                            )
                            
                            if created:
                                created_count += 1
                            else:
                                updated_count += 1
                        else:
                            # Missing required fields
                            error_count += 1
                    except Exception as e:
                        error_count += 1
                        print(f"Error importing row: {e}")
                
                messages.success(
                    request, 
                    f"Import complete: {created_count} created, {updated_count} updated, {error_count} errors"
                )
                return redirect('churches:church_list')
                
            except Exception as e:
                form.add_error('csv_file', f"Error processing CSV: {str(e)}")
                return render(request, 'churches/import_churches.html', {'form': form})
    else:
        form = ImportChurchesForm()
    
    return render(request, 'churches/import_churches.html', {'form': form})


@login_required
def export_churches(request):
    """
    Export churches to CSV file.
    """
    # Get query parameters for filtering
    query = request.GET.get('q', '')
    pipeline_stage = request.GET.get('pipeline_stage', '')
    priority = request.GET.get('priority', '')
    
    # Start with all churches
    churches = Church.objects.all()
    
    # Apply filters if provided
    if query:
        churches = churches.filter(
            Q(name__icontains=query) | 
            Q(location__icontains=query) | 
            Q(denomination__icontains=query)
        )
    
    if pipeline_stage:
        churches = churches.filter(church_pipeline=pipeline_stage)
    
    if priority:
        churches = churches.filter(priority=priority)
    
    # Create the HttpResponse object with CSV header
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="churches_export_{timestamp}.csv"'
    
    # Create CSV writer
    writer = csv.writer(response)
    
    # Write header row
    writer.writerow([
        'Name', 'Denomination', 'Website', 'Email', 'Phone', 
        'Address', 'Location', 'Congregation Size', 'Weekly Attendance', 'Year Founded',
        'Pipeline Stage', 'Priority', 'Notes', 'Created At'
    ])
    
    # Write data rows
    for church in churches:
        writer.writerow([
            church.name or '',
            church.denomination or '',
            church.website or '',
            church.pastor_email or '',  # Use pastor_email instead of email
            church.pastor_phone or '',  # Use pastor_phone instead of phone
            getattr(church, 'address', '') or '',
            church.location or '',
            str(church.congregation_size) if church.congregation_size is not None else '',
            str(church.weekly_attendance) if church.weekly_attendance is not None else '',
            str(church.year_founded) if church.year_founded is not None else '',
            church.church_pipeline or '',
            church.priority or '',  # Use priority directly since get_priority_display() doesn't exist
            getattr(church, 'notes', '') or '',
            getattr(church, 'created_at', '').strftime('%Y-%m-%d %H:%M:%S') if getattr(church, 'created_at', None) else ''
        ])
    
    return response


@login_required
def add_church_member(request, pk):
    """
    Add a person to a church with a specific role.
    """
    church = get_object_or_404(Church, pk=pk)
    
    if request.method == 'POST':
        person_id = request.POST.get('person')
        role = request.POST.get('role', 'member')
        is_primary_contact = request.POST.get('is_primary_contact') == 'on'
        notes = request.POST.get('notes', '')
        
        if person_id:
            from mobilize.contacts.models import Person
            try:
                person = Person.objects.get(pk=person_id)
                
                # Check if membership already exists
                existing_membership = ChurchMembership.objects.filter(
                    church=church, person=person
                ).first()
                
                if existing_membership:
                    messages.warning(request, f"{person.name} is already associated with this church.")
                else:
                    # Create new membership
                    membership = ChurchMembership.objects.create(
                        church=church,
                        person=person,
                        role=role,
                        is_primary_contact=is_primary_contact,
                        notes=notes,
                        status='active'
                    )
                    
                    messages.success(request, f"Successfully added {person.name} to {church.name} as {membership.get_role_display()}.")
                    
            except Person.DoesNotExist:
                messages.error(request, "Selected person not found.")
        else:
            messages.error(request, "Please select a person.")
    
    return redirect('churches:church_detail', pk=church.pk)


@login_required
def edit_church_member(request, membership_id):
    """
    Edit a church membership.
    """
    membership = get_object_or_404(ChurchMembership, pk=membership_id)
    
    if request.method == 'POST':
        role = request.POST.get('role', membership.role)
        is_primary_contact = request.POST.get('is_primary_contact') == 'on'
        notes = request.POST.get('notes', '')
        status = request.POST.get('status', membership.status)
        
        membership.role = role
        membership.is_primary_contact = is_primary_contact
        membership.notes = notes
        membership.status = status
        membership.save()
        
        messages.success(request, f"Updated {membership.person.name}'s role in {membership.church.name}.")
        
        return redirect('churches:church_detail', pk=membership.church.pk)
    
    # Return edit form (TODO: implement template)
    return JsonResponse({'error': 'Method not allowed'}, status=405)


@login_required
def set_primary_contact(request, membership_id):
    """
    Set a church member as the primary contact.
    """
    membership = get_object_or_404(ChurchMembership, pk=membership_id)
    
    if request.method == 'POST':
        membership.is_primary_contact = True
        membership.save()  # The model's save method will handle setting others to False
        
        messages.success(request, f"Set {membership.person.name} as primary contact for {membership.church.name}.")
    
    return redirect('churches:church_detail', pk=membership.church.pk)


@login_required
def remove_church_member(request, membership_id):
    """
    Remove a person from a church (delete the membership).
    """
    membership = get_object_or_404(ChurchMembership, pk=membership_id)
    church = membership.church
    person_name = membership.person.name
    
    if request.method == 'POST':
        membership.delete()
        messages.success(request, f"Removed {person_name} from {church.name}.")
    
    return redirect('churches:church_detail', pk=church.pk)
