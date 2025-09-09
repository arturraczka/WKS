from django import template

register = template.Library()


@register.filter
def dot_to_comma(value):
    return str(value).replace(".", ",")
