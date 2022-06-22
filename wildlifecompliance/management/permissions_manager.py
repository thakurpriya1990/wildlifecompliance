import importlib
import logging
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import Group, ContentType, Permission
from django.db import transaction, models
# from ledger.accounts.utils import get_app_label
from wildlifecompliance.components.licences.models import LicenceActivity
from wildlifecompliance.components.applications.models import ActivityPermissionGroup
#from wildlifecompliance.components.users.models import CompliancePermissionGroup
from wildlifecompliance.components.main.models import Region, District

from ledger.accounts.models import EmailUser

logger = logging.getLogger(__name__)


def get_app_label():
    try:
        return settings.SYSTEM_APP_LABEL
    except AttributeError:
        return ''

class PermissionCollector(object):

    MODULE_NAME = 'permissions'

    @classmethod
    def iter_app_configs(cls):
        for app in settings.INSTALLED_APPS:
            try:
                module = importlib.import_module('%s.%s' % (app, cls.MODULE_NAME))
            except ImportError:
                continue

            yield app, module

    @classmethod
    def default_objects(cls):
        """
        Collects up all of the custom configurations from the app_dir/permissions.py
        modules for each app in INSTALLED_APPS and returns a dictionary of the
        form:
            object_name: {object_spec}
        """
        collected_objects = {}

        for app, module in cls.iter_app_configs():
            module_objects = getattr(module, cls.COLLECTION_SOURCE, {})
            # Detect and exclude duplicate names
            if module_objects:
                for obj in module_objects:
                    object_name = obj['name'] if type(obj) == dict else obj
                    obj_data = obj if type(obj) == dict else module_objects[obj]
                    if object_name in collected_objects:
                        raise RuntimeError('Two {} created with the ' +
                                           'same name: {}'.format(cls.COLLECTION_SOURCE, object_name))
                    collected_objects[object_name] = obj_data

        return collected_objects


class CustomPermissionCollector(PermissionCollector):

    COLLECTION_SOURCE = 'CUSTOM_GROUP_PERMISSIONS'

    def get_or_create_models(self):
        """
        A mapping of permission name to permission instance. If the permission does not exist, it is created.
        """
        default_permissions = self.default_objects()
        actual = {}

        for permission_name, config in default_permissions.items():

            try:
                content_type = ContentType.objects.get(
                    model=config['model'],
                    app_label=config['app_label'],
                )
            except ObjectDoesNotExist:
                logger.error("Content Type {app_label} - {model} not found for permission: {codename}".format(
                    app_label=config['app_label'],
                    model=config['model'],
                    codename=permission_name,
                ))
                continue

            permission, created = Permission.objects.get_or_create(
                name=config['name'],
                content_type_id=content_type.id,
                codename=permission_name
            )
            if created:
                logger.info("Created custom permission: %s" % (permission_name))

            # Only assign permissions to default groups if they didn't exist in the database before.
            # Don't re-add permissions that were revoked by admins manually!
            if 'default_groups' in config and created:
                for group_name in config['default_groups']:
                    try:
                        group = Group.objects.get(name=group_name)
                    except ObjectDoesNotExist:
                        logger.error("Cannot assign permission {permission_name} to a non-existent group: {group}".format(
                            permission_name=permission_name,
                            group=group_name
                        ))
                        continue

                    group.permissions.add(permission)
                    logger.info("Assigned permission {permission_name} to group: {group}".format(
                        permission_name=permission_name,
                        group=group_name
                    ))

            actual[permission_name] = permission

        return actual


