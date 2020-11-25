from django.template import Library
from django.utils import timezone
from datetime import timedelta

from wildlifecompliance import helpers as wildlifecompliance_helpers
from wildlifecompliance.components.main.models import SystemMaintenance

register = Library()


@register.simple_tag(takes_context=True)
def is_customer(context):
    request = context['request']
    return wildlifecompliance_helpers.is_customer(request)

@register.simple_tag(takes_context=True)
def is_officer(context):
    request = context['request']
    return wildlifecompliance_helpers.is_officer(request)

@register.simple_tag(takes_context=True)
def is_wildlifecompliance_admin(context):
    # checks if user is an AdminUser
    request = context['request']
    return wildlifecompliance_helpers.is_wildlifecompliance_admin(request)


@register.simple_tag(takes_context=True)
def is_wildlifecompliance_payment_officer(context):
    request = context['request']
    is_ok = wildlifecompliance_helpers.is_wildlifecompliance_payment_officer(
        request
    )
    return is_ok


@register.simple_tag(takes_context=True)
def is_internal(context):
    # checks if user is a departmentuser and logged in via single sign-on
    request = context['request']
    return wildlifecompliance_helpers.is_internal(request)

@register.simple_tag(takes_context=True)
def is_model_backend(context):
    # Return True if user logged in via single sign-on (or False via
    # social_auth i.e. an external user signing in with a login-token)
    request = context['request']
    return wildlifecompliance_helpers.is_model_backend(request)

@register.simple_tag(takes_context=True)
def is_compliance_internal_user(context):
    request = context['request']
    return wildlifecompliance_helpers.is_compliance_internal_user(request)

@register.simple_tag(takes_context=True)
def prefer_compliance_management(context):
    request = context['request']
    return wildlifecompliance_helpers.prefer_compliance_management(request)

@register.simple_tag(takes_context=True)
def is_compliance_management_readonly_user(context):
    request = context['request']
    return wildlifecompliance_helpers.is_compliance_management_readonly_user(request)


@register.simple_tag()
def system_maintenance_due():
    '''
    Returns True (actually a time str), if within <timedelta hours> of system
    maintenance due datetime.
    '''
    import pytz
    from django.conf import settings

    tz = pytz.timezone(settings.TIME_ZONE)
    now = timezone.now()  # returns UTC time
    qs = SystemMaintenance.objects.filter(start_date__gte=now - timedelta(
        minutes=1)
    )
    if qs:
        obj = qs.earliest('start_date')
        if now >= obj.start_date - timedelta(
            hours=settings.SYSTEM_MAINTENANCE_WARNING
        ) and now <= obj.start_date + timedelta(minutes=1):
            # display time in local timezone
            return '{0} - {1} (Duration: {2} mins)'.format(
                obj.start_date.astimezone(tz=tz).ctime(),
                obj.end_date.astimezone(tz=tz).ctime(),
                obj.duration()
            )

    return False


@register.simple_tag()
def system_maintenance_can_start():
    '''
    Returns True if current datetime is within 1 minute past scheduled
    start_date.
    '''
    from django.utils import timezone
    from datetime import timedelta
    from wildlifecompliance.components.main.models import SystemMaintenance

    now = timezone.now()  # returns UTC time
    qs = SystemMaintenance.objects.filter(
        start_date__gte=now - timedelta(minutes=1)
    )
    if qs:
        obj = qs.earliest('start_date')
        if now >= obj.start_date \
                and now <= obj.start_date + timedelta(minutes=1):
            return True

    return False

