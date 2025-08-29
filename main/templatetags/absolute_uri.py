# main/templatetags/absolute_uri.py
from django import template

register = template.Library()

@register.simple_tag(takes_context=True)
def absolute_uri(context, path_or_fullpath):
    """
    Build an absolute URL from a relative path using the current request.
    Usage:
        {% absolute_uri static('img/social-card.jpg') as url %}
        {% absolute_uri request.get_full_path as canon %}
    """
    request = context.get('request')
    if not request:
        return path_or_fullpath  # fallback; better than nothing
    return request.build_absolute_uri(path_or_fullpath)
