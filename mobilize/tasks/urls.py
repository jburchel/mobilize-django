from django.urls import path
from . import views

app_name = "tasks"

urlpatterns = [
    # Task views
    path("", views.TaskListView.as_view(), name="task_list"),
    path("create/", views.TaskCreateView.as_view(), name="task_create"),
    path("<int:pk>/", views.TaskDetailView.as_view(), name="task_detail"),
    path("<int:pk>/update/", views.TaskUpdateView.as_view(), name="task_update"),
    path("<int:pk>/delete/", views.TaskDeleteView.as_view(), name="task_delete"),
    path("<int:pk>/complete/", views.TaskCompleteView.as_view(), name="task_complete"),
    # Bulk operations
    path("bulk/delete/", views.bulk_delete_tasks, name="bulk_delete"),
    path(
        "bulk/update-status/", views.bulk_update_task_status, name="bulk_update_status"
    ),
    path(
        "bulk/update-priority/",
        views.bulk_update_task_priority,
        name="bulk_update_priority",
    ),
    path("bulk/assign-user/", views.bulk_assign_task_user, name="bulk_assign_user"),
    path(
        "bulk/assign-office/", views.bulk_assign_task_office, name="bulk_assign_office"
    ),
    path("bulk/complete/", views.bulk_complete_tasks, name="bulk_complete"),
    # Task category views
    path("categories/", views.TaskCategoryListView.as_view(), name="category_list"),
    path(
        "categories/create/",
        views.TaskCategoryCreateView.as_view(),
        name="category_create",
    ),
    path(
        "categories/<int:pk>/",
        views.TaskCategoryDetailView.as_view(),
        name="category_detail",
    ),
    path(
        "categories/<int:pk>/update/",
        views.TaskCategoryUpdateView.as_view(),
        name="category_update",
    ),
    path(
        "categories/<int:pk>/delete/",
        views.TaskCategoryDeleteView.as_view(),
        name="category_delete",
    ),
]
