import sys
import abc
import requests
import logging

from decimal import Decimal

from wildlifecompliance import settings

from ledger.checkout.utils import calculate_excl_gst

from wildlifecompliance.components.licences.models import (
    LicencePurpose,
    LicenceSpecies,
)

from wildlifecompliance.components.applications.models import (
    Application,
    ApplicationFormDataRecord,
    ApplicationStandardCondition,
    ApplicationCondition,
    LicenceActivity,
)

logger = logging.getLogger(__name__)
logging.disable(logging.NOTSET)
logger.setLevel(logging.DEBUG)


class ApplicationService(object):
    """
    Services available for a Licence Application.
    """

    def __init__(self):
        pass

    @staticmethod
    def get_licence_species(species_list):
        """
        Gets species details.
        """
        requested_species = []
        for specie in species_list:
            details = []
            details = LicenceSpecies.objects.values('data').get(
                specie_id=specie)
            requested_species.append(details['data'])

        return requested_species

    @staticmethod
    def verify_licence_species():
        """
        Verifies species name identifier is current with the TSC database.
        """
        purposes = LicencePurpose.objects.all()
        species_list = []
        for purpose in purposes:
            species_list += purpose.get_group_species_list
            species_list += purpose.get_section_species_list

        tsc_service = TSCSpecieService(TSCSpecieCall())
        tsc_service.set_strategy(TSCSpecieXReferenceCall())

        species_set = set(species_list)     # create a list of unique values.
        species_list = (list(species_set))

        logger.info('ApplicationService: Verifying species.')

        for specie in species_list:
            tsc_service.search_taxon(specie)

        logger.info(
            'ApplicationService: Completed. Verified {0} species.'.format(
                len(species_list)))

    @staticmethod
    def verify_licence_specie_id(specie_id):
        """
        Verifies species name identifier is current with the TSC database.
        """
        tsc_service = TSCSpecieService(TSCSpecieCall())
        tsc_service.set_strategy(TSCSpecieXReferenceCall())
        logger.info('ApplicationService: Verifying species.')
        tsc_service.search_taxon(specie_id)
        logger.info('ApplicationService: Completed. Verified 1 specie.')

    @staticmethod
    def calculate_fees(application, data_source):
        """
        Calculates fees for Application and Licence. Application fee is
        calculated with the base fee in all instances to allow for adjustments
        made from form attributes. Previous attributes settings are not saved.
        Licence fees cannot be adjusted with form attributes.
        """
        return get_dynamic_schema_attributes(application, data_source)['fees']

    @staticmethod
    def get_product_lines(application):
        """
        Gets the application fee product lines to be charged through checkout.
        """
        return ApplicationFeePolicy.get_fee_product_lines_for(application)

    @staticmethod
    def process_form(
            request,
            application,
            form_data,
            action=ApplicationFormDataRecord.ACTION_TYPE_ASSIGN_VALUE):
        """
        Creates an application from Form attributes based on admin schema
        definition.
        """
        do_process_form(
            request,
            application,
            form_data,
            action=ApplicationFormDataRecord.ACTION_TYPE_ASSIGN_VALUE)

    @staticmethod
    def render_defined_conditions(application, form_data):
        """
        Checks for Standard Conditions defined on the application schema. 
        Field answers can trigger the creation of standard conditions for an
        application.
        """
        do_render_defined_conditions(application, form_data)

    @staticmethod
    def render_defined_inspections(application, form_data):
        """
        Checks for Inspections defined on the application schema. 
        Field answers can trigger the creation of an Inspection for an
        application.
        """
        do_render_defined_conditions(application, form_data)

    @staticmethod
    def update_dynamic_attributes(application):
        """
        Updates application attributes based on admin schema definition.
        """
        do_update_dynamic_attributes(application)

    def __str__(self):
        return 'ApplicationService'


"""
NOTE: This section for objects relate to Application Form rendering.
"""


