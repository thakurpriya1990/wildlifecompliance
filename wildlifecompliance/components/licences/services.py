import logging

from datetime import date
from django.db import transaction

from wildlifecompliance.components.licences.models import (
    WildlifeLicence,
)
from wildlifecompliance.components.licences.email import (
    send_licence_renewal_notification,
)
from wildlifecompliance.components.applications.models import (
    Application,
    ApplicationSelectedActivityPurpose,
)

logger = logging.getLogger(__name__)
logging.disable(logging.NOTSET)
logger.setLevel(logging.DEBUG)


class LicenceService(object):
    """
    Services available for Wildlife Licence.
    """

    def __init__(self):
        pass

    @staticmethod
    def get_activities_list_for(licence, request=None):
        '''
        Get a list of activities for the licence, merged by application per
        licence_activity_id (1 per LicenceActivity).
        '''
        latest_activities = licence.latest_activities

        # new_activities = [
        #     a for a in latest_activities
        #     if a.application.application_type in [
        #         'new_activity', 'new_licence']
        # ]

        # merge_ids = [
        #     a.id for a in latest_activities
        #     if a.application.application_type in [
        #         'amend_activity', 'renew_activity', 'system_generated'] and
        #     a.licence_activity_id in [
        #         n.licence_activity_id for n in new_activities
        #     ]
        # ]

        new_ids = [
            a.id for a in latest_activities
        ]

        merged_activities = {}

        if licence.is_latest_in_category:
            purposes_in_open_applications = list(
                licence.get_purposes_in_open_applications())
        else:
            purposes_in_open_applications = None

        for activity in latest_activities:

            if purposes_in_open_applications or\
                    purposes_in_open_applications == []:
                activity_can_action = activity.can_action(
                    purposes_in_open_applications)

            else:
                activity_can_action = {
                    'licence_activity_id': activity.licence_activity_id,
                    'can_renew': False,
                    'can_amend': False,
                    'can_surrender': False,
                    'can_cancel': False,
                    'can_suspend': False,
                    'can_reissue': False,
                    'can_reinstate': False,
                }

            # Check if a record for the licence_activity_id already exists, if
            # not, add.
            if activity.id in new_ids:
                issued_list = [
                    p for p in activity.proposed_purposes.all() if p.is_issued]

                if not len(issued_list):
                    continue

                merged_activities[activity] = {
                    'id': activity.id,
                    'licence_activity_id': activity.licence_activity_id,
                    'activity_name_str': activity.licence_activity.name,
                    'issue_date': activity.get_issue_date(),
                    'start_date': activity.get_start_date(),
                    'expiry_date': '\n'.join(['{}'.format(
                        p.expiry_date.strftime('%d/%m/%Y') if p.expiry_date else '')
                        for p in activity.proposed_purposes.all() if p.is_issued]),
                    'activity_purpose_names_and_status': '\n'.join(['{} ({})'.format(
                        p.purpose.name, activity.get_activity_status_display())
                        for p in activity.proposed_purposes.all() if p.is_issued]),
                    'can_action':
                        {
                            'licence_activity_id': activity.licence_activity_id,
                            'can_renew': activity_can_action['can_renew'],
                            'can_amend': activity_can_action['can_amend'],
                            'can_surrender': activity_can_action['can_surrender'],
                            'can_cancel': activity_can_action['can_cancel'],
                            'can_suspend': activity_can_action['can_suspend'],
                            'can_reissue': activity_can_action['can_reissue'],
                            'can_reinstate': activity_can_action['can_reinstate'],
                        }
                }

        merged_activities_list = merged_activities.values()

        return merged_activities_list

    @staticmethod
    def verify_expired_licences(request=None):
        '''
        Verifies licences requiring renewing by expiring licence purposes after
        their expiry date and sending out a renewal notification.
        '''
        try:
            # raise Exception('LicenceService not implemented')

            today = date.today()

            current_status = [
                ApplicationSelectedActivityPurpose.PURPOSE_STATUS_DEFAULT,
                ApplicationSelectedActivityPurpose.PURPOSE_STATUS_CURRENT,
            ]

            issued_status = [
                ApplicationSelectedActivityPurpose.PROCESSING_STATUS_ISSUED,
            ]

            # build application ids with expired purposes.
            apps = ApplicationSelectedActivityPurpose.objects.filter(
                expiry_date__lt=today,
                purpose_status__in=current_status,
                processing_status__in=issued_status,
            ).select_related(
                'selected_activity__application_id'
            ).distinct()

            app_ids = apps.values('selected_activity__application_id')

            # get unique licences for applications.
            licence_ids = Application.objects.values(
                'licence_id',
                ).filter(
                    id__in=app_ids,
                ).distinct()

            for licence_id in licence_ids:
                # for each licence id verify if renewal required.
                if not licence_id['licence_id']:
                    continue
                LicenceService.verify_expired_licence_for(
                    licence_id['licence_id']
                )

        except Exception as e:
            logger.error('ERR verify_licence_renewal: {0}'.format(e))
            raise Exception('Failed verifying licence renewal.')

        return True

    @staticmethod
    def verify_expired_licence_for(licence_id, request=None):
        '''
        Verifies licences requiring renewing by expiring licence purposes after
        their expiry date and sending out a renewal notification.
        '''
        EXPIRED = ApplicationSelectedActivityPurpose.PURPOSE_STATUS_EXPIRED
        try:
            # raise Exception('LicenceService not implemented')
            licence = WildlifeLicence.objects.get(
                id=licence_id
            )
            purposes_to_expire = licence.get_purposes_to_expire()

            # Set selected licence purpose to expired.
            with transaction.atomic():
                for purpose in purposes_to_expire:
                    purpose.purpose_status = EXPIRED
                    purpose.save()

            if purposes_to_expire:
                # Send out renewal notice. (only with request)
                send_licence_renewal_notification(
                    licence, purposes_to_expire, request)

                # Re-generate licence.
                licence.generate_doc()
                logger.info(
                    'Licence {0} re-generate with expired purpose.'.format(
                        licence.licence_number,
                    ))

        except Exception as e:
            logger.error('ERR verify_licence_renewal: {0}'.format(e))
            raise Exception('Failed verifying licence renewal.')

        return True
