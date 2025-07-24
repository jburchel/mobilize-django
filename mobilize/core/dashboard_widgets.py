"""
Dashboard widget configuration and customization utilities.

This module provides functionality for users to customize their dashboard
by selecting which widgets to display and in what order.
"""

from django.db import models
from django.conf import settings


# Default widget configuration
DEFAULT_WIDGETS = [
    {
        "id": "metrics_summary",
        "name": "Metrics Summary",
        "description": "People, Churches, Tasks, and Overdue counts",
        "enabled": True,
        "order": 1,
        "size": "full",  # full, half, quarter
        "columns": 4,  # 1-4 columns width
        "row": 0,
        "position": 0,
    },
    {
        "id": "pipeline_distribution",
        "name": "Pipeline Distribution",
        "description": "People distribution across pipeline stages",
        "enabled": True,
        "order": 2,
        "size": "full",
        "columns": 4,
        "row": 1,
        "position": 0,
    },
    {
        "id": "task_priorities",
        "name": "Task Priorities",
        "description": "Distribution of task priorities",
        "enabled": True,
        "order": 3,
        "size": "one_third",
        "columns": 1,
        "row": 2,
        "position": 0,
    },
    {
        "id": "pending_tasks",
        "name": "Pending Tasks",
        "description": "List of upcoming tasks",
        "enabled": True,
        "order": 4,
        "size": "full",
        "columns": 4,
        "row": 3,
        "position": 0,
    },
    {
        "id": "weekly_summary",
        "name": "Weekly Summary",
        "description": "Tasks completed and communications this week",
        "enabled": True,
        "order": 5,
        "size": "two_thirds",
        "columns": 2,
        "row": 2,
        "position": 1,
    },
    {
        "id": "recent_activity",
        "name": "Recent Activity",
        "description": "Recent communications and activity",
        "enabled": True,
        "order": 6,
        "size": "one_third",
        "columns": 1,
        "row": 2,
        "position": 2,
    },
    {
        "id": "activity_timeline",
        "name": "Activity Timeline",
        "description": "7-day activity chart",
        "enabled": True,
        "order": 7,
        "size": "full",
        "columns": 4,
        "row": 4,
        "position": 0,
    },
]


def get_user_dashboard_config(user):
    """
    Get dashboard configuration for a user.

    Args:
        user: User instance

    Returns:
        DashboardPreference instance
    """
    from mobilize.core.models import DashboardPreference

    try:
        return DashboardPreference.objects.get(user_id=user.id)
    except DashboardPreference.DoesNotExist:
        # Create default configuration
        return DashboardPreference.objects.create(
            user_id=user.id, widget_config={"widgets": DEFAULT_WIDGETS}
        )


def organize_widgets_by_row(widgets):
    """
    Organize widgets into rows based on their grid positions and column widths.

    Args:
        widgets: List of widget configurations

    Returns:
        List of rows, each containing widgets that fit together
    """
    if not widgets:
        return []

    # Sort widgets by row first, then by position within row
    sorted_widgets = sorted(
        widgets, key=lambda w: (w.get("row", 0), w.get("position", 0))
    )

    # Group widgets by row
    rows = {}
    for widget in sorted_widgets:
        row_num = widget.get("row", 0)
        if row_num not in rows:
            rows[row_num] = []
        rows[row_num].append(widget)

    # Convert to list of rows ordered by row number
    return [rows[row_num] for row_num in sorted(rows.keys())]


def get_widget_css_class(widget):
    """
    Get CSS class for widget size based on columns.

    Args:
        widget: Widget configuration dictionary

    Returns:
        CSS class string
    """
    columns = widget.get("columns", 4)

    # Map columns to Bootstrap grid classes (4 columns = full width)
    column_classes = {
        1: "col-lg-3",  # 1/4 width
        2: "col-lg-6",  # 1/2 width
        3: "col-lg-9",  # 3/4 width
        4: "col-12",  # full width
    }

    return column_classes.get(columns, "col-12")


def update_widget_preferences(user, widget_updates):
    """
    Update user's widget preferences.

    Args:
        user: User instance
        widget_updates: Dictionary of widget updates
    """
    prefs = get_user_dashboard_config(user)
    widgets = prefs.get_widget_config()

    # Update widgets based on the provided updates
    for widget in widgets:
        widget_id = widget["id"]
        if widget_id in widget_updates:
            widget.update(widget_updates[widget_id])

    prefs.set_widget_config(widgets)
    return prefs


def toggle_widget(user, widget_id, enabled):
    """
    Toggle a widget on/off for a user.

    Args:
        user: User instance
        widget_id: ID of the widget to toggle
        enabled: Boolean indicating if widget should be enabled
    """
    return update_widget_preferences(user, {widget_id: {"enabled": enabled}})


def reorder_widgets(user, widget_order):
    """
    Reorder widgets for a user.

    Args:
        user: User instance
        widget_order: List of widget IDs in desired order
    """
    prefs = get_user_dashboard_config(user)
    widgets = prefs.get_widget_config()

    # Create a mapping of widget ID to widget config
    widget_map = {w["id"]: w for w in widgets}

    # Reorder widgets and update order numbers
    reordered_widgets = []
    for i, widget_id in enumerate(widget_order):
        if widget_id in widget_map:
            widget = widget_map[widget_id].copy()
            widget["order"] = i + 1
            reordered_widgets.append(widget)

    # Add any widgets not in the order list at the end
    used_ids = set(widget_order)
    for widget in widgets:
        if widget["id"] not in used_ids:
            widget["order"] = len(reordered_widgets) + 1
            reordered_widgets.append(widget)

    prefs.set_widget_config(reordered_widgets)
    return prefs


def update_widget_layout(user, layout_data):
    """
    Update widget layout positions and sizes.

    Args:
        user: User instance
        layout_data: Dictionary containing layout information
                    Format: {"widget_id": {"row": 0, "position": 1, "columns": 2}}
    """
    prefs = get_user_dashboard_config(user)
    widgets = prefs.get_widget_config()

    # Update widgets with new layout data
    for widget in widgets:
        widget_id = widget["id"]
        if widget_id in layout_data:
            layout = layout_data[widget_id]
            widget.update(
                {
                    "row": layout.get("row", widget.get("row", 0)),
                    "position": layout.get("position", widget.get("position", 0)),
                    "columns": layout.get("columns", widget.get("columns", 4)),
                }
            )

            # Update legacy size field for backward compatibility
            columns = widget.get("columns", 4)
            size_map = {1: "quarter", 2: "half", 3: "three_quarters", 4: "full"}
            widget["size"] = size_map.get(columns, "full")

    prefs.set_widget_config(widgets)
    return prefs


def resize_widget(user, widget_id, columns):
    """
    Resize a specific widget.

    Args:
        user: User instance
        widget_id: ID of the widget to resize
        columns: Number of columns (1-4)
    """
    if columns not in [1, 2, 3, 4]:
        raise ValueError("Columns must be between 1 and 4")

    return update_widget_layout(user, {widget_id: {"columns": columns}})
