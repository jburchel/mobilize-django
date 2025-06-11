from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.utils import timezone
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
        pipeline = Pipeline.objects.first() # Replace with more specific logic

    stages_with_contacts = []
    if pipeline:
        for stage in pipeline.stages.all().order_by('order'):
            contacts_in_stage = PipelineContact.objects.filter(current_stage=stage, pipeline=pipeline)
            total_duration_in_stage = timezone.timedelta(0)
            contacts_count = contacts_in_stage.count()

            if contacts_count > 0:
                for contact in contacts_in_stage:
                    if contact.entered_at:
                        total_duration_in_stage += (timezone.now() - contact.entered_at)
                average_duration_in_stage = total_duration_in_stage / contacts_count
            else:
                average_duration_in_stage = None
            
            stages_with_contacts.append({
                'stage': stage, 
                'contacts': contacts_in_stage, 
                'average_duration': average_duration_in_stage})

    context = {
        'pipeline': pipeline,
        'stages_with_contacts': stages_with_contacts,
        'all_pipelines': Pipeline.objects.all() # Or filter by user's office
    }
    return render(request, 'pipeline/pipeline_visualization.html', context)

@login_required
@require_POST
def move_pipeline_contact(request):
    pipeline_contact_id = request.POST.get('pipeline_contact_id')
    target_stage_id = request.POST.get('target_stage_id')

    if not pipeline_contact_id or not target_stage_id:
        messages.error(request, "Missing contact or target stage information.")
        return redirect(request.META.get('HTTP_REFERER', 'pipeline:pipeline_visualization_default'))

    pipeline_contact = get_object_or_404(PipelineContact, pk=pipeline_contact_id)
    target_stage = get_object_or_404(PipelineStage, pk=target_stage_id, pipeline=pipeline_contact.pipeline)
    from_stage = pipeline_contact.current_stage

    if from_stage == target_stage:
        messages.info(request, f"{pipeline_contact.contact} is already in {target_stage.name}.")
        return redirect('pipeline:pipeline_visualization', pipeline_id=pipeline_contact.pipeline.id)

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
        notes=f"Moved from {from_stage.name} to {target_stage.name} by {request.user.username}."
    )

    messages.success(request, f"{pipeline_contact.contact} moved to {target_stage.name}.")
    return redirect('pipeline:pipeline_visualization', pipeline_id=pipeline_contact.pipeline.id)
