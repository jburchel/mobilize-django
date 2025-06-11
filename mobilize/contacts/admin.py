from django.contrib import admin
from .models import Contact, Person

@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('id', 'first_name', 'last_name', 'church_name', 'email', 'phone')
    list_filter = ('type',)
    search_fields = ('first_name', 'last_name', 'church_name', 'email', 'phone')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('first_name', 'last_name', 'church_name', 'email', 'phone', 'type', 'preferred_contact_method', 'image')
        }),
        ('Address', {
            'fields': ('street_address', 'city', 'state', 'zip_code', 'country', 'address')
        }),
        ('Notes', {
            'fields': ('notes', 'initial_notes')
        }),
        ('Google Integration', {
            'fields': ('google_resource_name', 'google_contact_id')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'date_created', 'date_modified', 'last_synced_at')
        }),
        ('Ownership', {
            'fields': ('office_id', 'user_id')
        }),
        ('Conflict Management', {
            'fields': ('conflict_data', 'has_conflict')
        }),
    )

@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ('id', 'first_name', 'last_name', 'email', 'phone')
    list_filter = ('pipeline_stage', 'priority', 'status')
    search_fields = ('first_name', 'last_name', 'email', 'phone')
    
    fieldsets = (
        ('Personal Details', {
            'fields': ('birthday', 'anniversary', 'marital_status', 'spouse_first_name', 'spouse_last_name', 'home_country', 'languages')
        }),
        ('Professional Details', {
            'fields': ('occupation', 'employer', 'skills', 'interests')
        }),
        ('Church Relationship', {
            'fields': ('church_id', 'church_role', 'is_primary_contact')
        }),
        ('Pipeline and Status', {
            'fields': ('pipeline_stage', 'pipeline_status', 'people_pipeline', 'priority', 'status')
        }),
        ('Dates and Tracking', {
            'fields': ('last_contact', 'next_contact', 'date_closed')
        }),
        ('Notes and Metadata', {
            'fields': ('info_given', 'desired_service', 'reason_closed', 'tags')
        }),
        ('Assignment and Ownership', {
            'fields': ('assigned_to',)
        }),
        ('Source Information', {
            'fields': ('source', 'referred_by')
        }),
        ('Social Media', {
            'fields': ('website', 'facebook', 'twitter', 'linkedin', 'instagram')
        }),
        ('Integration', {
            'fields': ('virtuous',)
        }),
    )
