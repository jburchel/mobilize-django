from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.core.paginator import Paginator
from django.db.models import Q
import csv
from datetime import datetime

from .models import Church
from .forms import ChurchForm, ImportChurchesForm

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
    
    # Pagination
    paginator = Paginator(churches, 25)  # Show 25 churches per page
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
    
    return render(request, 'churches/church_list.html', context)


@login_required
def church_detail(request, pk):
    """
    Display detailed information about a church.
    """
    church = get_object_or_404(Church, pk=pk)
    # Remove references to non-existent related models
    # contacts = church.contacts.all()
    # interactions = church.interactions.all()[:5]  # Get the 5 most recent interactions
    
    context = {
        'church': church,
        # 'contacts': contacts,
        # 'interactions': interactions,
    }
    
    return render(request, 'churches/church_detail_simple.html', context)


@login_required
def church_create(request):
    """
    Create a new church.
    """
    if request.method == 'POST':
        form = ChurchForm(request.POST)
        if form.is_valid():
            church = form.save(commit=False)
            church.created_by = request.user
            church.save()
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
