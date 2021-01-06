import json
import re
import operator
import traceback
import os
import base64
import geojson
from django.db.models import Q, Min, Max
from django.db import transaction
from django.http import HttpResponse
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.exceptions import ValidationError
from django.conf import settings
from wildlifecompliance import settings
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from rest_framework import viewsets, serializers, status, generics, views, filters
import rest_framework.exceptions as rest_exceptions
from rest_framework.decorators import (
    detail_route,
    list_route,
    renderer_classes,
    parser_classes,
    api_view
)
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser, BasePermission
from rest_framework.pagination import PageNumberPagination
from collections import OrderedDict
from django.core.cache import cache
from ledger.accounts.models import EmailUser, Address
from ledger.address.models import Country
from ledger.checkout.utils import calculate_excl_gst
from datetime import datetime, timedelta, date
from django.urls import reverse
from django.shortcuts import render, redirect, get_object_or_404
from wildlifecompliance.components.main.api import save_location
from wildlifecompliance.components.main.models import TemporaryDocumentCollection
from wildlifecompliance.components.main.process_document import (
        process_generic_document, 
        save_comms_log_document_obj
        )
from wildlifecompliance.components.main.email import prepare_mail
from wildlifecompliance.components.users.serializers import (
    UserAddressSerializer,
    ComplianceUserDetailsSerializer,
)
from wildlifecompliance.helpers import is_customer, is_internal
from wildlifecompliance.components.legal_case.models import (
    LegalCase,
    LegalCaseUserAction,
    LegalCaseCommsLogEntry,
    LegalCaseCommsLogDocument,
    LegalCasePriority,
    LegalCaseRunningSheetEntry,
    LegalCasePerson,
    CourtProceedingsJournalEntry,
    BriefOfEvidence,
    ProsecutionBrief,
    ProsecutionBriefDocument,
    CourtProceedings, CourtDate, Court, CourtOutcomeType)
from wildlifecompliance.components.legal_case.generate_pdf import create_document_pdf_bytes

from wildlifecompliance.components.call_email.models import (
        CallEmailUserAction,
        )
from wildlifecompliance.components.legal_case.serializers import (
    BaseLegalCaseSerializer,
    LegalCaseBriefOfEvidenceSerializer,
    LegalCaseProsecutionBriefSerializer,
    SaveLegalCaseSerializer,
    LegalCaseUserActionSerializer,
    LegalCaseCommsLogEntrySerializer,
    LegalCaseDatatableSerializer,
    UpdateAssignedToIdSerializer,
    LegalCasePrioritySerializer,
    CreateLegalCaseRunningSheetEntrySerializer,
    SaveLegalCaseRunningSheetEntrySerializer,
    LegalCaseRunningSheetSerializer,
    LegalCaseRunningSheetEntrySerializer,
    DeleteReinstateLegalCaseRunningSheetEntrySerializer,
    VersionSerializer,
    RunningSheetEntryHistorySerializer,
    CreateLegalCasePersonSerializer,
    JournalEntryHistorySerializer,
    CourtProceedingsJournalEntrySerializer,
    SaveCourtProceedingsJournalEntrySerializer,
    DeleteReinstateCourtProceedingsJournalEntrySerializer,
    CreateCourtProceedingsJournalEntrySerializer,
    CourtProceedingsJournalSerializer,
    BriefOfEvidenceSerializer,
    ProsecutionBriefSerializer,
    SaveCourtDateEntrySerializer, 
    CourtSerializer, 
    LegalCaseNoRunningSheetSerializer,
    CourtOutcomeTypeSerializer)
from wildlifecompliance.components.users.models import (
    CompliancePermissionGroup,    
)
from wildlifecompliance.components.organisations.models import (
    Organisation,    
)
from django.contrib.auth.models import Permission, ContentType

from rest_framework_datatables.pagination import DatatablesPageNumberPagination
from rest_framework_datatables.filters import DatatablesFilterBackend
from rest_framework_datatables.renderers import DatatablesRenderer

from wildlifecompliance.components.main.utils import FakeRequest
from wildlifecompliance.components.legal_case.email import (
    send_mail)
from wildlifecompliance.components.artifact.utils import (
        build_all_boe_roi_hierarchy, 
        update_boe_roi_ticked,
        update_pb_roi_ticked,
        build_all_boe_other_statements_hierarchy,
        update_boe_other_statements_ticked,
        update_pb_other_statements_ticked,
        generate_boe_physical_artifacts,
        generate_boe_document_artifacts,
        update_boe_physical_artifacts,
        update_boe_document_artifacts_ticked,
        update_pb_physical_artifacts,
        update_pb_document_artifacts_ticked,
        copy_brief_of_evidence_artifacts_to_prosecution_brief,
        )


#class FakeRequest():
 #   def __init__(self, data):
  #      self.data = data


