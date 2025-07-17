from django.contrib import admin
from .models import (
    EmailTemplate,
    EmailSignature,
    Communication,
)  # EmailAttachment temporarily removed


# EmailAttachmentInline temporarily disabled due to missing EmailAttachment table
# class EmailAttachmentInline(admin.TabularInline):
#     model = EmailAttachment
#     extra = 0
#     readonly_fields = ('size', 'content_type', 'created_at')
#     fk_name = 'communication'


@admin.register(EmailTemplate)
class EmailTemplateAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "subject",
        "category",
        "is_html",
        "is_active",
        "created_by",
        "updated_at",
    )
    list_filter = ("is_html", "is_active", "category", "created_at")
    search_fields = ("name", "subject", "body")
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        ("Template Information", {"fields": ("name", "category", "is_active")}),
        ("Email Content", {"fields": ("subject", "body", "is_html")}),
        (
            "Metadata",
            {
                "fields": ("created_by", "created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )


@admin.register(EmailSignature)
class EmailSignatureAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "is_default", "is_html", "updated_at")
    list_filter = ("is_default", "is_html", "created_at")
    search_fields = ("name", "content", "user__username", "user__email")
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        ("Signature Information", {"fields": ("user", "name", "is_default")}),
        ("Content", {"fields": ("content", "is_html")}),
        (
            "Metadata",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )


@admin.register(Communication)
class CommunicationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "subject",
        "type",
        "date",
        "direction",
        "get_person",
        "get_church",
    )
    list_filter = ("type", "direction", "date", "email_status")
    search_fields = (
        "subject",
        "message",
        "sender",
        "person__first_name",
        "person__last_name",
        "church__name",
    )
    readonly_fields = ("created_at", "updated_at")
    date_hierarchy = "date"
    # inlines = [EmailAttachmentInline]  # Temporarily disabled due to missing EmailAttachment table

    def get_person(self, obj):
        return obj.person.full_name if obj.person else None

    get_person.short_description = "Person"
    get_person.admin_order_field = "person__last_name"

    def get_church(self, obj):
        return obj.church.name if obj.church else None

    get_church.short_description = "Church"
    get_church.admin_order_field = "church__name"

    fieldsets = (
        (
            "Communication Details",
            {
                "fields": (
                    "subject",
                    "message",
                    "type",
                    "direction",
                    "date",
                    "date_sent",
                )
            },
        ),
        ("Related Records", {"fields": ("person", "church", "office")}),
        (
            "Email Information",
            {
                "fields": (
                    "gmail_message_id",
                    "gmail_thread_id",
                    "email_status",
                    "sender",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Assignment",
            {
                "fields": ("user_id", "owner_id"),
                "classes": ("collapse",),
            },
        ),
        (
            "Google Calendar Integration",
            {
                "fields": (
                    "google_calendar_event_id",
                    "google_meet_link",
                    "last_synced_at",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Attachments",
            {
                "fields": ("attachments",),
                "classes": ("collapse",),
            },
        ),
        (
            "Metadata",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )
