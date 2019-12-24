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
        save_comms_log_document_obj,
        save_default_document_obj,
        save_details_document_obj,
        save_storage_document_obj,
        )
from wildlifecompliance.components.main.email import prepare_mail
from wildlifecompliance.components.users.serializers import (
    UserAddressSerializer,
    ComplianceUserDetailsSerializer,
)
from wildlifecompliance.helpers import is_customer, is_internal
from wildlifecompliance.components.artifact.models import (
        Artifact,
        DocumentArtifact,
        PhysicalArtifact,
        DocumentArtifactType,
        PhysicalArtifactType,
        PhysicalArtifactDisposalMethod,
        ArtifactUserAction,
        )
from wildlifecompliance.components.artifact.serializers import (
        ArtifactSerializer,
        DocumentArtifactSerializer,
        SaveDocumentArtifactSerializer,
        SavePhysicalArtifactSerializer,
        PhysicalArtifactSerializer,
        DocumentArtifactTypeSerializer,
        PhysicalArtifactTypeSerializer,
        PhysicalArtifactDisposalMethodSerializer,
        ArtifactUserActionSerializer,
        ArtifactCommsLogEntrySerializer,
        ArtifactPaginatedSerializer,
        )
from wildlifecompliance.components.users.models import (
    CompliancePermissionGroup,    
)
from django.contrib.auth.models import Permission, ContentType
#from utils import SchemaParser

from rest_framework_datatables.pagination import DatatablesPageNumberPagination
from rest_framework_datatables.filters import DatatablesFilterBackend
from rest_framework_datatables.renderers import DatatablesRenderer

from wildlifecompliance.components.legal_case.email import (
    send_mail)
from reversion.models import Version
#import unicodedata


#class LegalCaseFilterBackend(DatatablesFilterBackend):
#
#    def filter_queryset(self, request, queryset, view):
#        #import ipdb; ipdb.set_trace()
#        # Get built-in DRF datatables queryset first to join with search text, then apply additional filters
#        # super_queryset = super(CallEmailFilterBackend, self).filter_queryset(request, queryset, view).distinct()
#
#        total_count = queryset.count()
#        status_filter = request.GET.get('status_description')
#        date_from = request.GET.get('date_from')
#        date_to = request.GET.get('date_to')
#        search_text = request.GET.get('search[value]')
#
#        if search_text:
#            search_text = search_text.lower()
#            search_text_legal_case_ids = []
#            for legal_case in queryset:
#                #lodged_on_str = time.strftime('%d/%m/%Y', call_email.lodged_on)
#                case_created_date_str = legal_case.case_created_date.strftime('%d/%m/%Y') if legal_case.case_created_date else ''
#                if (search_text in (legal_case.number.lower() if legal_case.number else '')
#                    or search_text in (legal_case.status.lower() if legal_case.status else '')
#                    or search_text in (case_created_date_str.lower() if case_created_date_str else '')
#                    or search_text in (legal_case.title.lower() if legal_case.title else '')
#                    or search_text in (
#                        legal_case.assigned_to.first_name.lower() + ' ' + legal_case.assigned_to.last_name.lower()
#                        if legal_case.assigned_to else ''
#                        )
#                    ):
#                    search_text_legal_case_ids.append(legal_case.id)
#
#            # use pipe to join both custom and built-in DRF datatables querysets (returned by super call above)
#            # (otherwise they will filter on top of each other)
#            #_queryset = queryset.filter(id__in=search_text_callemail_ids).distinct() | super_queryset
#            # BB 20190704 - is super_queryset necessary?
#            queryset = queryset.filter(id__in=search_text_legal_case_ids)
#
#        status_filter = status_filter.lower() if status_filter else 'all'
#        if status_filter != 'all':
#            status_filter_legal_case_ids = []
#            for legal_case in queryset:
#                if status_filter == legal_case.get_status_display().lower():
#                    status_filter_legal_case_ids.append(legal_case.id)
#            queryset = queryset.filter(id__in=status_filter_legal_case_ids)
#
#        if date_from:
#            queryset = queryset.filter(case_created_date__gte=date_from)
#        if date_to:
#            date_to = datetime.strptime(date_to, '%Y-%m-%d') + timedelta(days=1)
#            queryset = queryset.filter(case_created_date__lte=date_to)
#
#        # override queryset ordering, required because the ordering is usually handled
#        # in the super call, but is then clobbered by the custom queryset joining above
#        # also needed to disable ordering for all fields for which data is not an
#        # CallEmail model field, as property functions will not work with order_by
#        
#        getter = request.query_params.get
#        fields = self.get_fields(getter)
#        ordering = self.get_ordering(getter, fields)
#        if len(ordering):
#            for num, item in enumerate(ordering):
#                #if item == 'planned_for':
#                #    # ordering.pop(num)
#                #    # ordering.insert(num, 'planned_for_date')
#                #    ordering[num] = 'planned_for_date'
#                #elif item == '-planned_for':
#                #    # ordering.pop(num)
#                #    # ordering.insert(num, '-planned_for_date')
#                #    ordering[num] = '-planned_for_date'
#                if item == 'status__name':
#                    # ordering.pop(num)
#                    # ordering.insert(num, 'status')
#                    ordering[num] = 'status'
#                elif item == '-status__name':
#                    # ordering.pop(num)
#                    # ordering.insert(num, '-status')
#                    ordering[num] = '-status'
#
#            queryset = queryset.order_by(*ordering)
#
#        setattr(view, '_datatables_total_count', total_count)
#        return queryset
#
#
#class LegalCaseRenderer(DatatablesRenderer):
#    def render(self, data, accepted_media_type=None, renderer_context=None):
#        if 'view' in renderer_context and hasattr(renderer_context['view'], '_datatables_total_count'):
#            data['recordsTotal'] = renderer_context['view']._datatables_total_count
#        return super(LegalCaseRenderer, self).render(data, accepted_media_type, renderer_context)
#
#
#class LegalCasePaginatedViewSet(viewsets.ModelViewSet):
#    filter_backends = (LegalCaseFilterBackend,)
#    pagination_class = DatatablesPageNumberPagination
#    renderer_classes = (LegalCaseRenderer,)
#    queryset = LegalCase.objects.none()
#    serializer_class = LegalCaseDatatableSerializer
#    page_size = 10
#    
#    def get_queryset(self):
#        # import ipdb; ipdb.set_trace()
#        user = self.request.user
#        if is_internal(self.request):
#            return LegalCase.objects.all()
#        return LegalCase.objects.none()
#
#    @list_route(methods=['GET', ])
#    def get_paginated_datatable(self, request, *args, **kwargs):
#        print(request.GET)
#        queryset = self.get_queryset()
#
#        queryset = self.filter_queryset(queryset)
#        self.paginator.page_size = queryset.count()
#        result_page = self.paginator.paginate_queryset(queryset, request)
#        serializer = LegalCaseDatatableSerializer(
#            result_page, many=True, context={'request': request})
#        return self.paginator.get_paginated_response(serializer.data)


