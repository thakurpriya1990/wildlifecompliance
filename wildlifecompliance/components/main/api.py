import traceback
import logging

from wsgiref.util import FileWrapper

from django.http import HttpResponse
from django.db import transaction
from django.core.exceptions import ValidationError

from rest_framework import viewsets, serializers, views, status
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
# from rest_framework import generics
# from rest_framework import filters
from rest_framework.decorators import detail_route
from rest_framework.decorators import list_route
from rest_framework.decorators import renderer_classes
# from rest_framework.decorators import parser_classes
# from rest_framework.decorators import api_view
from rest_framework_datatables.pagination import DatatablesPageNumberPagination
from rest_framework_datatables.filters import DatatablesFilterBackend
from rest_framework_datatables.renderers import DatatablesRenderer

from ledger.payments.utils import oracle_parser

from wildlifecompliance.settings import WC_PAYMENT_SYSTEM_PREFIX
# from wildlifecompliance.settings import SYSTEM_NAME
from wildlifecompliance.components.call_email.models import Location
from wildlifecompliance.components.call_email.serializers import (
    LocationSerializer
)
from wildlifecompliance.components.licences.models import MasterlistQuestion
from wildlifecompliance.components.licences.models import LicencePurposeSection
# from wildlifecompliance.components.licences.models import SectionQuestion
from wildlifecompliance.components.licences.models import SectionQuestion
from wildlifecompliance.components.main.serializers import (
    TemporaryDocumentCollectionSerializer,
    BookingSettlementReportSerializer, OracleSerializer,
    DTSchemaMasterlistSerializer,
    DTSchemaMasterlistSelectSerializer,
    SchemaMasterlistSerializer,
    DTSchemaQuestionSerializer,
    DTSchemaQuestionSelectSerializer,
    SchemaQuestionSerializer,
    SchemaPurposeSerializer,
    SchemaGroupSerializer,
)
from wildlifecompliance.components.main.models import (
    TemporaryDocumentCollection
)
from wildlifecompliance.components.main.process_document import save_document
from wildlifecompliance.components.main.process_document import cancel_document
from wildlifecompliance.components.main.process_document import delete_document
from wildlifecompliance.components.wc_payments import reports
from wildlifecompliance.helpers import is_internal

logger = logging.getLogger(__name__)
# logger = logging


def save_location(location_request_data, *args, **kwargs):
    try:
        if location_request_data.get('id'):
            location_instance = Location.objects.get(
                id=location_request_data.get('id'))
            location_serializer = LocationSerializer(
                instance=location_instance,
                data=location_request_data,
                partial=True
            )
            location_serializer.is_valid(raise_exception=True)
            if location_serializer.is_valid():
                location_serializer.save()
        else:
            location_serializer = LocationSerializer(
                data=location_request_data,
                partial=True
            )
            location_serializer.is_valid(raise_exception=True)
            if location_serializer.is_valid():
                location_instance = location_serializer.save()
        return location_serializer.data
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


class SchemaMasterlistFilterBackend(DatatablesFilterBackend):
    """
    Custom filters
    """
    def filter_queryset(self, request, queryset, view):
        # Get built-in DRF datatables queryset first to join with search text,
        # then apply additional filters.
        # super_queryset = super(
        #     SchemaMasterlistFilterBackend, self
        # ).filter_queryset(request, queryset, view).distinct()

        search_text = request.GET.get('search[value]')

        if queryset.model is MasterlistQuestion:

            if search_text:
                search_text = search_text.lower()
                search_text_masterlist_ids = MasterlistQuestion.objects.values(
                    'id'
                ).filter(question__icontains=search_text)

                queryset = queryset.filter(
                    id__in=search_text_masterlist_ids
                ).distinct()

        total_count = queryset.count()
        # override queryset ordering, required because the ordering is usually
        # handled in the super call, but is then clobbered by the custom
        # queryset joining above also needed to disable ordering for all fields
        # for which data is not an Application model field, as property
        # functions will not work with order_by.
        getter = request.query_params.get
        fields = self.get_fields(getter)
        ordering = self.get_ordering(getter, fields)
        if len(ordering):
            queryset = queryset.order_by(*ordering)

        total_count = queryset.count()

        setattr(view, '_datatables_total_count', total_count)
        return queryset


