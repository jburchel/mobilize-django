# Generated manually to set up initial pipeline data

from django.db import migrations


def create_main_pipelines(apps, schema_editor):
    """Create the main People and Church pipelines with their stages"""
    Pipeline = apps.get_model("pipeline", "Pipeline")
    PipelineStage = apps.get_model("pipeline", "PipelineStage")

    # Main pipeline stage definitions
    MAIN_PEOPLE_PIPELINE_STAGES = [
        ("promotion", "Promotion"),
        ("information", "Information"),
        ("invitation", "Invitation"),
        ("confirmation", "Confirmation"),
        ("automation", "Automation"),
    ]

    MAIN_CHURCH_PIPELINE_STAGES = [
        ("promotion", "Promotion"),
        ("information", "Information"),
        ("invitation", "Invitation"),
        ("confirmation", "Confirmation"),
        ("automation", "Automation"),
        ("en42", "EN42"),
    ]

    # Create Main People Pipeline
    people_pipeline, created = Pipeline.objects.get_or_create(
        name="Main People Pipeline",
        pipeline_type="people",
        is_main_pipeline=True,
        office=None,
        defaults={
            "description": "Main pipeline for all people contacts across all offices"
        },
    )

    # Create stages for people pipeline
    for order, (stage_code, stage_name) in enumerate(MAIN_PEOPLE_PIPELINE_STAGES, 1):
        PipelineStage.objects.get_or_create(
            pipeline=people_pipeline,
            name=stage_name,
            defaults={
                "order": order,
                "description": f"Main {stage_name} stage for people",
            },
        )

    # Create Main Church Pipeline
    church_pipeline, created = Pipeline.objects.get_or_create(
        name="Main Church Pipeline",
        pipeline_type="church",
        is_main_pipeline=True,
        office=None,
        defaults={
            "description": "Main pipeline for all church contacts across all offices"
        },
    )

    # Create stages for church pipeline
    for order, (stage_code, stage_name) in enumerate(MAIN_CHURCH_PIPELINE_STAGES, 1):
        PipelineStage.objects.get_or_create(
            pipeline=church_pipeline,
            name=stage_name,
            defaults={
                "order": order,
                "description": f"Main {stage_name} stage for churches",
            },
        )


def reverse_main_pipelines(apps, schema_editor):
    """Remove the main pipelines (for rollback)"""
    Pipeline = apps.get_model("pipeline", "Pipeline")
    Pipeline.objects.filter(is_main_pipeline=True).delete()


class Migration(migrations.Migration):

    dependencies = [
        (
            "pipeline",
            "0003_pipelinecontact_contact_alter_pipelinecontact_church_and_more",
        ),
    ]

    operations = [
        migrations.RunPython(create_main_pipelines, reverse_main_pipelines),
    ]