class DocumentArtifactViewSet(viewsets.ModelViewSet):
    queryset = DocumentArtifact.objects.all()
    serializer_class = DocumentArtifactSerializer

    def get_queryset(self):
        # import ipdb; ipdb.set_trace()
        user = self.request.user
        if is_internal(self.request):
            return DocumentArtifact.objects.all()
        return DocumentArtifact.objects.none()

    def create(self, request, *args, **kwargs):
        print("create")
        print(request.data)
        try:
            with transaction.atomic():
                #request_data = request.data
                #document_type = request_data.get('document_type')
                #document_type_id = None
                #if document_type:
                #    document_type_id = document_type.get('id')
                #    request_data['document_type_id'] = document_type_id
                #serializer = SaveDocumentArtifactSerializer(
                #        data=request_data, 
                #        partial=True
                #        )
                #serializer.is_valid(raise_exception=True)
                #if serializer.is_valid():
                #    print("serializer.validated_data")
                #    print(serializer.validated_data)
                #    instance = serializer.save()
                #    headers = self.get_success_headers(serializer.data)
                request_data = request.data
                instance, headers = self.common_save(request, request_data)

                instance.log_user_action(
                        ArtifactUserAction.ACTION_CREATE_ARTIFACT.format(
                        instance.number), request)
                return_serializer = DocumentArtifactSerializer(instance, context={'request': request})
                return Response(
                        return_serializer.data,
                        status=status.HTTP_201_CREATED,
                        headers=headers
                        )
                    # Create comms_log and send mail
                    #res = self.workflow_action(request, instance, create_legal_case=True)
                    #if instance.call_email:
                     #   print("update parent")
                      #  self.update_parent(request, instance)
                    #return res
        except serializers.ValidationError:
            print(traceback.print_exc())
            raise
        except ValidationError as e:
            if hasattr(e, 'error_dict'):
                raise serializers.ValidationError(repr(e.error_dict))
            else:
                raise serializers.ValidationError(repr(e[0].encode('utf-8')))
        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))

    @renderer_classes((JSONRenderer,))
    #def inspection_save(self, request, workflow=False, *args, **kwargs):
    def update(self, request, workflow=False, *args, **kwargs):
        print(request.data)
        try:
            with transaction.atomic():
                instance = self.get_object()
                #if request.data.get('renderer_data'):
                 #   self.form_data(request)

                #serializer = SaveDocumentArtifactSerializer(instance, data=request.data)
                #serializer.is_valid(raise_exception=True)
                #if serializer.is_valid():
                #    serializer.save()
                request_data = request.data
                instance, headers = self.common_save(request, request_data, instance)
                instance.log_user_action(
                        ArtifactUserAction.ACTION_SAVE_ARTIFACT.format(
                        instance.number), request)
                #headers = self.get_success_headers(serializer.data)
                return_serializer = DocumentArtifactSerializer(instance, context={'request': request})
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

    def common_save(self, request, request_data, instance=None):
        try:
            with transaction.atomic():
                document_type = request_data.get('document_type')
                document_type_id = None
                if document_type:
                    document_type_id = document_type.get('id')
                    request_data['document_type_id'] = document_type_id
                #statement = request_data.get('statement')
                #statement_id = None
                #if statement:
                #    statement_id = statement.get('id')
                #    request_data['statement_id'] = statement_id
                if instance:
                    serializer = SaveDocumentArtifactSerializer(
                            instance=instance,
                            data=request_data, 
                            partial=True
                            )
                else:
                    serializer = SaveDocumentArtifactSerializer(
                            data=request_data, 
                            partial=True
                            )
                serializer.is_valid(raise_exception=True)
                if serializer.is_valid():
                    print("serializer.validated_data")
                    print(serializer.validated_data)
                    instance = serializer.save()
                    headers = self.get_success_headers(serializer.data)
                    return (instance, headers)
                    #instance.log_user_action(
                    #        ArtifactUserAction.ACTION_CREATE_ARTIFACT.format(
                    #        instance.number), request)
                    #return_serializer = DocumentArtifactSerializer(instance, context={'request': request})
                    #return Response(
                    #        return_serializer.data,
                    #        status=status.HTTP_201_CREATED,
                    #        headers=headers
                    #        )
        except serializers.ValidationError:
            print(traceback.print_exc())
            raise
        except ValidationError as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(repr(e.error_dict))
        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))


