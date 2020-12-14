import sys
import abc
import requests
import logging

from wildlifecompliance import settings

from wildlifecompliance.components.licences.models import (
    LicencePurpose,
    LicenceSpecies,
)

from wildlifecompliance.components.applications.payments import (
    ApplicationFeePolicy,
    InvoiceClearable,
)

from wildlifecompliance.components.main.utils import (
    get_session_application,
    delete_session_application,
    set_session_other_pay_method,
    create_other_application_invoice,
)

from wildlifecompliance.components.applications.models import (
    Application,
    ApplicationSelectedActivity,
    ApplicationSelectedActivityPurpose,
    ApplicationFormDataRecord,
    ApplicationStandardCondition,
    ApplicationCondition,
    LicenceActivity,
)

logger = logging.getLogger(__name__)
# logger = logging


class ApplicationService(object):
    """
    Services available for a Licence Application.
    """

    def __init__(self):
        pass

    @staticmethod
    def cash_payment_submission(request):
        '''
        Prepares licence application with cash payments.

        :return: invoice reference.
        '''
        try:
            application = get_session_application(request.session)
            delete_session_application(request.session)

            application.submit_type = Application.SUBMIT_TYPE_PAPER
            application.save()
            do_update_dynamic_attributes(application)

            set_session_other_pay_method(
                request.session, InvoiceClearable.TYPE_CASH
            )
            invoice = create_other_application_invoice(
                application, request
            )
            invoice_ref = invoice.reference

            # submit application if successful.
            application.submit(request)

        except Exception as e:
            delete_session_application(request.session)
            logger.error('Fail cash_payment_submission: {0}'.format(e))
            raise Exception('Failed cash payment application submission.')

        return invoice_ref

    @staticmethod
    def none_payment_submission(request):
        '''
        Prepares licence application with no base fee payment. Supports the
        migration of previously paid licenses not in the system.
        '''
        invoice_ref = None          # No invoice reference created.
        try:
            application = get_session_application(request.session)
            delete_session_application(request.session)

            application.submit_type = Application.SUBMIT_TYPE_MIGRATE
            application.application_fee = 0
            has_fee_exemption = True
            do_update_dynamic_attributes(application, has_fee_exemption)

            logger.info(
                'Zero amount payment submission for {0}'.format(
                    application.id))

            # submit application if successful.
            application.submit(request)

        except Exception as e:
            delete_session_application(request.session)
            logger.error('Fail none_payment_submission: {0}'.format(e))
            raise Exception('Failed none payment application submission.')

        return invoice_ref

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
        try:
            tsc_service = TSCSpecieService(TSCSpecieCall())
            tsc_service.set_strategy(TSCSpecieXReferenceCall())
            logger.info('ApplicationService: Verifying species.')
            tsc_service.search_taxon(specie_id)
            logger.info('ApplicationService: Completed. Verified 1 specie.')

        except BaseException as e:
            logger.error('ERR verify_licence_specie_id for {0} : {1}'.format(
                specie_id,
                e,
            ))

    @staticmethod
    def calculate_fees(application, data_source):
        """
        Calculates fees for Application and Licence. Application fee is
        calculated with the base fee in all instances to allow for adjustments
        made from form attributes. Previous attributes settings are not saved.
        """
        logger.debug('ApplicationService.calculate_fees() - start')
        # Get all fee adjustments made with checkboxes and radio buttons.
        checkbox = CheckboxAndRadioButtonVisitor(application, data_source)
        for_increase_fee_fields = IncreaseApplicationFeeFieldElement()
        for_increase_fee_fields.accept(checkbox)
        # set fee exemption for migrations.
        MIGRATE = Application.SUBMIT_TYPE_MIGRATE
        fee_exempted = True if application.submit_type == MIGRATE else False
        for_increase_fee_fields.set_has_fee_exemption(fee_exempted)
        logger.debug('ApplicationService.calculate_fees() - end')

        return for_increase_fee_fields.get_adjusted_fees()

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
        logger.debug('ApplicationService.process_form() - start')
        update_fee = form_data.pop('__update_fee', False)
        do_process_form(
            request,
            application,
            form_data,
            action)

        process_status = [
            Application.PROCESSING_STATUS_UNDER_REVIEW
        ]

        if update_fee or application.processing_status not in process_status:
            do_update_dynamic_attributes(application)
        # 
        # else:
        #     updated_app = Application.objects.get(id=application.id)
        #     updated_app.save()      # save for reversion log on form.

        logger.debug('ApplicationService.process_form() - end')

    @staticmethod
    def update_dynamic_attributes(application):
        """
        Updates application attributes based on admin schema definition.
        """
        try:
            do_update_dynamic_attributes(application)

        except BaseException as e:
            logger.error('ERR update_dynamic_attributes for {0} : {1}'.format(
                application.id,
                e,
            ))

    def __str__(self):
        return 'ApplicationService'