class ApplicationAttributeRenderer(object):

    def __init__(self, application, data_source):
        self._application = application
        self._data_source = data_source

    def parse_component(
            self,
            component,
            schema_name,
            adjusted_by_fields,
            activity):

        if set(['PromptInspection']).issubset(component):
            # TODO: set ispection flag for activity and application.
            pass

    def render(self):

        for selected_activity in self._application.activities:
            schema_fields = self._application.get_schema_fields_for_purposes(
                selected_activity.purposes.values_list('id', flat=True)
            )

            # Adjustments based on selected options (radios and checkboxes)
            adjusted_by_fields = {}
            for form_data_record in self._data_source:
                try:
                    # Retrieve dictionary of fields from a model instance
                    data_record = form_data_record.__dict__
                except AttributeError:
                    # If a raw form data (POST) is supplied, form_data_record
                    # is a key
                    data_record = self._data_source[form_data_record]

                schema_name = data_record['schema_name']
                if schema_name not in schema_fields:
                    continue
                schema_data = schema_fields[schema_name]

                if 'options' in schema_data:
                    for option in schema_data['options']:
                        # Only modifications if the current option is selected
                        if option['value'] != data_record['value']:
                            continue
                        self.parse_component(
                            component=option,
                            schema_name=schema_name,
                            adjusted_by_fields=adjusted_by_fields,
                            activity=selected_activity
                        )

                # If this is a checkbox - skip unchecked ones
                elif data_record['value'] == 'on':
                    self.parse_component(
                        component=schema_data,
                        schema_name=schema_name,
                        adjusted_by_fields=adjusted_by_fields,
                        activity=selected_activity
                    )


def do_process_form(
        request,
        application,
        form_data,
        action=ApplicationFormDataRecord.ACTION_TYPE_ASSIGN_VALUE):
    from wildlifecompliance.components.applications.utils import \
            MissingFieldsException
    can_edit_officer_comments = request.user.has_perm(
        'wildlifecompliance.licensing_officer'
    )
    can_edit_assessor_comments = request.user.has_perm(
        'wildlifecompliance.assessor'
    )
    can_edit_comments = can_edit_officer_comments \
        or can_edit_assessor_comments
    can_edit_deficiencies = request.user.has_perm(
        'wildlifecompliance.licensing_officer'
    )

    if action == ApplicationFormDataRecord.ACTION_TYPE_ASSIGN_COMMENT and\
            not can_edit_comments and not can_edit_deficiencies:
        raise Exception(
            'You are not authorised to perform this action!')

    is_draft = form_data.pop('__draft', False)
    visible_data_tree = application.get_visible_form_data_tree(
        form_data.items())
    required_fields = application.required_fields
    missing_fields = []

    for field_name, field_data in form_data.items():
        schema_name = field_data.get('schema_name', '')
        instance_name = field_data.get('instance_name', '')
        component_type = field_data.get('component_type', '')
        value = field_data.get('value', '')
        officer_comment = field_data.get('officer_comment', '')
        assessor_comment = field_data.get('assessor_comment', '')
        deficiency = field_data.get('deficiency_value', '')
        activity_id = field_data.get('licence_activity_id', '')
        purpose_id = field_data.get('licence_purpose_id', '')
        component_attribute = field_data.get('component_attribute', '')

        if ApplicationFormDataRecord.INSTANCE_ID_SEPARATOR in field_name:
            [parsed_schema_name, parsed_instance_name] = field_name.split(
                ApplicationFormDataRecord.INSTANCE_ID_SEPARATOR
            )
            schema_name = schema_name if schema_name \
                else parsed_schema_name
            instance_name = instance_name if instance_name \
                else parsed_instance_name

        try:
            visible_data_tree[instance_name][schema_name]
        except KeyError:
            continue

        form_data_record = ApplicationFormDataRecord.objects.filter(
            application_id=application.id,
            field_name=field_name,
            licence_activity_id=activity_id,
            licence_purpose_id=purpose_id,
        ).first()

        SPECIES = ApplicationFormDataRecord.COMPONENT_TYPE_SELECT_SPECIES
        if not form_data_record:
            form_data_record = ApplicationFormDataRecord.objects.create(
                application_id=application.id,
                field_name=field_name,
                schema_name=schema_name,
                instance_name=instance_name,
                component_type=component_type,
                licence_activity_id=activity_id,
                licence_purpose_id=purpose_id,
                component_attribute=component_attribute,
            )
        # Species list may not exist in last save because the component has
        # been copied from an amendment. Save new list for species component.
        elif form_data_record.component_type == SPECIES\
                and not form_data_record.component_attribute:
            form_data_record.component_attribute = component_attribute

        if action == ApplicationFormDataRecord.ACTION_TYPE_ASSIGN_VALUE:
            if not is_draft and not value \
                    and schema_name in required_fields:
                missing_item = {'field_name': field_name}
                missing_item.update(required_fields[schema_name])
                missing_fields.append(missing_item)
                continue
            form_data_record.value = value
        elif action == \
                ApplicationFormDataRecord.ACTION_TYPE_ASSIGN_COMMENT:
            if can_edit_officer_comments:
                form_data_record.officer_comment = officer_comment
            if can_edit_assessor_comments:
                form_data_record.assessor_comment = assessor_comment
            if can_edit_deficiencies:
                form_data_record.deficiency = deficiency
        form_data_record.save()

    if action == ApplicationFormDataRecord.ACTION_TYPE_ASSIGN_VALUE:
        do_update_dynamic_attributes(application)
        for existing_field in ApplicationFormDataRecord.objects.filter(
                application_id=application.id):
            if existing_field.field_name not in form_data.keys():
                existing_field.delete()

    if missing_fields:
        raise MissingFieldsException(
            [{'name': item['field_name'], 'label': '{label}'.format(
                label=item['label']
            )} for item in missing_fields]
        )


