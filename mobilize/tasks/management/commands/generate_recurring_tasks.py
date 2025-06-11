from django.core.management.base import BaseCommand
from django.utils import timezone
from mobilize.tasks.models import Task


class Command(BaseCommand):
    help = 'Generate recurring task occurrences for the next specified number of days'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--days-ahead',
            type=int,
            default=7,
            help='Number of days ahead to generate recurring tasks (default: 7)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be generated without actually creating tasks'
        )
    
    def handle(self, *args, **options):
        days_ahead = options['days_ahead']
        dry_run = options['dry_run']
        
        self.stdout.write(
            self.style.SUCCESS(
                f'{"[DRY RUN] " if dry_run else ""}Generating recurring tasks for the next {days_ahead} days...'
            )
        )
        
        if dry_run:
            # Show what would be generated
            cutoff_date = timezone.now() + timezone.timedelta(days=days_ahead)
            templates = Task.objects.filter(
                is_recurring_template=True,
                next_occurrence_date__lte=cutoff_date
            ).exclude(
                recurrence_end_date__lt=timezone.now().date()
            )
            
            count = 0
            for template in templates:
                temp_next_date = template.next_occurrence_date
                while (temp_next_date and 
                       temp_next_date <= cutoff_date and 
                       (not template.recurrence_end_date or 
                        temp_next_date.date() <= template.recurrence_end_date)):
                    
                    self.stdout.write(
                        f'  Would create: "{template.title}" due {temp_next_date.date()}'
                    )
                    count += 1
                    
                    # Calculate next occurrence for dry run
                    temp_next_date = template.calculate_next_occurrence()
                    if not temp_next_date:
                        break
            
            self.stdout.write(
                self.style.SUCCESS(f'[DRY RUN] Would generate {count} recurring task occurrences')
            )
        else:
            # Actually generate the tasks
            generated_count = Task.generate_pending_occurrences(days_ahead)
            
            self.stdout.write(
                self.style.SUCCESS(f'Successfully generated {generated_count} recurring task occurrences')
            )
            
            # Log some statistics
            total_templates = Task.objects.filter(is_recurring_template=True).count()
            active_templates = Task.objects.filter(
                is_recurring_template=True,
                next_occurrence_date__isnull=False
            ).exclude(
                recurrence_end_date__lt=timezone.now().date()
            ).count()
            
            self.stdout.write(f'Total recurring templates: {total_templates}')
            self.stdout.write(f'Active recurring templates: {active_templates}')