class SchemaMasterlistRenderer(DatatablesRenderer):
    def render(self, data, accepted_media_type=None, renderer_context=None):
        if 'view' in renderer_context and \
                hasattr(renderer_context['view'], '_datatables_total_count'):
            data['recordsTotal'] = \
                renderer_context['view']._datatables_total_count
        return super(SchemaMasterlistRenderer, self).render(
            data, accepted_media_type, renderer_context)


class SchemaMasterlistPaginatedViewSet(viewsets.ModelViewSet):
    filter_backends = (SchemaMasterlistFilterBackend,)
    pagination_class = DatatablesPageNumberPagination
    renderer_classes = (SchemaMasterlistRenderer,)
    queryset = MasterlistQuestion.objects.none()
    serializer_class = DTSchemaMasterlistSerializer
    page_size = 10

    def get_queryset(self):
        # user = self.request.user
        return MasterlistQuestion.objects.all()

    @list_route(methods=['GET', ])
    def schema_masterlist_datatable_list(self, request, *args, **kwargs):
        self.serializer_class = DTSchemaMasterlistSerializer
        queryset = self.get_queryset()

        queryset = self.filter_queryset(queryset)
        self.paginator.page_size = queryset.count()
        result_page = self.paginator.paginate_queryset(queryset, request)
        serializer = DTSchemaMasterlistSerializer(
            result_page, context={'request': request}, many=True
        )
        response = self.paginator.get_paginated_response(serializer.data)

        return response


class SchemaMasterlistViewSet(viewsets.ModelViewSet):
    queryset = MasterlistQuestion.objects.all()
    serializer_class = SchemaMasterlistSerializer

    def get_queryset(self):
        return self.queryset

    @detail_route(methods=['GET', ])
    def get_masterlist_selects(self, request, *args, **kwargs):
        '''
        Get independant Select lists associated with Schema Masterlist.
        '''
        try:

            instance = MasterlistQuestion.objects.last()
            serializer = DTSchemaMasterlistSelectSerializer(
                instance, context={'is_internal': is_internal(request)}
            )

            return Response(serializer.data)

        except serializers.ValidationError as ve:
            log = '{0} {1}'.format('get_masterlist_selects()', ve)
            logger.exception(log)
            raise

        except ValidationError as e:
            if hasattr(e, 'error_dict'):
                raise serializers.ValidationError(repr(e.error_dict))
            else:
                raise serializers.ValidationError(repr(e[0]))

        except Exception as e:
            logger.exception()
            raise serializers.ValidationError(str(e))

    @detail_route(methods=['DELETE', ])
    def delete_masterlist(self, request, *args, **kwargs):
        '''
        Delete Masterlist record.
        '''
        try:
            instance = self.get_object()

            with transaction.atomic():

                instance.delete()

            return Response(
                {'masterlist_id': instance.id},
                status=status.HTTP_200_OK
            )

        except serializers.ValidationError as ve:
            log = '{0} {1}'.format('save_masterlist()', ve)
            logger.exception(log)
            raise

        except ValidationError as e:
            if hasattr(e, 'error_dict'):
                raise serializers.ValidationError(repr(e.error_dict))
            else:
                raise serializers.ValidationError(repr(e[0]))

        except Exception as e:
            logger.exception()
            raise serializers.ValidationError(str(e))

    @detail_route(methods=['POST', ])
    def save_masterlist(self, request, *args, **kwargs):
        '''
        Save Masterlist record.
        '''
        try:
            instance = self.get_object()

            with transaction.atomic():

                serializer = SchemaMasterlistSerializer(
                    instance, data=request.data
                )
                serializer.is_valid(raise_exception=True)
                serializer.save()

            return Response(
                {'masterlist_id': instance.id},
                status=status.HTTP_200_OK
            )

        except serializers.ValidationError as ve:
            log = '{0} {1}'.format('save_masterlist()', ve)
            logger.exception(log)
            raise

        except ValidationError as e:
            if hasattr(e, 'error_dict'):
                raise serializers.ValidationError(repr(e.error_dict))
            else:
                raise serializers.ValidationError(repr(e[0]))

        except Exception as e:
            logger.exception()
            raise serializers.ValidationError(str(e))


class SchemaPurposeFilterBackend(DatatablesFilterBackend):
    """
    Custom filters
    """
    def filter_queryset(self, request, queryset, view):
        # Get built-in DRF datatables queryset first to join with search text,
        # then apply additional filters.
        super_queryset = super(
            SchemaPurposeFilterBackend, self
        ).filter_queryset(request, queryset, view).distinct()

        total_count = queryset.count()
        # override queryset ordering, required because the ordering is usually
        # handled in the super call, but is then clobbered by the custom
        # queryset joining above also needed to disable ordering for all fields
        # for which data is not an Application model field, as property
        # functions will not work with order_by.
        getter = request.query_params.get
        fields = self.get_fields(getter)
        ordering = self.get_ordering(getter, fields)
        if len(ordering):
            queryset = super_queryset.order_by(*ordering)

        total_count = queryset.count()

        setattr(view, '_datatables_total_count', total_count)
        return queryset