class PhysicalArtifactViewSet(viewsets.ModelViewSet):
    queryset = PhysicalArtifact.objects.all()
    serializer_class = PhysicalArtifactSerializer

    def get_queryset(self):
        # import ipdb; ipdb.set_trace()
        user = self.request.user
        if is_internal(self.request):
            return PhysicalArtifact.objects.all()
        return PhysicalArtifact.objects.none()

    def create(self, request, *args, **kwargs):
        print("create")
        print(request.data)
        try:
            with transaction.atomic():
                request_data = request.data
                physical_artifact_type = request_data.get('physical_artifact_type')
                physical_artifact_type_id = None
                if physical_artifact_type:
                    physical_artifact_type_id = physical_artifact_type.get('id')
                    request_data['physical_artifact_type_id'] = physical_artifact_type_id
                serializer = SavePhysicalArtifactSerializer(
                        data=request_data, 
                        partial=True
                        )
                serializer.is_valid(raise_exception=True)
                if serializer.is_valid():
                    print("serializer.validated_data")
                    print(serializer.validated_data)
                    instance = serializer.save()
                    instance.log_user_action(
                            ArtifactUserAction.ACTION_CREATE_ARTIFACT.format(
                            instance.number), request)
                    headers = self.get_success_headers(serializer.data)
                    return_serializer = PhysicalArtifactSerializer(instance, context={'request': request})
                    return Response(
                            return_serializer.data,
                            status=status.HTTP_201_CREATED,
                            headers=headers
                            )
                    # Create comms_log and send mail
                    #res = self.workflow_action(request, instance, create_legal_case=True)
                    #if instance.call_email:
                     #   print("update parent")
                      #  self.update_parent(request, instance)
                    #return res
        except serializers.ValidationError:
            print(traceback.print_exc())
            raise
        except ValidationError as e:
            if hasattr(e, 'error_dict'):
                raise serializers.ValidationError(repr(e.error_dict))
            else:
                raise serializers.ValidationError(repr(e[0].encode('utf-8')))
        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))

    @renderer_classes((JSONRenderer,))
    #def inspection_save(self, request, workflow=False, *args, **kwargs):
    def update(self, request, workflow=False, *args, **kwargs):
        print(request.data)
        try:
            with transaction.atomic():
                instance = self.get_object()
                #if request.data.get('renderer_data'):
                 #   self.form_data(request)

                serializer = SavePhysicalArtifactSerializer(instance, data=request.data)
                serializer.is_valid(raise_exception=True)
                if serializer.is_valid():
                    serializer.save()
                    instance.log_user_action(
                            ArtifactUserAction.ACTION_SAVE_ARTIFACT.format(
                            instance.number), request)
                    headers = self.get_success_headers(serializer.data)
                    return_serializer = PhysicalArtifactSerializer(instance, context={'request': request})
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