def do_render_defined_conditions(application, data_source):

    def parse_component(
            component,
            schema_name,
            adjusted_by_fields,
            activity):

        if set(['StandardCondition']).issubset(component):
            condition = ApplicationStandardCondition.objects.filter(
                code=component['StandardCondition'],
                obsolete=False).first()
            if condition:
                ApplicationCondition.objects.create(
                    standard_condition=condition,
                    is_rendered=True,
                    standard=True,
                    application=application,
                    licence_activity=LicenceActivity.objects.get(
                        id=activity.licence_activity_id),
                    return_type=condition.return_type)

    for selected_activity in application.activities:
        schema_fields = application.get_schema_fields_for_purposes(
            selected_activity.purposes.values_list('id', flat=True)
        )

        ApplicationCondition.objects.filter(
            application_id=application.id,
            licence_activity_id=selected_activity.licence_activity_id,
            is_rendered=True
        ).delete()

        # Adjustments based on selected options (radios and checkboxes)
        adjusted_by_fields = {}
        for form_data_record in data_source:
            try:
                # Retrieve dictionary of fields from a model instance
                data_record = form_data_record.__dict__
            except AttributeError:
                # If a raw form data (POST) is supplied, form_data_record
                # is a key
                data_record = data_source[form_data_record]

            schema_name = data_record['schema_name']
            if schema_name not in schema_fields:
                continue
            schema_data = schema_fields[schema_name]

            if 'options' in schema_data:
                for option in schema_data['options']:
                    # Only modifications if the current option is selected
                    if option['value'] != data_record['value']:
                        continue
                    parse_component(
                        component=option,
                        schema_name=schema_name,
                        adjusted_by_fields=adjusted_by_fields,
                        activity=selected_activity
                    )

            # If this is a checkbox - skip unchecked ones
            elif data_record['value'] == 'on':
                parse_component(
                    component=schema_data,
                    schema_name=schema_name,
                    adjusted_by_fields=adjusted_by_fields,
                    activity=selected_activity
                )


