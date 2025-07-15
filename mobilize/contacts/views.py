from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q
from django.views.decorators.http import require_POST
from django.urls import reverse
from django.db import transaction
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
from mobilize.core.permissions import get_data_access_manager


@login_required
@ensure_user_office_assignment
def person_list(request):
    """
    Display a list of people with filtering and pagination.
    Uses lazy loading for better performance.
    Uses DataAccessManager for view mode persistence.
    """
    # Get data access manager for view mode handling
    access_manager = get_data_access_manager(request)
    
    # Get query parameters for filtering and sorting
    query = request.GET.get('q', '')
    priority = request.GET.get('priority', '')
    pipeline_stage = request.GET.get('pipeline_stage', '')
    sort_by = request.GET.get('sort', 'name')  # Default sort by name
    
    # Enable lazy loading by default (with dynamic search)
    use_lazy_loading = request.GET.get('lazy', 'true').lower() == 'true'
    
    # Get pipeline stages for the dropdown
    from mobilize.pipeline.models import MAIN_PEOPLE_PIPELINE_STAGES, Pipeline
    
    if use_lazy_loading:
        # Get data for bulk operation dropdowns
        from mobilize.authentication.models import User
        from mobilize.admin_panel.models import Office
        
        # Get users for bulk assignment dropdown
        users = User.objects.filter(is_active=True).order_by('first_name', 'last_name', 'email')
        
        # Get offices for bulk assignment dropdown
        offices = Office.objects.all().order_by('name')
        
        # Get all offices for office selector (super admin only)
        all_offices = Office.objects.all().order_by('name')
        
        # Sort options for the template
        sort_options = [
            ('name', 'Name A-Z'),
            ('-name', 'Name Z-A'),
            ('email', 'Email A-Z'),
            ('-email', 'Email Z-A'),
            ('assigned_to', 'Assigned To A-Z'),
            ('-assigned_to', 'Assigned To Z-A'),
            ('priority', 'Priority Low-High'),
            ('-priority', 'Priority High-Low'),
            ('created', 'Oldest First'),
            ('-created', 'Newest First'),
            ('home_country', 'Home Country A-Z'),
            ('-home_country', 'Home Country Z-A'),
        ]
        
        # Get actual pipeline stages for bulk operations
        main_pipeline = Pipeline.get_main_people_pipeline()
        pipeline_stages_objects = []
        if main_pipeline:
            pipeline_stages_objects = main_pipeline.stages.all().order_by('order')
        
        # Use lazy loading template
        context = {
            'query': query,
            'priority': priority,
            'pipeline_stage': pipeline_stage,
            'sort_by': sort_by,
            'priorities': Contact.PRIORITY_CHOICES,
            'pipeline_stages': MAIN_PEOPLE_PIPELINE_STAGES,
            'pipeline_stages_objects': pipeline_stages_objects,
            'users': users,
            'offices': offices,
            'sort_options': sort_options,
            # Add view mode context
            'can_toggle_view': access_manager.can_view_all_data(),
            'current_view_mode': access_manager.view_mode,
            'view_mode_display': access_manager.get_view_mode_display(),
            'user_role': getattr(request.user, 'role', 'standard_user'),
            'all_offices': all_offices,
        }
        return render(request, 'contacts/person_list_lazy.html', context)
    else:
        # Fallback to traditional pagination
        # Use DataAccessManager for proper filtering
        people = access_manager.get_people_queryset().select_related('contact', 'contact__office')
        
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
        
        # Apply sorting
        sort_options_mapping = {
            'name': 'contact__last_name',
            'email': 'contact__email',
            'assigned_to': 'contact__user__first_name',
            'priority': 'contact__priority',
            'created': 'contact__created_at',
            'home_country': 'home_country',
            '-name': '-contact__last_name',
            '-email': '-contact__email',
            '-assigned_to': '-contact__user__first_name',
            '-priority': '-contact__priority',
            '-created': '-contact__created_at',
            '-home_country': '-home_country',
        }
        
        # Apply sorting with fallback ordering for consistent pagination
        if sort_by in sort_options_mapping:
            people = people.order_by(sort_options_mapping[sort_by], 'pk')
        else:
            people = people.order_by('contact__last_name', 'contact__first_name', 'pk')  # Default sort
        
        # Get items per page from request
        per_page = int(request.GET.get('per_page', 25))
        
        # Pagination
        paginator = Paginator(people, per_page)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)
        
        # Get priorities for filter dropdowns
        priorities = Contact.PRIORITY_CHOICES
        
        # Sort options for the template (same as lazy loading)
        sort_options = [
            ('name', 'Name A-Z'),
            ('-name', 'Name Z-A'),
            ('email', 'Email A-Z'),
            ('-email', 'Email Z-A'),
            ('assigned_to', 'Assigned To A-Z'),
            ('-assigned_to', 'Assigned To Z-A'),
            ('priority', 'Priority Low-High'),
            ('-priority', 'Priority High-Low'),
            ('created', 'Oldest First'),
            ('-created', 'Newest First'),
            ('home_country', 'Home Country A-Z'),
            ('-home_country', 'Home Country Z-A'),
        ]
        
        # Get actual pipeline stages for bulk operations
        main_pipeline = Pipeline.get_main_people_pipeline()
        pipeline_stages_objects = []
        if main_pipeline:
            pipeline_stages_objects = main_pipeline.stages.all().order_by('order')
        
        # Get data for bulk operation dropdowns
        from mobilize.authentication.models import User
        from mobilize.admin_panel.models import Office
        
        # Get users for bulk assignment dropdown
        users = User.objects.filter(is_active=True).order_by('first_name', 'last_name', 'email')
        
        # Get offices for bulk assignment dropdown
        offices = Office.objects.all().order_by('name')
        
        # Get all offices for office selector (super admin only)
        all_offices = Office.objects.all().order_by('name')
        
        context = {
            'page_obj': page_obj,
            'query': query,
            'priority': priority,
            'pipeline_stage': pipeline_stage,
            'sort_by': sort_by,
            'priorities': priorities,
            'pipeline_stages': MAIN_PEOPLE_PIPELINE_STAGES,
            'pipeline_stages_objects': pipeline_stages_objects,
            'users': users,
            'offices': offices,
            'sort_options': sort_options,
            'per_page': per_page,
            # Add view mode context
            'can_toggle_view': access_manager.can_view_all_data(),
            'current_view_mode': access_manager.view_mode,
            'view_mode_display': access_manager.get_view_mode_display(),
            'user_role': getattr(request.user, 'role', 'standard_user'),
            'all_offices': all_offices,
        }
        
        return render(request, 'contacts/person_list.html', context)


