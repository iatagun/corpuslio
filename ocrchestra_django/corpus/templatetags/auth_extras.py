from django import template
from django.contrib.auth.models import Group 

register = template.Library() 

@register.filter(name='has_group') 
def has_group(user, group_name):
    try:
        group = Group.objects.get(name=group_name) 
        return True if group in user.groups.all() else False
    except Group.DoesNotExist:
        return False


@register.filter(name='can_upload')
def can_upload(user):
    """Check if user can upload documents (Academician, Developer, or Superuser)."""
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return user.groups.filter(name__in=['Academician', 'Developer']).exists()
