import logging
import abc

from datetime import date

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from wildlifecompliance.components.main.models import (
    GlobalSettings,
)

from wildlifecompliance.components.licences.models import (
    WildlifeLicence,
)
from wildlifecompliance.components.licences.email import (
    send_licence_renewal_notification,
    send_licence_cancel_notification,
    send_licence_suspend_notification,
    send_licence_reinstate_notification,
    send_licence_surrender_notification,
)
from wildlifecompliance.components.applications.models import (
    Application,
    ApplicationSelectedActivity,
    ApplicationSelectedActivityPurpose,
    ApplicationUserAction,
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
    def request_licence_purpose_list(licence, request):
        '''
        List of licence purposes issued.
        '''
        purposes = None                     # licence purpose list.

        try:
            on_licence_actioner = LicenceActioner(licence)
            purposes = on_licence_actioner.get_latest_purposes_for_request(
                request
            )

        except Exception as e:
            logger.error('ERR request_licence_purpose_list: {0}'.format(e))
            raise Exception('Failed requesting licence purpose list.')

        return purposes

    @staticmethod
    def request_reissue_licence(licence, request):
        '''
        Process request to reissue licence.
        '''
        REISSUE = WildlifeLicence.ACTIVITY_PURPOSE_ACTION_REISSUE
        try:

            with transaction.atomic():

                on_licence_actioner = LicenceActioner(licence)
                on_licence_actioner.apply_action(request, REISSUE)

        except Exception as e:
            logger.error('ERR request_reissue_licence() ID {0}: {1}'.format(
                licence.id, e
            ))
            raise Exception('Failed reissuing licence.')

        return licence

    @staticmethod
    def request_surrender_licence(licence, request):
        '''
        Process request to surrender licence.
        '''
        SURRENDER = WildlifeLicence.ACTIVITY_PURPOSE_ACTION_SURRENDER

        try:

            with transaction.atomic():

                on_licence_actioner = LicenceActioner(licence)
                on_licence_actioner.apply_action(request, SURRENDER)

                purposes = on_licence_actioner.get_actioned_purposes()
                send_licence_surrender_notification(licence, purposes, request)

                # Regenerate licence and save.
                licence.generate_doc()
                application = licence.current_application
                application.licence_document = licence.licence_document
                application.save()

        except Exception as e:
            logger.error('ERR request_surrender_licence() ID {0}: {1}'.format(
                licence.id, e
            ))
            raise Exception('Failed surrendering licence.')

        return licence

    @staticmethod
    def request_cancel_licence(licence, request):
        '''
        Process request to cancel licence.
        '''
        CANCEL = WildlifeLicence.ACTIVITY_PURPOSE_ACTION_CANCEL

        try:

            with transaction.atomic():

                on_licence_actioner = LicenceActioner(licence)
                on_licence_actioner.apply_action(request, CANCEL)

                purposes = on_licence_actioner.get_actioned_purposes()
                send_licence_cancel_notification(licence, purposes, request)

                # Regenerate licence and save.
                licence.generate_doc()
                application = licence.current_application
                application.licence_document = licence.licence_document
                application.save()

        except Exception as e:
            logger.error('ERR request_cancel_licence() ID {0}: {1}'.format(
                licence.id, e
            ))
            raise Exception('Failed cancelling licence.')

        return licence

    @staticmethod
    def request_suspend_licence(licence, request):
        '''
        Suspend licence.
        '''
        SUSPEND = WildlifeLicence.ACTIVITY_PURPOSE_ACTION_SUSPEND

        try:

            with transaction.atomic():

                on_licence_actioner = LicenceActioner(licence)
                on_licence_actioner.apply_action(request, SUSPEND)

                purposes = on_licence_actioner.get_actioned_purposes()
                send_licence_suspend_notification(licence, purposes, request)

                # Regenerate licence and save.
                licence.generate_doc()
                application = licence.current_application
                application.licence_document = licence.licence_document
                application.save()

        except Exception as e:
            logger.error('ERR request_suspend_licence: {0}'.format(e))
            raise Exception('Failed suspending licence.')

        return licence

    @staticmethod
    def request_reinstate_licence(licence, request):
        '''
        Reinstate licence.
        '''
        REINSTATE = WildlifeLicence.ACTIVITY_PURPOSE_ACTION_REINSTATE

        try:

            with transaction.atomic():

                on_licence_actioner = LicenceActioner(licence)
                on_licence_actioner.apply_action(request, REINSTATE)

                purposes = on_licence_actioner.get_actioned_purposes()
                send_licence_reinstate_notification(licence, purposes, request)

                licence.generate_doc()
                application = licence.current_application
                application.licence_document = licence.licence_document
                application.save()

        except Exception as e:
            logger.error('ERR request_reinstate_licence: {0}'.format(e))
            raise Exception('Failed reinstating licence.')

        return licence

    @staticmethod
    def get_activities_list_for(licence, request=None):
        '''
        Get a list of activities for the licence, merged by application per
        licence_activity_id (1 per LicenceActivity).
        '''
        the_list = None
        try:
            on_licence_actioner = LicenceActioner(licence)
            the_list = on_licence_actioner.get_latest_activities_for_request()

        except Exception as e:
            logger.error('ERR get_activities_list_for() ID {0}: {1}'.format(
                licence.id, e
            ))
            raise Exception('Failed getting activities for licence.')

        return the_list

    @staticmethod
    def verify_licence_renewals(request=None):
        '''
        Verifies licences which have purposes about to expire and sends a
        notification the applicant.
        '''
        try:
            today = date.today()

            issued_status = [
                ApplicationSelectedActivityPurpose.PROCESSING_STATUS_ISSUED,
            ]

            # build application ids with renewable purposes.
            apps = ApplicationSelectedActivityPurpose.objects.filter(
                expiry_date__gte=today,
                processing_status__in=issued_status,
                purpose_status__in=ApplicationSelectedActivityPurpose.RENEWABLE
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
                LicenceService.verify_licence_renewal_for(
                    licence_id['licence_id']
                )

        except Exception as e:
            logger.error('ERR verify_licence_renewals: {0}'.format(e))
            raise Exception('Failed verifying licence renewal.')

        return True

    @staticmethod
    def verify_licence_renewal_for(licence_id, request=None):
        '''
        Verifies a licence requiring renewal and send a notification to the
        applicant.
        '''
        try:
            period_days = GlobalSettings.objects.values('value').filter(
                key=GlobalSettings.LICENCE_RENEW_DAYS
            ).first()
            period_days = int(period_days['value'])

            licence = WildlifeLicence.objects.get(
                id=licence_id
            )
            purposes_to_renew = licence.get_purposes_to_renew(period_days)

            # Set selected licence purpose to renew.
            with transaction.atomic():

                for purpose in purposes_to_renew:
                    purpose.sent_renewal = True
                    purpose.save()

            if purposes_to_renew:
                # Send out renewal notice. (only with request)
                send_licence_renewal_notification(
                    licence, purposes_to_renew, request)

        except Exception as e:
            logger.error('ERR verify_licence_renewal_for {0}: {1}'.format(
                licence_id,
                e
            ))
            raise Exception('Failed verifying licence renewal.')

        return True

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
                # Re-generate licence.
                licence.generate_doc()
                application = licence.current_application
                application.licence_document = licence.licence_document
                application.save()
                logger.info(
                    'Licence {0} re-generated with expired purpose.'.format(
                        licence.licence_number,
                    ))

        except Exception as e:
            logger.error('ERR verify_licence_renewal: {0}'.format(e))
            raise Exception('Failed verifying licence renewal.')

        return True


class LicenceActionable(object):
    '''
    An interface for LicenceActioner.
    '''
    __metaclass__ = abc.ABCMeta


class LicenceActioner(LicenceActionable):
    '''
    A representation of a Licence that can be actioned.
    '''
    licence = None                  # Composite licence.
    actioned_purposes = None
    filter_on_action = None

    CANCEL = WildlifeLicence.ACTIVITY_PURPOSE_ACTION_CANCEL
    SUSPEND = WildlifeLicence.ACTIVITY_PURPOSE_ACTION_SUSPEND
    SURRENDER = WildlifeLicence.ACTIVITY_PURPOSE_ACTION_SURRENDER
    RENEW = WildlifeLicence.ACTIVITY_PURPOSE_ACTION_REACTIVATE_RENEW
    REINSTATE = WildlifeLicence.ACTIVITY_PURPOSE_ACTION_REINSTATE
    REISSUE = WildlifeLicence.ACTIVITY_PURPOSE_ACTION_REISSUE

    ACTIVE = ApplicationSelectedActivityPurpose.ACTIVE
    ACTIONS = {
        REINSTATE: ApplicationSelectedActivityPurpose.REINSTATABLE,
        RENEW: ApplicationSelectedActivityPurpose.RENEWABLE,
    }

    def __init__(self, licence):
        super(LicenceActionable, self).__init__()
        self.licence = licence

    def __str__(self):
        return 'LicenceActioner for {0}'.format(self.licence.id)

    @staticmethod
    def get_current_activities_for_application_type(
            application_type, **kwargs):
        """
        Retrieves the current or suspended activities for an
        ApplicationSelectedActivity, filterable by LicenceActivity ID and
        Application.APPLICATION_TYPE in the case of the additional date_filter
        (use Application.APPLICATION_TYPE_SYSTEM_GENERATED for no
        APPLICATION_TYPE filters)
        """
        applications = kwargs.get('applications', Application.objects.none())
        activity_ids = kwargs.get('activity_ids', [])
        activities = None

        date_filter = Application.get_activity_date_filter(
            application_type)

        ACCEPT = ApplicationSelectedActivity.PROCESSING_STATUS_ACCEPTED
        # TODO: date_filter applies expiry_date
        activities = ApplicationSelectedActivity.objects.filter(
            Q(id__in=activity_ids) if activity_ids else
            Q(application_id__in=applications.values_list('id', flat=True)),
            # **date_filter
        ).filter(
            processing_status=ACCEPT
        ).exclude(
            activity_status__in=[
                ApplicationSelectedActivity.ACTIVITY_STATUS_SURRENDERED,
                ApplicationSelectedActivity.ACTIVITY_STATUS_EXPIRED,
                ApplicationSelectedActivity.ACTIVITY_STATUS_CANCELLED,
                ApplicationSelectedActivity.ACTIVITY_STATUS_REPLACED
            ]
        ).distinct()

        a_ids = ApplicationSelectedActivityPurpose.objects.filter(
            # Apply the date filtering on the Purposes.
            selected_activity_id__in=[a.id for a in activities],
            **date_filter
        ).values_list('selected_activity_id', flat=True)
        activities = activities.filter(id__in=a_ids)

        return activities

    def get_actioned_purposes(self):
        '''
        Get a list of purposes which were actioned by this actioner.
        '''
        return self.actioned_purposes

    def set_actioned_purposes(self, purpose_ids_list, selected_activity_id):
        '''
        Set the list of purposes to be actioned by this actioner.
        '''
        ids_list = None
        if purpose_ids_list:
            ids_list = [int(id) for id in purpose_ids_list]

        purposes = [
            p for p in self.licence.get_proposed_purposes_in_applications()
            if p.purpose_status in self.filter_on_action
            and (
                p.purpose.id in ids_list if ids_list else True
            )
            and (
                p.selected_activity_id == int(selected_activity_id)
                if selected_activity_id else True
            )
        ]

        self.actioned_purposes = purposes

    def can_action_purposes(self, purpose_list, activity):
        '''
        Applies a specified action to all licence purposes. For a selected
        licence activity_id and purposes list, the selected activity status
        will not be updated to allow further management of the activity.

        Returns a DICT object containing can_<action> Boolean results of each
        action check.
        '''
        SUSPENDED = ApplicationSelectedActivity.ACTIVITY_STATUS_SUSPENDED
        EXPIRED = ApplicationSelectedActivity.ACTIVITY_STATUS_EXPIRED
        ACCEPTED = ApplicationSelectedActivity.PROCESSING_STATUS_ACCEPTED

        can_action = {
            'licence_activity_id': activity.licence_activity_id,
            'can_amend': False,
            'can_renew': False,
            'can_reactivate_renew': False,
            'can_surrender': False,
            'can_cancel': False,
            'can_suspend': False,
            'can_reissue': False,
            'can_reinstate': False,
        }
        current_date = timezone.now().date()

        # return false for all actions if activity is not in latest licence.
        if not activity.is_in_latest_licence:
            return can_action

        # FIXME: Needs to allow for multiple activity purposes.
        # No action should be available if all of an activity's purposes are in
        # open applications check if there are any purposes in open
        # applications (i.e. can action) return false for all actions if no
        # purposes are still actionable.
        # activity_purposes = activity.purposes.values_list('id', flat=True)
        # if not len(list((set(activity_purposes) - set(purpose_list)))) > 0:
        #     return can_action

        # multiple activity purposes can exist. No action is available if
        # an open licence amendment application for activity purpose exist.
        if activity.has_licence_amendment():
            return can_action

        # can_amend is true if the activity can be included in a Amendment
        # Application Extra exclude for SUSPENDED due to get_current_activities
        # for_application_type intentionally not excluding these as part of the
        # default queryset.
        current = \
            self.get_current_activities_for_application_type(
                Application.APPLICATION_TYPE_AMENDMENT,
                activity_ids=[activity.id]
            ).exclude(activity_status=SUSPENDED).count() > 0

        can_action['can_amend'] = current

        # can_renew is true if the activity can be included in a Renewal
        # Application Extra exclude for SUSPENDED due to get_current_activities
        # for_application_type intentionally not excluding these as part of the
        # default queryset.
        current = self.get_current_activities_for_application_type(
            Application.APPLICATION_TYPE_RENEWAL,
            activity_ids=[activity.id]
        ).exclude(activity_status=SUSPENDED).count() > 0

        renewable = [
            p for p in activity.proposed_purposes.all() if p.is_renewable
        ]
        # can_renew when activity is current with renewable purposes.
        can_action['can_renew'] = current and len(renewable)

        # can_reactivate_renew is true if the activity has expired, excluding
        # if it was surrendered or cancelled
        current = ApplicationSelectedActivity.objects.filter(
            Q(id=activity.id, expiry_date__isnull=False),
            Q(expiry_date__lt=current_date) |
            Q(activity_status=EXPIRED)
        ).filter(
            processing_status=ACCEPTED
        ).exclude(
            activity_status__in=[
                ApplicationSelectedActivity.ACTIVITY_STATUS_SURRENDERED,
                ApplicationSelectedActivity.ACTIVITY_STATUS_CANCELLED,
                ApplicationSelectedActivity.ACTIVITY_STATUS_REPLACED
            ]
        ).count() > 0

        can_action['can_reactivate_renew'] = current

        # can_surrender is true if the activity is CURRENT or SUSPENDED
        # disable if there are any open applications to maintain licence
        # sequence data integrity.
        current = self.get_current_activities_for_application_type(
            Application.APPLICATION_TYPE_SYSTEM_GENERATED,
            activity_ids=[activity.id]
        ).exclude(activity_status=SUSPENDED).count() > 0

        surrenderable = [
            p for p in activity.proposed_purposes.all() 
            if p.is_issued and p.is_active
        ]

        can_action['can_surrender'] = current and len(surrenderable)

        # can_cancel is true if the activity is CURRENT or SUSPENDED disable if
        # there are any open applications to maintain licence sequence data
        # integrity.
        current = self.get_current_activities_for_application_type(
            Application.APPLICATION_TYPE_SYSTEM_GENERATED,
            activity_ids=[activity.id]
        ).exclude(activity_status=SUSPENDED).count() > 0

        cancelable = [
            p for p in activity.proposed_purposes.all()
            if p.is_issued and p.is_active
        ]

        can_action['can_cancel'] = current and len(cancelable)

        # can_suspend is true if the activity_status is CURRENT Extra exclude
        # for SUSPENDED due to get_current_activities_for_application_type
        # intentionally not excluding these as part of the default queryset
        current = self.get_current_activities_for_application_type(
            Application.APPLICATION_TYPE_SYSTEM_GENERATED,
            activity_ids=[activity.id]
        ).exclude(activity_status=SUSPENDED).count() > 0

        suspendable = [
            p for p in activity.proposed_purposes.all()
            if p.is_issued and p.is_active
        ]

        can_action['can_suspend'] = current and len(suspendable)

        # can_reissue is true if the activity can be included in a Reissue
        # Application Extra exclude for SUSPENDED due to
        # get_current_activities_for_application_type intentionally not
        # excluding these as part of the default queryset disable if there are
        # any open applications to maintain licence sequence data integrity.
        # if not purpose_list:
        if not activity.has_licence_amendment():
            current = self.get_current_activities_for_application_type(
                Application.APPLICATION_TYPE_REISSUE,
                activity_ids=[activity.id]
            ).exclude(
                activity_status__in=[SUSPENDED]
            ).count() > 0

            reissuable = [
                p for p in activity.proposed_purposes.all() if p.is_issued
            ]

            can_action['can_reissue'] = current and len(reissuable)

        # can_reinstate is true if the activity has not yet expired and is
        # currently SUSPENDED, CANCELLED or SURRENDERED.
        # current = self.get_current_activities_for_application_type(
        #     Application.APPLICATION_TYPE_RENEWAL,
        #     activity_ids=[activity.id]
        # ).exclude(activity_status=SUSPENDED).count() > 0

        reinstatable = [
            p for p in activity.proposed_purposes.all() if p.is_reinstatable
        ]
        can_action['can_reinstate'] = len(reinstatable)

        return can_action

    def get_latest_activities_for_request(self, request=None):
        '''
        Gets a list of current selected licence activities available on this
        licence for an action request. The list is a merged set of new and
        amended activities which can be actioned.

        :return a list of actionable current selected licence activities.
        '''
        # latest_activities = self.licence.latest_activities

        # include = [
        #     ApplicationSelectedActivityPurpose.PURPOSE_STATUS_SUSPENDED,
        #     ApplicationSelectedActivityPurpose.PURPOSE_STATUS_CURRENT,
        #     ApplicationSelectedActivityPurpose.PURPOSE_STATUS_DEFAULT,
        # ]

        licence_purposes = [
            p for p in self.licence.get_purposes_in_sequence()
            if p.is_issued
            # if p.purpose_status in include and p.is_issued
        ]
        latest_activities = []
        for purpose in licence_purposes:
            latest_activities.append(purpose.selected_activity)

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

        if self.licence.is_latest_in_category:
            purposes_in_open_applications = list(
                self.licence.get_purposes_in_open_applications())
        else:
            purposes_in_open_applications = None

        sequence = 0
        for activity in latest_activities:

            if purposes_in_open_applications or\
                    purposes_in_open_applications == []:

                activity_can_action = self.can_action_purposes(
                    purposes_in_open_applications,
                    activity,
                )

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

            sequence = sequence + 1

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
                    'expiry_date': '\n'.join([
                        '{}'.format(p.expiry_date.strftime(
                            '%d/%m/%Y') if p.expiry_date else '')
                        for p in activity.proposed_purposes.all()
                        if p.is_issued
                    ]),
                    'activity_purpose_names_and_status': '\n'.join([
                        '{} ({})'.format(p.purpose.name, p.purpose_status)
                        for p in activity.proposed_purposes.all()
                        if p.is_issued
                    ]),
                    'can_action':
                        {
                            'licence_activity_id':
                                activity.licence_activity_id,
                            'can_renew': activity_can_action['can_renew'],
                            'can_amend': activity_can_action['can_amend'],
                            'can_surrender':
                                activity_can_action['can_surrender'],
                            'can_cancel': activity_can_action['can_cancel'],
                            'can_suspend': activity_can_action['can_suspend'],
                            'can_reissue': activity_can_action['can_reissue'],
                            'can_reinstate':
                                activity_can_action['can_reinstate'],
                        },
                    'sequence': sequence,
                }

        merged_activities_list = merged_activities.values()

        return merged_activities_list

    def get_latest_purposes_for_request(self, request):
        '''
        Gets a list of current selected licence purposes available on this
        licence for an action request. The list excludes licence purposes under
        review.

        :param client request must include an 'action' to be performed and an
        'selected_activity_id' to be actioned.

        :return a list of current selected licence purposes for the activity.
        '''
        ISSUED = ApplicationSelectedActivityPurpose.PROCESSING_STATUS_ISSUED

        purposes = None
        action = request.GET.get('action', None)
        activity_id = request.GET.get('selected_activity_id', None)
        self.filter_on_action = self.ACTIONS.get(action, self.ACTIVE)

        purposes = ApplicationSelectedActivityPurpose.objects.filter(
            selected_activity_id=activity_id,
            processing_status=ISSUED,
            purpose_status__in=self.filter_on_action
        ).distinct()

        return purposes

    def apply_action(self, request, action):
        '''
        Applies a specified action to all licence purposes. For a selected
        licence activity_id and purposes list, the selected activity status
        will not be updated to allow further management of the activity.
        '''
        purpose_ids_list = request.data.get('purpose_ids_list', None)
        selected_activity_id = request.data.get('selected_activity_id', None)

        def _log_selected_activity_request(_activity, _action):
            '''
            Log applied action on application.
            '''
            selected_application = _activity.application

            selected_application.log_user_action(_action.format(
                    _activity.licence_activity.name), request)

            # Log entry for organisation
            if selected_application.org_applicant:
                selected_application.org_applicant.log_user_action(
                    _action.format(_activity.licence_activity.name), request)

            elif selected_application.proxy_applicant:
                selected_application.proxy_applicant.log_user_action(
                    _action.format(_activity.licence_activity.name), request)

            else:
                selected_application.submitter.log_user_action(
                    _action.format(_activity.licence_activity.name), request)

        '''
        Action process.
        1. Validate;
        2. Build purpose list;
        3. Action selected_activity_id; or
        4. Action licence when no selected_activity_id;
        5. Re-generate the licence and save.
        '''
        if action not in [
            self.RENEW, self.SURRENDER, self.CANCEL,
            self.SUSPEND, self.REINSTATE, self.REISSUE
        ]:
            raise ValidationError('Selected action is not valid')

        # Set purposes to be actioned on this actioner.
        self.filter_on_action = self.ACTIONS.get(action, self.ACTIVE)
        self.set_actioned_purposes(purpose_ids_list, selected_activity_id)

        action_licence = True
        selected_user_action = None
        selected_activities = self.licence.latest_activities

        if selected_activity_id:
            action_licence = False
            selected_activities = [
                a for a in selected_activities
                if a.id == int(selected_activity_id)
            ]

        for selected_activity in selected_activities:

            # build and order purposes on selected activity.
            if action_licence:
                purpose_ids_list = [
                    p.purpose.id
                    for p in selected_activity.proposed_purposes.all()
                    if p.is_issued
                ]
            purpose_ids_list = list(set(purpose_ids_list))
            purpose_ids_list.sort()

            selected_activity.updated_by = request.user

            if action == self.RENEW:
                # selected_activity.reactivate_renew(request)
                pass

            elif action == self.SURRENDER:
                selected_activity.surrender_purposes(purpose_ids_list)
                selected_user_action =\
                    ApplicationUserAction.ACTION_SURRENDER_LICENCE_

            elif action == self.CANCEL:
                selected_activity.cancel_purposes(purpose_ids_list)
                selected_user_action =\
                    ApplicationUserAction.ACTION_CANCEL_LICENCE_

            elif action == self.SUSPEND:
                selected_activity.suspend_purposes(purpose_ids_list)
                selected_user_action =\
                    ApplicationUserAction.ACTION_SUSPEND_LICENCE_

            elif action == self.REINSTATE:
                selected_activity.reinstate_purposes(purpose_ids_list)
                selected_user_action =\
                    ApplicationUserAction.ACTION_REINSTATE_LICENCE_

            elif action == self.REISSUE:
                selected_activity.reissue_purposes(purpose_ids_list)
                selected_user_action =\
                    ApplicationUserAction.ACTION_REISSUE_LICENCE_

            # Log action on the application for selected_activity
            _log_selected_activity_request(
                selected_activity,
                selected_user_action,
            )
