from django import template
from mobilize.core.dashboard_widgets import get_widget_css_class

register = template.Library()


@register.filter
def widget_css_class(widget):
    """Template filter to get CSS class for a widget."""
    return get_widget_css_class(widget)