@login_required
@office_object_permission_required(Person, 'contact__office')
def person_detail(request, pk):
    """
    Display detailed information about a person.
    Only accessible if user has office permission.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        # Get the person (office filtering is handled by decorator)
        person = get_object_or_404(Person.objects.select_related('contact', 'contact__office'), pk=pk)
        
        # Get recent communications for this person
        from mobilize.communications.models import Communication
        from django.db.models import Q
        recent_communications = Communication.objects.filter(
            Q(person__contact_id=person.contact.id) | Q(church__contact_id=person.contact.id)
        ).order_by('-date_sent', '-created_at')[:5]
        
        # Get related tasks for this person
        related_tasks = person.person_tasks.all().order_by('-due_date', '-created_at')[:10]
        
        # Get pipeline stages for the interactive slider
        from mobilize.pipeline.models import Pipeline, PipelineStage, PipelineContact
        
        # Debug logging
        logger.error(f"DEBUG: Getting main people pipeline for person {pk}")
        
        main_pipeline = Pipeline.get_main_people_pipeline()
        
        logger.error(f"DEBUG: Main pipeline = {main_pipeline}")
        
        pipeline_stages = []
        current_stage = None
        
        if main_pipeline:
            logger.error(f"DEBUG: Main pipeline ID = {main_pipeline.id}")
            pipeline_stages = main_pipeline.stages.all().order_by('order')
            logger.error(f"DEBUG: Found {pipeline_stages.count()} stages")
            
            # Get current pipeline stage for this person
            try:
                pipeline_contact = PipelineContact.objects.get(
                    contact=person.contact,
                    pipeline=main_pipeline
                )
                current_stage = pipeline_contact.current_stage
            except PipelineContact.DoesNotExist:
                current_stage = None
    except Exception as e:
        logger.error(f"ERROR in person_detail: {str(e)}", exc_info=True)
        raise
    
    context = {
        'person': person,
        'recent_communications': recent_communications,
        'related_tasks': related_tasks,
        'pipeline_stages': pipeline_stages,
        'current_stage': current_stage,
        'main_pipeline': main_pipeline,
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
            # Get the user's office assignment
            from mobilize.admin_panel.models import UserOffice
            user_office = UserOffice.objects.filter(user_id=str(request.user.id)).first()
            office = user_office.office if user_office else None
            
            person = form.save(commit=True, user=request.user, office=office)
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
        contact = person.contact
        
        try:
            # Use atomic transaction to ensure clean deletion
            with transaction.atomic():
                # Delete the contact, which will cascade delete the person
                # This is safer than deleting the person directly
                contact.delete()
                
            messages.success(request, f"Successfully deleted {name}")
        except Exception as e:
            # Log the error and show a user-friendly message
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error deleting person {name} (ID: {pk}): {str(e)}")
            logger.error(f"Exception type: {type(e).__name__}")
            logger.error(f"Full traceback: ", exc_info=True)
            messages.error(request, f"Error deleting {name}. Please try again or contact support.")
            return render(request, 'contacts/person_confirm_delete.html', {
                'person': person,
            })
        
        return redirect('contacts:person_list')
    
    return render(request, 'contacts/person_confirm_delete.html', {
        'person': person,
    })


@login_required
def person_list_api(request):
    """
    JSON API endpoint for lazy loading person list data.
    Uses DataAccessManager for proper filtering.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # Get data access manager for view mode handling
    access_manager = get_data_access_manager(request)
    
    # Get query parameters
    query = request.GET.get('q', '')
    priority = request.GET.get('priority', '')
    pipeline_stage = request.GET.get('pipeline_stage', '')
    sort_by = request.GET.get('sort', 'name')  # Default sort by name
    page = int(request.GET.get('page', 1))
    per_page = int(request.GET.get('per_page', 25))
    
    # Debug logging
    logger.info(f"🔍 DEBUG: User {request.user.email} (Role: {request.user.role}) accessing person_list_api with view_mode: {access_manager.view_mode}")
    
    # Use DataAccessManager for proper filtering
    try:
        people = access_manager.get_people_queryset()
        initial_count = people.count()
        logger.info(f"🔍 DEBUG: Initial people count after access filtering: {initial_count}")
            
    except Exception as e:
        logger.error(f"🔍 DEBUG: Basic queryset setup failed: {e}")
        return JsonResponse({
            'results': [],
            'page': page,
            'per_page': per_page,
            'total': 0,
            'has_next': False,
            'has_previous': False,
            'error': str(e)
        })
    
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
    
    # Simplified ordering and pagination test
    try:
        logger.info(f"🔍 DEBUG: Before pagination - people count: {people.count()}")
        
        # Apply sorting
        sort_options_mapping = {
            'name': 'contact__last_name',
            'email': 'contact__email',
            'assigned_to': 'contact__user__first_name',
            'priority': 'contact__priority',
            'created': 'contact__created_at',
            'home_country': 'home_country',
            '-name': '-contact__last_name',
            '-email': '-contact__email',
            '-assigned_to': '-contact__user__first_name',
            '-priority': '-contact__priority',
            '-created': '-contact__created_at',
            '-home_country': '-home_country',
        }
        
        # Apply sorting with fallback ordering for consistent pagination
        if sort_by in sort_options_mapping:
            people = people.order_by(sort_options_mapping[sort_by], 'pk')
            logger.info(f"🔍 DEBUG: Applied sorting: {sort_by} -> {sort_options_mapping[sort_by]}")
        else:
            people = people.order_by('contact__last_name', 'contact__first_name', 'pk')  # Default sort
            logger.info(f"🔍 DEBUG: Applied default sorting: last_name, first_name, pk")
        
        # Get total count first (this should always work)
        try:
            total_count = people.count()
            logger.info(f"🔍 DEBUG: Total people count: {total_count}, per_page: {per_page}")
        except Exception as e:
            logger.error(f"🔍 DEBUG: Failed to get total count: {e}")
            total_count = 0
        
        # Calculate pagination indices
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        
        # Get the page of results
        try:
            # Use list() to force evaluation of the queryset slice
            people_to_process = list(people[start_idx:end_idx])
            logger.info(f"🔍 DEBUG: Page {page}: requested {per_page} items, got {len(people_to_process)} people (indices {start_idx}:{end_idx} of {total_count} total)")
            
            # Calculate has_next and has_previous
            has_next = end_idx < total_count
            has_previous = page > 1
            
        except Exception as e:
            logger.error(f"🔍 DEBUG: Pagination slice failed: {e}")
            people_to_process = []
            has_next = False
            has_previous = False
                
    except Exception as e:
        logger.error(f"🔍 DEBUG: Pagination setup failed: {e}")
        return JsonResponse({
            'results': [],
            'page': page,
            'per_page': per_page,
            'total': 0,
            'has_next': False,
            'has_previous': False,
            'error': f'Pagination failed: {str(e)}'
        })
    
    # Build JSON response
    results = []
    logger.info(f"🔍 DEBUG: Processing {len(people_to_process)} people")
    
    for i, person in enumerate(people_to_process):
        try:
            logger.info(f"🔍 DEBUG: Processing person {i+1}: ID={person.pk}, Contact ID={person.contact.id}")
            
            # Build proper name display: "First Last" or "No name listed"
            first_name = person.contact.first_name or ""
            last_name = person.contact.last_name or ""
            
            # Clean up names - filter out obvious placeholders only
            first_name = first_name.strip()
            last_name = last_name.strip()
            
            logger.info(f"🔍 DEBUG: Raw names - First: '{first_name}', Last: '{last_name}'")
            
            # Only filter out obvious placeholders and standalone titles
            if first_name.lower().startswith('person ') and first_name[7:].isdigit():
                first_name = ""  # "Person 123" -> ""
            if last_name.isdigit():
                last_name = ""   # "123" -> ""
            
            # Keep short titles as they might be real names, only filter standalone common titles
            standalone_titles = {'mr', 'mrs', 'ms', 'dr'}
            if first_name.lower() in standalone_titles and not last_name:
                first_name = ""  # "Mr" alone -> "", but "Mr Smith" keeps "Mr"
            
            # Build full name
            full_name = f"{first_name} {last_name}".strip()
            
            # If no valid name parts, show "No name listed"
            if not full_name:
                full_name = "No name listed"
            
            logger.info(f"🔍 DEBUG: Person name: '{full_name}', Email: '{person.contact.email}'")
            
            # Test each field access
            priority = person.contact.priority
            priority_display = person.contact.get_priority_display()
            pipeline_stage = person.contact.get_pipeline_stage_code()
            
            logger.info(f"🔍 DEBUG: Priority: {priority}, Pipeline: {pipeline_stage}")
            
            result_item = {
                'id': person.contact.id,
                'name': full_name,
                'email': person.contact.email or "",
                'phone': person.contact.phone or "",
                'priority': priority,
                'priority_display': priority_display,
                'pipeline_stage': pipeline_stage,
                'detail_url': reverse('contacts:person_detail', args=[person.pk]),
                'edit_url': reverse('contacts:person_edit', args=[person.pk]),
                'delete_url': reverse('contacts:person_delete', args=[person.pk]),
            }
            
            results.append(result_item)
            logger.info(f"🔍 DEBUG: Successfully added person {i+1} to results")
            
        except Exception as e:
            logger.error(f"🔍 DEBUG: Error processing person {person.pk}: {e}")
            import traceback
            logger.error(f"🔍 DEBUG: Full traceback: {traceback.format_exc()}")
            continue
    
    logger.info(f"🔍 DEBUG: Final results count: {len(results)}, Total: {total_count}")
    
    # Ensure we're not returning more than per_page results
    if len(results) > per_page:
        logger.warning(f"⚠️ WARNING: Returning {len(results)} results but per_page is {per_page}")
        results = results[:per_page]
        has_next = True
    
    return JsonResponse({
        'results': results,
        'page': page,
        'per_page': per_page,
        'total': total_count,
        'has_next': has_next,
        'has_previous': has_previous,
    })