def get_dynamic_schema_attributes(application, data_source):

    fee_policy = ApplicationFeePolicy.get_fee_policy_for(application)
    if not data_source:  # No form data set fee from application fee.
        fee_policy.set_application_fee()
    dynamic_attributes = fee_policy.get_dynamic_attributes()

    def parse_modifiers(
            dynamic_attributes,
            component,
            schema_name,
            adjusted_by_fields,
            activity
            ):

        def increase_fee(fees, field, amount):
            fees[field] += amount
            fees[field] = fees[field] if fees[field] >= 0 else 0
            return True

        fee_modifier_keys = {
            'IncreaseLicenceFee': 'licence',
            'IncreaseApplicationFee': 'application',
        }
        increase_limit_key = 'IncreaseTimesLimit'
        try:
            increase_count = adjusted_by_fields[schema_name]
        except KeyError:
            increase_count = adjusted_by_fields[schema_name] = 0

        # Does this component / selected option enable the inspection
        # requirement?
        try:
            # If at least one component has a positive value - require
            # inspection for the entire activity.
            if component['InspectionRequired']:
                dynamic_attributes['activity_attributes'][activity][
                    'is_inspection_required'] = True
        except KeyError:
            pass

        if increase_limit_key in component:
            max_increases = int(component[increase_limit_key])
            if increase_count >= max_increases:
                return

        adjustments_performed = sum(key in component and increase_fee(
            dynamic_attributes['fees'],
            field,
            component[key]
        ) and increase_fee(
            dynamic_attributes['activity_attributes'][activity]['fees'],
            field,
            component[key]
        ) for key, field in fee_modifier_keys.items())

        if adjustments_performed:
            adjusted_by_fields[schema_name] += 1

    for selected_activity in application.activities:
        schema_fields = application.get_schema_fields_for_purposes(
            selected_activity.purposes.values_list('id', flat=True)
        )
        dynamic_attributes['activity_attributes'][selected_activity] = {
            'is_inspection_required': False,
            'fees': selected_activity.base_fees,
        }

        # Adjust fees based on selected options (radios and checkboxes)
        adjusted_by_fields = {}
        for form_data_record in data_source:
            try:
                # Retrieve dictionary of fields from a model instance
                data_record = form_data_record.__dict__
            except AttributeError:
                # If a raw form data (POST) is supplied, form_data_record
                # is a key
                data_record = data_source[form_data_record]

            schema_name = data_record['schema_name']
            if schema_name not in schema_fields:
                continue
            schema_data = schema_fields[schema_name]

            if 'options' in schema_data:
                for option in schema_data['options']:
                    # Only consider fee modifications if the current option
                    # is selected.
                    if option['value'] != data_record['value']:
                        continue
                    parse_modifiers(
                        dynamic_attributes=dynamic_attributes,
                        component=option,
                        schema_name=schema_name,
                        adjusted_by_fields=adjusted_by_fields,
                        activity=selected_activity
                    )

            # If this is a checkbox - skip unchecked ones
            elif data_record['value'] == 'on':
                parse_modifiers(
                    dynamic_attributes=dynamic_attributes,
                    component=schema_data,
                    schema_name=schema_name,
                    adjusted_by_fields=adjusted_by_fields,
                    activity=selected_activity
                )

    return dynamic_attributes


def do_update_dynamic_attributes(application):
    """ Update application and activity attributes based on selected JSON
        schema options.
    """
    if application.processing_status not in [
            Application.PROCESSING_STATUS_DRAFT,
            Application.PROCESSING_STATUS_AWAITING_APPLICANT_RESPONSE,
            Application.PROCESSING_STATUS_UNDER_REVIEW,
    ]:
        return

    dynamic_attributes = get_dynamic_schema_attributes(
        application,
        application.data)

    # Update application and licence fees
    fees = dynamic_attributes['fees']
    application.application_fee = fees['application']
    application.save()

    # Save any parsed per-activity modifiers
    for selected_activity, field_data in \
            dynamic_attributes['activity_attributes'].items():

        fees = field_data.pop('fees', {})
        selected_activity.licence_fee = fees['licence']
        selected_activity.application_fee = fees['application']

        # Check when under review for changes in fee amount.
        # Application fees can also be adjusted by internal officer.
        UNDER_REVIEW = Application.PROCESSING_STATUS_UNDER_REVIEW
        if application.processing_status == UNDER_REVIEW\
            and fees['application']\
                > selected_activity.base_fees['application']:
            selected_activity.application_fee = fees['application'] \
                - selected_activity.base_fees['application']

        # Check for refunds to Application Amendment, Renewals and Requested
        # Amendment Fees.
        REQUEST_AMEND = Application.CUSTOMER_STATUS_AMENDMENT_REQUIRED
        if application.application_type in [
            Application.APPLICATION_TYPE_AMENDMENT,
            Application.APPLICATION_TYPE_RENEWAL,
        ] or application.customer_status == REQUEST_AMEND:

            # set fee to zero when refund exists.
            if fees['application']\
                    < selected_activity.base_fees['application']:
                selected_activity.application_fee = Decimal(0.0)

        # Adjustments to Licence Fees
        # No Fee is required for Amendment but if application fee adjustment
        # exist then pay this with licence fee.
        if application.application_type in [
                Application.APPLICATION_TYPE_AMENDMENT]:
            selected_activity.licence_fee = Decimal(0.0)

        for field, value in field_data.items():
            setattr(selected_activity, field, value)
            selected_activity.save()


"""
NOTE: Section for objects relating to the calculation of Application Fees.
"""