class CustomGroupCollector(PermissionCollector):

    COLLECTION_SOURCE = 'PERMISSION_GROUPS'

    def get_or_create_group(self, group_name, config, activity=None):
        created = None
        if settings.GROUP_PREFIX and settings.GROUP_PREFIX not in group_name:
            group_name = "{prefix} - {name}".format(
                prefix=settings.GROUP_PREFIX,
                name=group_name
            )
        group = ActivityPermissionGroup.objects.filter(name=group_name).first()
        if not group:
            base_group = Group.objects.filter(name=group_name).first()
            if base_group:
                group = created = ActivityPermissionGroup.objects.create(
                    group_ptr_id=base_group.id,
                    name=base_group.name
                )
            else:
                # Check if groups with the same permissions (but a different name) already exist.
                # Do not re-create groups that have been manually re-named by admins.
                if config['permissions']:
                    groups_by_permission = ActivityPermissionGroup.objects.filter(permissions__codename__in=config['permissions'])
                    if activity is not None:
                        groups_by_permission = groups_by_permission.filter(
                            licence_activities__id=activity.id)
                    group = groups_by_permission.first()
                if not group:
                    group = created = ActivityPermissionGroup.objects.create(name=group_name)

        if created:
            logger.info("Created custom group: %s" % (group_name))

        if config['permissions'] and created:
            for permission_codename in config['permissions']:
                try:
                    permission = Permission.objects.get(
                        codename=permission_codename
                    )

                    group.permissions.add(permission)
                    logger.info("Assigned permission {permission_name} to group: {group}".format(
                        permission_name=permission_codename,
                        group=group_name
                    ))
                except ObjectDoesNotExist:
                    logger.error("Cannot assign non-existent permission {permission_name} to: {group}".format(
                        permission_name=permission_codename,
                        group=group_name
                    ))
                    raise 

        return group

    def get_or_create_models(self):
        """
        A mapping of group name to group instance. If the group does not exist, it is created.
        """
        default_groups = self.default_objects()
        actual = {}

        try:

            for group_name, config in default_groups.items():

                if config['per_activity']:
                    for activity in LicenceActivity.objects.all():
                        activity_group_name = "{}: {}".format(group_name, activity.name)
                        group = self.get_or_create_group(activity_group_name, config, activity)
                        group.licence_activities.add(activity)
                else:
                    group = self.get_or_create_group(group_name, config)

        except BaseException as e:
            logger.error("Creating Group mapping for {0}: {1}".format(
                group_name, e))

        return actual


#class CompliancePermissionCollector(PermissionCollector):
#
#    COLLECTION_SOURCE = 'COMPLIANCE_GROUP_PERMISSIONS'
#
#    def get_or_create_models(self):
#        """
#        A mapping of permission name to permission instance. If the permission does not exist, it is created.
#        """
#        default_permissions = self.default_objects()
#        actual = {}
#
#        try:
#            for permission_name, config in default_permissions.items():
#
#                try:
#                    content_type = ContentType.objects.get(
#                        model=config['model'],
#                        app_label=config['app_label'],
#                    )
#                except ObjectDoesNotExist:
#                    logger.error("Content Type {app_label} - {model} not found for permission: {codename}".format(
#                        app_label=config['app_label'],
#                        model=config['model'],
#                        codename=permission_name,
#                    ))
#                    continue
#
#                permission, created = Permission.objects.get_or_create(
#                    name=config['name'],
#                    content_type_id=content_type.id,
#                    codename=permission_name
#                )
#                if created:
#                    logger.info("Created custom permission: %s" % (permission_name))
#
#                # Only assign permissions to default groups if they didn't exist in the database before.
#                # Don't re-add permissions that were revoked by admins manually!
#                if 'default_groups' in config and created:
#                    for group_name in config['default_groups']:
#                        try:
#                            group = Group.objects.get(name=group_name)
#                        except ObjectDoesNotExist:
#                            logger.error("Cannot assign permission {permission_name} to a non-existent group: {group}".format(
#                                permission_name=permission_name,
#                                group=group_name
#                            ))
#                            continue
#
#                        group.permissions.add(permission)
#                        logger.info("Assigned permission {permission_name} to group: {group}".format(
#                            permission_name=permission_name,
#                            group=group_name
#                        ))
#
#                actual[permission_name] = permission
#
#        except BaseException as e:
#            logger.error("Creating permissions for {0}: {1}".format(
#                permission_name, e))
#
#        return actual
#
#
#class ComplianceGroupCollector(PermissionCollector):
#
#    COLLECTION_SOURCE = 'COMPLIANCE_PERMISSION_GROUPS'
#
#    def get_or_create_group(self, group_name, config, region=None, district=None):
#        created = None
#        if settings.COMPLIANCE_GROUP_PREFIX and settings.COMPLIANCE_GROUP_PREFIX not in group_name:
#            group_name = "{prefix} - {name}".format(
#                prefix=settings.COMPLIANCE_GROUP_PREFIX,
#                name=group_name
#            )
#        group = CompliancePermissionGroup.objects.filter(name=group_name).first()
#        if not group:
#            base_group = Group.objects.filter(name=group_name).first()
#            if base_group:
#                group = created = CompliancePermissionGroup.objects.create(
#                    group_ptr_id=base_group.id,
#                    name=base_group.name
#                )
#            else:
#                # Check if groups with the same permissions (but a different name) already exist.
#                # Do not re-create groups that have been manually re-named by admins.
#                #existing_groups = None
#                if config['permissions']:
#                    groups_by_permission = CompliancePermissionGroup.objects.filter(permissions__codename__in=config['permissions'])
#                    if region or district:
#                        groups_by_permission = groups_by_permission.filter(region=region, district=district)
#                    group = groups_by_permission.first()
#                    #if region or district:
#                        #existing_groups = groups_by_permission.filter(region=region, district=district)
#                if not group:
#                    group, created = CompliancePermissionGroup.objects.get_or_create(name=group_name, region=region, district=district)
#
#        if created:
#            logger.info("Created compliance group: %s" % (group_name))
#
#        if config['permissions'] and created:
#            for permission_codename in config['permissions']:
#                try:
#                    permission = Permission.objects.get(
#                        codename=permission_codename
#                    )
#
#                    group.permissions.add(permission)
#                    logger.info("Assigned permission {permission_name} to group: {group}".format(
#                        permission_name=permission_codename,
#                        group=group_name
#                    ))
#                except ObjectDoesNotExist:
#                    logger.error("Cannot assign non-existent permission {permission_name} to: {group}".format(
#                        permission_name=permission_codename,
#                        group=group_name
#                    ))
#                    raise 
#
#        return group
#
#    def get_or_create_models(self):
#        """
#        A mapping of group name to group instance. If the group does not exist, it is created.
#        """
#        default_groups = self.default_objects()
#        actual = {}
#
#        try:
#
#            for group_name, config in default_groups.items():
#                if config['per_district']:
#                    #for region_district in RegionDistrict.objects.all():
#                    #    compliance_group_name = "{}: {}".format(group_name, region_district.display_name())
#                    #    group = self.get_or_create_group(compliance_group_name, config, region_district)
#                    #    group.region_district.add(region_district)
#                    for region in Region.objects.all():
#                        compliance_group_name = "{}: {}".format(group_name, region.name)
#                        group = self.get_or_create_group(compliance_group_name, config, region=region, district=None)
#                    for district in District.objects.all():
#                        compliance_group_name = "{}: {}".format(group_name, district.name)
#                        group = self.get_or_create_group(compliance_group_name, config, region=None, district=district)
#                else:
#                    group = self.get_or_create_group(group_name, config)
#    
#        except BaseException as e:
#            logger.error("Creating mapping group to district for {0}: {1}".format(
#                group_name, e))
#
#        return actual
#

