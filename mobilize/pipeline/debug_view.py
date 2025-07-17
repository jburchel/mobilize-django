from django.http import JsonResponse
from django.contrib.admin.views.decorators import staff_member_required
from mobilize.pipeline.models import Pipeline, PipelineStage, PipelineContact


@staff_member_required
def debug_pipeline_data(request):
    """Debug view to check pipeline data integrity"""

    # Get all pipelines
    pipelines = Pipeline.objects.all().values(
        "id", "name", "pipeline_type", "is_main_pipeline"
    )

    # Get all stages
    stages = PipelineStage.objects.all().values("id", "name", "pipeline_id", "order")

    # Get main pipelines
    main_people = Pipeline.get_main_people_pipeline()
    main_church = Pipeline.get_main_church_pipeline()

    # Get stages for main pipelines
    people_stages = []
    church_stages = []

    if main_people:
        people_stages = list(main_people.stages.all().values("id", "name", "order"))

    if main_church:
        church_stages = list(main_church.stages.all().values("id", "name", "order"))

    # Check for duplicate stages
    from django.db.models import Count

    duplicate_stages = (
        PipelineStage.objects.values("pipeline_id", "name")
        .annotate(count=Count("id"))
        .filter(count__gt=1)
    )

    return JsonResponse(
        {
            "all_pipelines": list(pipelines),
            "all_stages": list(stages),
            "main_people_pipeline": {
                "exists": main_people is not None,
                "id": main_people.id if main_people else None,
                "stages": people_stages,
            },
            "main_church_pipeline": {
                "exists": main_church is not None,
                "id": main_church.id if main_church else None,
                "stages": church_stages,
            },
            "duplicate_stages": list(duplicate_stages),
            "pipeline_contact_count": PipelineContact.objects.count(),
        },
        json_dumps_params={"indent": 2},
    )
