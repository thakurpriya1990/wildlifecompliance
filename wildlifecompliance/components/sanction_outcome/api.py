import json
import logging
import mimetypes
import os
import traceback

from datetime import datetime

from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponse, FileResponse, HttpResponseNotFound
from ledger.payments.invoice.models import Invoice
from ledger.accounts.models import EmailUser

from rest_framework import viewsets, serializers, status
from rest_framework.decorators import list_route, detail_route, renderer_classes
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework_datatables.filters import DatatablesFilterBackend
from rest_framework_datatables.pagination import DatatablesPageNumberPagination

from wildlifecompliance.components.main.process_document import (
        process_generic_document,
        save_default_document_obj
        )
from wildlifecompliance.components.call_email.models import CallEmail, CallEmailUserAction
from wildlifecompliance.components.inspection.models import Inspection, InspectionUserAction
from wildlifecompliance.components.offence.models import AllegedOffence
from wildlifecompliance.components.sanction_outcome.email import send_infringement_notice, \
    send_due_date_extended_mail, send_return_to_officer_email, send_to_manager_email, send_withdraw_by_manager_email, \
    send_withdraw_by_branch_manager_email, send_return_to_infringement_notice_coordinator_email, send_decline_email, \
    send_escalate_for_withdrawal_email, email_detais_to_department_of_transport, send_remediation_notice, \
    send_caution_notice, send_letter_of_advice, send_parking_infringement_without_offenders, \
    send_remediation_action_submitted_notice, send_remediation_action_accepted_notice, \
    send_remediation_action_request_amendment_mail, send_infringement_notice_issued_on_paper, \
    send_remediation_notice_issued_on_paper, create_infringement_notice_ybw
from wildlifecompliance.components.sanction_outcome.models import SanctionOutcome, RemediationAction, \
    SanctionOutcomeCommsLogEntry, AllegedCommittedOffence, SanctionOutcomeUserAction, SanctionOutcomeCommsLogDocument, \
    AmendmentRequestReason, SanctionOutcomeDocument, SanctionOutcomeDocumentAccessLog
from wildlifecompliance.components.sanction_outcome.pdf import create_remediation_notice_pdf, create_caution_notice_pdf, \
    create_letter_of_advice_pdf
from wildlifecompliance.components.sanction_outcome.serializers import SanctionOutcomeSerializer, \
    SaveSanctionOutcomeSerializer, SaveRemediationActionSerializer, SanctionOutcomeDatatableSerializer, \
    UpdateAssignedToIdSerializer, SanctionOutcomeCommsLogEntrySerializer, SanctionOutcomeUserActionSerializer, \
    AllegedCommittedOffenceSerializer, RecordFerCaseNumberSerializer, \
    RemediationActionSerializer, RemediationActionUpdateStatusSerializer, AmendmentRequestReasonSerializer, \
    SaveAmendmentRequestForRemediationAction, AllegedCommittedOffenceCreateSerializer, \
    SanctionOutcomeDocumentAccessLogSerializer
#from wildlifecompliance.components.users.models import CompliancePermissionGroup
from wildlifecompliance.components.wc_payments.models import InfringementPenalty, InfringementPenaltyInvoice
from wildlifecompliance.helpers import is_authorised_to_modify, is_internal
from wildlifecompliance.components.main.models import TemporaryDocumentCollection
from wildlifecompliance.settings import SO_TYPE_CHOICES, SO_TYPE_REMEDIATION_NOTICE, SO_TYPE_INFRINGEMENT_NOTICE, \
    SO_TYPE_LETTER_OF_ADVICE, SO_TYPE_CAUTION_NOTICE

logger = logging.getLogger('compliancemanagement')


class SanctionOutcomeFilterBackend(DatatablesFilterBackend):

    def filter_queryset(self, request, queryset, view):
        total_count = queryset.count()

        # Storage for the filters
        # Required filters are accumulated here
        # Then issue a query once at last
        q_objects = Q()

        # Filter by the search_text
        search_text = request.GET.get('search[value]', '')
        if search_text:
            q_objects &= Q(lodgement_number__icontains=search_text) | \
                         Q(identifier__icontains=search_text) | \
                         Q(offender__person__first_name__icontains=search_text) | \
                         Q(offender__person__last_name__icontains=search_text) | \
                         Q(offender__person__email__icontains=search_text) | \
                         Q(driver__first_name__icontains=search_text) | \
                         Q(driver__last_name__icontains=search_text) | \
                         Q(driver__email__icontains=search_text) | \
                         Q(registration_holder__first_name__icontains=search_text) | \
                         Q(registration_holder__last_name__icontains=search_text) | \
                         Q(registration_holder__email__icontains=search_text) | \
                         Q(offender__organisation__organisation__name__icontains=search_text) | \
                         Q(offender__organisation__organisation__abn__icontains=search_text) | \
                         Q(offender__organisation__organisation__trading_name__icontains=search_text)

        type = request.GET.get('type', '').lower()
        if type and type != 'all':
            q_objects &= Q(type=type)

        status = request.GET.get('status', '').lower()
        if status and status != 'all':
            q_objects &= Q(status=status)

        payment_status = request.GET.get('payment_status', '').lower()
        if payment_status and payment_status != 'all':
            q_objects &= Q(payment_status=payment_status)

        date_from = request.GET.get('date_from', '').lower()
        if date_from:
            date_from = datetime.strptime(date_from, '%d/%m/%Y')
            q_objects &= Q(date_of_issue__gte=date_from)

        date_to = request.GET.get('date_to', '').lower()
        if date_to:
            date_to = datetime.strptime(date_to, '%d/%m/%Y')
            q_objects &= Q(date_of_issue__lte=date_to)

        region_id = request.GET.get('region_id', '').lower()
        if region_id and region_id != 'all':
            q_objects &= Q(region__id=region_id)

        district_id = request.GET.get('district_id', '').lower()
        if district_id and district_id != 'all':
            q_objects &= Q(district__id=district_id)

        # perform filters
        queryset = queryset.filter(q_objects)

        getter = request.query_params.get
        fields = self.get_fields(getter)
        ordering = self.get_ordering(getter, fields)
        if len(ordering):
            for num, item in enumerate(ordering):
                # offender is the foreign key of the sanction outcome
                if item == 'offender':
                    # offender can be a person or an organisation
                    ordering[num] = 'offender__person'
                    ordering.insert(num + 1, 'offender__organisation')
                elif item == '-offender':
                    ordering[num] = '-offender__person'
                    ordering.insert(num + 1, '-offender__organisation')
                elif item == 'status__name':
                    ordering[num] = 'status'
                elif item == '-status__name':
                    ordering[num] = '-status'
                elif item == 'lodgement_number':
                    ordering[num] = 'id'  # Prefixes, RN, IF, CN and LA should be ignored
                elif item == '-lodgement_number':
                    ordering[num] = '-id'  # Prefixes, RN, IF, CN and LA should be ignored

            queryset = queryset.order_by(*ordering).distinct()

        setattr(view, '_datatables_total_count', total_count)
        return queryset