# interaction_list view has been removed as the ContactInteraction model no longer exists


# Interaction-related functions have been removed as the ContactInteraction model no longer exists


@login_required
@ensure_user_office_assignment
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
                # Get the user's office assignment for imported contacts
                from mobilize.admin_panel.models import UserOffice
                user_office = UserOffice.objects.filter(user_id=str(request.user.id)).first()
                office = user_office.office if user_office else None
                
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
                                contact.office = office
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
                                    office=office,
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
                                office=office,
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
    
    # Use DataAccessManager for proper filtering
    access_manager = get_data_access_manager(request)
    people = access_manager.get_people_queryset().select_related('contact', 'contact__office')
    
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
    Add contacts from Google Workspace using the Google Contacts API.
    """
    from mobilize.communications.google_contacts_service import GoogleContactsService
    from mobilize.authentication.models import UserContactSyncSettings
    
    # Get user's sync settings
    sync_settings = None
    try:
        sync_settings = UserContactSyncSettings.objects.get(user=request.user)
    except UserContactSyncSettings.DoesNotExist:
        # Create default sync settings for the user
        sync_settings = UserContactSyncSettings.objects.create(
            user=request.user,
            sync_preference='crm_only',
            auto_sync_enabled=False
        )
    
    contacts_service = GoogleContactsService(request.user)
    
    context = {
        'sync_settings': sync_settings,
        'is_authenticated': contacts_service.is_authenticated(),
        'sync_choices': UserContactSyncSettings.SYNC_CHOICES,
    }
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'sync':
            if not contacts_service.is_authenticated():
                messages.error(request, "Google Contacts not authenticated. Please connect Gmail first.")
                return redirect('communications:gmail_auth')
            
            # Get sync preference from form
            sync_preference = request.POST.get('sync_preference', 'crm_only')
            
            # Temporarily update sync settings for this operation
            original_preference = sync_settings.sync_preference
            sync_settings.sync_preference = sync_preference
            
            # Perform the sync
            result = contacts_service.sync_contacts_based_on_preference()
            
            # Restore original preference
            sync_settings.sync_preference = original_preference
            sync_settings.save()
            
            if result['success']:
                messages.success(request, result['message'])
                # Add additional info about what was synced
                if 'created_count' in result and 'updated_count' in result:
                    messages.info(request, f"Created {result['created_count']} new contacts, updated {result['updated_count']} existing contacts")
                elif 'synced_count' in result:
                    messages.info(request, f"Synced {result['synced_count']} contacts")
                
                # Show any warnings
                if 'errors' in result and result['errors']:
                    for error in result['errors'][:3]:  # Show first 3 errors
                        messages.warning(request, error)
                    if len(result['errors']) > 3:
                        messages.warning(request, f"... and {len(result['errors']) - 3} more warnings")
            else:
                messages.error(request, f"Contact sync failed: {result.get('error', 'Unknown error')}")
        
        elif action == 'auth_google':
            return redirect('communications:gmail_auth')
    
    return render(request, 'contacts/google_sync.html', context)


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
    # Handle both list format and comma-separated string
    contact_ids = request.POST.getlist('contact_ids')
    
    # If we got a list with one item that contains commas, it's a comma-separated string
    if len(contact_ids) == 1 and ',' in contact_ids[0]:
        contact_ids = [id.strip() for id in contact_ids[0].split(',') if id.strip()]
    elif not contact_ids:
        # Try to get as a single comma-separated string
        contact_ids_str = request.POST.get('contact_ids', '')
        if contact_ids_str:
            contact_ids = [id.strip() for id in contact_ids_str.split(',') if id.strip()]
    
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
        
        # Convert string IDs to integers
        contact_ids = [int(id) for id in contact_ids if id]
        
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


@login_required
@require_POST
def bulk_assign_user(request):
    """
    Assign multiple contacts to a user at once.
    """
    # Handle both list format and comma-separated string
    contact_ids = request.POST.getlist('contact_ids')
    
    # If we got a list with one item that contains commas, it's a comma-separated string
    if len(contact_ids) == 1 and ',' in contact_ids[0]:
        contact_ids = [id.strip() for id in contact_ids[0].split(',') if id.strip()]
    elif not contact_ids:
        # Try to get as a single comma-separated string
        contact_ids_str = request.POST.get('contact_ids', '')
        if contact_ids_str:
            contact_ids = [id.strip() for id in contact_ids_str.split(',') if id.strip()]
    
    user_id = request.POST.get('user_id')
    
    if not contact_ids:
        messages.error(request, "No contacts selected for assignment")
        return redirect('contacts:person_list')
    
    if not user_id:
        messages.error(request, "Please select a user")
        return redirect('contacts:person_list')
    
    try:
        from mobilize.authentication.models import User
        user = get_object_or_404(User, id=user_id)
        
        # Convert string IDs to integers
        contact_ids = [int(id) for id in contact_ids if id]
        
        # Get the contacts to update
        contacts = Contact.objects.filter(id__in=contact_ids, type='person')
        count = contacts.count()
        
        if count == 0:
            messages.error(request, "No valid contacts found to assign")
            return redirect('contacts:person_list')
        
        # Update the user assignment
        contacts.update(user=user)
        
        user_display_name = user.get_full_name() or user.email
        messages.success(request, f"Successfully assigned {count} contact(s) to {user_display_name}")
        
    except Exception as e:
        messages.error(request, f"Error assigning contacts: {str(e)}")
    
    return redirect('contacts:person_list')