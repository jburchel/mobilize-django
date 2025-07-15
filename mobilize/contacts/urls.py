from django.urls import path
from . import views

app_name = 'contacts'

urlpatterns = [
    path('', views.person_list, name='person_list'),
    path('api/list/', views.person_list_api, name='person_list_api'),  # API endpoint for lazy loading
    path('create/', views.person_create, name='person_create'),
    path('<int:pk>/', views.person_detail, name='person_detail'),
    path('<int:pk>/edit/', views.person_edit, name='person_edit'),
    path('<int:pk>/delete/', views.person_delete, name='person_delete'),
    # Interaction-related URLs have been removed as the ContactInteraction model no longer exists
    path('import/', views.import_contacts, name='import_contacts'),
    path('export/', views.export_contacts, name='export_contacts'),
    path('google-sync/', views.google_sync, name='google_sync'),
    path('google-sync/selective/', views.selective_google_import, name='selective_google_import'),
    path('api/google-contacts/', views.google_contacts_api, name='google_contacts_api'),
    # Bulk operations
    path('bulk/delete/', views.bulk_delete, name='bulk_delete'),
    path('bulk/update-priority/', views.bulk_update_priority, name='bulk_update_priority'),
    path('bulk/assign-office/', views.bulk_assign_office, name='bulk_assign_office'),
    path('bulk/assign-user/', views.bulk_assign_user, name='bulk_assign_user'),
]