class SchemaPurposeRenderer(DatatablesRenderer):
    def render(self, data, accepted_media_type=None, renderer_context=None):
        if 'view' in renderer_context and \
                hasattr(renderer_context['view'], '_datatables_total_count'):
            data['recordsTotal'] = \
                renderer_context['view']._datatables_total_count
        return super(SchemaPurposeRenderer, self).render(
            data, accepted_media_type, renderer_context)


class SchemaPurposePaginatedViewSet(viewsets.ModelViewSet):
    filter_backends = (SchemaPurposeFilterBackend,)
    pagination_class = DatatablesPageNumberPagination
    renderer_classes = (SchemaPurposeRenderer,)
    queryset = LicencePurposeSection.objects.none()
    serializer_class = SchemaPurposeSerializer
    page_size = 10

    def get_queryset(self):
        # user = self.request.user
        return LicencePurposeSection.objects.all()

    @list_route(methods=['GET', ])
    def schema_purpose_datatable_list(self, request, *args, **kwargs):
        self.serializer_class = SchemaPurposeSerializer
        queryset = self.get_queryset()

        queryset = self.filter_queryset(queryset)
        self.paginator.page_size = queryset.count()
        # self.paginator.page_size = 0
        result_page = self.paginator.paginate_queryset(queryset, request)
        serializer = SchemaPurposeSerializer(
            result_page, context={'request': request}, many=True
        )
        response = self.paginator.get_paginated_response(serializer.data)

        return response


class SchemaPurposeViewSet(viewsets.ModelViewSet):
    queryset = LicencePurposeSection.objects.all()
    serializer_class = SchemaMasterlistSerializer

    def get_queryset(self):
        return self.queryset

    @detail_route(methods=['POST', ])
    def save_masterlist(self, request, *args, **kwargs):
        '''
        Save Masterlist record.
        '''
        try:
            with transaction.atomic():

                serializer = SchemaMasterlistSerializer(data=request.data)
                serializer.is_valid(raise_exception=True)
                serializer.save()

            return Response(serializer.data)

        except serializers.ValidationError as ve:
            log = '{0} {1}'.format('save_masterlist()', ve)
            logger.exception(log)
            raise

        except ValidationError as e:
            if hasattr(e, 'error_dict'):
                raise serializers.ValidationError(repr(e.error_dict))
            else:
                raise serializers.ValidationError(repr(e[0]))

        except Exception as e:
            logger.exception()
            raise serializers.ValidationError(str(e))


class SchemaGroupFilterBackend(DatatablesFilterBackend):
    """
    Custom filters
    """
    def filter_queryset(self, request, queryset, view):
        # Get built-in DRF datatables queryset first to join with search text,
        # then apply additional filters.
        super_queryset = super(
            SchemaGroupFilterBackend, self
        ).filter_queryset(request, queryset, view).distinct()

        total_count = queryset.count()
        # override queryset ordering, required because the ordering is usually
        # handled in the super call, but is then clobbered by the custom
        # queryset joining above also needed to disable ordering for all fields
        # for which data is not an Application model field, as property
        # functions will not work with order_by.
        getter = request.query_params.get
        fields = self.get_fields(getter)
        ordering = self.get_ordering(getter, fields)
        if len(ordering):
            queryset = super_queryset.order_by(*ordering)

        total_count = queryset.count()

        setattr(view, '_datatables_total_count', total_count)
        return queryset


class SchemaGroupRenderer(DatatablesRenderer):
    def render(self, data, accepted_media_type=None, renderer_context=None):
        if 'view' in renderer_context and \
                hasattr(renderer_context['view'], '_datatables_total_count'):
            data['recordsTotal'] = \
                renderer_context['view']._datatables_total_count
        return super(SchemaGroupRenderer, self).render(
            data, accepted_media_type, renderer_context)


