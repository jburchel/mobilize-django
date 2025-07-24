from django.urls import path
from . import views
from . import debug_views

app_name = "core"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("simple/", views.dashboard_simple, name="dashboard_simple"),
    path("profile/", views.profile, name="profile"),
    path("settings/", views.settings, name="settings"),
    path("settings-debug/", views.settings_debug, name="settings_debug"),
    path("reports/", views.reports, name="reports"),
    path("export/<str:report_type>/", views.export_report, name="export_report"),
    path("customize-dashboard/", views.customize_dashboard, name="customize_dashboard"),
    # Widget layout API endpoints
    path("api/widget-layout/", views.update_widget_layout_api, name="update_widget_layout_api"),
    path("api/widget-resize/", views.resize_widget_api, name="resize_widget_api"),
    path("api/widget-layout-get/", views.get_widget_layout_api, name="get_widget_layout_api"),
    path("db-diagnostic/", views.db_diagnostic, name="db_diagnostic"),
    path("permissions-debug/", views.permissions_debug, name="permissions_debug"),
    path("debug-oauth-uri/", views.debug_oauth_uri, name="debug_oauth_uri"),
    path("test-oauth-minimal/", views.test_oauth_minimal, name="test_oauth_minimal"),
    path("test-oauth-full/", views.test_oauth_full, name="test_oauth_full"),
    path(
        "debug-dashboard-toggle/",
        debug_views.debug_dashboard_toggle,
        name="debug_dashboard_toggle",
    ),
    path(
        "debug-dashboard-minimal/",
        debug_views.debug_dashboard_minimal,
        name="debug_dashboard_minimal",
    ),
]
