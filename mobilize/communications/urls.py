from django.urls import path
from . import views

app_name = "communications"

urlpatterns = [
    # Email templates
    path(
        "email-templates/",
        views.EmailTemplateListView.as_view(),
        name="email_template_list",
    ),
    path(
        "email-templates/create/",
        views.EmailTemplateCreateView.as_view(),
        name="email_template_create",
    ),
    path(
        "email-templates/<int:pk>/",
        views.EmailTemplateDetailView.as_view(),
        name="email_template_detail",
    ),
    path(
        "email-templates/<int:pk>/update/",
        views.EmailTemplateUpdateView.as_view(),
        name="email_template_update",
    ),
    path(
        "email-templates/<int:pk>/delete/",
        views.EmailTemplateDeleteView.as_view(),
        name="email_template_delete",
    ),
    # Email signatures
    path(
        "email-signatures/",
        views.EmailSignatureListView.as_view(),
        name="email_signature_list",
    ),
    path(
        "email-signatures/create/",
        views.EmailSignatureCreateView.as_view(),
        name="email_signature_create",
    ),
    path(
        "email-signatures/<int:pk>/",
        views.EmailSignatureDetailView.as_view(),
        name="email_signature_detail",
    ),
    path(
        "email-signatures/<int:pk>/update/",
        views.EmailSignatureUpdateView.as_view(),
        name="email_signature_update",
    ),
    path(
        "email-signatures/<int:pk>/delete/",
        views.EmailSignatureDeleteView.as_view(),
        name="email_signature_delete",
    ),
    # Communications
    path("", views.CommunicationListView.as_view(), name="communication_list"),
    path(
        "create/", views.CommunicationCreateView.as_view(), name="communication_create"
    ),
    path(
        "<int:pk>/",
        views.CommunicationDetailView.as_view(),
        name="communication_detail",
    ),
    path(
        "<int:pk>/update/",
        views.CommunicationUpdateView.as_view(),
        name="communication_update",
    ),
    path(
        "<int:pk>/delete/",
        views.CommunicationDeleteView.as_view(),
        name="communication_delete",
    ),
    # Email composition
    path("compose/", views.ComposeEmailView.as_view(), name="compose_email"),
    path("send-email/", views.send_email, name="send_email"),
    path(
        "preview-template/<int:template_id>/",
        views.preview_email_template,
        name="preview_template",
    ),
    # Gmail integration
    path("gmail/auth/", views.GmailAuthView.as_view(), name="gmail_auth"),
    path("gmail/callback/", views.GmailCallbackView.as_view(), name="gmail_callback"),
    path("gmail/compose/", views.GmailComposeView.as_view(), name="gmail_compose"),
    path("gmail/sync/", views.GmailSyncView.as_view(), name="gmail_sync"),
    path("gmail/status/", views.gmail_status, name="gmail_status"),
    path("gmail/disconnect/", views.gmail_disconnect, name="gmail_disconnect"),
    # Google Contacts sync
    path("contacts/sync/", views.ContactSyncView.as_view(), name="contact_sync"),
    path(
        "contacts/sync/status/", views.contact_sync_status, name="contact_sync_status"
    ),
    path(
        "contacts/sync/settings/",
        views.ContactSyncSettingsView.as_view(),
        name="contact_sync_settings",
    ),
    # Google Calendar integration
    path("calendar/", views.CalendarListView.as_view(), name="calendar_list"),
    path("calendar/auth/", views.CalendarAuthView.as_view(), name="calendar_auth"),
    path(
        "calendar/callback/",
        views.CalendarCallbackView.as_view(),
        name="calendar_callback",
    ),
    path(
        "calendar/create-event/",
        views.CalendarEventCreateView.as_view(),
        name="calendar_event_create",
    ),
    path("calendar/sync/", views.CalendarSyncView.as_view(), name="calendar_sync"),
    path("calendar/status/", views.calendar_status, name="calendar_status"),
    path("calendar/disconnect/", views.calendar_disconnect, name="calendar_disconnect"),
    # Bulk operations
    path("bulk/delete/", views.bulk_delete_communications, name="bulk_delete"),
    path("bulk/archive/", views.bulk_archive_communications, name="bulk_archive"),
    path(
        "bulk/update-status/",
        views.bulk_update_communication_status,
        name="bulk_update_status",
    ),
    path(
        "bulk/update-type/",
        views.bulk_update_communication_type,
        name="bulk_update_type",
    ),
    path(
        "bulk/assign-user/",
        views.bulk_assign_communication_user,
        name="bulk_assign_user",
    ),
    # SMS functionality
    path("sms/send/", views.send_sms_view, name="send_sms"),
    path("sms/webhook/", views.sms_webhook, name="sms_webhook"),
    # API endpoints
    path("api/contacts/", views.get_contacts_json, name="get_contacts_json"),
    path("api/create-meet/", views.create_meet_link, name="create_meet_link"),
    path(
        "api/check-notifications/",
        views.check_gmail_notifications,
        name="check_gmail_notifications",
    ),
]