class SchemaGroupPaginatedViewSet(viewsets.ModelViewSet):
    filter_backends = (SchemaGroupFilterBackend,)
    pagination_class = DatatablesPageNumberPagination
    renderer_classes = (SchemaGroupRenderer,)
    queryset = SectionQuestion.objects.none()
    serializer_class = SchemaGroupSerializer
    page_size = 10

    def get_queryset(self):
        return SectionQuestion.objects.all()

    @list_route(methods=['GET', ])
    def schema_group_datatable_list(self, request, *args, **kwargs):
        self.serializer_class = SchemaGroupSerializer
        queryset = self.get_queryset()

        queryset = self.filter_queryset(queryset)
        self.paginator.page_size = queryset.count()
        # self.paginator.page_size = 0
        result_page = self.paginator.paginate_queryset(queryset, request)
        serializer = SchemaGroupSerializer(
            result_page, context={'request': request}, many=True
        )
        response = self.paginator.get_paginated_response(serializer.data)

        return response


class SchemaGroupViewSet(viewsets.ModelViewSet):
    queryset = SectionQuestion.objects.all()
    serializer_class = SchemaMasterlistSerializer

    def get_queryset(self):
        return self.queryset

    @detail_route(methods=['POST', ])
    def save_masterlist(self, request, *args, **kwargs):
        '''
        Save Masterlist record.
        '''
        try:
            with transaction.atomic():

                serializer = SchemaMasterlistSerializer(data=request.data)
                serializer.is_valid(raise_exception=True)
                serializer.save()

            return Response(serializer.data)

        except serializers.ValidationError as ve:
            log = '{0} {1}'.format('save_masterlist()', ve)
            logger.exception(log)
            raise

        except ValidationError as e:
            if hasattr(e, 'error_dict'):
                raise serializers.ValidationError(repr(e.error_dict))
            else:
                raise serializers.ValidationError(repr(e[0]))

        except Exception as e:
            logger.exception()
            raise serializers.ValidationError(str(e))


class SchemaQuestionFilterBackend(DatatablesFilterBackend):
    """
    Custom filters
    """
    def filter_queryset(self, request, queryset, view):
        # Get built-in DRF datatables queryset first to join with search text,
        # then apply additional filters.
        # super_queryset = super(
        #     SchemaQuestionFilterBackend, self
        # ).filter_queryset(request, queryset, view).distinct()

        search_text = request.GET.get('search[value]')
        purpose = request.GET.get('licence_purpose_id')
        section = request.GET.get('section_id')

        if queryset.model is SectionQuestion:

            if search_text:
                search_text = search_text.lower()
                search_text_question_ids = SectionQuestion.objects.values(
                    'id'
                ).filter(
                    section__licence_purpose__name__icontains=search_text
                )

                queryset = queryset.filter(
                    id__in=search_text_question_ids
                ).distinct()

            purpose = purpose.lower() if purpose else 'all'
            if purpose != 'all':
                purpose_ids = SectionQuestion.objects.values(
                    'id'
                ).filter(
                    section__licence_purpose_id=int(purpose)
                )
                queryset = queryset.filter(id__in=purpose_ids)

            section = section.lower() if section else 'all'
            if section != 'all':
                section_ids = SectionQuestion.objects.values(
                    'id'
                ).filter(
                    section_id=int(section)
                )
                queryset = queryset.filter(id__in=section_ids)

        total_count = queryset.count()
        # override queryset ordering, required because the ordering is usually
        # handled in the super call, but is then clobbered by the custom
        # queryset joining above also needed to disable ordering for all fields
        # for which data is not an Application model field, as property
        # functions will not work with order_by.
        getter = request.query_params.get
        fields = self.get_fields(getter)
        ordering = self.get_ordering(getter, fields)
        if len(ordering):
            queryset = queryset.order_by(*ordering)

        total_count = queryset.count()

        setattr(view, '_datatables_total_count', total_count)
        return queryset


class SchemaQuestionRenderer(DatatablesRenderer):
    def render(self, data, accepted_media_type=None, renderer_context=None):
        if 'view' in renderer_context and \
                hasattr(renderer_context['view'], '_datatables_total_count'):
            data['recordsTotal'] = \
                renderer_context['view']._datatables_total_count
        return super(SchemaQuestionRenderer, self).render(
            data, accepted_media_type, renderer_context)