class ApplicationFeePolicy(object):
    """
    A Payment Policy Interface for Licence Applications.
    """
    __metaclass__ = abc.ABCMeta

    @staticmethod
    def get_fee_policy_for(application):

        AMEND = Application.APPLICATION_TYPE_AMENDMENT
        RENEW = Application.APPLICATION_TYPE_RENEWAL
        NEW = Application.APPLICATION_TYPE_NEW_LICENCE
        # New Activity is set for multiple activities on application.
        NEW_ACTIVITY = Application.APPLICATION_TYPE_ACTIVITY

        get_policy = {
            AMEND: AmendApplicationFeePolicy(application),
            RENEW: RenewApplicationFeePolicy(application),
            NEW: NewApplicationFeePolicy(application),
            NEW_ACTIVITY: NewApplicationFeePolicy(application),
        }
        policy = get_policy.get(
            application.application_type, NewApplicationFeePolicy(application))

        return policy

    @staticmethod
    def get_fee_product_lines_for(application):
        """
        Gets the checkout product lines for this application which inlcudes
        fee for both the application and licence activities.
        """
        product_lines = []

        # application.
        activities_with_fees = [
            a for a in application.activities if a.application_fee > 0]

        for activity in activities_with_fees:
            product_lines.append({
                'ledger_description': '{} (Application Fee)'.format(
                    activity.licence_activity.name),
                'quantity': 1,
                'price_incl_tax': str(activity.application_fee),
                'price_excl_tax': str(calculate_excl_gst(
                    activity.application_fee)),
                'oracle_code': ''
            })

        # licence activities.
        activities_with_fees = [
            a for a in application.activities if a.licence_fee > 0]

        for activity in activities_with_fees:
            product_lines.append({
                'ledger_description': '{} (Licence Fee)'.format(
                    activity.licence_activity.name),
                'quantity': 1,
                'price_incl_tax': str(activity.licence_fee),
                'price_excl_tax': str(calculate_excl_gst(
                        activity.licence_fee)),
                'oracle_code': ''
            })

        return product_lines

    @abc.abstractmethod
    def get_dynamic_attributes(self):
        """
        Gets a new application fee based on attributes set.
        """
        pass

    @abc.abstractmethod
    def set_application_fee(self):
        """
        Sets the application fee from what was previously saved on the model.
        """
        pass


class AmendApplicationFeePolicy(ApplicationFeePolicy):
    """
    Amendment Application maintains the status of the previous application.
    Allows applicant to change the application status after a licence has been
    issued.

    Note: No refunds are provided.
    """
    def __init__(self, application):
        self._application = application
        self.init_dynamic_attributes()

    def set_application_fee(self):
        """
        Set Application fee from the saved model.
        """
        application_fees = Application.calculate_base_fees(
                self._application.licence_purposes.values_list('id', flat=True)
            )['application']

        if self._application.application_fee > 0:
            application_fees = self._application.application_fee

        self._dynamic_attributes = {
            'fees': {
                'application': application_fees,
                'licence': Decimal(0.0),
                },
            'activity_attributes': {},
        }

    def init_dynamic_attributes(self):
        """
        Initialise the dynamic attributes.
        """
        application_fees = Application.calculate_base_fees(
            self._application.licence_purposes.values_list(
                'id', flat=True))['application']

        self._dynamic_attributes = {
            'fees': {
                'application': application_fees,
                'licence': Decimal(0.0),
            },
            'activity_attributes': {},
        }

    def set_dynamic_attributes(self, attributes):
        self._dynamic_attributes = attributes

    def get_dynamic_attributes(self):
        return self._dynamic_attributes

    def __str__(self):
        return 'AmendApplicaitonFeePolicy'


class RenewApplicationFeePolicy(ApplicationFeePolicy):
    """
    Renewal Application maintains the status of the previous application.
    Allows applicant to renew a licence.

    1. No refunds are provided.
    """
    def __init__(self, application):
        self._application = application
        self.init_dynamic_attributes()

    def set_application_fee(self):
        """
        Set Application fee from the saved model.
        """
        application_fees = Application.calculate_base_fees(
                self._application.licence_purposes.values_list('id', flat=True)
            )['application']
        licence_fees = Application.calculate_base_fees(
                self._application.licence_purposes.values_list('id', flat=True)
            )['licence']

        if self._application.application_fee > 0:
            application_fees = self._application.application_fee

        self._dynamic_attributes = {
            'fees': {
                'application': application_fees,
                'licence': licence_fees,
                },
            'activity_attributes': {},
        }

    def init_dynamic_attributes(self):
        self._dynamic_attributes = {
            'fees': Application.calculate_base_fees(
                self._application.licence_purposes.values_list('id', flat=True)
            ),
            'activity_attributes': {},
        }

    def set_dynamic_attributes(self, attributes):
        self._dynamic_attributes = attributes

    def get_dynamic_attributes(self):
        return self._dynamic_attributes

    def __str__(self):
        return 'RenewApplicationFeePolicy'


