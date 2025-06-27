from django.urls import path
from . import views
from .debug_view import debug_pipeline_data

app_name = 'pipeline'

urlpatterns = [
    path('', views.pipeline_visualization, name='pipeline_visualization_default'),
    path('<int:pipeline_id>/', views.pipeline_visualization, name='pipeline_visualization'),
    path('move-contact/', views.move_pipeline_contact, name='move_pipeline_contact'),
    path('update-stage/', views.update_contact_pipeline_stage, name='update_contact_pipeline_stage'),
    path('debug/', debug_pipeline_data, name='debug_pipeline_data'),
]

    # Add other pipeline-related URLs here as needed