class SchemaQuestionPaginatedViewSet(viewsets.ModelViewSet):
    filter_backends = (SchemaQuestionFilterBackend,)
    pagination_class = DatatablesPageNumberPagination
    renderer_classes = (SchemaQuestionRenderer,)
    queryset = SectionQuestion.objects.none()
    serializer_class = DTSchemaQuestionSerializer
    page_size = 10

    def get_queryset(self):
        # user = self.request.user
        return SectionQuestion.objects.all()

    @list_route(methods=['GET', ])
    def schema_question_datatable_list(self, request, *args, **kwargs):
        self.serializer_class = DTSchemaQuestionSerializer
        queryset = self.get_queryset()

        queryset = self.filter_queryset(queryset)
        self.paginator.page_size = queryset.count()
        # self.paginator.page_size = 0
        result_page = self.paginator.paginate_queryset(queryset, request)
        serializer = DTSchemaQuestionSerializer(
            result_page, context={'request': request}, many=True
        )
        response = self.paginator.get_paginated_response(serializer.data)

        return response


class SchemaQuestionViewSet(viewsets.ModelViewSet):
    queryset = SectionQuestion.objects.all()
    serializer_class = SchemaQuestionSerializer

    def get_queryset(self):
        return self.qeryset

    @detail_route(methods=['GET', ])
    def get_question_parents(self, request, *args, **kwargs):
        '''
        Get all Parent Question associated with Schema Questions in Section.
        '''
        try:
            section_id = request.data.get('section_id', None)
            instance = SectionQuestion.objects.last()


            return Response(serializer.data)

        except serializers.ValidationError as ve:
            log = '{0} {1}'.format('get_question_sections()', ve)
            logger.exception(log)
            raise

        except ValidationError as e:
            if hasattr(e, 'error_dict'):
                raise serializers.ValidationError(repr(e.error_dict))
            else:
                raise serializers.ValidationError(repr(e[0]))

        except Exception as e:
            logger.exception()
            raise serializers.ValidationError(str(e))

    @detail_route(methods=['GET', ])
    def get_question_sections(self, request, *args, **kwargs):
        '''
        Get all Sections associated with Schema Questions with Licence Purpose.
        '''
        try:
            purpose_id = request.data.get('licence_purpose_id', None)

            instance = SectionQuestion.objects.last()
            sections = LicencePurposeSection.objects.filter(
                licence_purpose_id=int(purpose_id)
            )
            serializer = SchemaPurposeSerializer(
                instance, context={'is_internal': is_internal(request)}
            )

            return Response(serializer.data)

        except serializers.ValidationError as ve:
            log = '{0} {1}'.format('get_question_sections()', ve)
            logger.exception(log)
            raise

        except ValidationError as e:
            if hasattr(e, 'error_dict'):
                raise serializers.ValidationError(repr(e.error_dict))
            else:
                raise serializers.ValidationError(repr(e[0]))

        except Exception as e:
            logger.exception()
            raise serializers.ValidationError(str(e))

    @detail_route(methods=['GET', ])
    def get_question_selects(self, request, *args, **kwargs):
        '''
        Get independant Select lists associated with Schema Questions.
        '''
        try:

            instance = SectionQuestion.objects.last()
            serializer = DTSchemaQuestionSelectSerializer(
                instance, context={'is_internal': is_internal(request)}
            )

            return Response(serializer.data)

        except serializers.ValidationError as ve:
            log = '{0} {1}'.format('get_question_selects()', ve)
            logger.exception(log)
            raise

        except ValidationError as e:
            if hasattr(e, 'error_dict'):
                raise serializers.ValidationError(repr(e.error_dict))
            else:
                raise serializers.ValidationError(repr(e[0]))

        except Exception as e:
            logger.exception()
            raise serializers.ValidationError(str(e))

    @detail_route(methods=['DELETE', ])
    def delete_question(self, request, *args, **kwargs):
        '''
        Delete Section Question record.
        '''
        try:
            instance = self.get_object()

            with transaction.atomic():

                instance.delete()

            return Response(
                {'masterlist_id': instance.id},
                status=status.HTTP_200_OK
            )

        except serializers.ValidationError as ve:
            log = '{0} {1}'.format('delete_question()', ve)
            logger.exception(log)
            raise

        except ValidationError as e:
            if hasattr(e, 'error_dict'):
                raise serializers.ValidationError(repr(e.error_dict))
            else:
                raise serializers.ValidationError(repr(e[0]))

        except Exception as e:
            logger.exception()
            raise serializers.ValidationError(str(e))

    @detail_route(methods=['POST', ])
    def save_question(self, request, *args, **kwargs):
        '''
        Save Section Question record.
        '''
        try:
            with transaction.atomic():

                serializer = SchemaMasterlistSerializer(data=request.data)
                serializer.is_valid(raise_exception=True)
                serializer.save()

            return Response(
                {'question_id': serializer.data.id},
                status=status.HTTP_200_OK
            )

        except serializers.ValidationError as ve:
            log = '{0} {1}'.format('save_question()', ve)
            logger.exception(log)
            raise

        except ValidationError as e:
            if hasattr(e, 'error_dict'):
                raise serializers.ValidationError(repr(e.error_dict))
            else:
                raise serializers.ValidationError(repr(e[0]))

        except Exception as e:
            logger.exception()
            raise serializers.ValidationError(str(e))