class LegalCaseFilterBackend(DatatablesFilterBackend):

    def filter_queryset(self, request, queryset, view):
        # Get built-in DRF datatables queryset first to join with search text, then apply additional filters
        # super_queryset = super(CallEmailFilterBackend, self).filter_queryset(request, queryset, view).distinct()

        total_count = queryset.count()
        status_filter = request.GET.get('status_description')
        date_from = request.GET.get('date_from')
        date_to = request.GET.get('date_to')
        search_text = request.GET.get('search[value]')

        if search_text:
            search_text = search_text.lower()
            search_text_legal_case_ids = []
            for legal_case in queryset:
                #lodged_on_str = time.strftime('%d/%m/%Y', call_email.lodged_on)
                case_created_date_str = legal_case.case_created_date.strftime('%d/%m/%Y') if legal_case.case_created_date else ''
                if (search_text in (legal_case.number.lower() if legal_case.number else '')
                    or search_text in (legal_case.status.lower() if legal_case.status else '')
                    or search_text in (case_created_date_str.lower() if case_created_date_str else '')
                    or search_text in (legal_case.title.lower() if legal_case.title else '')
                    or search_text in (
                        legal_case.assigned_to.first_name.lower() + ' ' + legal_case.assigned_to.last_name.lower()
                        if legal_case.assigned_to else ''
                        )
                    ):
                    search_text_legal_case_ids.append(legal_case.id)

            # use pipe to join both custom and built-in DRF datatables querysets (returned by super call above)
            # (otherwise they will filter on top of each other)
            #_queryset = queryset.filter(id__in=search_text_callemail_ids).distinct() | super_queryset
            # BB 20190704 - is super_queryset necessary?
            queryset = queryset.filter(id__in=search_text_legal_case_ids)

        status_filter = status_filter.lower() if status_filter else 'all'
        if status_filter != 'all':
            status_filter_legal_case_ids = []
            for legal_case in queryset:
                if status_filter == legal_case.get_status_display().lower():
                    status_filter_legal_case_ids.append(legal_case.id)
            queryset = queryset.filter(id__in=status_filter_legal_case_ids)

        if date_from:
            queryset = queryset.filter(case_created_date__gte=date_from)
        if date_to:
            date_to = datetime.strptime(date_to, '%Y-%m-%d') + timedelta(days=1)
            queryset = queryset.filter(case_created_date__lte=date_to)

        # override queryset ordering, required because the ordering is usually handled
        # in the super call, but is then clobbered by the custom queryset joining above
        # also needed to disable ordering for all fields for which data is not an
        # CallEmail model field, as property functions will not work with order_by
        
        getter = request.query_params.get
        fields = self.get_fields(getter)
        ordering = self.get_ordering(getter, fields)
        if len(ordering):
            for num, item in enumerate(ordering):
                if item == 'status__name':
                    ordering[num] = 'status'
                elif item == '-status__name':
                    ordering[num] = '-status'

            queryset = queryset.order_by(*ordering)

        setattr(view, '_datatables_total_count', total_count)
        return queryset


class LegalCaseRenderer(DatatablesRenderer):
    def render(self, data, accepted_media_type=None, renderer_context=None):
        if 'view' in renderer_context and hasattr(renderer_context['view'], '_datatables_total_count'):
            data['recordsTotal'] = renderer_context['view']._datatables_total_count
        return super(LegalCaseRenderer, self).render(data, accepted_media_type, renderer_context)