class NewApplicationFeePolicy(ApplicationFeePolicy):
    """
    1. Set application from admin base fee
    2. NewApplicationFeePolicy applies to Requested Amendment.
    """
    def __init__(self, application):
        self._application = application
        self.init_dynamic_attributes()

    def set_application_fee(self):
        """
        Set Application fee from the saved model.
        """
        application_fees = Application.calculate_base_fees(
                self._application.licence_purposes.values_list('id', flat=True)
            )['application']
        licence_fees = Application.calculate_base_fees(
                self._application.licence_purposes.values_list('id', flat=True)
            )['licence']

        if self._application.application_fee > 0:
            application_fees = self._application.application_fee

        self._dynamic_attributes = {
            'fees': {
                'application': application_fees,
                'licence': licence_fees,
                },
            'activity_attributes': {},
        }

    def init_dynamic_attributes(self):
        self._dynamic_attributes = {
            'fees': Application.calculate_base_fees(
                self._application.licence_purposes.values_list('id', flat=True)
            ),
            'activity_attributes': {},
        }

    def set_dynamic_attributes(self, attributes):
        self._dynamic_attributes = attributes

    def get_dynamic_attributes(self):
        return self._dynamic_attributes

    def __str__(self):
        return 'NewApplicationFeePolicy'


"""
NOTE: Section for objects relating to generating Application species list.
"""


class TSCSpecieService():
    """
    Interface for Threatened Species Communities api services.
    """
    def __init__(self, call_strategy):
        self._strategy = call_strategy

    def set_strategy(self, call_strategy):
        self._strategy = call_strategy

    def get_strategy(self):
        return self._strategy

    def search_taxon(self, specie_id):
        """
        Search taxonomy for specie details and save search data.
        """
        try:
            token = None
            identifier = None
            search_data = self._strategy.request_species(specie_id)

            if search_data:
                if isinstance(self._strategy, TSCSpecieXReferenceCall):
                    token = search_data[0]['xref_id']
                    identifier = self._strategy._CODE

                # Save searched details.
                specie, verified = LicenceSpecies.objects.get_or_create(
                    specie_id=int(specie_id)
                )
                specie.verify_id = identifier
                specie.verify_token = token
                specie.data = search_data
                specie.save()  # save specie to update verification date.

            return search_data

        except BaseException:
            print "{} error: {}".format(self._strategy, sys.exc_info()[0])
            raise

    def __str__(self):
        return 'TSCSpecieService: {}'.format(self._strategy)


class TSCSpecieCallStrategy(object):
    """
    A Strategy Interface declaring a common operation for the TSCSpecie Call.
    """

    _AUTHORISE = {"Authorization": settings.TSC_AUTH}
    _CODE = None

    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def request_species(self, species):
        """
        Operation for consuming TSCSpecie details.
        """
        pass


class TSCSpecieCall(TSCSpecieCallStrategy):
    """
    A TSCSpecie Call.
    """
    _CODE = 'TAXON'
    _URL = "https://tsc.dbca.wa.gov.au/api/1/taxon/?format=json"

    def __init__(self):
        super(TSCSpecieCallStrategy, self).__init__()
        self._depth = sys.getrecursionlimit()

    def set_depth(self, depth):
        """
        Set the number of recursion levels.
        """
        self._depth = depth if depth > 0 else sys.getrecursionlimit()

    def request_species(self, specie_id):

        def send_request(specie_id):
            url = '{0}&name_id={1}'.format(self._URL, specie_id)
            specie_json = requests.get(url, headers=self._AUTHORISE).json()
            return specie_json

        details = send_request(specie_id)
        specie = {
            'name_id': details['features'][0]['name_id'],
            'name':  details['features'][0]['name'],
            'canonical_name': details['features'][0]['canonical_name'],
            'vernacular_name': details['features'][0]['vernacular_name'],
            }

        return specie