class TemporaryDocumentCollectionViewSet(viewsets.ModelViewSet):
    queryset = TemporaryDocumentCollection.objects.all()
    serializer_class = TemporaryDocumentCollectionSerializer

    def get_queryset(self):
        # import ipdb; ipdb.set_trace()
        # user = self.request.user
        if is_internal(self.request):
            return TemporaryDocumentCollection.objects.all()
        return TemporaryDocumentCollection.objects.none()

    def create(self, request, *args, **kwargs):
        print("create temp doc coll")
        print(request.data)
        try:
            with transaction.atomic():
                serializer = TemporaryDocumentCollectionSerializer(
                        data=request.data, 
                        )
                serializer.is_valid(raise_exception=True)
                if serializer.is_valid():
                    instance = serializer.save()
                    save_document(
                        request,
                        instance, comms_instance=None, document_type=None
                    )

                    return Response(serializer.data)
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
    # Designed for uploading comms_log files within "create" modals when no
    # parent entity instance yet exists
    # response returned to compliance_file.vue
    def process_temp_comms_log_document(self, request, *args, **kwargs):
        print("process_temp_comms_log_document")
        print(request.data)
        try:
            instance = self.get_object()
            action = request.data.get('action')
            # comms_instance = None

            if action == 'list':
                pass

            elif action == 'delete':
                delete_document(
                    request, instance, comms_instance=None, document_type=None)

            elif action == 'cancel':
                cancel_document(
                    request, instance, comms_instance=None, document_type=None)

            elif action == 'save':
                save_document(
                    request, instance, comms_instance=None, document_type=None)

            returned_file_data = [dict(
                        file=d._file.url,
                        id=d.id,
                        name=d.name,
                        ) for d in instance.documents.all() if d._file]
            return Response({'filedata': returned_file_data})

        except Exception as e:
            print(traceback.print_exc())
            raise e


class BookingSettlementReportView(views.APIView):
    renderer_classes = (JSONRenderer,)

    def get(self, request, format=None):
        try:
            # http_status = status.HTTP_200_OK
            # parse and validate data
            report = None
            data = {
                "date": request.GET.get('date'),
            }
            serializer = BookingSettlementReportSerializer(data=data)
            serializer.is_valid(raise_exception=True)
            filename = 'Booking Settlement Report-{}'.format(
                str(serializer.validated_data['date'])
            )
            # Generate Report
            report = reports.booking_bpoint_settlement_report(
                serializer.validated_data['date']
            )
            if report:
                response = HttpResponse(
                    FileWrapper(report), content_type='text/csv'
                )
                response[
                    'Content-Disposition'
                ] = 'attachment; filename="{}.csv"'.format(filename)
                return response
            else:
                raise serializers.ValidationError('No report was generated.')
        except serializers.ValidationError:
            raise
        except Exception:
            traceback.print_exc()


def oracle_integration(date, override):
    system = WC_PAYMENT_SYSTEM_PREFIX
    # oracle_codes = oracle_parser(
    # date, system, 'Commercial Operator Licensing', override=override
    # )
    oracle_codes = oracle_parser(
        date, system, 'WildlifeCompliance', override=override
    )


class OracleJob(views.APIView):
    renderer_classes = [JSONRenderer, ]

    def get(self, request, format=None):
        try:
            data = {
                "date": request.GET.get("date"),
                "override": request.GET.get("override")
            }
            serializer = OracleSerializer(data=data)
            serializer.is_valid(raise_exception=True)
            oracle_integration(
                serializer.validated_data[
                    'date'
                ].strftime('%Y-%m-%d'), serializer.validated_data['override']
            )
            data = {'successful': True}
            return Response(data)
        except serializers.ValidationError:
            print(traceback.print_exc())
            raise
        except ValidationError as e:
            raise serializers.ValidationError(repr(e.error_dict)) if hasattr(
                e, 'error_dict'
            ) else serializers.ValidationError(e)
        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e[0]))