"""
NOTE: This section for objects relate to Application Form rendering.
"""


class BulkCreateManager(object):
    '''
    This helper class keeps track of ORM objects to be created for multiple
    model classess, automatically creates those objects with `bulk_create`
    when the number of objects accumulated for a given model class exceeds
    `chunk_size`.

    https://www.caktusgroup.com/blog/2019/01/09/django-bulk-inserts/
    '''
    def __init__(self, obj, chunk_size=100):
        from collections import defaultdict

        self._create_queues = defaultdict(list)
        self.chunk_size = chunk_size
        self.model_class = type(obj)
        objs = self.model_class.objects.filter(
            application_id=obj.application_id
        ).all()
        objs.delete()

    def _commit(self, model_class):
        model_key = model_class._meta.label
        model_class.objects.bulk_create(self._create_queues[model_key])
        self._create_queues[model_key] = []

    def add(self, obj):
        '''
        Add an object to the queue to be created, and call bulk_create if we
        have enough objects.
        '''
        model_class = type(obj)
        model_key = model_class._meta.label
        self._create_queues[model_key].append(obj)
        if len(self._create_queues[model_key]) >= self.chunk_size:
            self._commit(model_class)

    def done(self):
        '''
        Always call this upon completion to make sure the final partial chunk
        is saved.
        '''
        from django.apps import apps

        for model_name, objs in self._create_queues.items():
            if len(objs) > 0:
                self._commit(apps.get_model(model_name))


class ApplicationFormCompositor(object):
    """
    Declares an interface common to all supported Application Form algorithms.
    A context can use this interface to call a specific algorithm to act on
    a Special Field Element on a Application Form.
    """
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def do_algorithm(self, special_field_element):
        """
        Performs an algorithm applicable to a Special Field Element.
        """
        pass


class CheckboxAndRadioButtonCompositor(ApplicationFormCompositor):
    """
    A Class for objects which encapsulates an algorithm for formatting Checkbox
    and Radio buttons on an Application Form.
    """
    def __init__(self, application, data_source):
        self._application = application
        self._data_source = data_source
        self._children = set()

    def do_algorithm(self, special_field_element):
        self._field = special_field_element
        self.render()

    def render(self):
        logger.debug('CheckboxAndRadioButtonCompositor.render()')
        for selected_activity in self._application.activities:

            self._field.reset(selected_activity)

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

                if schema_data['type'] not in ['checkbox', 'radiobuttons']:
                    continue

                if 'options' in schema_data:
                    for option in schema_data['options']:
                        # Only modifications if the current option is selected
                        if option['value'] != data_record['value']:
                            continue
                        self._field.parse_component(
                            component=option,
                            schema_name=schema_name,
                            adjusted_by_fields=adjusted_by_fields,
                            activity=selected_activity,
                            purpose_id=schema_data['licence_purpose_id']
                        )

                elif data_record['value'] == 'on':
                    self._field.parse_component(
                        component=schema_data,
                        schema_name=schema_name,
                        adjusted_by_fields=adjusted_by_fields,
                        activity=selected_activity,
                        purpose_id=schema_data['licence_purpose_id']
                    )
                elif data_record['value'] == '':
                    # if unchecked reset field adjustments.
                    self._field.reset_licence_purpose(
                        selected_activity, schema_data['licence_purpose_id']
                    )


class TextAreaCompositor(ApplicationFormCompositor):
    """
    A Class for objects which encapsulates an algorithm for formatting Text
    Areas on an Application Form.
    """
    def __init__(self, application, data_source):
        self._application = application
        self._data_source = data_source
        self._children = set()

    def do_algorithm(self, special_field_element):
        self._field = special_field_element
        self.render()

    def render(self):
        for selected_activity in self._application.activities:

            self._field.reset(selected_activity)

            schema_fields = self._application.get_schema_fields_for_purposes(
                selected_activity.purposes.values_list('id', flat=True)
            )

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

                if schema_data['type'] == 'text_area':
                    self._field.parse_component(
                        component=schema_data,
                        schema_name=schema_name,
                        adjusted_by_fields=adjusted_by_fields,
                        activity=selected_activity,
                        purpose_id=schema_data['licence_purpose_id']
                    )


