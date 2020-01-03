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
        try:
            with transaction.atomic():
                request_data = request.data
                instance, headers = self.common_save(request_data)

                instance.log_user_action(
                        ArtifactUserAction.ACTION_CREATE_ARTIFACT.format(
                        instance.number), request)
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
        try:
            with transaction.atomic():
                instance = self.get_object()
                request_data = request.data
                instance, headers = self.common_save(request_data, instance)
                instance.log_user_action(
                        ArtifactUserAction.ACTION_SAVE_ARTIFACT.format(
                        instance.number), request)
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

    def common_save(self, request_data, instance=None):
        print("common save")
        print(request_data)
        try:
            with transaction.atomic():
                document_type = request_data.get('document_type')
                document_type_id = None
                if document_type:
                    document_type_id = document_type.get('id')
                    request_data['document_type_id'] = document_type_id

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
                    # save legal_case_id
                    legal_case_id = request_data.get('legal_case_id')
                    if legal_case_id:
                        instance.add_legal_case(legal_case_id)
                    # TODO add people attending

                    return (instance, headers)
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
                instance, headers = self.common_save(request_data)

                instance.log_user_action(
                        ArtifactUserAction.ACTION_CREATE_ARTIFACT.format(
                        instance.number), request)
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
                request_data = request.data
                instance, headers = self.common_save(request_data, instance)
                instance.log_user_action(
                        ArtifactUserAction.ACTION_SAVE_ARTIFACT.format(
                        instance.number), request)
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

    def common_save(self, request_data, instance=None):
        try:
            with transaction.atomic():
                physical_artifact_type = request_data.get('physical_artifact_type')
                physical_artifact_type_id = None
                if physical_artifact_type:
                    physical_artifact_type_id = physical_artifact_type.get('id')
                    request_data['physical_artifact_type_id'] = physical_artifact_type_id

                if instance:
                    serializer = SavePhysicalArtifactSerializer(
                            instance=instance,
                            data=request_data, 
                            partial=True
                            )
                else:
                    serializer = SavePhysicalArtifactSerializer(
                            data=request_data, 
                            partial=True
                            )
                serializer.is_valid(raise_exception=True)
                if serializer.is_valid():
                    print("serializer.validated_data")
                    print(serializer.validated_data)
                    instance = serializer.save()
                    headers = self.get_success_headers(serializer.data)
                    # save legal_case_id
                    legal_case_id = request_data.get('legal_case_id')
                    if legal_case_id:
                        instance.add_legal_case(legal_case_id)
                    return (instance, headers)
        except serializers.ValidationError:
            print(traceback.print_exc())
            raise
        except ValidationError as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(repr(e.error_dict))
        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))

    #def create(self, request, *args, **kwargs):
    #    print("create")
    #    print(request.data)
    #    try:
    #        with transaction.atomic():
    #            request_data = request.data
    #            physical_artifact_type = request_data.get('physical_artifact_type')
    #            physical_artifact_type_id = None
    #            if physical_artifact_type:
    #                physical_artifact_type_id = physical_artifact_type.get('id')
    #                request_data['physical_artifact_type_id'] = physical_artifact_type_id
    #            serializer = SavePhysicalArtifactSerializer(
    #                    data=request_data, 
    #                    partial=True
    #                    )
    #            serializer.is_valid(raise_exception=True)
    #            if serializer.is_valid():
    #                print("serializer.validated_data")
    #                print(serializer.validated_data)
    #                instance = serializer.save()
    #                instance.log_user_action(
    #                        ArtifactUserAction.ACTION_CREATE_ARTIFACT.format(
    #                        instance.number), request)
    #                headers = self.get_success_headers(serializer.data)
    #                return_serializer = PhysicalArtifactSerializer(instance, context={'request': request})
    #                return Response(
    #                        return_serializer.data,
    #                        status=status.HTTP_201_CREATED,
    #                        headers=headers
    #                        )
    #                # Create comms_log and send mail
    #                #res = self.workflow_action(request, instance, create_legal_case=True)
    #                #if instance.call_email:
    #                 #   print("update parent")
    #                  #  self.update_parent(request, instance)
    #                #return res
    #    except serializers.ValidationError:
    #        print(traceback.print_exc())
    #        raise
    #    except ValidationError as e:
    #        if hasattr(e, 'error_dict'):
    #            raise serializers.ValidationError(repr(e.error_dict))
    #        else:
    #            raise serializers.ValidationError(repr(e[0].encode('utf-8')))
    #    except Exception as e:
    #        print(traceback.print_exc())
    #        raise serializers.ValidationError(str(e))

    #@renderer_classes((JSONRenderer,))
    ##def inspection_save(self, request, workflow=False, *args, **kwargs):
    #def update(self, request, workflow=False, *args, **kwargs):
    #    print(request.data)
    #    try:
    #        with transaction.atomic():
    #            instance = self.get_object()
    #            #if request.data.get('renderer_data'):
    #             #   self.form_data(request)

    #            serializer = SavePhysicalArtifactSerializer(instance, data=request.data)
    #            serializer.is_valid(raise_exception=True)
    #            if serializer.is_valid():
    #                serializer.save()
    #                instance.log_user_action(
    #                        ArtifactUserAction.ACTION_SAVE_ARTIFACT.format(
    #                        instance.number), request)
    #                headers = self.get_success_headers(serializer.data)
    #                return_serializer = PhysicalArtifactSerializer(instance, context={'request': request})
    #                return Response(
    #                        return_serializer.data,
    #                        status=status.HTTP_201_CREATED,
    #                        headers=headers
    #                        )
    #    except serializers.ValidationError:
    #        print(traceback.print_exc())
    #        raise
    #    except ValidationError as e:
    #        print(traceback.print_exc())
    #        raise serializers.ValidationError(repr(e.error_dict))
    #    except Exception as e:
    #        print(traceback.print_exc())
    #        raise serializers.ValidationError(str(e))



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

