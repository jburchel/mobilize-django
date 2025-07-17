from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .models import Pipeline, PipelineStage, PipelineContact, PipelineStageHistory

# Create your views here.


@login_required
def pipeline_visualization(request, pipeline_id=None):
    # If no pipeline_id is provided, try to get the main pipeline for the user's office
    # This logic will need to be refined based on how you determine the "current" or "default" pipeline
    if pipeline_id:
        pipeline = get_object_or_404(Pipeline, pk=pipeline_id)
    else:
        # Placeholder: Get the first pipeline available or the one marked as main for the user's office
        # You'll need to implement logic to get the user's office and then the main pipeline for that office.
        pipeline = Pipeline.objects.first()  # Replace with more specific logic

    stages_with_contacts = []
    if pipeline:
        for stage in pipeline.stages.all().order_by("order"):
            contacts_in_stage = PipelineContact.objects.filter(
                current_stage=stage, pipeline=pipeline
            )
            total_duration_in_stage = timezone.timedelta(0)
            contacts_count = contacts_in_stage.count()

            if contacts_count > 0:
                for contact in contacts_in_stage:
                    if contact.entered_at:
                        total_duration_in_stage += timezone.now() - contact.entered_at
                average_duration_in_stage = total_duration_in_stage / contacts_count
            else:
                average_duration_in_stage = None

            stages_with_contacts.append(
                {
                    "stage": stage,
                    "contacts": contacts_in_stage,
                    "average_duration": average_duration_in_stage,
                }
            )

    context = {
        "pipeline": pipeline,
        "stages_with_contacts": stages_with_contacts,
        "all_pipelines": Pipeline.objects.all(),  # Or filter by user's office
    }
    return render(request, "pipeline/pipeline_visualization.html", context)


@login_required
@require_POST
def move_pipeline_contact(request):
    pipeline_contact_id = request.POST.get("pipeline_contact_id")
    target_stage_id = request.POST.get("target_stage_id")

    if not pipeline_contact_id or not target_stage_id:
        messages.error(request, "Missing contact or target stage information.")
        return redirect(
            request.META.get("HTTP_REFERER", "pipeline:pipeline_visualization_default")
        )

    pipeline_contact = get_object_or_404(PipelineContact, pk=pipeline_contact_id)
    target_stage = get_object_or_404(
        PipelineStage, pk=target_stage_id, pipeline=pipeline_contact.pipeline
    )
    from_stage = pipeline_contact.current_stage

    if from_stage == target_stage:
        messages.info(
            request, f"{pipeline_contact.contact} is already in {target_stage.name}."
        )
        return redirect(
            "pipeline:pipeline_visualization", pipeline_id=pipeline_contact.pipeline.id
        )

    # Update contact's stage and entry date
    pipeline_contact.current_stage = target_stage
    pipeline_contact.entered_at = timezone.now()
    pipeline_contact.save()

    # Log the history
    PipelineStageHistory.objects.create(
        pipeline_contact=pipeline_contact,
        from_stage=from_stage,
        to_stage=target_stage,
        created_by=request.user,
        notes=f"Moved from {from_stage.name} to {target_stage.name} by {request.user.username}.",
    )

    messages.success(
        request, f"{pipeline_contact.contact} moved to {target_stage.name}."
    )
    return redirect(
        "pipeline:pipeline_visualization", pipeline_id=pipeline_contact.pipeline.id
    )