class TextCompositor(ApplicationFormCompositor):
    """
    A Class for objects which encapsulates an algorithm for formatting Text
     on an Application Form.
    """
    def __init__(self, application, data_source):
        self._application = application
        self._data_source = data_source
        self._children = set()

    def do_algorithm(self, special_field_element):
        self._field = special_field_element
        self.render()

    def render(self):
        for selected_activity in self._application.activities:

            self._field.reset(selected_activity)

            schema_fields = self._application.get_schema_fields_for_purposes(
                selected_activity.purposes.values_list('id', flat=True)
            )

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

                if schema_data['type'] == 'text':
                    self._field.parse_component(
                        component=schema_data,
                        schema_name=schema_name,
                        adjusted_by_fields=adjusted_by_fields,
                        activity=selected_activity,
                        purpose_id=schema_data['licence_purpose_id']
                    )


class ApplicationFormVisitor(object):
    """
    An Interface for Application Form component fields which can be visited.
    """
    __metaclass__ = abc.ABCMeta


class CheckboxAndRadioButtonVisitor(ApplicationFormVisitor):
    """
    An implementation of an operation declared by ApplicationFormVisitor to do
    an algorithm specific to Checkbox and Radio Buttons for a Form.

    NOTE: Local state is stored and will accumulate during the traversal of the
    Form.
    """
    def __init__(self, application, data_source):
        self._application = application
        self._data_source = data_source
        # Apply a traversal strategy.
        self._compositor = CheckboxAndRadioButtonCompositor(
            application,
            data_source
        )

    def visit_prompt_inspection_field(self, prompt_inspection_field):
        logger.debug('CheckboxButtonVisitor.visit_prompt_inspection_field()')
        self._prompt_inspection_field = prompt_inspection_field
        self._compositor.do_algorithm(self._prompt_inspection_field)

    def visit_standard_condition_field(self, standard_condition_field):
        logger.debug('CheckboxButtonVisitor.visit_standard_condition_field()')
        self._standard_condition_field = standard_condition_field
        self._compositor.do_algorithm(self._standard_condition_field)

    def visit_increase_application_fee_field(self, increase_fee_field):
        logger.debug('CheckboxButtonVisitor.visit_increase_fee_field()')
        self._increase_application_fee_field = increase_fee_field
        self._compositor.do_algorithm(self._increase_application_fee_field)

    def visit_species_options_field(self, species_options_field):
        logger.debug('CheckboxButtonVisitor.visit_species_opt_field()')
        self._species_options_field = species_options_field
        self._compositor.do_algorithm(self._species_options_field)


class TextAreaVisitor(ApplicationFormVisitor):
    """
    An implementation of an operation declared by ApplicationFormVisitor to do
    an algorithm specific to Text Area on a Form.

    NOTE: Local state is stored and will accumulate during the traversal of the
    Form.
    """
    def __init__(self, application, data_source):
        self._application = application
        self._data_source = data_source
        # Apply a traversal strategy.
        self._compositor = TextAreaCompositor(application, data_source)

    def visit_copy_to_licence_field(self, copy_to_licence_field):
        self._copy_to_licence_field = copy_to_licence_field
        self._compositor.do_algorithm(self._copy_to_licence_field)


class TextVisitor(ApplicationFormVisitor):
    """
    An implementation of an operation declared by ApplicationFormVisitor to do
    an algorithm specific to Text on a Form.

    NOTE: Local state is stored and will accumulate during the traversal of the
    Form.
    """
    def __init__(self, application, data_source):
        self._application = application
        self._data_source = data_source
        # Apply a traversal strategy.
        self._compositor = TextCompositor(application, data_source)

    def visit_copy_to_licence_field(self, copy_to_licence_field):
        self._copy_to_licence_field = copy_to_licence_field
        self._compositor.do_algorithm(self._copy_to_licence_field)


class SpecialFieldElement(object):
    """
    Special Field that defines an Accept operation that takes a
    ApplicationFormVisitor as an argument.
    """
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def accept(self, visitor):
        pass

    def reset(self, licence_activity):
        """
        Reset previous option settings on the licence activity by removing.
        """
        pass

    def reset_licence_purpose(self, licence_activity, purpose_id):
        """
        Reset previous options settings on the licence purpose by removing.
        """
        pass


