from django import template
from django.utils.timesince import timesince

register = template.Library()


@register.filter
def humanize_duration(timedelta_obj):
    if timedelta_obj is None:
        return "N/A"

    days = timedelta_obj.days
    hours, remainder = divmod(timedelta_obj.seconds, 3600)
    minutes, _ = divmod(remainder, 60)

    if days > 0:
        return (
            f"{days} day{'s' if days > 1 else ''}, {hours} hr{'s' if hours > 1 else ''}"
        )
    elif hours > 0:
        return f"{hours} hr{'s' if hours > 1 else ''}, {minutes} min{'s' if minutes > 1 else ''}"
    return f"{minutes} min{'s' if minutes > 1 else ''}"
