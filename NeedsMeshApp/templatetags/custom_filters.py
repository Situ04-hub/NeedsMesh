from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter
def filter_status(queryset, status):
    if not queryset or not hasattr(queryset, 'filter'):
        return []
    return queryset.filter(status=status)

@register.filter
def add_class(value, arg):
    """Adds a CSS class to a form field without overwriting existing attributes."""
    if not hasattr(value, 'as_widget'):
        return value
    attrs = value.field.widget.attrs.copy()
    existing_class = attrs.get('class', '')
    if existing_class:
        if arg not in existing_class:
            attrs['class'] = f"{existing_class} {arg}"
    else:
        attrs['class'] = arg
    return value.as_widget(attrs=attrs)

@register.filter
def subtract(value, arg):
    """Subtracts arg from value."""
    try:
        return int(value) - int(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def percentage(value, arg):
    """Calculates percentage: (value / arg) * 100."""
    try:
        return (int(value) / int(arg)) * 100
    except (ValueError, ZeroDivisionError, TypeError):
        return 0

@register.simple_tag
def urgency_badge(urgency):
    """Renders a styled urgency pill based on level."""
    try:
        u = int(float(urgency))
    except (ValueError, TypeError):
        u = 0
    
    label = f"Priority {u}"
    if u >= 9: label = "CRITICAL"
    elif u >= 7: label = "HIGH"
    
    return mark_safe(f'<span class="urgency-pill urgency-{u} shadow-sm">{label}</span>')