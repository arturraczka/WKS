from django import template
import logging

logger = logging.getLogger("django.server")
register = template.Library()


@register.filter
def format_decimal(value, decimal_places=3):
    try:
        formatted_value = round(float(value), decimal_places)
    except TypeError:
        return ""
    formatted_str = str(formatted_value).rstrip("0").rstrip(".")
    return formatted_str
