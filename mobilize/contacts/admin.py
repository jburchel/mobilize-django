from django.contrib import admin
from .models import Contact, Person

@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('id', 'first_name', 'last_name', 'church_name', 'email', 'phone', 'type')
    list_filter = ('type', 'priority', 'status')
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
            'fields': ('office', 'user')
        }),
        ('Pipeline', {
            'fields': ('priority', 'status', 'last_contact_date', 'next_contact_date')
        }),
        ('Custom Data', {
            'fields': ('tags', 'custom_fields')
        }),
        ('Conflict Management', {
            'fields': ('conflict_data', 'has_conflict')
        }),
    )
    readonly_fields = ('created_at', 'updated_at')

@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ('get_id', 'get_first_name', 'get_last_name', 'get_email', 'get_phone')
    list_filter = ('contact__priority', 'contact__status', 'marital_status')
    search_fields = ('contact__first_name', 'contact__last_name', 'contact__email', 'contact__phone')
    raw_id_fields = ('primary_church',)
    
    def get_id(self, obj):
        return obj.contact.id
    get_id.short_description = 'ID'
    get_id.admin_order_field = 'contact__id'
    
    def get_first_name(self, obj):
        return obj.contact.first_name
    get_first_name.short_description = 'First Name'
    get_first_name.admin_order_field = 'contact__first_name'
    
    def get_last_name(self, obj):
        return obj.contact.last_name
    get_last_name.short_description = 'Last Name'
    get_last_name.admin_order_field = 'contact__last_name'
    
    def get_email(self, obj):
        return obj.contact.email
    get_email.short_description = 'Email'
    get_email.admin_order_field = 'contact__email'
    
    def get_phone(self, obj):
        return obj.contact.phone
    get_phone.short_description = 'Phone'
    get_phone.admin_order_field = 'contact__phone'
    
    fieldsets = (
        ('Personal Details', {
            'fields': ('title', 'preferred_name', 'birthday', 'anniversary', 'marital_status', 
                      'spouse_first_name', 'spouse_last_name', 'home_country', 'languages')
        }),
        ('Professional Details', {
            'fields': ('profession', 'organization')
        }),
        ('Church Relationship', {
            'fields': ('primary_church', 'church_role')
        }),
        ('Social Media', {
            'fields': ('linkedin_url', 'facebook_url', 'twitter_url', 'instagram_url')
        }),
        ('Integration', {
            'fields': ('google_contact_id',)
        }),
    )
