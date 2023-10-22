from django import template

register = template.Library()


@register.filter
def format_decimal(value, decimal_places=3):
    formatted_value = round(float(value), decimal_places)
    formatted_str = str(formatted_value).rstrip("0").rstrip(".")
    return formatted_str