class SanctionOutcomePaginatedViewSet(viewsets.ModelViewSet):
    filter_backends = (SanctionOutcomeFilterBackend,)
    pagination_class = DatatablesPageNumberPagination
    queryset = SanctionOutcome.objects.none()
    serializer_class = SanctionOutcomeDatatableSerializer
    page_size = 10

    def get_queryset(self):
        # user = self.request.user
        if is_internal(self.request):
            return SanctionOutcome.objects.all()
        return SanctionOutcome.objects.none()

    @list_route(methods=['GET', ])
    def get_paginated_datatable(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        queryset = self.filter_queryset(queryset)
        self.paginator.page_size = queryset.count()
        result_page = self.paginator.paginate_queryset(queryset, request)
        serializer = SanctionOutcomeDatatableSerializer(result_page, many=True, context={'request': request, 'internal': is_internal(request)})
        s_data = serializer.data
        ret = self.paginator.get_paginated_response(s_data)
        return ret

    @list_route(methods=['GET', ])
    def external_datatable_list(self, request, *args, **kwargs):
        """
        This function is called from the external dashboard page by external user
        """
        queryset = SanctionOutcome.objects_for_external.filter(
            (Q(offender__person=request.user) & Q(offender__removed=False) & Q(registration_holder__isnull=True) & Q(driver__isnull=True)) |
            (Q(offender__isnull=True) & Q(registration_holder=request.user) & Q(driver__isnull=True)) |
            (Q(offender__isnull=True) & Q(driver=request.user))
        )
        queryset = self.filter_queryset(queryset).order_by('-id')
        self.paginator.page_size = queryset.count()
        result_page = self.paginator.paginate_queryset(queryset, request)
        serializer = SanctionOutcomeDatatableSerializer(result_page, many=True, context={'request': request, 'internal': is_internal(request)})
        ret = self.paginator.get_paginated_response(serializer.data)
        return ret

    @list_route(methods=['GET', ])
    def person_org_datatable_list(self, request, *args, **kwargs):
        """
        This function is called from the external dashboard page by external user
        """
        entity_id = request.GET.get('entity_id')
        entity_type = request.GET.get('entity_type')
        person = None
        org = None
        if entity_type == 'person':
            person = EmailUser.objects.get(id=entity_id)
        ## Expand to include Orgs
        elif entity_type == 'org':
            pass
        #import ipdb; ipdb.set_trace()
        queryset = SanctionOutcome.objects.filter(
            (Q(offender__person=person) & Q(offender__removed=False) & Q(registration_holder__isnull=True) & Q(driver__isnull=True)) |
            (Q(offender__isnull=True) & Q(registration_holder=person) & Q(driver__isnull=True)) |
            (Q(offender__isnull=True) & Q(driver=person))
        )
        queryset = self.filter_queryset(queryset).order_by('-id')
        self.paginator.page_size = queryset.count()
        result_page = self.paginator.paginate_queryset(queryset, request)
        serializer = SanctionOutcomeDatatableSerializer(result_page, many=True, context={'request': request, 'internal': is_internal(request)})
        ret = self.paginator.get_paginated_response(serializer.data)
        return ret


# class AmendmentRequestReasonViewSet(viewsets.ModelViewSet):
#     queryset = AmendmentRequestReason.objects.all()
#     serializer_class = AmendmentRequestReasonSerializer
#
#     @list_route(methods=['GET', ])
#     def reasons(self, request, *args, **kwargs):
#         try:
#             qs = self.get_queryset()
#             serializer = AmendmentRequestReasonSerializer(qs, many=True, context={'request': request})
#             return Response(serializer.data)
#
#         except serializers.ValidationError:
#             print(traceback.print_exc())
#             raise
#         except ValidationError as e:
#             print(traceback.print_exc())
#             if hasattr(e, 'error_dict'):
#                 raise serializers.ValidationError(repr(e.error_dict))
#             else:
#                 raise serializers.ValidationError(repr(e[0].encode('utf-8')))
#         except Exception as e:
#             print(traceback.print_exc())
#             raise serializers.ValidationError(str(e))


class RemediationActionViewSet(viewsets.ModelViewSet):
    queryset = RemediationAction.objects.all()
    serializer_class = RemediationActionSerializer

    @detail_route(methods=['POST'])
    @renderer_classes((JSONRenderer,))
    def request_amendment(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
                # Save the amendment request
                serializer = SaveAmendmentRequestForRemediationAction(data=request.data)
                serializer.is_valid(raise_exception=True)
                serializer.save()

                # Set this remediation action status to the 'OPEN'
                ra = self.get_object()
                serializer = RemediationActionUpdateStatusSerializer(ra, data={'status': RemediationAction.STATUS_OPEN}, context={'request': request})
                serializer.is_valid(raise_exception=True)
                serializer.save()

                # Email to the offender
                to_address = [ra.sanction_outcome.get_offender()[0].email, ]
                cc = None
                bcc = [member.email for member in ra.sanction_outcome.allocated_group.members]
                email_data = send_remediation_action_request_amendment_mail(to_address, ra, request, cc, bcc)

                # Comms log to the sanction outcome
                if email_data:
                    email_data['sanction_outcome'] = ra.sanction_outcome.id
                    serializer = SanctionOutcomeCommsLogEntrySerializer(data=email_data, partial=True)
                    serializer.is_valid(raise_exception=True)
                    serializer.save()

                # Action log to the sanction outcome
                ra.sanction_outcome.log_user_action(SanctionOutcomeUserAction.ACTION_REQUEST_AMENDMENT.format(ra.remediation_action_id), request)

                return Response(
                    serializer.data,
                    status=status.HTTP_201_CREATED
                )

        except serializers.ValidationError:
            print(traceback.print_exc())
            raise
        except ValidationError as e:
            print(traceback.print_exc())
            if hasattr(e, 'error_dict'):
                raise serializers.ValidationError(repr(e.error_dict))
            else:
                # raise serializers.ValidationError(repr(e[0].encode('utf-8')))
                raise serializers.ValidationError(repr(e[0]))
        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))

    @detail_route(methods=['GET'])
    @renderer_classes((JSONRenderer,))
    def accept(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
                ra = self.get_object()
                serializer = RemediationActionUpdateStatusSerializer(ra, data={'status': RemediationAction.STATUS_ACCEPTED}, context={'request': request})
                serializer.is_valid(raise_exception=True)

                # Action log to the sanction outcome before serializer.save() so that ACCEPTED log locates before CLOSED log.
                ra.sanction_outcome.log_user_action(SanctionOutcomeUserAction.ACTION_REMEDIATION_ACTION_ACCEPTED.format(ra.remediation_action_id), request)

                serializer.save()  # This may add CLOSE log to the action log

                # Email to the offender
                to_address = [ra.sanction_outcome.get_offender()[0].email, ]
                cc = None
                bcc = [member.email for member in ra.sanction_outcome.allocated_group.members]
                email_data = send_remediation_action_accepted_notice(to_address, ra, request, cc, bcc)

                # Comms log to the sanction outcome
                if email_data:
                    email_data['sanction_outcome'] = ra.sanction_outcome.id
                    serializer = SanctionOutcomeCommsLogEntrySerializer(data=email_data, partial=True)
                    serializer.is_valid(raise_exception=True)
                    serializer.save()

                headers = self.get_success_headers(serializer.data)
                return Response(
                    {},
                    status=status.HTTP_200_OK,
                    headers=headers
                )

        except serializers.ValidationError:
            print(traceback.print_exc())
            raise
        except ValidationError as e:
            print(traceback.print_exc())
            if hasattr(e, 'error_dict'):
                raise serializers.ValidationError(repr(e.error_dict))
            else:
                # raise serializers.ValidationError(repr(e[0].encode('utf-8')))
                raise serializers.ValidationError(repr(e[0]))
        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))

    @detail_route(methods=['POST'])
    @renderer_classes((JSONRenderer,))
    def submit(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
                serializer = self._update_instance(request)
                ra = serializer.instance
                instance = self.get_object()

                # Ensure status is Open and submbitter is same as offender.
                is_authorised_to_modify(request, instance)

                # Update status
                serializer = RemediationActionUpdateStatusSerializer(serializer.instance, data={'status': RemediationAction.STATUS_SUBMITTED}, context={'request': request})
                serializer.is_valid(raise_exception=True)
                serializer.save()

                # Email
                to_address = [member.email for member in ra.sanction_outcome.allocated_group.members]
                cc = None
                bcc = None
                email_data = send_remediation_action_submitted_notice(to_address, ra, request, cc, bcc)

                # Create new comms log entry
                data = {'sanction_outcome': ra.sanction_outcome.id}
                serializer = SanctionOutcomeCommsLogEntrySerializer(data=data)
                serializer.is_valid(raise_exception=True)
                comms_log_entry = serializer.save()

                # Attach files submitted to the communication log entry, so that they are displayed in the comms log table
                for document in ra.documents.all():
                    doc = comms_log_entry.documents.create(name=document.name)
                    doc._file = document._file
                    doc.save()

                # Log the above email as a communication log entry
                if email_data:
                    serializer = SanctionOutcomeCommsLogEntrySerializer(instance=comms_log_entry, data=email_data, partial=True)
                    serializer.is_valid(raise_exception=True)
                    serializer.save()

                # Action log to the sanction outcome
                user_action = ra.sanction_outcome.log_user_action(SanctionOutcomeUserAction.ACTION_REMEDIATION_ACTION_SUBMITTED.format(ra.remediation_action_id), request)
                user_action_serializer = SanctionOutcomeUserActionSerializer(user_action)
                data_returned = user_action_serializer.data

                headers = self.get_success_headers(serializer.data)
                return Response(
                    data_returned,
                    status=status.HTTP_200_OK,
                    headers=headers
                )

        except serializers.ValidationError:
            print(traceback.print_exc())
            raise
        except ValidationError as e:
            print(traceback.print_exc())
            if hasattr(e, 'error_dict'):
                raise serializers.ValidationError(repr(e.error_dict))
            else:
                # raise serializers.ValidationError(repr(e[0].encode('utf-8')))
                raise serializers.ValidationError(repr(e[0]))
        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))

    def get_queryset(self):
        if is_internal(self.request):
            return RemediationAction.objects.all()
        else:
            return RemediationAction.objects_for_external.filter(
                (Q(sanction_outcome__offender__person=self.request.user) & Q(sanction_outcome__registration_holder__isnull=True) & Q(sanction_outcome__driver__isnull=True)) |
                (Q(sanction_outcome__offender__isnull=True) & Q(sanction_outcome__registration_holder=self.request.user) & Q(sanction_outcome__driver__isnull=True)) |
                (Q(sanction_outcome__offender__isnull=True) & Q(sanction_outcome__driver=self.request.user))
            )
            # return RemediationAction.objects_for_external.filter(sanction_outcome__offender__person=self.request.user)

    def retrieve(self, request, *args, **kwargs):
        """
        Get existing
        """
        return super(RemediationActionViewSet, self).retrieve(request, *args, **kwargs)

    def _update_instance(self, request):
        instance = self.get_object()
        request_data = request.data

        due_date = request.data.get('due_date')
        due_date = datetime.strptime(due_date, '%d/%m/%Y')
        request_data['due_date'] = due_date.strftime('%Y-%m-%d')

        serializer = SaveRemediationActionSerializer(instance, data=request_data, partial=True, )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return serializer

    def update(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
                serializer = self._update_instance(request)

                headers = self.get_success_headers(serializer.data)
                return Response(
                    {},
                    status=status.HTTP_200_OK,
                    headers=headers
                )

        except serializers.ValidationError:
            print(traceback.print_exc())
            raise
        except ValidationError as e:
            print(traceback.print_exc())
            if hasattr(e, 'error_dict'):
                raise serializers.ValidationError(repr(e.error_dict))
            else:
                # raise serializers.ValidationError(repr(e[0].encode('utf-8')))
                raise serializers.ValidationError(repr(e[0]))
        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))

    @detail_route(methods=['POST'])
    @renderer_classes((JSONRenderer,))
    def process_default_document(self, request, *args, **kwargs):
        """
        Request sent from the immediate file uploader comes here for both saving and canceling.
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        print("process_default_document")
        print(request.data)
        try:
            instance = self.get_object()
            # process docs
            returned_data = process_generic_document(request, instance)
            # delete Sanction Outcome if user cancels modal
            action = request.data.get('action')
            if action == 'cancel' and returned_data:
                instance.status = 'discarded'
                instance.save()

            # return response
            if returned_data:
                return Response(returned_data)
            else:
                return Response()

        except serializers.ValidationError:
            print(traceback.print_exc())
            raise
        except ValidationError as e:
            if hasattr(e, 'error_dict'):
                raise serializers.ValidationError(repr(e.error_dict))
            else:
                # raise serializers.ValidationError(repr(e[0].encode('utf-8')))
                raise serializers.ValidationError(repr(e[0]))
        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))


class SanctionOutcomeViewSet(viewsets.ModelViewSet):
    queryset = SanctionOutcome.objects.all()
    serializer_class = SanctionOutcomeSerializer

    @detail_route(methods=['GET',])
    def doc(self, request, *args, **kwargs):
        try:
            file_name = request.GET['name']
            sanction_outcome_id = kwargs.get('pk', None)

            sanction_outcome = SanctionOutcome.objects_for_external.get(
                (
                    (Q(offender__person=request.user) & Q(registration_holder__isnull=True) & Q(driver__isnull=True)) |
                    (Q(offender__isnull=True) & Q(registration_holder=request.user) & Q(driver__isnull=True)) |
                    (Q(offender__isnull=True) & Q(driver=request.user))
                )
                & Q(id=sanction_outcome_id))
            so_file = SanctionOutcomeDocument.objects.get(Q(sanction_outcome=sanction_outcome) & Q(_file__icontains=file_name))

            with open(so_file._file.path, 'r') as f:
                mimetypes.init()
                f_name = os.path.basename(so_file._file.path)
                mime_type_guess = mimetypes.guess_type(f_name)
                if mime_type_guess is not None:
                    response = HttpResponse(f, content_type=mime_type_guess[0])
                response['Content-Disposition'] = 'inline;filename={}'.format(f_name)

                # Log access
                serializer = SanctionOutcomeDocumentAccessLogSerializer(data={'accessed_by_id': request.user.id, 'sanction_outcome_document_id': so_file.id})
                serializer.is_valid(raise_exception=True)
                serializer.save()

                return response
        except IOError:
            response = HttpResponseNotFound()
        return response

    @list_route(methods=['GET', ])
    def reasons(self, request, *args, **kwargs):
        qs = AmendmentRequestReason.objects.all()
        serializer = AmendmentRequestReasonSerializer(qs, many=True, context={'request': request})
        return Response(serializer.data)

    def get_queryset(self):
        # user = self.request.user
        if is_internal(self.request):
            return SanctionOutcome.objects.all()
        else:
            return SanctionOutcome.objects_for_external.filter(
                (Q(offender__person=self.request.user) & Q(registration_holder__isnull=True) & Q(driver__isnull=True)) |
                (Q(offender__isnull=True) & Q(registration_holder=self.request.user) & Q(driver__isnull=True)) |
                (Q(offender__isnull=True) & Q(driver=self.request.user))
            )
        return SanctionOutcome.objects.none()

    @list_route(methods=['GET', ])
    def types(self, request, *args, **kwargs):
        res_obj = []
        for choice in SO_TYPE_CHOICES:
            res_obj.append({'id': choice[0], 'display': choice[1]});
        res_json = json.dumps(res_obj)
        return HttpResponse(res_json, content_type='application/json')

    @list_route(methods=['GET', ])
    def statuses(self, request, *args, **kwargs):
        res_obj = []
        for choice in SanctionOutcome.STATUS_CHOICES:
            res_obj.append({'id': choice[0], 'display': choice[1]});
        res_json = json.dumps(res_obj)
        return HttpResponse(res_json, content_type='application/json')

    @list_route(methods=['GET', ])
    def payment_statuses(self, request, *args, **kwargs):
        res_obj = []
        for choice in SanctionOutcome.PAYMENT_STATUS_CHOICES:
            res_obj.append({'id': choice[0], 'display': choice[1]});
        res_json = json.dumps(res_obj)
        return HttpResponse(res_json, content_type='application/json')

    @list_route(methods=['GET', ])
    def statuses_for_external(self, request, *args, **kwargs):
        res_obj = []
        for choice in SanctionOutcome.STATUS_CHOICES_FOR_EXTERNAL:
            res_obj.append({'id': choice[0], 'display': choice[1]});
        res_json = json.dumps(res_obj)
        return HttpResponse(res_json, content_type='application/json')

    def retrieve(self, request, *args, **kwargs):
        """
        Get existing sanction outcome
        """
        return super(SanctionOutcomeViewSet, self).retrieve(request, *args, **kwargs)

    #def get_compliance_permission_groups(self, region_district_id, workflow_type):
    #    """
    #    Determine which CompliancePermissionGroup this sanction outcome should belong to
    #    :param region_district_id: The regionDistrict id this sanction outcome is in
    #    :param workflow_type: string like 'send_to_manager', 'return_to_officer', ...
    #    :return: CompliancePermissionGroup quersyet
    #    """
    #    # 1. Determine regionDistrict of this sanction outcome
    #    region_district = RegionDistrict.objects.filter(id=region_district_id)

    #    # 2. Determine which permission(s) is going to be apllied
    #    compliance_content_type = ContentType.objects.get(model="compliancepermissiongroup")
    #    codename = 'officer'
    #    if workflow_type == SanctionOutcome.WORKFLOW_SEND_TO_MANAGER:
    #        codename = 'manager'
    #    elif workflow_type == SanctionOutcome.WORKFLOW_DECLINE:
    #        codename = '---'
    #    elif workflow_type == SanctionOutcome.WORKFLOW_ENDORSE:
    #        codename = 'infringement_notice_coordinator'
    #    elif workflow_type == SanctionOutcome.WORKFLOW_RETURN_TO_OFFICER:
    #        codename = 'officer'
    #    elif workflow_type == SanctionOutcome.WORKFLOW_WITHDRAW:
    #        codename = '---'
    #    elif workflow_type == SanctionOutcome.WORKFLOW_CLOSE:
    #        codename = '---'
    #    else:
    #        # Should not reach here
    #        # instance.save()
    #        pass

    #    permissions = Permission.objects.filter(codename=codename, content_type_id=compliance_content_type.id)

    #    # 3. Find groups which has the permission(s) determined above in the regionDistrict.
    #    groups = CompliancePermissionGroup.objects.filter(region_district__in=region_district, permissions__in=permissions)

    #    return groups

    @detail_route(methods=['POST', ])
    @renderer_classes((JSONRenderer,))
    def update_assigned_to_id(self, request, *args, **kwargs):
        try:
            instance = self.get_object()

            validation_serializer = SanctionOutcomeSerializer(instance, context={'request': request})
            user_in_group = validation_serializer.data.get('user_in_group')

            if user_in_group:
                # current user is in the group
                if request.data.get('current_user'):
                    # current user is going to assign him or herself to the object
                    serializer_partial = UpdateAssignedToIdSerializer(instance=instance, data={'assigned_to_id': request.user.id,})
                else:
                    # current user is going to assign someone else to the object
                    serializer_partial = UpdateAssignedToIdSerializer(instance=instance, data=request.data)

                if serializer_partial.is_valid(raise_exception=True):
                    # Update only assigned_to_id data
                    serializer_partial.save()

                # Construct return value
                return_serializer = SanctionOutcomeSerializer(instance=instance, context={'request': request})
                headers = self.get_success_headers(return_serializer.data)
                return Response(return_serializer.data, status=status.HTTP_200_OK, headers=headers)
            else:
                return Response(validation_serializer.data, status=status.HTTP_200_OK)

        except serializers.ValidationError:
            print(traceback.print_exc())
            raise
        except ValidationError as e:
            print(traceback.print_exc())
            if hasattr(e, 'error_dict'):
                raise serializers.ValidationError(repr(e.error_dict))
            else:
                # raise serializers.ValidationError(repr(e[0].encode('utf-8')))
                raise serializers.ValidationError(repr(e[0]))
        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))

    @detail_route(methods=['GET', ])
    def action_log(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            qs = instance.action_logs.all()
            serializer = SanctionOutcomeUserActionSerializer(qs, many=True)
            return Response(serializer.data)
        except serializers.ValidationError:
            print(traceback.print_exc())
            raise
        except ValidationError as e:
            print(traceback.print_exc())
            if hasattr(e, 'error_dict'):
                raise serializers.ValidationError(repr(e.error_dict))
            else:
                # raise serializers.ValidationError(repr(e[0].encode('utf-8')))
                raise serializers.ValidationError(repr(e[0]))
        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))

    @detail_route(methods=['GET', ])
    def comms_log(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            qs = instance.comms_logs.all()
            serializer = SanctionOutcomeCommsLogEntrySerializer(qs, many=True)
            return Response(serializer.data)
        except serializers.ValidationError:
            print(traceback.print_exc())
            raise
        except ValidationError as e:
            print(traceback.print_exc())
            if hasattr(e, 'error_dict'):
                raise serializers.ValidationError(repr(e.error_dict))
            else:
                # raise serializers.ValidationError(repr(e[0].encode('utf-8')))
                raise serializers.ValidationError(repr(e[0]))
        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))

    def update(self, request, *args, **kwargs):
        # raise serializers.ValidationError('This is ValidationError in the update()')
        """
        Update existing sanction outcome
        """
        try:
            with transaction.atomic():
                instance = self.get_object()
                request_data = request.data

                # Offence should not be changed
                # Offender
                request_data['offender_id'] = request_data.get('current_offender', {}).get('id', None)
                if not request_data['offender_id'] and request_data.get('offender') and request_data.get('offender').get('id'):
                    request_data['offender_id'] = request_data.get('offender').get('id')
                else:
                    if not instance.is_parking_offence:
                        raise serializers.ValidationError('An offender must be selected.')

                # No workflow
                # No allocated group changes

                # When updated from with_dot status by adding registration_holder, status becomes awaiting_issuance
                if request_data['status']['id'] == SanctionOutcome.STATUS_WITH_DOT and (request_data['registration_holder_id'] or request_data['driver_id']):
                    request_data['status'] = SanctionOutcome.STATUS_AWAITING_ISSUANCE
                else:
                    request_data['status'] = request_data['status']['id']

                # Add number of files attached to the instance
                # By the filefield component in the front end, files should be already uploaded as attachment of this instance
                num_of_documents = instance.documents.all().count()

                serializer = SaveSanctionOutcomeSerializer(instance, data=request_data, partial=True, context={'num_of_documents_attached': num_of_documents})
                serializer.is_valid(raise_exception=True)
                instance = serializer.save()

                # Handle alleged committed offences
                # Once included=True, never set included=False
                # Once removed=True, never set removed=False
                for existing_aco in AllegedCommittedOffence.objects.filter(sanction_outcome=instance):
                    for new_aco in request_data.get('alleged_committed_offences', {}):
                        if existing_aco.id == new_aco.get('id') and existing_aco.included != new_aco.get('included'):
                            serializer = AllegedCommittedOffenceSerializer(existing_aco, data={'included': new_aco.get('included')}, partial=True)
                            serializer.is_valid(raise_exception=True)
                            serializer.save()
                            if existing_aco.included:
                                instance.log_user_action(SanctionOutcomeUserAction.ACTION_RESTORE_ALLEGED_COMMITTED_OFFENCE.format(existing_aco.alleged_offence), request)
                            else:
                                instance.log_user_action(SanctionOutcomeUserAction.ACTION_REMOVE_ALLEGED_COMMITTED_OFFENCE.format(existing_aco.alleged_offence), request)

                instance.log_user_action(SanctionOutcomeUserAction.ACTION_UPDATE.format(instance.lodgement_number), request)

                # Return
                return_serializer = SanctionOutcomeSerializer(instance=instance, context={'request': request})
                headers = self.get_success_headers(return_serializer.data)
                return Response(
                    return_serializer.data,
                    status=status.HTTP_200_OK,
                    headers=headers
                )

        except serializers.ValidationError:
            print(traceback.print_exc())
            raise
        except ValidationError as e:
            print(traceback.print_exc())
            if hasattr(e, 'error_dict'):
                raise serializers.ValidationError(repr(e.error_dict))
            else:
                # raise serializers.ValidationError(repr(e[0].encode('utf-8')))
                raise serializers.ValidationError(repr(e[0]))
        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))

    def create(self, request, *args, **kwargs):
        """
        Create new sanction outcome from the modal
        """
        try:
            with transaction.atomic():
                res_json = {}

                request_data = request.data

                if request_data['type'] == SO_TYPE_REMEDIATION_NOTICE:
                    if not len(request_data['remediation_actions']):
                        # Type is remediation action but no remediation actions defined
                        raise serializers.ValidationError(['You must define at least one remediation action.'])

                # offence and offender
                request_data['offence_id'] = request_data.get('current_offence', {}).get('id', None)  # This raises an error when empty string is passed
                request_data['offender_id'] = request_data.get('current_offender', {})
                if request_data['offender_id'] in ({}, ''):
                    request_data['offender_id'] = None
                else:
                    request_data['offender_id'] = request_data['offender_id'].get('id', None)

                # workflow
                workflow_type = request_data.get('workflow_type', '')

                # allocated group
                regionDistrictId = request_data['district_id'] if request_data['district_id'] else request_data['region_id']
                groups = self.get_compliance_permission_groups(regionDistrictId, workflow_type)
                if groups.count() == 1:
                    group = groups.first()
                elif groups.count() > 1:
                    group = groups.first()
                request_data['allocated_group_id'] = group.id

                # Count number of files uploaded
                num_of_documents = 0
                temporary_document_collection_id = request.data.get('temporary_document_collection_id')
                if temporary_document_collection_id:
                    temp_doc_collection, created = TemporaryDocumentCollection.objects.get_or_create(
                        id=temporary_document_collection_id)
                    if temp_doc_collection:
                        num_of_documents = temp_doc_collection.documents.count()
                # request_data['num_of_documents_attached'] = num_of_documents  # Pass number of files attached for validation
                                                                              # You can access this data by self.initial_data['num_of_documents_attached'] in validate(self, data) method

                # Save sanction outcome (offence, offender, alleged_offences)
                if hasattr(request_data, 'id') and request_data['id']:
                    instance = SanctionOutcome.objects.get(id=request_data['id'])
                    serializer = SaveSanctionOutcomeSerializer(instance, data=request_data, partial=True, context={'num_of_documents_attached': num_of_documents})
                else:
                    serializer = SaveSanctionOutcomeSerializer(data=request_data, partial=True, context={'num_of_documents_attached': num_of_documents})
                serializer.is_valid(raise_exception=True)
                instance = serializer.save()

                # Action log for creation
                instance.log_user_action(SanctionOutcomeUserAction.ACTION_CREATE.format(instance.lodgement_number), request)

                # Link temp uploaded files to the sanction outcome
                if num_of_documents:
                    for doc in temp_doc_collection.documents.all():
                        save_default_document_obj(instance, doc)
                    temp_doc_collection.delete()

                # Create relations between this sanction outcome and the alleged offence(s)
                count_alleged_offences = 0
                for ao_id in request_data['alleged_offence_ids_included']:
                    # alleged_offence = AllegedOffence.objects.get(id=ao_id)
                    # alleged_commited_offence = AllegedCommittedOffence.objects.create(sanction_outcome=instance, alleged_offence=alleged_offence, included=True)

                    data = {'alleged_offence_id': ao_id, 'sanction_outcome_id': instance.id}
                    serializer = AllegedCommittedOffenceCreateSerializer(data=data, context={'request': request})
                    serializer.is_valid(raise_exception=True)
                    serializer.save()
                    count_alleged_offences += 1

                # Validate if alleged offences are selected
                if count_alleged_offences == 0:
                    if instance.type == SO_TYPE_INFRINGEMENT_NOTICE:
                        raise serializers.ValidationError(['You must select an alleged committed offence.'])
                    else:
                        raise serializers.ValidationError(['You must select at least one alleged committed offence.'])

                # Validate if an offender is selected
                if not instance.offender:
                    if not instance.is_parking_offence:  #
                        raise serializers.ValidationError(['An offender must be selected.'])

                # Validate if an offender or a registration number is set at least
                if instance.is_parking_offence:
                    if not instance.registration_number and not instance.offender:
                        raise serializers.ValidationError(['Either offender or registration number is required.'])

                for id in request_data['alleged_offence_ids_excluded']:
                    try:
                        alleged_offence = AllegedOffence.objects.get(id=id)
                        alleged_commited_offence = AllegedCommittedOffence.objects.create(sanction_outcome=instance, alleged_offence=alleged_offence, included=False)
                    except:
                        pass  # Should not reach here

                # Handle workflow
                if workflow_type == SanctionOutcome.WORKFLOW_SEND_TO_MANAGER:
                    instance.send_to_manager(request)
                elif not workflow_type:
                    instance.save()

                # Save remediation action, and link to the sanction outcome
                for dict in request_data['remediation_actions']:
                    dict['sanction_outcome_id'] = instance.id
                    dict['action'] = dict['action_text']
                    remediation_action = SaveRemediationActionSerializer(data=dict)
                    if remediation_action.is_valid(raise_exception=True):
                        remediation_action.save()

                # Log CallEmail action
                if request_data.get('call_email_id'):
                    call_email = CallEmail.objects.get(id=request_data.get('call_email_id'))
                    call_email.log_user_action(
                            CallEmailUserAction.ACTION_SANCTION_OUTCOME.format(
                                instance.lodgement_number), 
                            request)

                # Log Inspection action
                if request_data.get('inspection_id'):
                    inspection = Inspection.objects.get(id=request_data.get('inspection_id'))
                    inspection.log_user_action(
                            InspectionUserAction.ACTION_SANCTION_OUTCOME.format(
                                instance.lodgement_number), 
                            request)

                # Create/Retrieve comms log entry
                comms_log_id = request.data.get('comms_log_id')
                if comms_log_id and comms_log_id is not 'null':
                    workflow_entry = instance.comms_logs.get(id=comms_log_id)
                else:
                    workflow_entry = self.add_comms_log(request, instance, workflow=True)

                if workflow_type == SanctionOutcome.WORKFLOW_SEND_TO_MANAGER:
                    # email_data = prepare_mail(request, instance, workflow_entry, send_mail)
                    #compliance_group = CompliancePermissionGroup.objects.get(id=request.data.get('allocated_group_id'))
                    to_address = [user.email for user in compliance_group.members.all()]
                    cc = [request.user.email,]
                    bcc = None
                    email_data = send_to_manager_email(to_address, instance, workflow_entry, request, cc, bcc)

                    # Log email communication
                    serializer = SanctionOutcomeCommsLogEntrySerializer(instance=workflow_entry, data=email_data, partial=True)
                    serializer.is_valid(raise_exception=True)
                    serializer.save()

                # Return
                return HttpResponse(res_json, content_type='application/json')

        except serializers.ValidationError:
            print(traceback.print_exc())
            raise
        except ValidationError as e:
            print(traceback.print_exc())
            if hasattr(e, 'error_dict'):
                raise serializers.ValidationError(repr(e.error_dict))
            else:
                # raise serializers.ValidationError(repr(e[0].encode('utf-8')))
                raise serializers.ValidationError(repr(e[0]))
        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))

    @detail_route(methods=['POST'])
    @renderer_classes((JSONRenderer,))
    def process_default_document(self, request, *args, **kwargs):
        """
        Request sent from the immediate file uploader comes here for both saving and canceling.
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        print("process_default_document")
        print(request.data)
        try:
            instance = self.get_object()
            # process docs
            returned_data = process_generic_document(request, instance)
            # delete Sanction Outcome if user cancels modal
            action = request.data.get('action')
            if action == 'cancel' and returned_data:
                instance.status = 'discarded'
                instance.save()

            # return response
            if returned_data:
                return Response(returned_data)
            else:
                return Response()

        except serializers.ValidationError:
            print(traceback.print_exc())
            raise
        except ValidationError as e:
            if hasattr(e, 'error_dict'):
                raise serializers.ValidationError(repr(e.error_dict))
            else:
                # raise serializers.ValidationError(repr(e[0].encode('utf-8')))
                raise serializers.ValidationError(repr(e[0]))
        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))

    @list_route(methods=['GET', ])
    def datatable_list(self, request, *args, **kwargs):
        try:
            qs = self.get_queryset()
            serializer = SanctionOutcomeSerializer(qs, many=True, context={'request': request})
            return Response({ 'tableData': serializer.data })

        except serializers.ValidationError:
            print(traceback.print_exc())
            raise
        except ValidationError as e:
            print(traceback.print_exc())
            if hasattr(e, 'error_dict'):
                raise serializers.ValidationError(repr(e.error_dict))
            else:
                # raise serializers.ValidationError(repr(e[0].encode('utf-8')))
                raise serializers.ValidationError(repr(e[0]))
        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))

    @detail_route(methods=['POST'])
    @renderer_classes((JSONRenderer,))
    def process_comms_log_document(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            returned_data = process_generic_document(
                request,
                instance,
                document_type='comms_log'
            )
            if returned_data:
                return Response(returned_data)
            else:
                return Response()

        except serializers.ValidationError:
            print(traceback.print_exc())
            raise
        except ValidationError as e:
            if hasattr(e, 'error_dict'):
                raise serializers.ValidationError(repr(e.error_dict))
            else:
                # raise serializers.ValidationError(repr(e[0].encode('utf-8')))
                raise serializers.ValidationError(repr(e[0]))
        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))

    @detail_route(methods=['POST'])
    @renderer_classes((JSONRenderer,))
    def send_parking_infringement(self, request, instance=None, *args, **kwargs):
        try:
            with transaction.atomic():

                instance = self.get_object() if not instance else instance
                # instance.endorse_parking_infringement()

                comms_log_id = request.data.get('comms_log_id')
                if comms_log_id and comms_log_id is not 'null':
                    workflow_entry = instance.comms_logs.get(id=comms_log_id)
                # else:
                #     workflow_entry = self.add_comms_log(request, instance, workflow=True)
                if workflow_entry:
                    workflow_entry.delete()

                # workflow_entry = self.add_comms_log(request, instance, workflow=True)  # We don't send email, therefore we don't need comms log here
                instance.endorse()
                if not instance.issued_on_paper:
                    # attachments = create_infringement_notice_ybw(instance, workflow_entry)
                    attachments = create_infringement_notice_ybw(instance)

                    # Log action
                    instance.log_user_action(SanctionOutcomeUserAction.ACTION_ENDORSE_AND_ISSUE.format(instance.lodgement_number), request)

                # Email to the offender, and bcc to the respoinsible officer, manager and infringement notice coordinators
                # inc_group = SanctionOutcome.get_compliance_permission_group(None, SanctionOutcome.WORKFLOW_ENDORSE)
                # inc_emails = [member.email for member in inc_group.members]
                # to_address = [instance.get_offender()[0].email, ]
                # cc = None
                # bcc = [instance.responsible_officer.email, request.user.email] + inc_emails
                # email_data = send_infringement_notice(to_address, instance, workflow_entry, request, cc, bcc)

                # Log the above email as a communication log entry
                # if email_data:
                #     email_data['sanction_outcome'] = instance.id
                #     serializer = SanctionOutcomeCommsLogEntrySerializer(instance=workflow_entry, data=email_data, partial=True)
                #     serializer.is_valid(raise_exception=True)
                #     serializer.save()

                # instance.log_user_action(SanctionOutcomeUserAction.ACTION_ISSUE_PARKING_INFRINGEMENT.format(instance.lodgement_number, ', '.join(to_address)), request)

                return Response(
                    # return_serializer.data,
                    status=status.HTTP_200_OK,
                    # headers=headers
                )

        except serializers.ValidationError:
            print(traceback.print_exc())
            raise
        except ValidationError as e:
            print(traceback.print_exc())
            if hasattr(e, 'error_dict'):
                raise serializers.ValidationError(repr(e.error_dict))
            else:
                # raise serializers.ValidationError(repr(e[0].encode('utf-8')))
                raise serializers.ValidationError(repr(e[0]))
        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))

    @detail_route(methods=['POST'])
    @renderer_classes((JSONRenderer,))
    def record_fer_case_number(self, request, instance=None, *args, **kwargs):
        try:
            with transaction.atomic():
                instance = self.get_object() if not instance else instance
                data_requested = request.data.get('fer_case_number_1st', '') + '/' + request.data.get('fer_case_number_2nd', '')
                serializer = RecordFerCaseNumberSerializer(instance=instance, data={'fer_case_number': data_requested},)
                serializer.is_valid(raise_exception=True)
                serializer.save()

                # instance.status = SanctionOutcome.STATUS_CLOSED
                instance.save()
                instance.close()

                return_serializer = SanctionOutcomeSerializer(instance=instance, context={'request': request})
                headers = self.get_success_headers(return_serializer.data)
                return Response(
                    return_serializer.data,
                    status=status.HTTP_200_OK,
                    headers=headers
                )

        except serializers.ValidationError:
            print(traceback.print_exc())
            raise
        except ValidationError as e:
            print(traceback.print_exc())
            if hasattr(e, 'error_dict'):
                raise serializers.ValidationError(repr(e.error_dict))
            else:
                # raise serializers.ValidationError(repr(e[0].encode('utf-8')))
                raise serializers.ValidationError(repr(e[0]))
        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))

    @detail_route(methods=['POST'])
    @renderer_classes((JSONRenderer,))
    def extend_due_date(self, request, instance=None, *args, **kwargs):
        try:
            with transaction.atomic():
                if not instance:
                    instance = self.get_object()

                comms_log_id = request.data.get('comms_log_id')
                if comms_log_id and comms_log_id is not 'null':
                    workflow_entry = instance.comms_logs.get(id=comms_log_id)
                else:
                    workflow_entry = self.add_comms_log(request, instance, workflow=True)
                # workflow_entry.text = 'test katsu'
                workflow_entry.save()

                new_due_date = request.data.get('new_due_date', None)
                if not new_due_date:
                    raise serializers.ValidationError({'New due date': ['You must enter a new due date.', ]})

                new_due_date = datetime.strptime(new_due_date, '%d/%m/%Y').date()
                reason = request.data.get('reason', '')

                if instance.extend_due_date(new_due_date, reason, request.user.id):
                    # Action log
                    dates = instance.due_dates.all().order_by('-id')
                    last_date = dates[0]
                    second_last = dates[1]
                    instance.log_user_action(SanctionOutcomeUserAction.ACTION_EXTEND_DUE_DATE.format(
                        instance.lodgement_number,
                        second_last.due_date_applied.strftime('%d/%m/%Y'),
                        last_date.due_date_applied.strftime('%d/%m/%Y')),
                        request)

                to_address = [instance.get_offender()[0].email,]
                cc = None
                bcc = [instance.responsible_officer.email, request.user.email] if instance.responsible_officer else None
                email_data = send_due_date_extended_mail(to_address, instance, workflow_entry, request, cc, bcc)

                # Log the above email as a communication log entry
                if email_data:
                    serializer = SanctionOutcomeCommsLogEntrySerializer(instance=workflow_entry, data=email_data, partial=True)
                    serializer.is_valid(raise_exception=True)
                    serializer.save()

                # Return
                return_serializer = SanctionOutcomeSerializer(instance=instance, context={'request': request})
                headers = self.get_success_headers(return_serializer.data)
                return Response(
                    return_serializer.data,
                    status=status.HTTP_201_CREATED,
                    headers=headers
                )

        except serializers.ValidationError:
            print(traceback.print_exc())
            raise
        except ValidationError as e:
            print(traceback.print_exc())
            if hasattr(e, 'error_dict'):
                raise serializers.ValidationError(repr(e.error_dict))
            else:
                # raise serializers.ValidationError(repr(e[0].encode('utf-8')))
                raise serializers.ValidationError(repr(e[0]))
        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))


    @detail_route(methods=['POST'])
    @renderer_classes((JSONRenderer,))
    def workflow_action(self, request, instance=None, *args, **kwargs):
        try:
            with transaction.atomic():
                if not instance:
                    instance = self.get_object()

                comms_log_id = request.data.get('comms_log_id')
                if comms_log_id and comms_log_id is not 'null':
                    workflow_entry = instance.comms_logs.get(id=comms_log_id)
                else:
                    workflow_entry = self.add_comms_log(request, instance, workflow=True)

                # Set status
                workflow_type = request.data.get('workflow_type')
                reason = request.data.get('details')
                email_data = None

                if workflow_type == SanctionOutcome.WORKFLOW_SEND_TO_MANAGER:
                    instance.send_to_manager(request)

                    # Email to manager
                    to_address = [member.email for member in instance.allocated_group.members]
                    cc = [instance.responsible_officer.email,] if instance.responsible_officer else None
                    bcc = None
                    email_data = send_to_manager_email(to_address, instance, workflow_entry, request, cc, bcc)

                elif workflow_type == SanctionOutcome.WORKFLOW_DECLINE:
                    if not reason:
                        raise serializers.ValidationError({'Reason': ['You must enter the reason.', ]})
                    instance.decline(request)

                    to_address = [instance.responsible_officer.email,]
                    cc = [request.user.email, ]
                    bcc = None
                    email_data = send_decline_email(to_address, instance, workflow_entry, request, cc, bcc)

                elif workflow_type == SanctionOutcome.WORKFLOW_ENDORSE:
                    if instance.type == SO_TYPE_LETTER_OF_ADVICE:
                        instance.endorse()
                        if not instance.issued_on_paper:
                            pdf_file_name = 'letter_of_advice_{}_{}.pdf'.format(instance.lodgement_number, datetime.now().strftime("%Y%m%d%H%M%S"))
                            document = create_letter_of_advice_pdf(pdf_file_name, instance)

                            # Action log for endorsement and issuance
                            instance.log_user_action(SanctionOutcomeUserAction.ACTION_ENDORSE_AND_ISSUE.format(instance.lodgement_number), request)
                            instance.status = SanctionOutcome.STATUS_AWAITING_PRINT_AND_POST
                            instance.save()
                        else:
                            instance.log_user_action(SanctionOutcomeUserAction.ACTION_ENDORSE.format(instance.lodgement_number), request)
                            instance.status = SanctionOutcome.STATUS_CLOSED
                            instance.log_user_action(SanctionOutcomeUserAction.ACTION_CLOSE.format(instance.lodgement_number), request)
                            instance.save()

                    elif instance.type == SO_TYPE_CAUTION_NOTICE:
                        instance.endorse()
                        if not instance.issued_on_paper:
                            pdf_file_name = 'caution_notice_{}_{}.pdf'.format(instance.lodgement_number, datetime.now().strftime("%Y%m%d%H%M%S"))
                            document = create_caution_notice_pdf(pdf_file_name, instance)

                            # Action log for endorsement and issuance
                            instance.log_user_action(SanctionOutcomeUserAction.ACTION_ENDORSE_AND_ISSUE.format(instance.lodgement_number), request)
                            instance.status = SanctionOutcome.STATUS_AWAITING_PRINT_AND_POST
                            instance.save()
                        else:
                            instance.log_user_action(SanctionOutcomeUserAction.ACTION_ENDORSE.format(instance.lodgement_number), request)
                            instance.status = SanctionOutcome.STATUS_CLOSED
                            instance.log_user_action(SanctionOutcomeUserAction.ACTION_CLOSE.format(instance.lodgement_number), request)
                            instance.save()

                    elif instance.type == SO_TYPE_REMEDIATION_NOTICE:
                        instance.endorse()
                        if not instance.issued_on_paper:
                            # email_data = send_remediation_notice(to_address, instance, workflow_entry, request, cc, bcc)
                            pdf_file_name = 'remediation_notice_{}_{}.pdf'.format(instance.lodgement_number, datetime.now().strftime( "%Y%m%d%H%M%S"))
                            document = create_remediation_notice_pdf(pdf_file_name, instance)
                        else:
                            # Nothing to do here.  All done in the instance.endorse() method
                            pass
                    elif instance.type == SO_TYPE_INFRINGEMENT_NOTICE:
                        # This is Infringement Notice
                        workflow_entry.delete()  # Now we don't send an email.  Therefore we don't need this object created above to store comms log.
                        if not instance.is_parking_offence or (instance.is_parking_offence and instance.offender):
                            instance.endorse()
                            if not instance.issued_on_paper:
                                # attachments = create_infringement_notice_ybw(instance, workflow_entry)
                                attachments = create_infringement_notice_ybw(instance)

                                # Log action
                                instance.log_user_action(SanctionOutcomeUserAction.ACTION_ENDORSE_AND_ISSUE.format(instance.lodgement_number), request)
                            else:
                                # Nothing to do here.  All done in the instance.endorse() method
                                pass
                        else:
                            # This is a parking infringement but no offenders are set
                            instance.send_to_inc()

                            # Because we send emails by cron job anyway, we don't send emails here
                            # inc_group = SanctionOutcome.get_compliance_permission_group(None, SanctionOutcome.WORKFLOW_ENDORSE)
                            # inc_emails = [member.email for member in inc_group.members]
                            # to_address = inc_emails
                            # cc = [instance.responsible_officer.email, request.user.email]
                            # bcc = []

                            # Email to infringement notice coordinators
                            # email_data = send_parking_infringement_without_offenders(to_address, instance, workflow_entry, request, cc, bcc)

                            # Log action
                            instance.log_user_action(SanctionOutcomeUserAction.ACTION_ENDORSE.format(instance.lodgement_number), request)
                    else:
                        # Should not reach here
                        pass

                elif workflow_type == SanctionOutcome.WORKFLOW_RETURN_TO_OFFICER:
                    if not reason:
                        raise serializers.ValidationError({'Reason': ['You must enter the reason.', ]})
                    instance.return_to_officer(request)

                    # Email to the responsible officer
                    to_address = [instance.responsible_officer.email,]
                    cc = [request.user.email,] if request.user else None
                    bcc = None
                    email_data = send_return_to_officer_email(to_address, instance, workflow_entry, request, cc, bcc)

                elif workflow_type == SanctionOutcome.WORKFLOW_ESCALATE_FOR_WITHDRAWAL:
                    if not reason:
                        raise serializers.ValidationError({'Reason': ['You must enter the reason.', ]})
                    instance.escalate_for_withdrawal(request)

                    # Email to branch manager,
                    to_address = [member.email for member in instance.allocated_group.members]
                    cc = [request.user.email,] if request.user else None
                    bcc = None
                    email_data = send_escalate_for_withdrawal_email(to_address, instance, workflow_entry, request, cc, bcc)

                elif workflow_type == SanctionOutcome.WORKFLOW_WITHDRAW_BY_MANAGER:
                    if not reason:
                        raise serializers.ValidationError({'Reason': ['You must enter the reason.', ]})
                    instance.withdraw_by_manager(request)

                    # Email to offender
                    to_address = [instance.get_offender()[0].email, ]
                    cc = [request.user.email, instance.responsible_officer.email, ] if request else None
                    bcc = None
                    email_data = send_withdraw_by_manager_email(to_address, instance, workflow_entry, request, cc, bcc)

                elif workflow_type == SanctionOutcome.WORKFLOW_WITHDRAW_BY_BRANCH_MANAGER:
                    if not reason:
                        raise serializers.ValidationError({'Reason': ['You must enter the reason.', ]})
                    instance.withdraw_by_branch_manager(request)

                    # Email to offender
                    to_address = [instance.get_offender()[0].email, ]
                    cc = [request.user.email, instance.responsible_officer.email, ] if request else None
                    bcc = None
                    email_data = send_withdraw_by_branch_manager_email(to_address, instance, workflow_entry, request, cc, bcc)

                elif workflow_type == SanctionOutcome.WORKFLOW_RETURN_TO_INFRINGEMENT_NOTICE_COORDINATOR:
                    if not reason:
                        raise serializers.ValidationError({'Reason': ['You must enter the reason.', ]})
                    instance.return_to_infringement_notice_coordinator(request)

                    # Email to Infringement Notice Coordinator
                    to_address = [member.email for member in instance.allocated_group.members]
                    cc = [instance.responsible_officer.email, request.user.email]
                    bcc = None
                    email_data = send_return_to_infringement_notice_coordinator_email(to_address, instance, workflow_entry, request, cc, bcc)

                elif workflow_type == SanctionOutcome.WORKFLOW_MARK_DOCUMENT_POSTED:
                    workflow_entry.delete()
                    instance.mark_document_posted(request)
                    instance.log_user_action(SanctionOutcomeUserAction.ACTION_MARK_AS_POSTED.format(instance.lodgement_number), request)

                else:
                    # Should not reach here
                    # instance.save()
                    pass

                # Log the above email as a communication log entry
                if email_data:
                    serializer = SanctionOutcomeCommsLogEntrySerializer(instance=workflow_entry, data=email_data, partial=True)
                    serializer.is_valid(raise_exception=True)
                    serializer.save()

                return_serializer = SanctionOutcomeSerializer(instance=instance, context={'request': request})
                headers = self.get_success_headers(return_serializer.data)
                return Response(
                    return_serializer.data,
                    status=status.HTTP_201_CREATED,
                    headers=headers
                )
        except serializers.ValidationError:
            print(traceback.print_exc())
            raise
        except ValidationError as e:
            print(traceback.print_exc())
            if hasattr(e, 'error_dict'):
                raise serializers.ValidationError(repr(e.error_dict))
            else:
                # raise serializers.ValidationError(repr(e[0].encode('utf-8')))
                raise serializers.ValidationError(repr(e[0]))
        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))

    @detail_route(methods=['POST', ])
    @renderer_classes((JSONRenderer,))
    def add_comms_log(self, request, instance=None, workflow=False, *args, **kwargs):
        print('SanctionOutcome.add_comms_log')
        try:
            with transaction.atomic():
                # create sanction outcome instance if not passed to this method
                if not instance:
                    instance = self.get_object()
                # add sanction outcome attribute to request_data
                request_data = request.data.copy()
                request_data['sanction_outcome'] = u'{}'.format(instance.id)
                if request_data.get('comms_log_id'):
                    comms = SanctionOutcomeCommsLogEntry.objects.get(id=request_data.get('comms_log_id'))
                    serializer = SanctionOutcomeCommsLogEntrySerializer(instance=comms, data=request_data)
                else:
                    serializer = SanctionOutcomeCommsLogEntrySerializer(data=request_data)
                serializer.is_valid(raise_exception=True)
                # overwrite comms with updated instance
                comms = serializer.save()

                if workflow:
                    return comms
                else:
                    return Response(serializer.data)
        except serializers.ValidationError:
            print(traceback.print_exc())
            raise
        except ValidationError as e:
            print(traceback.print_exc())
            if hasattr(e, 'error_dict'):
                raise serializers.ValidationError(repr(e.error_dict))
            else:
                # raise serializers.ValidationError(repr(e[0].encode('utf-8')))
                raise serializers.ValidationError(repr(e[0]))
        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))