class SpeciesOptionsFieldElement(SpecialFieldElement):
    """
    An implementation of an SpecialFieldElement operation that takes a
    ApplicationFormVisitor as an argument.

    example:

        "options": [
          {
            "value": "yes",
            "label": "Yes",
          },
          {
            "value": "no",
            "label": "No",
            "species": [33974,33977]
          }
        ],
        "type": "radiobuttons",
        "name": "ATO-Import3",
        "label": "Do you need to apply for a licence to import?",
        "SpeciesOptions": true

    """
    _NAME = 'SpeciesOptions'
    _SPECIES = 'species'

    is_refreshing = False       # Flag indicating a page refresh.
    records = None

    def accept(self, application_form_visitor):
        self._terms = {'terms': []}
        self._application = application_form_visitor._application
        self._data_source = application_form_visitor._data_source
        if not self._data_source:
            self.is_refreshing = True
        application_form_visitor.visit_species_options_field(self)

    def parse_component(
            self,
            component,
            schema_name,
            adjusted_by_fields,
            activity,
            purpose_id):

        if self.is_refreshing:
            # No user update with a page refesh.
            return

        if set([self._SPECIES]).issubset(component):
            '''
            Set the species options on the form.
            '''
            # update the species component value on the form to reference ids.
            # else create one using name + '-SpeciesOptions'.
            species_ids = ""
            try:
                species_ids = [str(s) for s in component[self._SPECIES]]

            except BaseException:
                pass

            records = ApplicationFormDataRecord.objects.filter(
                    application_id=self._application.id,
                    licence_activity_id=activity.licence_activity_id,
                    licence_purpose_id=purpose_id,
                    component_type=self._SPECIES
            ).update(
                 value=species_ids
            )

            if not records:
                ApplicationFormDataRecord.objects.create(
                    field_name='{0}-SpeciesOptions'.format(schema_name),
                    schema_name='{0}-SpeciesOptions'.format(schema_name),
                    component_type=self._SPECIES,
                    value=species_ids,
                    application_id=self._application.id,
                    licence_activity_id=activity.licence_activity_id,
                    licence_purpose_id=purpose_id
                )
        else:
            '''
            SpeciesOptions is set with no species ids therefore clear all
            species on the application form.
            '''
            records = ApplicationFormDataRecord.objects.filter(
                    application_id=self._application.id,
                    licence_activity_id=activity.licence_activity_id,
                    licence_purpose_id=purpose_id,
                    component_type=self._SPECIES
            ).update(
                 value=''
            )

    def __str__(self):
        return 'Field Element: {0}'.format(self._NAME)


class CopyToLicenceFieldElement(SpecialFieldElement):
    """
    An implementation of an SpecialFieldElement operation that takes a
    ApplicationFormVisitor as an argument.
    """
    _NAME = 'CopyToLicence'

    is_refreshing = False       # Flag indicating a page refresh.

    def accept(self, application_form_visitor):
        self._terms = {'terms': []}
        self._application = application_form_visitor._application
        self._data_source = application_form_visitor._data_source
        if not self._data_source:
            self.is_refreshing = True
        application_form_visitor.visit_copy_to_licence_field(self)

    def reset(self, licence_activity):
        """
        Reset the selected licence activity to have no CopyToLicenceFields.
        """
        if self.is_refreshing:
            # No user update with a page refesh.
            return

        if isinstance(licence_activity, ApplicationSelectedActivity):
            licence_activity.additional_licence_info = self._terms
            licence_activity.save()

    def parse_component(
            self,
            component,
            schema_name,
            adjusted_by_fields,
            activity,
            purpose_id):

        if self.is_refreshing:
            # No user update with a page refesh.
            return

        if set([self._NAME]).issubset(component):
            """
            Set the selected licence activity to have CopyToLicenceFields.
            """
            _header = {
                'header': component[self._NAME],
                'condition': component['condition'],
                'name': component['name']
                }
            activity.additional_licence_info['terms'].append(_header)
            activity.save()

    def __str__(self):
        return 'Field Element: {0}'.format(self._NAME)


