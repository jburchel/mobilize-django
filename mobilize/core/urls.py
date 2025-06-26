from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.dashboard_simple, name='dashboard'),
    path('full/', views.dashboard, name='dashboard_full'),
    path('profile/', views.profile, name='profile'),
    path('settings/', views.settings, name='settings'),
    path('reports/', views.reports, name='reports'),
    path('export/<str:report_type>/', views.export_report, name='export_report'),
    path('customize-dashboard/', views.customize_dashboard, name='customize_dashboard'),
]
