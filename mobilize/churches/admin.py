from django.contrib import admin
from django.contrib.auth import get_user_model
from .models import Church

User = get_user_model()


@admin.register(Church)
class ChurchAdmin(admin.ModelAdmin):
    list_display = ('contact_id', 'name', 'denomination', 'get_contact_pipeline_stage', 'get_contact_priority')
    list_filter = ('denomination', 'contact__office') # Filter by fields on Church or related Contact
    search_fields = ('name', 'denomination', 'pastor_name', 'contact__email')
    
    fieldsets = (
        # Contact fields are managed through the Contact admin
        ('Church-specific Information', {
            'fields': ('name', 'denomination', 'year_founded', 'website', 
                       'primary_language', 'secondary_languages')
        }),
        ('Size Information', {
            'fields': ('congregation_size', 'weekly_attendance', 'service_times', 
                       'facilities', 'ministries')
        }),
        ('Senior Pastor', {
            'fields': ('pastor_name', 'senior_pastor_first_name', 'senior_pastor_last_name', 
                     'pastor_phone', 'pastor_email')
        }),
        ('Missions Pastor', {
            'fields': ('missions_pastor_first_name', 'missions_pastor_last_name', 
                     'missions_pastor_phone', 'missions_pastor_email')
        }),
        ('Primary Contact', {
            'fields': ('primary_contact_first_name', 'primary_contact_last_name', 
                     'primary_contact_phone', 'primary_contact_email', 'main_contact_id')
        }),
        ('Status & Source', { # Renamed section, removed pipeline/priority
            'fields': ('virtuous', 'date_closed', 'source', 'referred_by')
        }),
        ('Church-specific Notes', {
            'fields': ('info_given', 'reason_closed')
        }),
    )

    def get_contact_pipeline_stage(self, obj):
        return obj.contact.pipeline_stage
    get_contact_pipeline_stage.short_description = 'Pipeline Stage (Contact)'
    get_contact_pipeline_stage.admin_order_field = 'contact__pipeline_stage'

    def get_contact_priority(self, obj):
        return obj.contact.priority
    get_contact_priority.short_description = 'Priority (Contact)'
    get_contact_priority.admin_order_field = 'contact__priority'


# ChurchContact and ChurchInteraction models have been removed as they don't exist in Supabase
