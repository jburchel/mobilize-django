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
            Q(city__icontains=query) | 
            Q(state__icontains=query) | 
            Q(denomination__icontains=query)
        )
    
    if pipeline_stage:
        churches = churches.filter(pipeline_stage=pipeline_stage)
    
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
    contacts = church.contacts.all()
    interactions = church.interactions.all()[:5]  # Get the 5 most recent interactions
    
    context = {
        'church': church,
        'contacts': contacts,
        'interactions': interactions,
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
    
    return render(request, 'churches/church_contacts.html', context)


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
                        # Check if church exists by name and city/state
                        name = row.get('name', '').strip()
                        city = row.get('city', '').strip()
                        state = row.get('state', '').strip()
                        
                        if name and (city or state):
                            church, created = Church.objects.update_or_create(
                                name=name,
                                city=city,
                                state=state,
                                defaults={
                                    'denomination': row.get('denomination', '').strip(),
                                    'website': row.get('website', '').strip(),
                                    'email': row.get('email', '').strip(),
                                    'phone': row.get('phone', '').strip(),
                                    'address_line1': row.get('address_line1', '').strip(),
                                    'address_line2': row.get('address_line2', '').strip(),
                                    'postal_code': row.get('postal_code', '').strip(),
                                    'country': row.get('country', 'United States').strip(),
                                    'size': row.get('size', '').strip(),
                                    'pipeline_stage': row.get('pipeline_stage', 'new').strip(),
                                    'priority': row.get('priority', 'medium').strip(),
                                    'notes': row.get('notes', '').strip(),
                                    'created_by': request.user,
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
                messages.error(request, f"Error processing CSV: {str(e)}")
                return redirect('churches:import_churches')
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
            Q(city__icontains=query) | 
            Q(state__icontains=query) | 
            Q(denomination__icontains=query)
        )
    
    if pipeline_stage:
        churches = churches.filter(pipeline_stage=pipeline_stage)
    
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
            church.name,
            church.denomination or '',
            church.website or '',
            church.email or '',
            church.phone or '',
            church.address or '',
            church.location or '',
            str(church.congregation_size) if church.congregation_size is not None else '',
            str(church.weekly_attendance) if church.weekly_attendance is not None else '',
            str(church.year_founded) if church.year_founded is not None else '',
            church.church_pipeline or '',
            church.get_priority_display(),
            church.notes or '',
            church.created_at.strftime('%Y-%m-%d %H:%M:%S')
        ])
    
    return response