class LegalCasePaginatedViewSet(viewsets.ModelViewSet):
    filter_backends = (LegalCaseFilterBackend,)
    pagination_class = DatatablesPageNumberPagination
    renderer_classes = (LegalCaseRenderer,)
    queryset = LegalCase.objects.none()
    serializer_class = LegalCaseDatatableSerializer
    page_size = 10
    
    def get_queryset(self):
        user = self.request.user
        if is_internal(self.request):
            return LegalCase.objects.all()
        return LegalCase.objects.none()

    @list_route(methods=['GET', ])
    def get_paginated_datatable(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        queryset = self.filter_queryset(queryset)
        self.paginator.page_size = queryset.count()
        result_page = self.paginator.paginate_queryset(queryset, request)
        serializer = LegalCaseDatatableSerializer(
            result_page, many=True, context={'request': request})
        return self.paginator.get_paginated_response(serializer.data)


class LegalCaseViewSet(viewsets.ModelViewSet):
    queryset = LegalCase.objects.all()
    serializer_class = BaseLegalCaseSerializer

    def get_queryset(self):
        user = self.request.user
        if is_internal(self.request):
            return LegalCase.objects.all()
        return LegalCase.objects.none()

    def variable_serializer(self, request, instance):
        if instance.status == 'open':
            serializer = BaseLegalCaseSerializer
        elif instance.status in ['brief_of_evidence', 'with_manager', 'with_prosecution_coordinator']:
            serializer = LegalCaseBriefOfEvidenceSerializer
        elif instance.status in [
                'with_prosecution_coordinator_prosecution_brief', 
                'with_prosecution_council', 
                'with_prosecution_manager',
                'with_prosecution_coordinator_court',
                'closed',
                ]:
            serializer = LegalCaseProsecutionBriefSerializer
        else:
            serializer = BaseLegalCaseSerializer
        serialized_instance = serializer(instance, context={'request': request})
        return serialized_instance

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serialized_instance = self.variable_serializer(request, instance)
        return Response(serialized_instance.data)

    @list_route(methods=['GET', ])
    def court_outcome_type_list(self, request):
        try:
            qs = CourtOutcomeType.objects.all()
            serializer = CourtOutcomeTypeSerializer(qs, many=True, context={'request': request})
            return Response(serializer.data)
        except serializers.ValidationError:
            print(traceback.print_exc())
            raise
        except ValidationError as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(repr(e.error_dict))
        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))

    @list_route(methods=['GET', ])
    def court_list(self, request):
        try:
            qs = Court.objects.all()
            serializer = CourtSerializer(qs, many=True, context={'request': request})
            return Response(serializer.data)
        except serializers.ValidationError:
            print(traceback.print_exc())
            raise
        except ValidationError as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(repr(e.error_dict))
        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))

    @list_route(methods=['GET', ])
    def datatable_list(self, request, *args, **kwargs):
        try:
            qs = self.get_queryset()
            serializer = LegalCaseDatatableSerializer(
                qs, many=True, context={'request': request})
            return Response(serializer.data)
        except serializers.ValidationError:
            print(traceback.print_exc())
            raise
        except ValidationError as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(repr(e.error_dict))
        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))

    @list_route(methods=['GET', ])    
    def status_choices(self, request, *args, **kwargs):
        res_obj = [] 
        for choice in LegalCase.STATUS_CHOICES:
            res_obj.append({'id': choice[0], 'display': choice[1]});
        res_json = json.dumps(res_obj)
        return HttpResponse(res_json, content_type='application/json')

    @detail_route(methods=['GET', ])
    def no_running_sheet(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            #qs = instance.action_logs.all()
            #serializer = LegalCaseUserActionSerializer(qs, many=True)
            return_serializer = LegalCaseNoRunningSheetSerializer(
                    instance, 
                    context={'request': request}
                    )
            return Response(
                    return_serializer.data,
                    #status=status.HTTP_201_CREATED,
                    #headers=headers
                    )
            #return Response(serializer.data)
        except serializers.ValidationError:
            print(traceback.print_exc())
            raise
        except ValidationError as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(repr(e.error_dict))
        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))

    @detail_route(methods=['GET', ])
    def action_log(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            qs = instance.action_logs.all()
            serializer = LegalCaseUserActionSerializer(qs, many=True)
            return Response(serializer.data)
        except serializers.ValidationError:
            print(traceback.print_exc())
            raise
        except ValidationError as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(repr(e.error_dict))
        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))

    @detail_route(methods=['GET', ])
    def comms_log(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            qs = instance.comms_logs.all()
            serializer = LegalCaseCommsLogEntrySerializer(qs, many=True)
            return Response(serializer.data)
        except serializers.ValidationError:
            print(traceback.print_exc())
            raise
        except ValidationError as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(repr(e.error_dict))
        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))

    @detail_route(methods=['POST', ])
    @renderer_classes((JSONRenderer,))
    def add_comms_log(self, request, instance=None, workflow=False, *args, **kwargs):
        try:
            with transaction.atomic():
                # create Inspection instance if not passed to this method
                if not instance:
                    instance = self.get_object()
                # add Inspection attribute to request_data
                request_data = request.data.copy()
                request_data['legal_case'] = u'{}'.format(instance.id)
                if request_data.get('comms_log_id'):
                    comms = LegalCaseCommsLogEntry.objects.get(
                        id=request_data.get('comms_log_id')
                        )
                    serializer = LegalCaseCommsLogEntrySerializer(
                        instance=comms, 
                        data=request.data)
                else:
                    serializer = LegalCaseCommsLogEntrySerializer(
                        data=request_data
                        )
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
            raise serializers.ValidationError(repr(e.error_dict))
        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))

    def add_associated_persons(self, instance, request):
        running_sheet_person_list = request.data.get('running_sheet_person_list')
        if running_sheet_person_list:
            for person in running_sheet_person_list:
                person_id = person.get('id')
                email_user = EmailUser.objects.get(id=person_id)
                if email_user not in instance.associated_persons.all():
                        instance.associated_persons.add(email_user)
                        instance.save()

    @renderer_classes((JSONRenderer,))
    def update(self, request, workflow=False, *args, **kwargs):
        try:
            with transaction.atomic():
                instance = self.get_object()
                # Running Sheet
                running_sheet_entries = request.data.get('running_sheet_transform')
                if running_sheet_entries and len(running_sheet_entries) > 0:
                    for entry in running_sheet_entries:
                        entry_copy = dict(entry)
                        description = entry_copy.get('description', '')
                        ascii_description = description.encode('ascii', 'xmlcharrefreplace')
                        entry_copy.update({'description': ascii_description})
                        entry_id = LegalCaseRunningSheetEntry.objects.get(id = entry_copy.get('id'))
                        running_sheet_entry_serializer = SaveLegalCaseRunningSheetEntrySerializer(
                                instance=entry_id, 
                                data=entry_copy)
                        running_sheet_entry_serializer.is_valid(raise_exception=True)
                        if running_sheet_entry_serializer.is_valid():
                            running_sheet_entry_serializer.save()
                # Court Proceedings
                court_proceedings = request.data.get('court_proceedings', {})
                if court_proceedings:
                    court_proceedings['court_outcome_type_id'] = court_proceedings['court_outcome_type']['id'] if court_proceedings['court_outcome_type'] else None
                    serializer = CourtProceedingsJournalSerializer(instance=instance.court_proceedings, data=court_proceedings)
                    if serializer.is_valid(raise_exception=True):
                        serializer.save()
                    journal_entries = court_proceedings.get('journal_entries_transform')
                    if journal_entries:
                        for key, entry in journal_entries.items():
                            entry_copy = dict(entry)
                            description = entry_copy.get('description', '')
                            ascii_description = description.encode('ascii', 'xmlcharrefreplace')
                            entry_copy.update({'description': ascii_description})
                            entry_id = CourtProceedingsJournalEntry.objects.get(id=entry_copy.get('id'))
                            journal_entry_serializer = SaveCourtProceedingsJournalEntrySerializer(
                                    instance=entry_id,
                                    data=entry_copy)
                            if journal_entry_serializer.is_valid(raise_exception=True):
                                journal_entry_serializer.save()
                    court_dates = court_proceedings.get('date_entries_updated')
                    if court_dates:
                        for key, entry in court_dates.items():
                            entry_copy = dict(entry)
                            comments = entry_copy.get('comments', '')
                            ascii_comments = comments.encode('ascii', 'xmlcharrefreplace')
                            entry_copy.update({'comments': ascii_comments})
                            entry_copy['court_id'] = entry_copy['court']['id'] if entry_copy['court'] else None
                            if entry_copy.get('id'):
                                # Update existing court_date
                                court_date = CourtDate.objects.get(id=entry_copy.get('id'))
                                serializer = SaveCourtDateEntrySerializer(instance=court_date, data=entry_copy)
                                if serializer.is_valid(raise_exception=True):
                                    serializer.save()
                            else:
                                # Create new court_date
                                entry_copy['court_proceedings_id'] = instance.court_proceedings.id
                                serializer = SaveCourtDateEntrySerializer(data=entry_copy)
                                if serializer.is_valid(raise_exception=True):
                                    serializer.save()

                ## Brief Of Evidence
                brief_of_evidence = request.data.get('brief_of_evidence')
                if brief_of_evidence:
                    self.save_brief_of_evidence(request, instance)

                ## Prosecution Brief
                prosecution_brief = request.data.get('prosecution_brief')
                if prosecution_brief:
                    self.save_prosecution_brief(request, instance)

                # LegalCasePerson
                self.add_associated_persons(instance, request)
                serializer = SaveLegalCaseSerializer(instance, data=request.data)
                serializer.is_valid(raise_exception=True)
                if serializer.is_valid():
                    serializer.save()
                    instance.log_user_action(
                            LegalCaseUserAction.ACTION_SAVE_LEGAL_CASE.format(
                            instance.number), request)
                    headers = self.get_success_headers(serializer.data)
                    full_http_response = request.data.get('full_http_response')
                    #no_running_sheet = request.data.get('no_running_sheet')
                    if full_http_response:
                        return_serializer = self.variable_serializer(request, instance)
                        return Response(
                                return_serializer.data,
                                status=status.HTTP_201_CREATED,
                                headers=headers
                                )
                    #elif no_running_sheet:
                     #   return_serializer = LegalCaseNoRunningSheetSerializer(
                      #          instance, 
                       #         context={'request': request}
                        #        )
                        #return Response(
                         #       return_serializer.data,
                          #      status=status.HTTP_201_CREATED,
                           #     headers=headers
                            #    )
                    else:
                        return Response(
                                status=status.HTTP_201_CREATED,
                                headers=headers
                                )

        except serializers.ValidationError:
            print(traceback.print_exc())
            raise
        except ValidationError as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(repr(e.error_dict))
        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))

    def save_brief_of_evidence(self, request, instance):
        try:
            brief_of_evidence = request.data.get('brief_of_evidence')
            if brief_of_evidence:
                boe_instance, created = BriefOfEvidence.objects.get_or_create(legal_case=instance)
                boe_serializer = BriefOfEvidenceSerializer(boe_instance, data=brief_of_evidence)
                if boe_serializer.is_valid():
                    boe_serializer.save()

            boe_roi_ticked = request.data.get('boe_roi_ticked')
            if boe_roi_ticked:
                update_boe_roi_ticked(instance, boe_roi_ticked)
            boe_other_statements_ticked = request.data.get('boe_other_statements_ticked')
            if boe_other_statements_ticked:
                update_boe_other_statements_ticked(instance, boe_other_statements_ticked)
            boe_document_artifacts = request.data.get('boe_document_artifacts')
            if boe_document_artifacts:
                update_boe_document_artifacts_ticked(instance, boe_document_artifacts)
            # physical artifacts
            boe_physical_artifacts_used = request.data.get('boe_physical_artifacts_used')
            if boe_physical_artifacts_used:
                update_boe_physical_artifacts(instance, boe_physical_artifacts_used)
            boe_physical_artifacts_sensitive_unused = request.data.get('boe_physical_artifacts_sensitive_unused')
            if boe_physical_artifacts_sensitive_unused:
                update_boe_physical_artifacts(instance, boe_physical_artifacts_sensitive_unused)
            boe_physical_artifacts_non_sensitive_unused = request.data.get('boe_physical_artifacts_non_sensitive_unused')
            if boe_physical_artifacts_non_sensitive_unused:
                update_boe_physical_artifacts(instance, boe_physical_artifacts_non_sensitive_unused)
        except serializers.ValidationError:
            print(traceback.print_exc())
            raise
        except ValidationError as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(repr(e.error_dict))
        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))

    def save_prosecution_brief(self, request, instance):
        try:
            prosecution_brief = request.data.get('prosecution_brief')
            if prosecution_brief:
                pb_instance, created = ProsecutionBrief.objects.get_or_create(legal_case=instance)
                pb_serializer = ProsecutionBriefSerializer(pb_instance, data=prosecution_brief)
                if pb_serializer.is_valid():
                    pb_serializer.save()

            pb_roi_ticked = request.data.get('pb_roi_ticked')
            if pb_roi_ticked:
                update_pb_roi_ticked(instance, pb_roi_ticked)
            pb_other_statements_ticked = request.data.get('pb_other_statements_ticked')
            if pb_other_statements_ticked:
                update_pb_other_statements_ticked(instance, pb_other_statements_ticked)
            pb_document_artifacts_ticked = request.data.get('pb_document_artifacts_ticked')
            if pb_document_artifacts_ticked:
                update_pb_document_artifacts_ticked(instance, pb_document_artifacts_ticked)
            # physical artifacts
            pb_physical_artifacts_used = request.data.get('pb_physical_artifacts_used')
            if pb_physical_artifacts_used:
                update_pb_physical_artifacts(instance, pb_physical_artifacts_used)
            pb_physical_artifacts_sensitive_unused = request.data.get('pb_physical_artifacts_sensitive_unused')
            if pb_physical_artifacts_sensitive_unused:
                update_pb_physical_artifacts(instance, pb_physical_artifacts_sensitive_unused)
            pb_physical_artifacts_non_sensitive_unused = request.data.get('pb_physical_artifacts_non_sensitive_unused')
            if pb_physical_artifacts_non_sensitive_unused:
                update_pb_physical_artifacts(instance, pb_physical_artifacts_non_sensitive_unused)
        except serializers.ValidationError:
            print(traceback.print_exc())
            raise
        except ValidationError as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(repr(e.error_dict))
        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))

    @detail_route(methods=['POST', ])
    @renderer_classes((JSONRenderer,))
    def journal_entry_history(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            entry_number = request.data.get("journal_entry_number")
            row_num = entry_number.split('-')[1]
            entry_instance = instance.court_proceedings.journal_entries.get(row_num=row_num)

            serializer = JournalEntryHistorySerializer(entry_instance)
            return Response(
                    serializer.data, 
                    status=status.HTTP_200_OK,
                    )
        except serializers.ValidationError:
            print(traceback.print_exc())
            raise
        except ValidationError as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(repr(e.error_dict))
        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))

    @detail_route(methods=['POST', ])
    @renderer_classes((JSONRenderer,))
    def running_sheet_history(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            entry_number = request.data.get("running_sheet_entry_number")
            row_num = entry_number.split('-')[1]
            entry_instance = instance.running_sheet_entries.get(row_num=row_num)

            serializer = RunningSheetEntryHistorySerializer(entry_instance)
            return Response(
                    serializer.data, 
                    status=status.HTTP_200_OK,
                    )
        except serializers.ValidationError:
            print(traceback.print_exc())
            raise
        except ValidationError as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(repr(e.error_dict))
        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))

    @detail_route(methods=['POST', ])
    @renderer_classes((JSONRenderer,))
    def update_assigned_to_id(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = None

            validation_serializer = BaseLegalCaseSerializer(instance, context={'request': request})
            user_in_group = validation_serializer.data.get('user_in_group')

            if request.data.get('current_user') and user_in_group:
                serializer = UpdateAssignedToIdSerializer(
                        instance=instance,
                        data={
                            'assigned_to_id': request.user.id,
                            }
                        )
            elif user_in_group:
                serializer = UpdateAssignedToIdSerializer(instance=instance, data=request.data)
            
            if serializer:
                serializer.is_valid(raise_exception=True)
                if serializer.is_valid():
                    serializer.save()
                    return_serializer = BaseLegalCaseSerializer(instance=instance,
                            context={'request': request}
                            )
                    headers = self.get_success_headers(return_serializer.data)
                    return Response(
                            return_serializer.data, 
                            status=status.HTTP_201_CREATED,
                            headers=headers
                            )
            else:
                return Response(validation_serializer.data, 
                                status=status.HTTP_201_CREATED
                                )
        except serializers.ValidationError:
            print(traceback.print_exc())
            raise
        except ValidationError as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(repr(e.error_dict))
        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))

    @detail_route(methods=['POST'])
    @renderer_classes((JSONRenderer,))
    def process_brief_of_evidence_document(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            if hasattr(instance, 'brief_of_evidence'):
                returned_data = process_generic_document(request, instance.brief_of_evidence)
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
    #@renderer_classes((JSONRenderer,))
    #@renderer_classes([PDFRenderer])
    def generate_document(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            document_label = ''
            if request.data.get("document_type") == 'brief_of_evidence':
                document_label = "Brief of Evidence"
            elif request.data.get("document_type") == 'prosecution_brief':
                document_label = "Prosecution Brief"
            elif request.data.get("document_type") == 'prosecution_notice':
                document_label = "Prosecution Notice"
            elif request.data.get("document_type") == 'court_hearing_notice':
                document_label = "Court Hearing Notice"

            section_list = ''
            if request.data.get('include_statement_of_facts'):
                section_list += "Statement of Facts"
            if request.data.get('include_case_information_form'):
                if section_list:
                    section_list += ", "
                section_list += "Case Information Form"
            if request.data.get('include_offences_offenders_roi'):
                if section_list:
                    section_list += ", "
                section_list += "Offences, Offenders and Records of Interview"
            if request.data.get('include_witness_officer_other_statements'):
                if section_list:
                    section_list += ", "
                section_list += "Witness Statements, Officer Statements, Expert Statements"
            if request.data.get('include_physical_artifacts'):
                if section_list:
                    section_list += ", "
                section_list += "List of Exhibits, Sensitive Unused and Non-sensitive Unused Materials"
            if request.data.get('include_document_artifacts'):
                if section_list:
                    section_list += ", "
                section_list += "List of Photographic, Video and Sound Exhibits"

            http_response = create_document_pdf_bytes(instance, request.data)

            if http_response:
                instance.log_user_action(
                        LegalCaseUserAction.ACTION_GENERATE_DOCUMENT.format(
                        document_label,
                        instance.number,
                        section_list
                        ), request)
                return http_response
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
    def process_court_hearing_notice_document(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            # process docs
            returned_data = process_generic_document(request, instance, 'court_hearing_notice')
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


    @detail_route(methods=['POST'])
    @renderer_classes((JSONRenderer,))
    def process_prosecution_notice_document(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            # process docs
            returned_data = process_generic_document(request, instance, 'prosecution_notice')
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


    @detail_route(methods=['POST'])
    @renderer_classes((JSONRenderer,))
    def process_prosecution_brief_document(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            if hasattr(instance, 'prosecution_brief'):
                returned_data = process_generic_document(request, instance.prosecution_brief)
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
    def process_default_document(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            returned_data = process_generic_document(request, instance)
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
                raise serializers.ValidationError(repr(e[0]))
                # raise serializers.ValidationError(repr(e[0].encode('utf-8')))
        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))

    @detail_route(methods=['POST'])
    @renderer_classes((JSONRenderer,))
    def process_court_outcome_document(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            returned_data = process_generic_document(request, instance, document_type='court_outcome')
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

    def create(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
                serializer = SaveLegalCaseSerializer(
                        data=request.data, 
                        partial=True
                        )
                serializer.is_valid(raise_exception=True)
                if serializer.is_valid():
                    print("serializer.validated_data")
                    print(serializer.validated_data)
                    instance = serializer.save()
                    instance.log_user_action(
                            LegalCaseUserAction.ACTION_CREATE_LEGAL_CASE.format(
                            instance.number), request)

                    # Create comms_log and send mail
                    res = self.workflow_action(request, instance, create_legal_case=True)
                    if instance.call_email:
                        print("update parent")
                        self.update_parent(request, instance)
                    return res
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

    def update_parent(self, request, instance, *args, **kwargs):
        # Log parent actions and update status
        if instance.call_email:
            instance.call_email.log_user_action(
                    CallEmailUserAction.ACTION_ALLOCATE_FOR_LEGAL_CASE.format(
                    instance.call_email.number), request)
            # instance.call_email.close(request)
            instance.call_email.status = 'open_case'
            instance.call_email.save()

    @detail_route(methods=['POST'])
    @renderer_classes((JSONRenderer,))
    def workflow_action(self, request, instance=None, create_legal_case=None, *args, **kwargs):
        try:
            with transaction.atomic():
                # email recipient
                #recipient_id = None

                if not instance:
                    instance = self.get_object()

                comms_log_id = request.data.get('legal_case_comms_log_id')
                if comms_log_id and comms_log_id is not 'null':
                    workflow_entry = instance.comms_logs.get(
                            id=comms_log_id)
                else:
                    workflow_entry = self.add_comms_log(request, instance, workflow=True)
                    temporary_document_collection_id = request.data.get('temporary_document_collection_id')
                    if temporary_document_collection_id:
                        temp_doc_collection, created = TemporaryDocumentCollection.objects.get_or_create(
                                id=temporary_document_collection_id)
                        if temp_doc_collection:
                            for doc in temp_doc_collection.documents.all():
                                save_comms_log_document_obj(instance, workflow_entry, doc)
                            temp_doc_collection.delete()

                ## Set Inspection status depending on workflow type
                workflow_type = request.data.get('workflow_type')
                if workflow_type == 'close':
                    instance.close(request)
                elif workflow_type == 'brief_of_evidence':
                    self.process_brief_of_evidence(instance, request)
                elif workflow_type == 'send_to_manager':
                    instance.send_to_manager(request)
                elif workflow_type == 'back_to_case':
                    instance.back_to_case(request)
                elif workflow_type == 'back_to_officer':
                    instance.back_to_officer(request)
                elif workflow_type == 'approve_brief_of_evidence':
                    instance.send_to_prosecution_coordinator(request)
                elif workflow_type == 'prosecution_brief':
                    self.process_prosecution_brief(instance, request)
                elif workflow_type == 'send_to_prosecution_council':
                    instance.send_to_prosecution_council(request)
                elif workflow_type == 'back_to_prosecution_coordinator':
                    instance.back_to_prosecution_coordinator(request)
                elif workflow_type == 'endorse_prosecution_brief':
                    instance.send_to_prosecution_manager(request)
                elif workflow_type == 'approve_for_court':
                    instance.approve_for_court(request)
                elif workflow_type == 'back_to_prosecution_council':
                    instance.send_to_prosecution_council(request)
                if create_legal_case:
                    instance.region_id = None if not request.data.get('region_id') else request.data.get('region_id')
                    instance.district_id = None if not request.data.get('district_id') else request.data.get('district_id')
                    instance.assigned_to_id = None if not request.data.get('assigned_to_id') else request.data.get('assigned_to_id')
                    instance.legal_case_priority_id = None if not request.data.get('legal_case_priority_id') else request.data.get('legal_case_priority_id')
                    instance.allocated_group_id = None if not request.data.get('allocated_group_id') else request.data.get('allocated_group_id')
                    instance.call_email_id = None if not request.data.get('call_email_id') else request.data.get('call_email_id')
                    instance.details = None if not request.data.get('details') else request.data.get('details')

                instance.save()

                ## send email
                email_data = prepare_mail(request, instance, workflow_entry, send_mail)
                serializer = LegalCaseCommsLogEntrySerializer(instance=workflow_entry, data=email_data, partial=True)
                serializer.is_valid(raise_exception=True)
                if serializer.is_valid():
                    serializer.save()
                    return_serializer = self.variable_serializer(request, instance)
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
            raise serializers.ValidationError(repr(e.error_dict))
        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))

    def process_brief_of_evidence(self, instance, request):
        boe_instance, created = BriefOfEvidence.objects.get_or_create(legal_case=instance)
        #instance.set_status_brief_of_evidence(request)
        build_all_boe_other_statements_hierarchy(instance)
        build_all_boe_roi_hierarchy(instance)
        generate_boe_document_artifacts(instance)
        generate_boe_physical_artifacts(instance)
        instance.set_status_brief_of_evidence(request)

    def process_prosecution_brief(self, instance, request):
        boe_instance, created = BriefOfEvidence.objects.get_or_create(legal_case=instance)
        pb_instance, created = ProsecutionBrief.objects.get_or_create(legal_case=instance)
        # copy model fields
        pb_instance.statement_of_facts = boe_instance.statement_of_facts
        pb_instance.victim_impact_statement_taken = boe_instance.victim_impact_statement_taken
        pb_instance.statements_pending = boe_instance.statements_pending
        pb_instance.vulnerable_hostile_witnesses = boe_instance.vulnerable_hostile_witnesses
        pb_instance.witness_refusing_statement = boe_instance.witness_refusing_statement
        pb_instance.problems_needs_prosecution_witnesses = boe_instance.problems_needs_prosecution_witnesses
        pb_instance.accused_bad_character = boe_instance.accused_bad_character
        pb_instance.further_persons_interviews_pending = boe_instance.further_persons_interviews_pending
        pb_instance.other_interviews = boe_instance.other_interviews
        pb_instance.relevant_persons_pending_charges = boe_instance.relevant_persons_pending_charges
        pb_instance.other_persons_receiving_sanction_outcome = boe_instance.other_persons_receiving_sanction_outcome
        pb_instance.local_public_interest = boe_instance.local_public_interest
        pb_instance.applications_orders_requests = boe_instance.applications_orders_requests
        pb_instance.applications_orders_required = boe_instance.applications_orders_required
        pb_instance.other_legal_matters = boe_instance.other_legal_matters

        pb_instance.victim_impact_statement_taken_details = boe_instance.victim_impact_statement_taken_details
        pb_instance.statements_pending_details = boe_instance.statements_pending_details
        pb_instance.vulnerable_hostile_witnesses_details = boe_instance.vulnerable_hostile_witnesses_details
        pb_instance.witness_refusing_statement_details = boe_instance.witness_refusing_statement_details
        pb_instance.problems_needs_prosecution_witnesses_details = boe_instance.problems_needs_prosecution_witnesses_details
        pb_instance.accused_bad_character_details = boe_instance.accused_bad_character_details
        pb_instance.further_persons_interviews_pending_details = boe_instance.further_persons_interviews_pending_details
        pb_instance.other_interviews_details = boe_instance.other_interviews_details
        pb_instance.relevant_persons_pending_charges_details = boe_instance.relevant_persons_pending_charges_details
        pb_instance.other_persons_receiving_sanction_outcome_details = boe_instance.other_persons_receiving_sanction_outcome_details
        pb_instance.local_public_interest_details = boe_instance.local_public_interest_details
        pb_instance.applications_orders_requests_details = boe_instance.applications_orders_requests_details
        pb_instance.applications_orders_required_details = boe_instance.applications_orders_required_details
        pb_instance.other_legal_matters_details = boe_instance.other_legal_matters_details
        pb_instance.save()

        # copy additional documents
        for doc in boe_instance.documents.all():
            req = FakeRequest(data={
                    "_file": doc._file,
                    "filename": doc.name,
                    "action": "save",
                    })
            self.process_prosecution_brief_document(req)

        # copy artifact sections
        copy_brief_of_evidence_artifacts_to_prosecution_brief(instance)
        # change status
        instance.set_status_generate_prosecution_brief(request)

    @detail_route(methods=['POST'])
    @renderer_classes((JSONRenderer,))
    def create_legal_case_process_comms_log_document(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            # process docs
            returned_data = process_generic_document(request, instance, document_type='comms_log')
            # delete Inspection if user cancels modal
            action = request.data.get('action')
            if action == 'cancel' and returned_data:
                # returned_data = instance.delete()
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

    @detail_route(methods=['POST'])
    @renderer_classes((JSONRenderer,))
    def delete_reinstate_journal_entry(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            journal_entry_id = request.data.get("journal_entry_id")
            deleted = request.data.get("deleted")
            if journal_entry_id:
                journal_entry_instance = CourtProceedingsJournalEntry.objects.get(id=journal_entry_id)
                serializer = DeleteReinstateLegalCaseRunningSheetEntrySerializer(
                        instance=journal_entry_instance, 
                        data=request.data)
                serializer.is_valid(raise_exception=True)
                if serializer.is_valid():
                    saved_instance = serializer.save()
                    #headers = self.get_success_headers(serializer.data)
                    return_serializer = CourtProceedingsJournalEntrySerializer(saved_instance)
                    return Response(
                            return_serializer.data,
                            #status=status.HTTP_201_CREATED,
                            #headers=headers
                            )

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
    def create_journal_entry(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            request_data = {
                            "court_proceedings_id": request.data.get('court_proceedings_id'),
                            "user_id": request.data.get('user_id'),
                            }
            serializer = CreateCourtProceedingsJournalEntrySerializer(data=request_data)
            serializer.is_valid(raise_exception=True)
            if serializer.is_valid():
                court_proceedings_entry = serializer.save()
                return_serializer = CourtProceedingsJournalEntrySerializer(court_proceedings_entry)
                return Response(
                        return_serializer.data,
                        status=status.HTTP_201_CREATED,
                        )

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

###########
    @detail_route(methods=['POST'])
    @renderer_classes((JSONRenderer,))
    def delete_reinstate_running_sheet_entry(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            running_sheet_id = request.data.get("running_sheet_id")
            deleted = request.data.get("deleted")
            if running_sheet_id:
                running_sheet_instance = LegalCaseRunningSheetEntry.objects.get(id=running_sheet_id)
                serializer = DeleteReinstateLegalCaseRunningSheetEntrySerializer(
                        instance=running_sheet_instance, 
                        data=request.data)
                serializer.is_valid(raise_exception=True)
                if serializer.is_valid():
                    saved_instance = serializer.save()
                    #headers = self.get_success_headers(serializer.data)
                    return_serializer = LegalCaseRunningSheetEntrySerializer(saved_instance)
                    return Response(
                            return_serializer.data,
                            #status=status.HTTP_201_CREATED,
                            #headers=headers
                            )

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
    def create_running_sheet_entry(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            request_data = {
                            "legal_case_id": instance.id,
                            "user_id": request.user.id
                            }
            serializer = CreateLegalCaseRunningSheetEntrySerializer(data=request_data)
            serializer.is_valid(raise_exception=True)
            if serializer.is_valid():
                running_sheet_entry = serializer.save()
                #return running_sheet_entry
                return_serializer = LegalCaseRunningSheetEntrySerializer(running_sheet_entry)
                return Response(
                        return_serializer.data,
                        status=status.HTTP_201_CREATED,
                        )

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


class LegalCasePriorityViewSet(viewsets.ModelViewSet):
   queryset = LegalCasePriority.objects.all()
   serializer_class = LegalCasePrioritySerializer

   def get_queryset(self):
       # user = self.request.user
       if is_internal(self.request):
           return LegalCasePriority.objects.all()
       return LegalCasePriority.objects.none()