@login_required
@require_POST
def update_contact_pipeline_stage(request):
    """
    AJAX endpoint to update a contact's pipeline stage from detail pages.
    Expects JSON data with contact_id, contact_type, and stage_id.
    """
    try:
        data = json.loads(request.body)
        contact_id = data.get("contact_id")
        contact_type = data.get("contact_type")  # 'person' or 'church'
        stage_id = data.get("stage_id")

        if not all([contact_id, contact_type, stage_id]):
            return JsonResponse(
                {"success": False, "error": "Missing required parameters"}, status=400
            )

        # Get the target stage
        target_stage = get_object_or_404(PipelineStage, pk=stage_id)

        # Import models here to avoid circular imports
        from mobilize.contacts.models import Contact

        # Get the contact
        contact = get_object_or_404(Contact, pk=contact_id)

        # Get or create pipeline contact entry
        pipeline_contact, created = PipelineContact.objects.get_or_create(
            contact=contact,
            contact_type=contact_type,
            pipeline=target_stage.pipeline,
            defaults={"current_stage": target_stage, "entered_at": timezone.now()},
        )

        # If not created, update the stage
        if not created:
            from_stage = pipeline_contact.current_stage

            # Only update if it's a different stage
            if from_stage != target_stage:
                pipeline_contact.current_stage = target_stage
                pipeline_contact.entered_at = timezone.now()
                pipeline_contact.save()

                # Log the history
                PipelineStageHistory.objects.create(
                    pipeline_contact=pipeline_contact,
                    from_stage=from_stage,
                    to_stage=target_stage,
                    created_by=request.user,
                    notes=f"Updated via detail page by {request.user.username}",
                )

                return JsonResponse(
                    {
                        "success": True,
                        "message": f"Moved from {from_stage.name} to {target_stage.name}",
                        "stage_name": target_stage.name,
                        "stage_code": target_stage.name.lower(),
                    }
                )
            else:
                return JsonResponse(
                    {
                        "success": True,
                        "message": f"Already in {target_stage.name}",
                        "stage_name": target_stage.name,
                        "stage_code": target_stage.name.lower(),
                    }
                )
        else:
            return JsonResponse(
                {
                    "success": True,
                    "message": f"Added to {target_stage.name}",
                    "stage_name": target_stage.name,
                    "stage_code": target_stage.name.lower(),
                }
            )

    except json.JSONDecodeError:
        return JsonResponse(
            {"success": False, "error": "Invalid JSON data"}, status=400
        )
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@login_required
@require_POST
def batch_update_pipeline_stage(request):
    """
    AJAX endpoint to update multiple contacts' pipeline stages at once.
    Expects JSON data with contact_ids, contact_type, and stage_id.
    """
    try:
        data = json.loads(request.body)
        contact_ids = data.get("contact_ids", [])
        contact_type = data.get("contact_type")  # 'person' or 'church'
        stage_id = data.get("stage_id")

        if not all([contact_ids, contact_type, stage_id]):
            return JsonResponse(
                {"success": False, "error": "Missing required parameters"}, status=400
            )

        if not isinstance(contact_ids, list) or len(contact_ids) == 0:
            return JsonResponse(
                {"success": False, "error": "contact_ids must be a non-empty list"},
                status=400,
            )

        # Get the target stage
        target_stage = get_object_or_404(PipelineStage, pk=stage_id)

        # Import models here to avoid circular imports
        from mobilize.contacts.models import Contact

        # Get the contacts
        contacts = Contact.objects.filter(pk__in=contact_ids)

        if contacts.count() != len(contact_ids):
            return JsonResponse(
                {"success": False, "error": "Some contacts not found"}, status=404
            )

        updated_count = 0
        created_count = 0
        errors = []

        # Update each contact's pipeline stage
        for contact in contacts:
            try:
                # Get or create pipeline contact entry
                pipeline_contact, created = PipelineContact.objects.get_or_create(
                    contact=contact,
                    contact_type=contact_type,
                    pipeline=target_stage.pipeline,
                    defaults={
                        "current_stage": target_stage,
                        "entered_at": timezone.now(),
                    },
                )

                if created:
                    created_count += 1
                else:
                    from_stage = pipeline_contact.current_stage

                    # Only update if it's a different stage
                    if from_stage != target_stage:
                        pipeline_contact.current_stage = target_stage
                        pipeline_contact.entered_at = timezone.now()
                        pipeline_contact.save()

                        # Log the history
                        PipelineStageHistory.objects.create(
                            pipeline_contact=pipeline_contact,
                            from_stage=from_stage,
                            to_stage=target_stage,
                            created_by=request.user,
                            notes=f"Batch update by {request.user.username}",
                        )

                        updated_count += 1

            except Exception as e:
                errors.append(f"Contact {contact.id}: {str(e)}")

        # Prepare response message
        total_processed = updated_count + created_count
        messages = []

        if updated_count > 0:
            messages.append(
                f"{updated_count} contact{'s' if updated_count != 1 else ''} moved to {target_stage.name}"
            )

        if created_count > 0:
            messages.append(
                f"{created_count} contact{'s' if created_count != 1 else ''} added to {target_stage.name}"
            )

        if errors:
            messages.append(
                f"{len(errors)} error{'s' if len(errors) != 1 else ''} occurred"
            )

        return JsonResponse(
            {
                "success": True,
                "message": "; ".join(messages),
                "updated_count": updated_count,
                "created_count": created_count,
                "total_processed": total_processed,
                "errors": errors,
                "stage_name": target_stage.name,
            }
        )

    except json.JSONDecodeError:
        return JsonResponse(
            {"success": False, "error": "Invalid JSON data"}, status=400
        )
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)
