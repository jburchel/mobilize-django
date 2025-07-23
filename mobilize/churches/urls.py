from django.urls import path
from . import views

app_name = "churches"

urlpatterns = [
    path("", views.church_list, name="church_list"),
    path("api/list/", views.church_list_api, name="church_list_api"),
    path("create/", views.church_create, name="church_create"),
    path("<int:pk>/", views.church_detail, name="church_detail"),
    path("<int:pk>/edit/", views.church_edit, name="church_edit"),
    path("<int:pk>/delete/", views.church_delete, name="church_delete"),
    # Interaction and contact-related URLs removed as the models no longer exist in Supabase
    path(
        "<int:pk>/contacts/", views.church_contacts, name="church_contacts"
    ),  # Kept for compatibility
    path("import/", views.import_churches, name="import_churches"),
    path("export/", views.export_churches, name="export_churches"),
    # Church membership management
    path("<int:pk>/add-member/", views.add_church_member, name="add_church_member"),
    path(
        "membership/<int:membership_id>/edit/",
        views.edit_church_member,
        name="edit_church_member",
    ),
    path(
        "membership/<int:membership_id>/set-primary/",
        views.set_primary_contact,
        name="set_primary_contact",
    ),
    path(
        "membership/<int:membership_id>/remove/",
        views.remove_church_member,
        name="remove_church_member",
    ),
    # Bulk operations
    path("bulk/delete/", views.bulk_delete_churches, name="bulk_delete_churches"),
    path(
        "bulk/update-priority/",
        views.bulk_update_church_priority,
        name="bulk_update_church_priority",
    ),
    path(
        "bulk/assign-user/",
        views.bulk_assign_church_user,
        name="bulk_assign_church_user",
    ),
    path(
        "bulk/assign-office/",
        views.bulk_assign_church_office,
        name="bulk_assign_church_office",
    ),
]
