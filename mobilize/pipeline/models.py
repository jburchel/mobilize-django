from django.db import models
from django.conf import settings
from django.utils import timezone


# Pipeline type constants
PIPELINE_TYPE_PEOPLE = 'people'
PIPELINE_TYPE_CHURCH = 'church'
PIPELINE_TYPE_CUSTOM = 'custom'

PIPELINE_TYPE_CHOICES = [
    (PIPELINE_TYPE_PEOPLE, 'People Pipeline'),
    (PIPELINE_TYPE_CHURCH, 'Church Pipeline'),
    (PIPELINE_TYPE_CUSTOM, 'Custom Pipeline'),
]


class Pipeline(models.Model):
    """Model for defining sales or recruitment pipelines"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    pipeline_type = models.CharField(max_length=50, choices=PIPELINE_TYPE_CHOICES, default=PIPELINE_TYPE_CUSTOM)
    office = models.ForeignKey(
        'admin_panel.Office',
        on_delete=models.CASCADE,
        related_name='pipelines'
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    is_main_pipeline = models.BooleanField(default=False, null=True)
    parent_pipeline_stage = models.CharField(max_length=100, blank=True, null=True)
    
    class Meta:
        verbose_name = 'Pipeline'
        verbose_name_plural = 'Pipelines'
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['pipeline_type']),
            models.Index(fields=['office']),
            models.Index(fields=['is_main_pipeline']),
        ]
    
    def __str__(self):
        return self.name


class PipelineStage(models.Model):
    """Model for defining stages within a pipeline"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    order = models.PositiveIntegerField()
    color = models.CharField(max_length=20, blank=True, null=True)
    pipeline = models.ForeignKey(
        Pipeline,
        on_delete=models.CASCADE,
        related_name='stages'
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    auto_move_days = models.IntegerField(blank=True, null=True)
    auto_reminder = models.BooleanField(default=False, null=True)
    auto_task_template = models.TextField(blank=True, null=True)
    
    class Meta:
        verbose_name = 'Pipeline Stage'
        verbose_name_plural = 'Pipeline Stages'
        ordering = ['pipeline', 'order', 'name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['pipeline', 'order']),
        ]
    
    def __str__(self):
        return f"{self.pipeline.name} - {self.name}"


class PipelineContact(models.Model):
    """Model for tracking contacts within pipelines"""
    # We'll use separate fields for person and church to support both types
    person = models.ForeignKey(
        'contacts.Person',
        on_delete=models.CASCADE,
        related_name='pipeline_entries',
        null=True,
        blank=True
    )
    church = models.ForeignKey(
        'churches.Church',
        on_delete=models.CASCADE,
        related_name='pipeline_entries',
        null=True,
        blank=True
    )
    # This field is used to determine which type of contact this is
    contact_type = models.CharField(
        max_length=10,
        choices=[('person', 'Person'), ('church', 'Church')],
        default='person'
    )
    pipeline = models.ForeignKey(
        Pipeline,
        on_delete=models.CASCADE,
        related_name='contacts'
    )
    current_stage = models.ForeignKey(
        PipelineStage,
        on_delete=models.CASCADE,
        related_name='current_contacts'
    )
    entered_at = models.DateTimeField(default=timezone.now, null=True)
    last_updated = models.DateTimeField(auto_now=True, null=True)
    
    class Meta:
        verbose_name = 'Pipeline Contact'
        verbose_name_plural = 'Pipeline Contacts'
        indexes = [
            models.Index(fields=['person']),
            models.Index(fields=['church']),
            models.Index(fields=['contact_type']),
            models.Index(fields=['pipeline']),
            models.Index(fields=['current_stage']),
            models.Index(fields=['entered_at']),
        ]
    
    def __str__(self):
        contact_name = self.person if self.contact_type == 'person' else self.church
        return f"{contact_name} in {self.pipeline.name} at {self.current_stage.name}"
        
    @property
    def contact(self):
        """Return the actual contact object (either person or church)"""
        return self.person if self.contact_type == 'person' else self.church


class PipelineStageHistory(models.Model):
    """Model for tracking contact movement through pipeline stages"""
    pipeline_contact = models.ForeignKey(
        PipelineContact,
        on_delete=models.CASCADE,
        related_name='stage_history'
    )
    from_stage = models.ForeignKey(
        PipelineStage,
        on_delete=models.CASCADE,
        related_name='from_stage_history',
        null=True,
        blank=True
    )
    to_stage = models.ForeignKey(
        PipelineStage,
        on_delete=models.CASCADE,
        related_name='to_stage_history'
    )
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='stage_changes'
    )
    
    class Meta:
        verbose_name = 'Pipeline Stage History'
        verbose_name_plural = 'Pipeline Stage History'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['pipeline_contact']),
            models.Index(fields=['from_stage']),
            models.Index(fields=['to_stage']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.pipeline_contact.contact} moved from {self.from_stage or 'None'} to {self.to_stage}"
