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
        'id': 'metrics_summary',
        'name': 'Metrics Summary',
        'description': 'People, Churches, Tasks, and Overdue counts',
        'enabled': True,
        'order': 1,
        'size': 'full',  # full, half, quarter
    },
    {
        'id': 'pipeline_distribution',
        'name': 'Pipeline Distribution',
        'description': 'People distribution across pipeline stages',
        'enabled': True,
        'order': 2,
        'size': 'two_thirds',
    },
    {
        'id': 'task_priorities',
        'name': 'Task Priorities',
        'description': 'Distribution of task priorities',
        'enabled': True,
        'order': 3,
        'size': 'one_third',
    },
    {
        'id': 'pending_tasks',
        'name': 'Pending Tasks',
        'description': 'List of upcoming tasks',
        'enabled': True,
        'order': 4,
        'size': 'full',
    },
    {
        'id': 'weekly_summary',
        'name': 'Weekly Summary',
        'description': 'Tasks completed and communications this week',
        'enabled': True,
        'order': 5,
        'size': 'two_thirds',
    },
    {
        'id': 'recent_activity',
        'name': 'Recent Activity',
        'description': 'Recent communications and activity',
        'enabled': True,
        'order': 6,
        'size': 'one_third',
    },
    {
        'id': 'activity_timeline',
        'name': 'Activity Timeline',
        'description': '7-day activity chart',
        'enabled': True,
        'order': 7,
        'size': 'full',
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
            user_id=user.id,
            widget_config={'widgets': DEFAULT_WIDGETS}
        )


def organize_widgets_by_row(widgets):
    """
    Organize widgets into rows based on their sizes.
    
    Args:
        widgets: List of widget configurations
        
    Returns:
        List of rows, each containing widgets that fit together
    """
    rows = []
    current_row = []
    current_row_size = 0
    
    # Size mappings (in terms of 12-column grid)
    size_map = {
        'full': 12,
        'two_thirds': 8,
        'half': 6,
        'one_third': 4,
        'quarter': 3,
    }
    
    for widget in widgets:
        widget_size = size_map.get(widget.get('size', 'full'), 12)
        
        # If this widget would overflow the current row, start a new row
        if current_row_size + widget_size > 12:
            if current_row:
                rows.append(current_row)
            current_row = [widget]
            current_row_size = widget_size
        else:
            current_row.append(widget)
            current_row_size += widget_size
    
    # Add the last row if it has widgets
    if current_row:
        rows.append(current_row)
    
    return rows


def get_widget_css_class(widget_size):
    """
    Get CSS class for widget size.
    
    Args:
        widget_size: Size string
        
    Returns:
        CSS class string
    """
    size_classes = {
        'full': 'col-12',
        'two_thirds': 'col-lg-8',
        'half': 'col-lg-6',
        'one_third': 'col-lg-4',
        'quarter': 'col-lg-3',
    }
    return size_classes.get(widget_size, 'col-12')


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
        widget_id = widget['id']
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
    return update_widget_preferences(user, {
        widget_id: {'enabled': enabled}
    })


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
    widget_map = {w['id']: w for w in widgets}
    
    # Reorder widgets and update order numbers
    reordered_widgets = []
    for i, widget_id in enumerate(widget_order):
        if widget_id in widget_map:
            widget = widget_map[widget_id].copy()
            widget['order'] = i + 1
            reordered_widgets.append(widget)
    
    # Add any widgets not in the order list at the end
    used_ids = set(widget_order)
    for widget in widgets:
        if widget['id'] not in used_ids:
            widget['order'] = len(reordered_widgets) + 1
            reordered_widgets.append(widget)
    
    prefs.set_widget_config(reordered_widgets)
    return prefs