from django import template

register = template.Library()

@register.simple_tag(takes_context=True)
def url_replace(context, **kwargs):
    """
    Return an encoded string of query parameters, replacing any keys
    provided in kwargs.
    Example usage: {% url_replace page=page_obj.next_page_number %}
    """
    query = context['request'].GET.copy()
    for key, value in kwargs.items():
        query[key] = value
    return query.urlencode()