class ArtifactFilterBackend(DatatablesFilterBackend):
    def filter_queryset(self, request, queryset, view):
        total_count = queryset.count()

        # Storage for the filters
        # Required filters are accumulated here
        # Then issue a query once at last

        # Filter by the search_text
        search_text = request.GET.get('search[value]', '')

        q_objects = Q()
        ids = []

        if search_text:
            # Found ids of the Artifact model
            ids_p = PhysicalArtifact.objects.filter(Q(physical_artifact_type__artifact_type__icontains=search_text)).values_list('artifact_ptr_id', flat=True).distinct()
            ids_d = DocumentArtifact.objects.filter(Q(document_type__artifact_type__icontains=search_text)).values_list('artifact_ptr_id', flat=True).distinct()

            # Q object for filtering Artifact
            q_objects &= Q(identifier__icontains=search_text) | \
                         Q(number__icontains=search_text) | \
                         Q(id__in=ids_p) | \
                         Q(id__in=ids_d)

        # TODO: implement filtering by the dropdown filters
        # type = request.GET.get('type', '').lower()
        # if type and type != 'all':
        #     q_objects &= Q(type=type)
        #
        # status = request.GET.get('status', '').lower()
        # if status and status != 'all':
        #     q_objects &= Q(status=status)
        #
        date_from = request.GET.get('date_from', '').lower()
        if date_from:
            date_from = datetime.strptime(date_from, '%d/%m/%Y')
            q_objects &= Q(artifact_date__gte=date_from)

        date_to = request.GET.get('date_to', '').lower()
        if date_to:
            date_to = datetime.strptime(date_to, '%d/%m/%Y')
            q_objects &= Q(artifact_date__lte=date_to)

        # perform filters
        queryset = queryset.filter(q_objects)

        getter = request.query_params.get
        fields = self.get_fields(getter)
        ordering = self.get_ordering(getter, fields)
        if len(ordering):
            for num, item in enumerate(ordering):
                pass
                # TODO: implement ordering
                if item == 'number':
                    ordering[num] = 'number'
                elif item == '-number':
                    ordering[num] = '-number'
                elif item == 'identifier':
                    ordering[num] = 'identifier'
                elif item == '-identifier':
                    ordering[num] = '-identifier'

            queryset = queryset.order_by(*ordering).distinct()

        setattr(view, '_datatables_total_count', total_count)
        return queryset


class ArtifactPaginatedViewSet(viewsets.ModelViewSet):
    filter_backends = (ArtifactFilterBackend,)
    pagination_class = DatatablesPageNumberPagination
    queryset = Artifact.objects.none()
    serializer_class = ArtifactPaginatedSerializer
    page_size = 10

    def get_queryset(self):
        # user = self.request.user
        if is_internal(self.request):
            return Artifact.objects.all()
        return Artifact.objects.none()

    @list_route(methods=['GET', ])
    def get_paginated_datatable(self, request, *args, **kwargs):

        queryset = self.get_queryset()
        queryset = self.filter_queryset(queryset)
        self.paginator.page_size = queryset.count()
        result_page = self.paginator.paginate_queryset(queryset, request)
        serializer = ArtifactPaginatedSerializer(result_page, many=True, context={'request': request})
        ret = self.paginator.get_paginated_response(serializer.data)
        return ret