class PromptInspectionFieldElement(SpecialFieldElement):
    """
    An implementation of an SpecialFieldElement operation that takes a
    ApplicationFormVisitor as an argument.
    """
    _NAME = 'PromptInspection'

    is_refreshing = False       # Flag indicating a page refresh.

    def accept(self, application_form_visitor):
        self._application = application_form_visitor._application
        self._data_source = application_form_visitor._data_source
        if not self._data_source:
            self.is_refreshing = True
        application_form_visitor.visit_prompt_inspection_field(self)

    def reset_licence_purpose(self, licence_activity, purpose_id):
        """
        Reset previous options settings on the licence purpose by removing.
        """
        if self.is_refreshing:
            # No user update with a page refesh.
            return

        if licence_activity.is_inspection_required:
            licence_activity.is_inspection_required = False
            licence_activity.save()

    def parse_component(
            self,
            component,
            schema_name,
            adjusted_by_fields,
            activity,
            purpose_id):

        if self.is_refreshing:
            # No user update with a page refesh.
            return

        activity.is_inspection_required = False
        if set([self._NAME]).issubset(component):
            activity.is_inspection_required = True
        activity.save()

    def __str__(self):
        return 'Field Element: {0}'.format(self._NAME)


class StandardConditionFieldElement(SpecialFieldElement):
    """
    An implementation of an SpecialFieldElement operation that takes a
    ApplicationFormVisitor as an argument.
    """
    _NAME = 'StandardCondition'

    is_refreshing = False       # Flag indicating a page refresh.

    def accept(self, application_form_visitor):
        self._application = application_form_visitor._application
        self._data_source = application_form_visitor._data_source
        if not self._data_source:
            self.is_refreshing = True
        application_form_visitor.visit_standard_condition_field(self)

    def reset(self, licence_activity):
        """
        Reset the Selected Activity to have no Standard Condition created.

        NOTE: Standard Conditions created will need to be manually deleted
        by the officer when need to change so that it is audited.
        """
        if self.is_refreshing:
            # No user update with a page refesh.
            return

        if isinstance(licence_activity, ApplicationSelectedActivity):
            # delete existing rendered standard conditions.
            for condition in ApplicationCondition.objects.filter(
                is_rendered=True,
                standard=True,
                application=self._application,
                licence_activity_id=licence_activity.id
            ):
                condition.delete()

    def parse_component(
            self,
            component,
            schema_name,
            adjusted_by_fields,
            activity,
            purpose_id):

        if self.is_refreshing:
            # No user update with a page refesh.
            return

        if set([self._NAME]).issubset(component):
            """
            Set the Selected Activity to contain Standard Conditon.
            """
            condition = ApplicationStandardCondition.objects.filter(
                code=component[self._NAME],
                obsolete=False).first()
            if condition:
                purpose = LicencePurpose.objects.get(
                       id=purpose_id
                )
                ac, created = ApplicationCondition.objects.get_or_create(
                    standard_condition=condition,
                    is_rendered=True,
                    standard=True,
                    application=self._application)
                ac.licence_activity = LicenceActivity.objects.get(
                        id=activity.licence_activity_id)
                ac.licence_purpose = purpose
                ac.return_type = condition.return_type
                ac.save()

    def __str__(self):
        return 'Field Element: {0}'.format(self._NAME)