class CollectorManager(object):

    def __init__(self):
        if not get_app_label():
            raise Exception("SYSTEM_APP_LABEL is missing from settings.py or is blank!\
            \nPlease set it to the global app_label of the current system (e.g. 'wildlifecompliance').")
        with transaction.atomic():
            logger.info("Verifying presence of custom group permissions in the database...")
            CustomPermissionCollector().get_or_create_models()
            logger.info("Verifying presence of custom groups in the database...")
            CustomGroupCollector().get_or_create_models()
            logger.info("Finished collecting custom groups and permissions.")
            #logger.info("Verifying presence of compliance group permissions in the database...")
            #CompliancePermissionCollector().get_or_create_models()
            #logger.info("Verifying presence of compliance groups in the database...")
            #ComplianceGroupCollector().get_or_create_models()
            #logger.info("Finished collecting compliance groups and permissions.")

class PermissionUser(object):
    def __init__(self, a_user):
        self._user = a_user

    def has_wildlifelicenceactivity_perm(self, permission_codename, licence_activity_id):
        app_label = get_app_label()
        group_queryset = self._user.groups.filter(
            permissions__codename__in=permission_codename if isinstance(
                permission_codename, (list, models.query.QuerySet)
            ) else [permission_codename],
            activitypermissiongroup__licence_activities__id__in=licence_activity_id if isinstance(
                licence_activity_id, (list, models.query.QuerySet)
            ) else [licence_activity_id]
        )
        if app_label:
            group_queryset = group_queryset.filter(permissions__content_type__app_label=app_label)
        return group_queryset.count()

    def get_wildlifelicence_permission_group(self, permission_codename, activity_id=None, first=True):
        app_label = get_app_label()
        qs = self._user.groups.filter(
            permissions__codename=permission_codename
        )
        if activity_id is not None:
            qs = qs.filter(
                activitypermissiongroup__licence_activities__id__in=activity_id if isinstance(
                    activity_id, (list, models.query.QuerySet)
                ) else [activity_id]
            )
        if app_label:
            qs = qs.filter(permissions__content_type__app_label=app_label)
        return qs.first() if first else qs