class ArtifactViewSet(viewsets.ModelViewSet):
    queryset = Artifact.objects.all()
    serializer_class = ArtifactSerializer

    def get_queryset(self):
        # import ipdb; ipdb.set_trace()
        user = self.request.user
        if is_internal(self.request):
            return Artifact.objects.all()
        return Artifact.objects.none()

    @detail_route(methods=['GET', ])
    def action_log(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            qs = instance.action_logs.all()
            serializer = ArtifactUserActionSerializer(qs, many=True)
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
            serializer = ArtifactCommsLogEntrySerializer(qs, many=True)
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
                request_data['artifact'] = u'{}'.format(instance.id)
                if request_data.get('comms_log_id'):
                    comms = ArtifactCommsLogEntry.objects.get(
                        id=request_data.get('comms_log_id')
                        )
                    serializer = ArtifactCommsLogEntrySerializer(
                        instance=comms, 
                        data=request.data)
                else:
                    serializer = ArtifactCommsLogEntrySerializer(
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

    @list_route(methods=['GET', ])
    def types(self, request, *args, **kwargs):
        #### TODO: This is just for now
        res_obj = [{'id': 'type_1', 'display': 'Type 1'}, {'id': 'type_2', 'display': 'Type 2'}]
        res_json = json.dumps(res_obj)
        return HttpResponse(res_json, content_type='application/json')
        #########################

        res_obj = []
        for choice in Artifact.TYPE_CHOICES:
            res_obj.append({'id': choice[0], 'display': choice[1]});
        res_json = json.dumps(res_obj)

        return HttpResponse(res_json, content_type='application/json')

    @list_route(methods=['GET', ])
    def statuses(self, request, *args, **kwargs):
        #### TODO: This is just for now
        res_obj = [{'id': 'status_1', 'display': 'Status 1'}, {'id': 'status_2', 'display': 'Status 2'}]
        res_json = json.dumps(res_obj)
        return HttpResponse(res_json, content_type='application/json')
        #########################

        res_obj = []
        for choice in Artifact.STATUS_CHOICES:
            res_obj.append({'id': choice[0], 'display': choice[1]});
        res_json = json.dumps(res_obj)
        return HttpResponse(res_json, content_type='application/json')


#class LegalCasePriorityViewSet(viewsets.ModelViewSet):
#   queryset = LegalCasePriority.objects.all()
#   serializer_class = LegalCasePrioritySerializer
#
#   def get_queryset(self):
#       # user = self.request.user
#       if is_internal(self.request):
#           return LegalCasePriority.objects.all()
#       return LegalCasePriority.objects.none()

   #@detail_route(methods=['GET',])
   #@renderer_classes((JSONRenderer,))
   #def get_schema(self, request, *args, **kwargs):
   #    instance = self.get_object()
   #    try:
   #        serializer = InspectionTypeSchemaSerializer(instance)
   #        return Response(
   #            serializer.data,
   #            status=status.HTTP_201_CREATED,
   #            )
   #    except serializers.ValidationError:
   #        print(traceback.print_exc())
   #        raise
   #    except ValidationError as e:
   #        print(traceback.print_exc())
   #        raise serializers.ValidationError(repr(e.error_dict))
   #    except Exception as e:
   #        print(traceback.print_exc())
   #        raise serializers.ValidationError(str(e))

class DocumentArtifactTypeViewSet(viewsets.ModelViewSet):
   queryset = DocumentArtifactType.objects.all()
   serializer_class = DocumentArtifactTypeSerializer

   def get_queryset(self):
       # user = self.request.user
       if is_internal(self.request):
           return DocumentArtifactType.objects.all()
       return DocumentArtifactType.objects.none()

   #@detail_route(methods=['GET',])
   #@renderer_classes((JSONRenderer,))
   #def get_schema(self, request, *args, **kwargs):
   #    instance = self.get_object()
   #    try:
   #        serializer = InspectionTypeSchemaSerializer(instance)
   #        return Response(
   #            serializer.data,
   #            status=status.HTTP_201_CREATED,
   #            )
   #    except serializers.ValidationError:
   #        print(traceback.print_exc())
   #        raise
   #    except ValidationError as e:
   #        print(traceback.print_exc())
   #        raise serializers.ValidationError(repr(e.error_dict))
   #    except Exception as e:
   #        print(traceback.print_exc())
   #        raise serializers.ValidationError(str(e))

class PhysicalArtifactTypeViewSet(viewsets.ModelViewSet):
   queryset = PhysicalArtifactType.objects.all()
   serializer_class = PhysicalArtifactTypeSerializer

   def get_queryset(self):
       # user = self.request.user
       if is_internal(self.request):
           return PhysicalArtifactType.objects.all()
       return PhysicalArtifactType.objects.none()