class IncreaseApplicationFeeFieldElement(SpecialFieldElement):
    """
    An implementation of an SpecialFieldElement operation that takes a
    ApplicationFormVisitor as an argument and dynamically updates any increased
    adjustments to the application fee for the Activity/Purpose.
    """
    NAME = 'IncreaseApplicationFee'
    LICENCE = 'IncreaseLicenceFee'

    fee_policy = None           # Policy applied to the fee update.
    dynamic_attributes = None   # Attributes on the Activity Purpose.
    is_updating = False         # Flag indicating if update or retrieval.
    is_refreshing = False       # Flag indicating a page refresh.
    has_fee_exemption = False   # Allow exemption for zero amount invoice.

    adjusted_fee = 0
    adjusted_licence_fee = 0

    def __init__(self):
        pass

    def __str__(self):
        return 'Field Element: {0}'.format(self._NAME)

    def accept(self, application_form_visitor):
        logger.debug('IncreaseApplicationFeeFieldElement.accept() - start')
        self._app = application_form_visitor._application
        self._data_source = application_form_visitor._data_source
        # Add relevant Fee policy to impact the Increase Application Fee.
        logger.debug('IncreaseApplicationFeeFieldElement.accept() #2')
        self.fee_policy = ApplicationFeePolicy.get_fee_policy_for(self._app)
        if not self._data_source:  # No form data set fee from application fee.
            self.fee_policy.set_application_fee()
            self.is_refreshing = True
        self.dynamic_attributes = self.fee_policy.get_dynamic_attributes()
        logger.debug('IncreaseApplicationFeeFieldElement.accept() #3')
        application_form_visitor.visit_increase_application_fee_field(self)
        logger.debug('IncreaseApplicationFeeFieldElement.accept() - end')

    def set_updating(self, is_update):
        '''
        Sets the flag indicating that this visit is an update and not retrieve
        for estimate calculation.
        '''
        self.is_updating = is_update

    def set_has_fee_exemption(self, is_exempt):
        '''
        Sets the flag indicating that this visit will force a zero amount to be
        calculated for invoicing (zero amount invoice). The fee stored is only
        for the adjusted amounts on the licence purpose.
        '''
        self.has_fee_exemption = is_exempt
        self.fee_policy.set_has_fee_exemption(is_exempt)

    def reset(self, licence_activity):
        '''
        Reset the fees for the licence activity to it base fee amount.
        '''
        logger.debug('IncreaseApplicationFeeFieldElement.reset()')
        self.adjusted_fee = 0
        self.adjusted_licence_fee = 0

        if self.is_refreshing:
            # No user update with a page refesh.
            return

        if isinstance(licence_activity, ApplicationSelectedActivity):
            self.dynamic_attributes[
                'activity_attributes'][licence_activity] = {
                    'fees': licence_activity.base_fees
                }

            if self.is_updating:
                licence_activity.save_without_cache()

    def reset_licence_purpose(self, licence_activity, purpose_id):
        """
        Reset previous options settings on the licence purpose by removing.
        """
        logger.debug(
            'IncreaseApplicationFeeFieldElement.reset_licence_purpose()'
        )
        if self.is_refreshing or not self.is_updating:
            # No user update with a page refesh.
            return

        # reset purpose adjusted fee amount.
        purposes = ApplicationSelectedActivityPurpose.objects.filter(
            selected_activity=licence_activity,
        )
        for p in purposes:
            p.adjusted_fee = self.adjusted_fee
            p.adjusted_licence_fee = self.adjusted_licence_fee
            p.save()

    def parse_component(
            self,
            component,
            schema_name,
            adjusted_by_fields,
            activity,
            purpose_id):
        '''
        Aggregate adjusted fees for the Activity/Purpose.
        '''
        from decimal import Decimal as D
        from decimal import ROUND_DOWN

        logger.debug('IncreaseApplicationFeeFieldElement.parse_component()')

        if self.is_refreshing:
            # No user update with a page refesh.
            return

        if set([self.NAME]).issubset(component) \
                or set([self.LICENCE]).issubset(component):
            def increase_fee(fees, field, amount):
                if self.has_fee_exemption:
                    return True
                amount = D(amount).quantize(D('0.01'), rounding=ROUND_DOWN)
                fees[field] += amount
                fees[field] = fees[field] if fees[field] >= 0 else 0
                return True

            def adjusted_fee(field, amount):
                amount = D(amount).quantize(D('0.01'), rounding=ROUND_DOWN)
                if field == 'licence':
                    self.adjusted_licence_fee += amount
                elif field == 'application':
                    self.adjusted_fee += amount
                return True

            fee_modifier_keys = {
                self.LICENCE: 'licence',
                self.NAME: 'application',
            }
            increase_limit_key = 'IncreaseTimesLimit'
            try:
                increase_count = adjusted_by_fields[schema_name]
            except KeyError:
                increase_count = adjusted_by_fields[schema_name] = 0

            if increase_limit_key in component:
                max_increases = int(component[increase_limit_key])
                if increase_count >= max_increases:
                    return

            adjustments_performed = sum(key in component and increase_fee(
                self.dynamic_attributes['fees'],
                field,
                component[key]
            ) and increase_fee(
                self.dynamic_attributes[
                    'activity_attributes'][activity]['fees'],
                field,
                component[key]
            ) and adjusted_fee(
                field,
                component[key]
            ) for key, field in fee_modifier_keys.items())

            if adjustments_performed:
                adjusted_by_fields[schema_name] += 1

            if adjustments_performed and self.is_updating:
                purpose = LicencePurpose.objects.get(
                       id=purpose_id
                )
                # update adjusted fee for the activity purpose.
                p, c = ApplicationSelectedActivityPurpose.objects.\
                    get_or_create(purpose=purpose, selected_activity=activity)

                if c:  # Only save base fees for those not created.
                    p.application_fee = purpose.base_application_fee
                    p.licence_fee = purpose.base_licence_fee

                # self.adjusted_fee = D(p.adjusted_fee) + self.adjusted_fee
                # self.adjusted_licence_fee = \
                #     D(p.adjusted_licence_fee) + self.adjusted_licence_fee

                p.adjusted_fee = self.adjusted_fee
                p.adjusted_licence_fee = self.adjusted_licence_fee
                p.save()

    def get_adjusted_fees(self):
        '''
        Gets the new dynamic attributes after the Increase Application Fee
        has been applied with the relevant fee policy.
        '''
        if self.is_refreshing:
            # don't calculate new fees for attributes.
            return self.dynamic_attributes['fees']
        # apply fee policy to re-calculate total fees for application.
        self.fee_policy.set_dynamic_attributes(self.dynamic_attributes)

        return self.dynamic_attributes['fees']

    def set_adjusted_fees_for(self, activity):
        '''
        Sets the Increase Application Fee on the licence activity applying the
        relevant fee policy.
        '''
        if self.is_refreshing:
            # don't calculate new fees for attributes.
            return
        # apply fee policy to re-calculate total fees for application.
        self.fee_policy.set_dynamic_attributes_for(activity)

    def get_dynamic_attributes(self):
        '''
        Gets the current dynamic attributes created by this Field Element.
        '''
        if self.is_refreshing:
            # don't calculate new fees for attributes.
            return self.dynamic_attributes
        # apply fee policy to re-calculate total fees for application.
        self.fee_policy.set_has_fee_exemption(self.has_fee_exemption)
        self.fee_policy.set_dynamic_attributes(self.dynamic_attributes)

        return self.dynamic_attributes


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

    bulk_mgr = BulkCreateManager(
        ApplicationFormDataRecord(application_id=application.id)
    )
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

        SPECIES = ApplicationFormDataRecord.COMPONENT_TYPE_SELECT_SPECIES
        form_data_record = ApplicationFormDataRecord(
            application_id=application.id,
            field_name=field_name,
            licence_activity_id=activity_id,
            licence_purpose_id=purpose_id,
            schema_name=schema_name,
            instance_name=instance_name,
            component_type=component_type,
            component_attribute=component_attribute,
            officer_comment=officer_comment,
            assessor_comment=assessor_comment,
            deficiency=deficiency
        )

        # Species list may not exist in last save because the component has
        # been copied from an amendment. Save new list for species component.
        if component_type == SPECIES\
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

        # elif action == \
        #         ApplicationFormDataRecord.ACTION_TYPE_ASSIGN_COMMENT:
        #     if can_edit_officer_comments:
        #         form_data_record.officer_comment = officer_comment
        #     if can_edit_assessor_comments:
        #         form_data_record.assessor_comment = assessor_comment
        #     if can_edit_deficiencies:
        #         form_data_record.deficiency = deficiency

        bulk_mgr.add(form_data_record)

    bulk_mgr.done()
    if action == ApplicationFormDataRecord.ACTION_TYPE_ASSIGN_VALUE:

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


