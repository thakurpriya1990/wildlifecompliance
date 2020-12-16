from __future__ import unicode_literals

import logging

from django.contrib.auth.models import Group
from ledger.accounts.models import EmailUser
from wildlifecompliance import settings
from wildlifecompliance.components.applications.models import ActivityPermissionGroup
from wildlifecompliance.components.users.models import (
        CompliancePermissionGroup, 
        ComplianceManagementUserPreferences,
        )
from confy import env

DEBUG = env('DEBUG', False)
BASIC_AUTH = env('BASIC_AUTH', False)

logger = logging.getLogger(__name__)
# logger = logging

def belongs_to(user, group_name):
    """
    Check if the user belongs to the given group.
    :param user:
    :param group_name:
    :return:
    """
    return user.groups.filter(name=group_name).exists()


def belongs_to_list(user, group_names):
    """
    Check if the user belongs to the given list of groups.
    :param user:
    :param list_of_group_names:
    :return:
    """
    return user.groups.filter(name__in=group_names).exists()


def is_model_backend(request):
    # Return True if user logged in via single sign-on (i.e. an internal)
    logger.debug(
        'helpers.is_model_backend(): {0}'.format(
            request.session.get('_auth_user_backend')
        ))
    return 'ModelBackend' in request.session.get('_auth_user_backend')


def is_email_auth_backend(request):
    # Return True if user logged in via social_auth (i.e. an external user
    # signing in with a login-token)
    return 'EmailAuth' in request.session.get('_auth_user_backend')


def is_wildlifecompliance_admin(request):
    return request.user.is_authenticated() and \
           is_model_backend(request) and \
           in_dbca_domain(request) and \
           (
               request.user.has_perm('wildlifecompliance.system_administrator') or
               request.user.is_superuser or
               request.user.groups.filter(name__in=['Wildlife Compliance Admin - Licensing', 'Wildlife Compliance Admin - Compliance']).exists()
           )


def is_wildlifecompliance_payment_officer(request):
    '''
    Check user for request has payment officer permissions.

    :return: boolean
    '''
    PAYMENTS_GROUP_NAME = 'Wildlife Compliance - Payment Officers'

    is_payment_officer = request.user.is_authenticated() and \
        is_model_backend(request) and \
        in_dbca_domain(request) and \
        (
            request.user.groups.filter(name__in=[PAYMENTS_GROUP_NAME]).exists()
        )

    return is_payment_officer


def in_dbca_domain(request):
    user = request.user
    domain = user.email.split('@')[1]
    if domain in settings.DEPT_DOMAINS:
        if not user.is_staff:
            # hack to reset department user to is_staff==True, if the user
            # logged in externally (external departmentUser login defaults to
            # is_staff=False)
            user.is_staff = True
            user.save()
        return True
    return False


def is_departmentUser(request):
    return request.user.is_authenticated() and (is_model_backend(
        request) or settings.ALLOW_EMAIL_ADMINS) and in_dbca_domain(request)


def is_reception(request):
    '''
    A check whether request is performed by Wildlife Licensing Reception.
    '''
    from wildlifecompliance.components.licences.models import (
            WildlifeLicenceReceptionEmail,
    )

    is_reception_email = WildlifeLicenceReceptionEmail.objects.filter(
        email=request.user.email
    ).exists()

    return request.user.is_authenticated() and is_reception_email


def is_customer(request):
    return request.user.is_authenticated() and is_email_auth_backend(request)


def is_internal(request):
    if DEBUG and BASIC_AUTH:
        return True
    else:
        return is_departmentUser(request)

def is_officer(request):
    licence_officer_groups = [group.name for group in ActivityPermissionGroup.objects.filter(
            permissions__codename__in=['organisation_access_request',
                                       'licensing_officer',
                                       'issuing_officer',
                                       'assessor',
                                       'return_curator',
                                       'payment_officer'])]
    return request.user.is_authenticated() and (belongs_to_list(
        request.user, licence_officer_groups) or request.user.is_superuser)

def prefer_compliance_management(request):
    if request.user.is_authenticated():
        preference_qs, created = ComplianceManagementUserPreferences.objects.get_or_create(email_user=request.user)
        if preference_qs and preference_qs.prefer_compliance_management and is_compliance_management_readonly_user(request):
            return True
    else:
        return False

def is_compliance_internal_user(request):
    compliance_groups = [group.name for group in CompliancePermissionGroup.objects.filter(
            permissions__codename__in=['volunteer',
                                       'triage_call_email',
                                       'issuing_officer',
                                       'officer',
                                       'infringement_notice_coordinator',
                                       # 'branch_manager',
                                       'manager'])]
    return request.user.is_authenticated() and (belongs_to_list(
        request.user, compliance_groups) or request.user.is_superuser)

def is_compliance_management_readonly_user(request):
    compliance_group = CompliancePermissionGroup.objects.get(permissions__codename='compliance_management_readonly')
    return request.user.is_authenticated() and (belongs_to(request.user, compliance_group) or request.user.is_superuser)

def is_able_to_view_sanction_outcome_pdf(user):
    compliance_groups = [group.name for group in CompliancePermissionGroup.objects.filter(
        permissions__codename__in=['officer',
                                   'infringement_notice_coordinator',
                                   'manager'])]
    return user.is_authenticated() and (belongs_to_list(
        user, compliance_groups) or user.is_superuser)


def get_all_officers():
    licence_officer_groups = ActivityPermissionGroup.objects.filter(
            permissions__codename__in=['organisation_access_request',
                                       'licensing_officer',
                                       'issuing_officer',
                                       'assessor',
                                       'return_curator',
                                       'payment_officer'])
    return EmailUser.objects.filter(
        groups__name__in=licence_officer_groups)
