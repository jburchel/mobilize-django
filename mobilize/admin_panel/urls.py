from django.urls import path
from . import views

app_name = 'admin_panel'

urlpatterns = [
    # Office views
    path('offices/', views.OfficeListView.as_view(), name='office_list'),
    path('offices/create/', views.OfficeCreateView.as_view(), name='office_create'),
    path('offices/<int:pk>/', views.OfficeDetailView.as_view(), name='office_detail'),
    path('offices/<int:pk>/update/', views.OfficeUpdateView.as_view(), name='office_update'),
    path('offices/<int:pk>/delete/', views.OfficeDeleteView.as_view(), name='office_delete'),
    
    # Cross-office reporting
    path('reports/cross-office/', views.CrossOfficeReportView.as_view(), name='cross_office_report'),
    
    # User-Office management
    path('offices/<int:office_id>/users/', views.OfficeUserListView.as_view(), name='office_users'),
    path('offices/<int:office_id>/users/add/', views.AddUserToOfficeView.as_view(), name='add_user_to_office'),
    path('offices/<int:office_id>/users/<int:user_id>/remove/', views.RemoveUserFromOfficeView.as_view(), name='remove_user_from_office'),
    path('offices/<int:office_id>/users/<int:user_id>/update-primary/', views.UpdateUserOfficePrimaryView.as_view(), name='update_user_office_primary'),
    
    # User management views
    path('users/', views.UserManagementView.as_view(), name='user_management'),
    path('users/<int:pk>/', views.UserDetailView.as_view(), name='user_detail'),
    path('users/<int:pk>/update/', views.UserUpdateView.as_view(), name='user_update'),
    path('users/<int:pk>/toggle-active/', views.UserToggleActiveView.as_view(), name='user_toggle_active'),
    path('users/<int:user_id>/assign-office/', views.AssignUserToOfficeView.as_view(), name='assign_user_to_office'),
    path('users/<int:user_id>/remove-office/<int:office_id>/', views.RemoveUserFromOfficeView.as_view(), name='remove_user_from_office_direct'),
]