def do_update_dynamic_attributes(application, fee_exemption=False):
    '''
    Update application and activity attributes based on selected JSON schema
    options. Any attributes which impact the fee for the application can be
    exempted.
    '''
    logger.debug('service.do_update_dynamic_attributes() - start')

    if application.processing_status not in [
            Application.PROCESSING_STATUS_DRAFT,
            Application.PROCESSING_STATUS_AWAITING_APPLICANT_RESPONSE,
            Application.PROCESSING_STATUS_UNDER_REVIEW,
    ]:
        return

    # Get all fee adjustments made with check boxes and radio buttons.
    checkbox = CheckboxAndRadioButtonVisitor(application, application.data)
    for_increase_fee_fields = IncreaseApplicationFeeFieldElement()
    for_increase_fee_fields.set_updating(True)
    for_increase_fee_fields.accept(checkbox)
    for_increase_fee_fields.set_has_fee_exemption(fee_exemption)
    dynamic_attributes = for_increase_fee_fields.get_dynamic_attributes()

    # Save any parsed per-activity modifiers
    for selected_activity, field_data in \
            dynamic_attributes['activity_attributes'].items():
        logger.debug('service.do_update_dynamic_attributes() - save Activity')
        fees = field_data.pop('fees', {})
        selected_activity.licence_fee = fees['licence']
        selected_activity.application_fee = fees['application']

        # Adjust fees to include the Increase Fee updated form questions.
        for_increase_fee_fields.set_adjusted_fees_for(selected_activity)

        for field, value in field_data.items():
            setattr(selected_activity, field, value)

        selected_activity.save()
    logger.debug('service.do_update_dynamic_attributes() - save Application')
    # Update application and licence fees
    fees = dynamic_attributes['fees']
    application.application_fee = fees['application']
    application.set_property_cache_licence_fee(fees['licence'])
    application.save()
    logger.debug('service.do_update_dynamic_attributes() - end')


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

    def search_filtered_taxon(self, filter_str, category):
        """
        Search filtered taxonomy of results for specie details.
        """
        try:
            search_data = self._strategy.request_filtered_species(
                filter_str, category
            )

            return search_data

        except BaseException as e:
            logger.error('{0} - {1}'.format(
                TSCSpecieService.search_filtered_taxon(), e
            ))
            raise

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
            logger.error(
                'TSCSpecieService.search_taxon(): {0}'.format(
                    self._strategy, sys.exc_info()[0]
                ))
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

    @abc.abstractmethod
    def request_filtered_species(self, species, category):
        """
        Operation for consuming a filtered set of TSCSpecie details.
        """
        pass


