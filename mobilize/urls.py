"""
URL configuration for mobilize project.
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings # Expected one or more symbol names after "import"
from django.conf.urls.static import static
from django.views.generic import RedirectView



urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('mobilize.core.urls')),
    path('contacts/', include('mobilize.contacts.urls')),
    path('churches/', include('mobilize.churches.urls')),
    path('communications/', include('mobilize.communications.urls')),
    path('tasks/', include('mobilize.tasks.urls')),
    path('auth/', include('mobilize.authentication.urls')),
    path('admin-panel/', include('mobilize.admin_panel.urls')),
    path('pipeline/', include('mobilize.pipeline.urls')),
]

# Add debug toolbar URLs in development
if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [
        path('__debug__/', include(debug_toolbar.urls)),
    ]
    
    # Serve media files in development
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
