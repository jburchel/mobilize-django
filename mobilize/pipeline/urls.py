from django.urls import path
from . import views

app_name = 'pipeline'

urlpatterns = [
    path('', views.pipeline_visualization, name='pipeline_visualization_default'),
    path('<int:pipeline_id>/', views.pipeline_visualization, name='pipeline_visualization'),
    path('move-contact/', views.move_pipeline_contact, name='move_pipeline_contact'),
]

    # Add other pipeline-related URLs here as needed