class HerbieSpecieKMICall(TSCSpecieCallStrategy):
    '''
    Public Herbie from KMI.
    '''
    _CODE = 'HERBIE'
    _URL = 'https://kmi.dpaw.wa.gov.au/geoserver/ows?service=wfs&version=1.1.0'
    FLORA = 'flora'
    FAUNA = 'fauna'

    def __init__(self):
        super(TSCSpecieCallStrategy, self).__init__()
        self._depth = sys.getrecursionlimit()

    def set_depth(self, depth):
        '''
        Set the number of recursion levels.
        '''
        self._depth = depth if depth > 0 else sys.getrecursionlimit()

    def request_filtered_species(self, search_data, category):
        '''
        Search herbie for species and return a list of matching species in the
        form 'scientific name (common name)'.
        The 'search' parameter is used to search (icontains like) through the
        species_name (scientific name) and vernacular property (common name).
        The 'type'=['fauna'|'flora'] parameter can be used to limit the
        kingdom.

        :return: a list of matching species in the form 'scientific name
        (common name)'
        '''
        import sys
        # from importlib import reload
        # reload(sys)
        # sys.setdefaultencoding('utf8')
        filtered_species = {}
        results = []
        params = {
            'propertyName': '(species_name,vernacular)',
            'sortBy': 'species_name'
        }

        def add_filter(cql_filter, params):
            if 'cql_filter' not in params:
                params['cql_filter'] = cql_filter
            else:
                params['cql_filter'] = params['cql_filter'] \
                                                    + ' AND ' + cql_filter

        def send_request(search):
            A = '&request=GetFeature&typeNames=public:herbie_hbvspecies_public'
            B = '&outputFormat=application/json'

            kingdom = category.lower()
            fauna_kingdom = 5
            if kingdom == self.FAUNA:
                add_filter('kingdom_id IN ({})'.format(fauna_kingdom), params)

            elif kingdom == self.FLORA:
                add_filter('kingdom_id NOT IN ({})'.format(
                    fauna_kingdom
                ), params)

            if search_data:
                f_ = "(species_name ILIKE '%{1}%'" \
                    "OR vernacular ILIKE '%{1}%')".format(search, search)
                add_filter(f_, params)

            url = '{0}{1}{2}'.format(self._URL, A, B)
            _request_results = requests.get(url, params=params, verify=False)
            return _request_results

        request_result = send_request(search_data)
        if request_result:
            features = request_result.json()['features']
            for f in features:
                specie = {}
                name = f['properties']['species_name']
                common_name = f[
                    'properties'
                ]['vernacular'] if 'vernacular' in f['properties'] else None

                if common_name:
                    # name += ' ({0})'.format(common_name.encode("utf-8"))
                    name += ' ({0})'.format(common_name)

                specie['text'] = name
                specie['id'] = name
                results.append(specie)

        filtered_species['results'] = results

        return filtered_species

    def request_species(self, specie_id):
        '''
        Search herbie for species and return a list of matching species in the
        form 'scientific name (common name)'.
        The 'search' parameter is used to search (icontains like) through the
        species_name (scientific name) and vernacular property (common name).
        The 'type'=['fauna'|'flora'] parameter can be used to limit the
        kingdom.

        :return: a list of matching species in the form 'scientific name
        (common name)'
        '''
        def send_request(specie_id):
            url = '{0}'.format(self._URL)
            specie_json = requests.get(url, headers=self._AUTHORISE).json()
            return specie_json

        details = send_request(specie_id)

        return details


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