class TSCSpecieRecursiveCall(TSCSpecieCallStrategy):
    """
    A Recursive strategy for the TSCSpecie Call.
    To be implemented. Recursive action on TSC server-side.
    """
    _CODE = 'TAXON1'

    def __init__(self):
        super(TSCSpecieCallStrategy, self).__init__()
        self._depth = sys.getrecursionlimit()

    def set_depth(self, depth):
        pass

    def request_species(self, species):
        pass

    def __str__(self):
        return 'Recursive call with max depth {}'.format(self.depth)


class TSCSpecieXReferenceCall(TSCSpecieCallStrategy):
    """
    A Recursive strategy for the TSCSpecie Call.

    Reason 0: Misapplied name
    Reason 1: Taxonomic synonym
    Reason 2: Nomenclatural synonym
    Reason 3: Excluded name
    Reason 4: Concept change
    Reason 5: Formal description
    Reason 6: Orthographic variant
    Reason 7: Name in error
    Reason 8: Informal Synonym
    """
    _CODE = "XREF"
    _XREF = "https://tsc.dbca.wa.gov.au/api/1/crossreference/?format=json"
    _TAXN = "https://tsc.dbca.wa.gov.au/api/1/taxon-fast/?format=json"

    def __init__(self):
        super(TSCSpecieCallStrategy, self).__init__()
        self._depth = sys.getrecursionlimit()

    def set_depth(self, depth):
        """
        Set the number of recursion levels.
        """
        self._depth = depth if depth > 0 else sys.getrecursionlimit()

    def request_species(self, species):
        LEVEL = 0
        level_list = [{'name_id': species}]

        return self.get_level_species(LEVEL, level_list)

    def get_level_species(self, level_no, level_species):
        requested_species = []

        def send_request_successor(level_species):
            # sends a request to TSC for each specie in level using specie_id
            # to retrieve successors.
            level_list = []
            for specie in level_species:

                # check if verified and recursively decend from that token.
                try:
                    xref_id = LicenceSpecies.objects.values(
                        'verify_token').get(specie_id=specie['name_id'])

                    return send_request_token(xref_id['verify_token'])

                except LicenceSpecies.DoesNotExist:
                    pass
                except KeyError:
                    pass

                url = '{0}&predecessor__name_id={1}'.format(
                    self._XREF, specie['name_id'])
                xref = requests.get(url, headers=self._AUTHORISE).json()

                if (xref['count'] and xref['count'] > 0):
                    xref['results'][0]['successor'][
                        'authorised_on'] = xref['results'][0]['authorised_on']
                    xref['results'][0]['successor'][
                        'xref_id'] = xref['results'][0]['xref_id']
                    level_list.append(xref['results'][0]['successor'])

            return level_list

        def send_request_node(level_species):
            # Sends a request to TSC for each specie in level using specie id
            # to retrieve specie details.
            level_list = []
            for specie in level_species:

                url = '{0}&name_id={1}'.format(
                    self._TAXN, specie['name_id'])
                taxon = requests.get(url, headers=self._AUTHORISE).json()

                if (taxon['count'] and taxon['count'] > 0):
                    taxon['features'][0]['authorised_on'] = None
                    taxon['features'][0]['xref_id'] = 0
                    level_list.append(taxon['features'][0])

            return level_list

        def send_request_token(xref_id):
            # Send a request to TSC using xref identifier to retrieve
            # successors.
            level_list = []
            for specie in level_species:

                url = '{0}&xref_id={1}'.format(
                    self._XREF, xref_id)
                xref = requests.get(url, headers=self._AUTHORISE).json()

                if (xref['count'] and xref['count'] > 0):
                    xref['results'][0]['successor'][
                        'authorised_on'] = xref['results'][0]['authorised_on']
                    xref['results'][0]['successor'][
                        'xref_id'] = xref['results'][0]['xref_id']
                    level_list.append(xref['results'][0]['successor'])

            return level_list

        # recursive descent.
        level_no = level_no + 1
        if level_no < self._depth:  # stopping rule.
            successor = send_request_successor(level_species)
            requested_species = successor
            if successor:
                next_level_species = self.get_level_species(
                    level_no, successor)

                for specie in next_level_species:
                    requested_species.append(specie)
        else:
            raise Exception('{0} - Recursion limit exceeded.'.format(self))

        if not requested_species and level_no < 2:
            # When no successor from root retrieve root node.
            requested_species = send_request_node(level_species)

        return requested_species

    def __str__(self):
        return 'XRef call with max depth {}'.format(self._depth)
