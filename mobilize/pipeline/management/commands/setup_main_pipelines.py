from django.core.management.base import BaseCommand
from mobilize.pipeline.models import (
    Pipeline, PipelineStage, 
    PIPELINE_TYPE_PEOPLE, PIPELINE_TYPE_CHURCH,
    MAIN_PEOPLE_PIPELINE_STAGES, MAIN_CHURCH_PIPELINE_STAGES
)


class Command(BaseCommand):
    help = 'Set up the main People and Church pipelines shared across all offices'

    def handle(self, *args, **options):
        self.stdout.write('Setting up main pipelines...')
        
        # Create Main People Pipeline
        people_pipeline, created = Pipeline.objects.get_or_create(
            name='Main People Pipeline',
            pipeline_type=PIPELINE_TYPE_PEOPLE,
            is_main_pipeline=True,
            office=None,  # NULL = shared across all offices
            defaults={
                'description': 'Main pipeline for all people contacts across all offices'
            }
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS(f'Created main people pipeline: {people_pipeline.name}')
            )
        else:
            self.stdout.write(f'Main people pipeline already exists: {people_pipeline.name}')
        
        # Create stages for people pipeline
        for order, (stage_code, stage_name) in enumerate(MAIN_PEOPLE_PIPELINE_STAGES, 1):
            stage, created = PipelineStage.objects.get_or_create(
                pipeline=people_pipeline,
                name=stage_name,
                defaults={
                    'order': order,
                    'description': f'Main {stage_name} stage for people'
                }
            )
            if created:
                self.stdout.write(f'  Created people stage: {stage_name}')
        
        # Create Main Church Pipeline
        church_pipeline, created = Pipeline.objects.get_or_create(
            name='Main Church Pipeline',
            pipeline_type=PIPELINE_TYPE_CHURCH,
            is_main_pipeline=True,
            office=None,  # NULL = shared across all offices
            defaults={
                'description': 'Main pipeline for all church contacts across all offices'
            }
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS(f'Created main church pipeline: {church_pipeline.name}')
            )
        else:
            self.stdout.write(f'Main church pipeline already exists: {church_pipeline.name}')
        
        # Create stages for church pipeline
        for order, (stage_code, stage_name) in enumerate(MAIN_CHURCH_PIPELINE_STAGES, 1):
            stage, created = PipelineStage.objects.get_or_create(
                pipeline=church_pipeline,
                name=stage_name,
                defaults={
                    'order': order,
                    'description': f'Main {stage_name} stage for churches'
                }
            )
            if created:
                self.stdout.write(f'  Created church stage: {stage_name}')
        
        self.stdout.write(
            self.style.SUCCESS('Main pipelines setup completed!')
        )
        
        # Show summary
        self.stdout.write('\nPipeline Summary:')
        self.stdout.write(f'Main People Pipeline stages: {", ".join([s[1] for s in MAIN_PEOPLE_PIPELINE_STAGES])}')
        self.stdout.write(f'Main Church Pipeline stages: {", ".join([s[1] for s in MAIN_CHURCH_PIPELINE_STAGES])}')
        self.stdout.write('\nCustom pipelines can be created by office admins and linked to these main stages.')