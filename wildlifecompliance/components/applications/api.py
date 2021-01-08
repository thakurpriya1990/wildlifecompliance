import traceback
import os
import logging

from datetime import datetime, timedelta
from django.db.models import Q
from django.db import transaction
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.exceptions import ValidationError
from rest_framework import viewsets, serializers, status, views
from rest_framework.decorators import (
    detail_route, list_route, renderer_classes
)
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
from ledger.accounts.models import EmailUser
from ledger.checkout.utils import calculate_excl_gst
from django.urls import reverse
from django.shortcuts import redirect, render
from wildlifecompliance.components.applications.utils import (
    SchemaParser,
    MissingFieldsException,
)
from wildlifecompliance.components.main.utils import (
    checkout,
    set_session_application,
    set_session_activity,
    delete_session_application
)
from wildlifecompliance.helpers import is_customer, is_internal
from wildlifecompliance.components.applications.email import (
    send_application_amendment_notification,
)
from wildlifecompliance.components.applications.models import (
    Application,
    ApplicationSelectedActivity,
    ApplicationCondition,
    ApplicationStandardCondition,
    Assessment,
    ActivityPermissionGroup,
    AmendmentRequest,
    ApplicationUserAction,
    ApplicationFormDataRecord,
    ApplicationInvoice,
    ApplicationSelectedActivityPurpose,
)
from wildlifecompliance.components.applications.services import (
    ApplicationService,
    CheckboxAndRadioButtonVisitor,
    SpeciesOptionsFieldElement,
    StandardConditionFieldElement,
    PromptInspectionFieldElement,
    TSCSpecieService,
    HerbieSpecieKMICall,
)
from wildlifecompliance.components.applications.serializers import (
    ApplicationSerializer,
    InternalApplicationSerializer,
    SaveApplicationSerializer,
    BaseApplicationSerializer,
    CreateExternalApplicationSerializer,
    DTInternalApplicationSerializer,
    DTExternalApplicationSerializer,
    ApplicationUserActionSerializer,
    ApplicationLogEntrySerializer,
    ApplicationConditionSerializer,
    ApplicationStandardConditionSerializer,
    ProposedLicenceSerializer,
    ProposedDeclineSerializer,
    AssessmentSerializer,
    ActivityPermissionGroupSerializer,
    SaveAssessmentSerializer,
    SimpleSaveAssessmentSerializer,
    AmendmentRequestSerializer,
    ApplicationProposedIssueSerializer,
    DTAssessmentSerializer,
    ApplicationSelectedActivitySerializer,
    ValidCompleteAssessmentSerializer,
    DTExternalApplicationSelectedActivitySerializer,
    DTInternalApplicationSelectedActivitySerializer,
    IssueLicenceSerializer,
    DTApplicationSelectSerializer,
)

from wildlifecompliance.components.main.process_document import (
        process_generic_document,
        )

from rest_framework_datatables.pagination import DatatablesPageNumberPagination
from rest_framework_datatables.filters import DatatablesFilterBackend
from rest_framework_datatables.renderers import DatatablesRenderer

from wildlifecompliance.management.permissions_manager import PermissionUser

logger = logging.getLogger(__name__)
# logger = logging


def application_refund_callback(invoice_ref, bpoint_tid):
    '''
    Callback routine for Ledger when refund transaction.

    Required to update payment status on application as this property is
    cached and can only be updated on save.
    '''
    logger.info(
        'application_refund_callback: Inv {0}'.format(invoice_ref)
    )
    try:
        ai = ApplicationInvoice.objects.filter(
            invoice_reference=invoice_ref
        )

        for i in ai:
            i.application.save()

    except Exception as e:
        logger.error(
            'app_refund_callback(): Inv {0} - {1}'.format(invoice_ref, e)
        )


def application_invoice_callback(invoice_ref):
    '''
    Callback routine for Ledger when record transaction.

    Required to update payment status on application as this property is
    cached and can only be updated on save.
    '''
    logger.info(
        'application_invoice_callback: Inv {0}'.format(invoice_ref)
    )
    try:
        ai = ApplicationInvoice.objects.filter(
            invoice_reference=invoice_ref
        )

        for i in ai:
            i.application.save()

    except Exception as e:
        logger.error(
            'app_invoice_callback(): Inv {0} - {1}'.format(invoice_ref, e)
        )


class GetEmptyList(views.APIView):
    renderer_classes = [JSONRenderer, ]

    def get(self, request, format=None):
        return Response([])


class ApplicationFilterBackend(DatatablesFilterBackend):
    """
    Custom filters
    """
    def filter_queryset(self, request, queryset, view):
        # Get built-in DRF datatables queryset first to join with search text,
        # then apply additional filters.
        super_queryset = super(ApplicationFilterBackend, self).filter_queryset(
            request, queryset, view
        ).distinct()

        total_count = queryset.count()
        date_from = request.GET.get('date_from')
        date_to = request.GET.get('date_to')
        category_name = request.GET.get('category_name')
        processing_status = request.GET.get('processing_status')
        customer_status = request.GET.get('customer_status')
        status_filter = request.GET.get('status')
        submitter = request.GET.get('submitter')
        search_text = request.GET.get('search[value]')

        if queryset.model is Application:
            # search_text filter, join all custom search columns
            # where ('searchable: false' in the datatable defintion)
            if search_text:
                search_text = search_text.lower()
                # join queries for the search_text search
                # search_text_app_ids = []
                search_text_app_ids = Application.objects.values(
                    'id'
                ).filter(
                    Q(proxy_applicant__first_name__icontains=search_text) |
                    Q(proxy_applicant__last_name__icontains=search_text)
                )
                # use pipe to join both custom and built-in DRF datatables
                # querysets (returned by super call above)
                # (otherwise they will filter on top of each other)
                queryset = queryset.filter(
                    id__in=search_text_app_ids
                ).distinct() | super_queryset

            # apply user selected filters
            category_name = category_name.lower() if category_name else 'all'
            if category_name != 'all':
                # category_name_app_ids = []
                category_name_app_ids = Application.objects.values(
                    'id'
                ).filter(
                    selected_activities__licence_activity__licence_category__name__icontains=category_name
                )
                queryset = queryset.filter(id__in=category_name_app_ids)
            processing_status = processing_status.lower() if processing_status else 'all'
            if processing_status != 'all':
                # processing_status_app_ids = []
                processing_status_app_ids = [
                    application.id for application in queryset.all()
                    if processing_status in application.processing_status.lower()
                    or (
                        processing_status == Application.PROCESSING_STATUS_DRAFT
                        and Application.PROCESSING_STATUS_AWAITING_APPLICANT_RESPONSE in application.processing_status.lower()
                    )
                ]
                # for application in queryset:
                #     if processing_status in application.processing_status.lower():
                #         processing_status_app_ids.append(application.id)
                queryset = queryset.filter(id__in=processing_status_app_ids)
            customer_status = customer_status.lower() if customer_status else 'all'
            if customer_status != 'all':
                customer_status_app_ids = []
                for application in queryset:
                    if customer_status in application.customer_status.lower():
                        customer_status_app_ids.append(application.id)
                queryset = queryset.filter(id__in=customer_status_app_ids)
            if date_from:
                queryset = queryset.filter(lodgement_date__gte=date_from)
            if date_to:
                date_to = datetime.strptime(date_to, '%Y-%m-%d') + timedelta(days=1)
                queryset = queryset.filter(lodgement_date__lte=date_to)
            submitter = submitter.lower() if submitter else 'all'
            if submitter != 'all':
                queryset = queryset.filter(submitter__email__iexact=submitter)

        if queryset.model is Assessment:
            # search_text filter, join all custom search columns
            # where ('searchable: false' in the datatable definition)
            if search_text:
                search_text = search_text.lower()
                # join queries for the search_text search
                search_text_ass_ids = []
                for assessment in queryset:
                    if (search_text in assessment.application.licence_category.lower()
                        or search_text in assessment.licence_activity.short_name.lower()
                        or search_text in assessment.application.applicant.lower()
                        or search_text in assessment.get_status_display().lower()
                    ):
                        search_text_ass_ids.append(assessment.id)
                    # if applicant is not an organisation, also search against the user's email address
                    if (assessment.application.applicant_type == Application.APPLICANT_TYPE_PROXY and
                        search_text in assessment.application.proxy_applicant.email.lower()):
                            search_text_ass_ids.append(assessment.id)
                    if (assessment.application.applicant_type == Application.APPLICANT_TYPE_SUBMITTER and
                        search_text in assessment.application.submitter.email.lower()):
                            search_text_ass_ids.append(assessment.id)
                # use pipe to join both custom and built-in DRF datatables querysets (returned by super call above)
                # (otherwise they will filter on top of each other)
                queryset = queryset.filter(id__in=search_text_ass_ids).distinct() | super_queryset

            # apply user selected filters
            category_name = category_name.lower() if category_name else 'all'
            if category_name != 'all':
                category_name_app_ids = []
                for assessment in queryset:
                    if category_name in assessment.application.licence_category_name.lower():
                        category_name_app_ids.append(assessment.id)
                queryset = queryset.filter(id__in=category_name_app_ids)
            status_filter = status_filter.lower() if status_filter else 'all'
            if status_filter != 'all':
                queryset = queryset.filter(status=status_filter)
            if date_from:
                queryset = queryset.filter(application__lodgement_date__gte=date_from)
            if date_to:
                date_to = datetime.strptime(date_to, '%Y-%m-%d') + timedelta(days=1)
                queryset = queryset.filter(application__lodgement_date__lte=date_to)
            submitter = submitter.lower() if submitter else 'all'
            if submitter != 'all':
                queryset = queryset.filter(application__submitter__email__iexact=submitter)

        # override queryset ordering, required because the ordering is usually handled
        # in the super call, but is then clobbered by the custom queryset joining above
        # also needed to disable ordering for all fields for which data is not an
        # Application model field, as property functions will not work with order_by
        getter = request.query_params.get
        fields = self.get_fields(getter)
        ordering = self.get_ordering(getter, fields)
        if len(ordering):
            queryset = queryset.order_by(*ordering)

        setattr(view, '_datatables_total_count', total_count)
        return queryset


class ApplicationRenderer(DatatablesRenderer):
    def render(self, data, accepted_media_type=None, renderer_context=None):
        if 'view' in renderer_context and hasattr(renderer_context['view'], '_datatables_total_count'):
            data['recordsTotal'] = renderer_context['view']._datatables_total_count
        return super(ApplicationRenderer, self).render(data, accepted_media_type, renderer_context)


class ApplicationPaginatedViewSet(viewsets.ModelViewSet):
    filter_backends = (ApplicationFilterBackend,)
    pagination_class = DatatablesPageNumberPagination
    renderer_classes = (ApplicationRenderer,)
    queryset = Application.objects.none()
    serializer_class = DTExternalApplicationSerializer
    page_size = 10

    def get_queryset(self):
        user = self.request.user
        if is_internal(self.request):
            return Application.objects.all()\
                .exclude(application_type=Application.APPLICATION_TYPE_SYSTEM_GENERATED)
        elif is_customer(self.request):
            user_orgs = [
                org.id for org in user.wildlifecompliance_organisations.all()]
            return Application.objects.filter(Q(org_applicant_id__in=user_orgs) | Q(
                proxy_applicant=user) | Q(submitter=user))\
                .exclude(application_type=Application.APPLICATION_TYPE_SYSTEM_GENERATED)
        return Application.objects.none()

    @list_route(methods=['GET', ])
    def internal_datatable_list(self, request, *args, **kwargs):
        self.serializer_class = DTInternalApplicationSerializer
        #self.serializer_class = DTInternalApplicationDashboardSerializer
        queryset = self.get_queryset()
        # Filter by org
        org_id = request.GET.get('org_id', None)
        if org_id:
            queryset = queryset.filter(org_applicant_id=org_id)
        # Filter by proxy_applicant
        proxy_applicant_id = request.GET.get('proxy_applicant_id', None)
        if proxy_applicant_id:
            queryset = queryset.filter(proxy_applicant_id=proxy_applicant_id)
        # Filter by submitter
        submitter_id = request.GET.get('submitter_id', None)
        if submitter_id:
            queryset = queryset.filter(submitter_id=submitter_id)
        # Filter by user (submitter or proxy_applicant)
        user_id = request.GET.get('user_id', None)
        if user_id:
            user_orgs = [
                org.id for org in EmailUser.objects.get(id=user_id).wildlifecompliance_organisations.all()]
            queryset = queryset.filter(
                Q(proxy_applicant=user_id) |
                Q(submitter=user_id) |
                Q(org_applicant_id__in=user_orgs)
            )
        queryset = self.filter_queryset(queryset)
        self.paginator.page_size = queryset.count()
        result_page = self.paginator.paginate_queryset(queryset, request)
        # TODO: add caching
        # cached_response = cache.get('internalapplications_{}'.format(result_page))
        # if cached_response:
        #     return cached_response
        serializer = DTInternalApplicationSerializer(result_page, context={'request': request}, many=True)
        # most expensive query that traverses properties etc
        response = self.paginator.get_paginated_response(serializer.data)
        # cache.set('internalapplications_{}'.format(result_page), response, 3600)
        return response

    @list_route(methods=['GET', ])
    def external_datatable_list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        # Filter by org
        org_id = request.GET.get('org_id', None)
        if org_id:
            queryset = queryset.filter(org_applicant_id=org_id)
        # Filter by proxy_applicant
        proxy_applicant_id = request.GET.get('proxy_applicant_id', None)
        if proxy_applicant_id:
            queryset = queryset.filter(proxy_applicant_id=proxy_applicant_id)
        # Filter by submitter
        submitter_id = request.GET.get('submitter_id', None)
        if submitter_id:
            queryset = queryset.filter(submitter_id=submitter_id)
        self.serializer_class = DTExternalApplicationSerializer
        user_orgs = [
            org.id for org in request.user.wildlifecompliance_organisations.all()]
        queryset = self.get_queryset().filter(
            Q(submitter=request.user) |
            Q(proxy_applicant=request.user) |
            Q(org_applicant_id__in=user_orgs)
        ).computed_exclude(
            processing_status=Application.PROCESSING_STATUS_DISCARDED
        ).distinct()
        queryset = self.filter_queryset(queryset)
        self.paginator.page_size = queryset.count()
        result_page = self.paginator.paginate_queryset(queryset, request)
        serializer = DTExternalApplicationSerializer(result_page, context={'request': request}, many=True)
        return self.paginator.get_paginated_response(serializer.data)


class ApplicationViewSet(viewsets.ModelViewSet):
    queryset = Application.objects.all()
    serializer_class = ApplicationSerializer

    def get_queryset(self):
        user = self.request.user
        if is_internal(self.request):
            return Application.objects.all()
        elif is_customer(self.request):
            user_orgs = [
                org.id for org in user.wildlifecompliance_organisations.all()]
            return Application.objects.filter(Q(org_applicant_id__in=user_orgs) | Q(
                proxy_applicant=user) | Q(submitter=user))
        return Application.objects.none()

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = BaseApplicationSerializer(
            queryset, many=True, context={'request': request})
        return Response(serializer.data)

    @detail_route(methods=['POST'])
    @renderer_classes((JSONRenderer,))
    def process_document(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            action = request.POST.get('action')
            section = request.POST.get('input_name')
            if action == 'list' and 'input_name' in request.POST:
                pass

            elif action == 'delete' and 'document_id' in request.POST:
                document_id = request.POST.get('document_id')
                document = instance.documents.get(id=document_id)

                if document._file and os.path.isfile(
                        document._file.path) and document.can_delete:
                    os.remove(document._file.path)

                document.delete()
                instance.save(version_comment='Approval File Deleted: {}'.format(
                    document.name))  # to allow revision to be added to reversion history

            elif action == 'save' and 'input_name' in request.POST and 'filename' in request.POST:
                application_id = request.POST.get('application_id')
                filename = request.POST.get('filename')
                _file = request.POST.get('_file')
                if not _file:
                    _file = request.FILES.get('_file')

                document = instance.documents.get_or_create(
                    input_name=section, name=filename)[0]
                path = default_storage.save(
                    'applications/{}/documents/{}'.format(
                        application_id, filename), ContentFile(
                        _file.read()))

                document._file = path
                document.save()
                # to allow revision to be added to reversion history
                instance.save(
                    version_comment='File Added: {}'.format(filename))

            return Response(
                [
                    dict(
                        input_name=d.input_name,
                        name=d.name,
                        file=d._file.url,
                        id=d.id,
                        can_delete=d.can_delete) for d in instance.documents.filter(
                        input_name=section) if d._file])

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

    @detail_route(methods=['GET', ])
    def action_log(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            qs = instance.action_logs.all()
            serializer = ApplicationUserActionSerializer(qs, many=True)
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
            serializer = ApplicationLogEntrySerializer(qs, many=True)
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
    def add_comms_log(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
                instance = self.get_object()
                request.data['application'] = u'{}'.format(instance.id)
                request.data['staff'] = u'{}'.format(request.user.id)
                request.data['log_type'] = request.data['type']
                serializer = ApplicationLogEntrySerializer(data=request.data)
                serializer.is_valid(raise_exception=True)
                comms = serializer.save()
                # Save the files
                for f in request.FILES:
                    document = comms.documents.create()
                    document.name = str(request.FILES[f])
                    document._file = request.FILES[f]
                    document.save()
                # End Save Documents

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
    def get_application_selects(self, request, *args, **kwargs):
        '''
        Returns all drop-down lists for application dashboard.
        '''
        try:

            instance = Application.objects.last()
            serializer = DTApplicationSelectSerializer(instance)

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
    def conditions(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            qs = instance.conditions.all()
            licence_activity = self.request.query_params.get(
                'licence_activity', None)
            if licence_activity is not None:
                qs = qs.filter(licence_activity=licence_activity)
            serializer = ApplicationConditionSerializer(
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

    @detail_route(methods=['GET', ])
    def assessments(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            qs = instance.assessments
            serializer = AssessmentSerializer(qs, many=True)
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
    def assign_application_assessment(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            instance.assign_application_assessment(request)
            serializer = InternalApplicationSerializer(
                instance, context={'request': request})
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
    def complete_application_assessments(self, request, *args, **kwargs):
        try:
            validator = ValidCompleteAssessmentSerializer(data=request.data)
            validator.is_valid(raise_exception=True)
            instance = self.get_object()
            instance.complete_application_assessments_by_user(request)
            serializer = InternalApplicationSerializer(
                instance, context={'request': request})
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

    @detail_route(methods=['POST', ])
    def add_assessment_inspection(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            for assessment in instance.assessments:
                if assessment.licence_activity.id == \
                   request.data.get('licence_activity_id'):
                    assessment.add_inspection(request)
            serializer = InternalApplicationSerializer(
                instance, context={'request': request})
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
    def active_licence_application(self, request, *args, **kwargs):
        # active_application = Application.get_active_licence_applications(
        #     request).first()
        active_application = Application.get_first_active_licence_application(
            request
        )
        if not active_application:
            return Response({'application': None})

        serializer = DTExternalApplicationSerializer(
            active_application, context={'request': request})
        return Response({'application': serializer.data})

    @list_route(methods=['POST', ])
    def estimate_price(self, request, *args, **kwargs):
        purpose_ids = request.data.get('purpose_ids', [])
        application_id = request.data.get('application_id')
        licence_type = request.data.get('licence_type')

        with transaction.atomic():
            if application_id is not None:
                application = Application.objects.get(id=application_id)
                return Response({
                    'fees': ApplicationService.calculate_fees(
                        application, request.data.get('field_data', {}))
                })
            return Response({
                'fees': Application.calculate_base_fees(
                    purpose_ids, licence_type)
            })

    @list_route(methods=['GET', ])
    def internal_datatable_list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = DTInternalApplicationSerializer(
            queryset, many=True, context={'request': request})
        return Response(serializer.data)

    @list_route(methods=['GET', ])
    def user_list(self, request, *args, **kwargs):
        user_orgs = [
            org.id for org in request.user.wildlifecompliance_organisations.all()]

        queryset = self.get_queryset().filter(
            Q(submitter=request.user) |
            Q(proxy_applicant=request.user) |
            Q(org_applicant_id__in=user_orgs)
        ).computed_exclude(
            processing_status=Application.PROCESSING_STATUS_DISCARDED
        ).distinct()

        serializer = DTExternalApplicationSerializer(
            queryset, many=True, context={'request': request})
        return Response(serializer.data)

    @detail_route(methods=['GET', ])
    def internal_application(self, request, *args, **kwargs):
        logger.debug('ApplicationViewSet.internal_application() - start')
        instance = self.get_object()
        serializer = InternalApplicationSerializer(
            instance, context={'request': request})
        response = Response(serializer.data)
        logger.debug('ApplicationViewSet.internal_application() - end')

        return response

    @detail_route(methods=['post'])
    @renderer_classes((JSONRenderer,))
    def submit(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            try:
                instance.submit(request)
            except MissingFieldsException as e:
                return Response({
                    'missing': e.error_list},
                    status=status.HTTP_400_BAD_REQUEST
                )
            serializer = self.get_serializer(instance)
            return Response(serializer.data)
        except serializers.ValidationError:
            delete_session_application(request.session)
            print(traceback.print_exc())
            raise
        except ValidationError as e:
            if hasattr(e, 'error_dict'):
                raise serializers.ValidationError(repr(e.error_dict))
            else:
                # raise serializers.ValidationError(repr(e[0].encode('utf-8')))
                raise serializers.ValidationError(repr(e[0]))
        except Exception as e:
            delete_session_application(request.session)
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))

    @detail_route(methods=['post'])
    @renderer_classes((JSONRenderer,))
    def application_fee_checkout(self, request, *args, **kwargs):
        try:
            checkout_result = None
            instance = self.get_object()

            with transaction.atomic():

                product_lines = []
                if instance.application_fee < 1:
                    raise Exception('Checkout request for zero amount.')

                application_submission = u'Application No: {}'.format(
                    instance.lodgement_number
                )

                set_session_application(request.session, instance)
                product_lines = ApplicationService.get_product_lines(instance)

                checkout_result = checkout(
                    request, instance, lines=product_lines,
                    invoice_text=application_submission
                )

            return checkout_result

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

    @detail_route(methods=['post'])
    @renderer_classes((JSONRenderer,))
    def application_fee_reception(self, request, *args, **kwargs):
        '''
        Process to pay application fee and record by licensing reception.
        '''
        try:
            instance = self.get_object()

            with transaction.atomic():

                # if not request.user.is_staff:
                #     raise Exception('Non staff member.')

                session = request.session
                set_session_application(session, instance)

                if instance.submit_type == Application.SUBMIT_TYPE_PAPER:
                    invoice = ApplicationService.cash_payment_submission(
                        request)
                    invoice_url = request.build_absolute_uri(
                        reverse(
                            'payments:invoice-pdf',
                            kwargs={'reference': invoice}))

                elif instance.submit_type == Application.SUBMIT_TYPE_MIGRATE:
                    invoice = ApplicationService.none_payment_submission(
                        request)
                    invoice_url = None

                else:
                    raise Exception('Cannot make this type of payment.')

                # return template application-success
                template_name = 'wildlifecompliance/application_success.html'
                context = {
                    'application': instance,
                    'invoice_ref': invoice,
                    'invoice_url': invoice_url
                }

            return render(request, template_name, context)

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

    @detail_route(methods=['post'])
    @renderer_classes((JSONRenderer,))
    def licence_fee_checkout(self, request, *args, **kwargs):
        from wildlifecompliance.components.applications.payments import (
            LicenceFeeClearingInvoice,
            ApplicationFeePolicy,
        )
        PAY_STATUS = ApplicationSelectedActivity.PROCESSING_STATUS_AWAITING_LICENCE_FEE_PAYMENT
        try:
            instance = self.get_object()
            activity_id = request.data.get('activity_id')
            if not activity_id:
                raise Exception('No activity selected for payment!')

            product_lines = []
            application_submission = u'Application No: {}'.format(
                instance.lodgement_number)

            activities = instance.selected_activities.all()
            # store first activity on session for id.
            set_session_activity(request.session, activities[0])

            # Adjustments occuring only to the application fee.
            # if instance.has_adjusted_fees or instance.has_additional_fees \
            if instance.has_additional_fees \
                or instance.has_payable_fees_at_finalisation:

                # activities = instance.amended_activities
                # only fees awaiting payment
                activities_pay = [
                    a for a in activities if a.processing_status == PAY_STATUS
                ]
                # only fees with adjustments or additional fee.
                activities_adj = [
                   a for a in activities_pay
                #    if a.has_adjusted_application_fee
                if a.has_payable_fees_at_issue
                   or a.has_adjusted_licence_fee
                   or a.has_additional_fee
                ]
                # only fees which are greater than zero.
                # activities_with_fees = [
                #    a for a in activities_adj
                #    if a.application_fee > 0 or a.licence_fee > 0
                # ]

                for activity in activities_adj:

                    # Check if refund is required and can be included.
                    clear_inv = LicenceFeeClearingInvoice(instance)

                    paid_purposes = [
                        p for p in activity.proposed_purposes.all()
                        if p.is_payable
                    ]

                    for p in paid_purposes:
                        oracle_code = p.purpose.oracle_account_code
                        fee = p.get_payable_application_fee()

                        if fee > 0:
                            price_excl = calculate_excl_gst(fee)
                            if ApplicationFeePolicy.GST_FREE:
                                price_excl = fee
                            product_lines.append(
                                {
                                    'ledger_description': '{} {}'.format(
                                        p.purpose.name,
                                        '(Application Fee)'
                                    ),
                                    'quantity': 1,
                                    'price_incl_tax': str(fee),
                                    'price_excl_tax': str(price_excl),
                                    'oracle_code': oracle_code
                                }
                            )

                        fee = p.get_payable_licence_fee()
                        if fee > 0:
                            price_excl = calculate_excl_gst(fee)
                            if ApplicationFeePolicy.GST_FREE:
                                price_excl = fee
                            product_lines.append(
                                {
                                    'ledger_description': '{} {}'.format(
                                        p.purpose.name,
                                        '(Licence Fee)'
                                    ),
                                    'quantity': 1,
                                    'price_incl_tax': str(fee),
                                    'price_excl_tax': str(price_excl),
                                    'oracle_code': oracle_code
                                }
                            )

                        fee = p.additional_fee
                        if fee > 0:
                            price_excl = calculate_excl_gst(fee)
                            if ApplicationFeePolicy.GST_FREE:
                                price_excl = fee
                            product_lines.append(
                                {
                                    'ledger_description': '{}'.format(
                                        p.additional_fee_text,
                                    ),
                                    'quantity': 1,
                                    'price_incl_tax': str(fee),
                                    'price_excl_tax': str(price_excl),
                                    'oracle_code': oracle_code
                                }
                            )

                        if clear_inv.is_refundable:
                            product_lines.append(
                                clear_inv.get_product_line_refund_for(p)
                            )

            # Check if refund is required from last invoice.
            # last_inv = LicenceFeeClearingInvoice(instance)
            # if last_inv.is_refundable:
            #     product_lines.append(last_inv.get_product_line_for_refund())

                # # refund any application fee adjustments.
                # if instance.application_fee < 0:

                #     price_excl = calculate_excl_gst(instance.application_fee)
                #     if ApplicationFeePolicy.GST_FREE:
                #         price_excl = instance.application_fee
                #     # _code = activity.licence_activity.oracle_account_code
                #     oracle_code = ''

                #     product_lines.append({
                #         'ledger_description': 'Adjusted fee refund',
                #         'quantity': 1,
                #         'price_incl_tax': str(instance.application_fee),
                #         'price_excl_tax': str(price_excl),
                #         'oracle_code': oracle_code
                #     })

            checkout_result = checkout(
                request, instance,
                lines=product_lines,
                invoice_text=application_submission,
                add_checkout_params={
                    'return_url': request.build_absolute_uri(
                        reverse('external-licence-fee-success-invoice'))
                },
            )
            return checkout_result
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

    @detail_route(methods=['POST', ])
    def accept_id_check(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            instance.accept_id_check(request)
            # serializer = InternalApplicationSerializer(
            #     instance, context={'request': request})
            # return Response(serializer.data)
            return Response(
                {'id_check_status': instance.id_check_status},
                status=status.HTTP_200_OK
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
    def reset_id_check(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            instance.reset_id_check(request)
            # serializer = InternalApplicationSerializer(
            #     instance, context={'request': request})
            # return Response(serializer.data)
            return Response(
                {'id_check_status': instance.id_check_status},
                status=status.HTTP_200_OK
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
    def request_id_check(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            instance.request_id_check(request)
            # serializer = InternalApplicationSerializer(
            #     instance, context={'request': request})
            # return Response(serializer.data)
            return Response(
                {'id_check_status': instance.id_check_status},
                status=status.HTTP_200_OK
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
    def get_activities(self, request, *args, **kwargs):
        try:
            instance = self.get_object()

            if is_internal(request):
                serializer = DTInternalApplicationSelectedActivitySerializer(
                    instance.activities, many=True)

            if is_customer(request):
                serializer = DTExternalApplicationSelectedActivitySerializer(
                    instance.activities, many=True)

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
    def accept_character_check(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            instance.accept_character_check(request)
            # serializer = InternalApplicationSerializer(
            #     instance, context={'request': request})
            # return Response(serializer.data)
            return Response(
                {'character_check_status': instance.character_check_status},
                status=status.HTTP_200_OK
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
    def reset_character_check(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            instance.reset_character_check(request)

            return Response(
                {'character_check_status': instance.character_check_status},
                status=status.HTTP_200_OK
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
    def accept_return_check(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            instance.accept_return_check(request)
            # serializer = InternalApplicationSerializer(
            #     instance, context={'request': request})
            # return Response(serializer.data)
            return Response(
                {'return_check_status': instance.return_check_status},
                status=status.HTTP_200_OK
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
    def reset_return_check(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            instance.reset_return_check(request)
            # serializer = InternalApplicationSerializer(
            #     instance, context={'request': request})
            # return Response(serializer.data)
            return Response(
                {'return_check_status': instance.return_check_status},
                status=status.HTTP_200_OK
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

    @detail_route(methods=['GET', ])
    def last_current_activity(self, request, *args, **kwargs):
        '''
        NOTE: retrieval of last current activity is only utilised in the
        Reissuing process. Filtered on this action.
        '''
        instance = self.get_object()
        user = request.user
        if user not in instance.licence_officers:
            raise serializers.ValidationError(
                'You are not authorised for this application.')

        if not instance:
            return Response({'activity': None})

        current = ApplicationSelectedActivity.ACTIVITY_STATUS_CURRENT
        last_activity = instance.get_current_activity_chain(
            activity_status=current,
            decision_action='reissue'
        ).first()

        if not last_activity:
            return Response({'activity': None})

        serializer = ApplicationSelectedActivitySerializer(
            last_activity, context={'request': request})
        return Response({'activity': serializer.data})

    @detail_route(methods=['POST', ])
    def assign_to_me(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            user = request.user
            if user not in instance.licence_officers:
                raise serializers.ValidationError(
                    'You are not in any relevant licence officer groups for this application.')
            instance.assign_officer(request, request.user)
            # serializer = InternalApplicationSerializer(
            #     instance, context={'request': request})
            # return Response(serializer.data)
            return Response(
                {'assigned_officer_id': user.id},
                status=status.HTTP_200_OK
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
    def assign_officer(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            user_id = request.data.get('officer_id', None)
            user = None
            if not user_id:
                raise serializers.ValidationError('An officer id is required')
            try:
                user = EmailUser.objects.get(id=user_id)
            except EmailUser.DoesNotExist:
                raise serializers.ValidationError(
                    'A user with the id passed in does not exist')
            if not request.user.has_perm('wildlifecompliance.licensing_officer'):
                raise serializers.ValidationError(
                    'You are not authorised to assign officers to applications')
            if user not in instance.licence_officers:
                raise serializers.ValidationError(
                    'User is not in any relevant licence officer groups for this application')
            instance.assign_officer(request, user)
            # serializer = InternalApplicationSerializer(
            #     instance, context={'request': request})
            # return Response(serializer.data)
            return Response(
                {'assigned_officer_id': user.id},
                status=status.HTTP_200_OK
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
    def unassign_officer(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            instance.unassign_officer(request)
            # serializer = InternalApplicationSerializer(
            #     instance, context={'request': request})
            # return Response(serializer.data)
            return Response(
                {'assigned_officer_id': None},
                status=status.HTTP_200_OK
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
    def make_me_activity_approver(self, request, *args, **kwargs):
        try:
            activity_id = request.data.get('activity_id', None)
            instance = self.get_object()
            me = request.user

            if me not in instance.licence_approvers:
                raise serializers.ValidationError('You are not in any relevant \
                    licence approver groups for this application.')

            instance.set_activity_approver(activity_id, me)
            # serializer = InternalApplicationSerializer(
            #     instance, context={'request': request})

            # return Response(serializer.data)

            return Response(
                {'assigned_approver_id': me.id},
                status=status.HTTP_200_OK
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
    def assign_activity_approver(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            activity_id = request.data.get('activity_id', None)
            approver_id = request.data.get('approver_id', None)
            approver = None

            if not approver_id:
                raise serializers.ValidationError('Could not Assign Approver.')

            try:
                approver = EmailUser.objects.get(id=approver_id)

            except EmailUser.DoesNotExist:
                raise serializers.ValidationError('A user with the id passed in\
                    does not exist.')

            if not request.user.has_perm('wildlifecompliance.issuing_officer'):
                raise serializers.ValidationError('You are not authorised to\
                    assign approvers for application activity.')

            if approver not in instance.licence_approvers:
                raise serializers.ValidationError('User is not in any relevant\
                    licence approver groups for application activity.')

            instance.set_activity_approver(activity_id, approver)
            # serializer = InternalApplicationSerializer(
            #     instance, context={'request': request})

            # return Response(serializer.data)

            return Response(
                {'assigned_approver_id': approver.id},
                status=status.HTTP_200_OK
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
    def unassign_activity_approver(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            activity_id = request.data.get('activity_id', None)
            instance.set_activity_approver(activity_id, None)
            # serializer = InternalApplicationSerializer(
            #     instance, context={'request': request})

            # return Response(serializer.data)

            return Response(
                {'assigned_approver_id': None},
                status=status.HTTP_200_OK
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
    def return_to_officer(self, request, *args, **kwargs):

        try:
            instance = self.get_object()
            activity_id = request.data.get('activity_id')
            if not activity_id:
                raise serializers.ValidationError(
                    'Activity ID is required!')

            instance.return_to_officer_conditions(request, activity_id)
            serializer = InternalApplicationSerializer(
                instance, context={'request': request})
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

    @detail_route(methods=['POST', ])
    def update_activity_status(self, request, *args, **kwargs):

        try:
            instance = self.get_object()
            activity_id = request.data.get('activity_id')
            status = request.data.get('status')
            if not status or not activity_id:
                raise serializers.ValidationError(
                    'Status and activity id is required')
            else:
                if not ApplicationSelectedActivity.is_valid_status(status):
                    raise serializers.ValidationError(
                        'The status provided is not allowed')
            instance.set_activity_processing_status(activity_id, status)
            serializer = InternalApplicationSerializer(
                instance, context={'request': request})
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

    @detail_route(methods=['POST', ])
    def complete_assessment(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            instance.complete_assessment(request)
            serializer = InternalApplicationSerializer(
                instance, context={'request': request})
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

    @detail_route(methods=['POST', ])
    def proposed_licence(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = ProposedLicenceSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            instance.proposed_licence(request, serializer.validated_data)
            # serializer = InternalApplicationSerializer(
            #     instance, context={'request': request})
            # return Response(serializer.data)

            return Response({'success': True})

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

    @detail_route(methods=['GET', ])
    def get_proposed_decisions(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            qs = instance.get_proposed_decisions(request)
            serializer = ApplicationProposedIssueSerializer(qs, many=True)
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

    @detail_route(methods=['post'])
    @renderer_classes((JSONRenderer,))
    def assessment_data(self, request, *args, **kwargs):
        logger.debug('assessment_data()')
        try:
            instance = self.get_object()
            assess = request.data.pop('__assess', False)
            with transaction.atomic():
                is_initial_assess = instance.get_property_cache_assess()
                if assess or is_initial_assess:

                    checkbox = CheckboxAndRadioButtonVisitor(
                        instance, request.data
                    )
                    # Set StandardCondition Fields.
                    for_condition_fields = StandardConditionFieldElement()
                    for_condition_fields.accept(checkbox)

                    # Set PromptInspection Fields.
                    for_inspection_fields = PromptInspectionFieldElement()
                    for_inspection_fields.accept(checkbox)

                    if is_initial_assess:
                        instance.set_property_cache_assess(False)
                        instance.save()

            logger.debug('assessment_data() - response success')
            return Response({'success': True})

        except MissingFieldsException as e:
            return Response({
                'missing': e.error_list},
                status=status.HTTP_400_BAD_REQUEST
            )
        except ValidationError as e:
            raise serializers.ValidationError(repr(e.error_dict))
        except Exception as e:
            print(traceback.print_exc())
        raise serializers.ValidationError(str(e))

    @detail_route(methods=['post'])
    @renderer_classes((JSONRenderer,))
    def final_decision_data(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            with transaction.atomic():
                checkbox = CheckboxAndRadioButtonVisitor(
                    instance, request.data
                )

                # Set species Fields for Checkbox and RadioButtons.
                # save on purpose approval.
                for_species_options_fields = SpeciesOptionsFieldElement()
                for_species_options_fields.accept(checkbox)

            return Response({'success': True})
        except MissingFieldsException as e:
            return Response({
                'missing': e.error_list},
                status=status.HTTP_400_BAD_REQUEST
            )
        except ValidationError as e:
            raise serializers.ValidationError(repr(e.error_dict))
        except Exception as e:
            print(traceback.print_exc())
        raise serializers.ValidationError(str(e))

    @detail_route(methods=['POST', ])
    def final_decision(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = IssueLicenceSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            instance.final_decision(request)
            # serializer = InternalApplicationSerializer(
            #     instance, context={'request': request})
            # return Response(serializer.data)

            return Response({'success': True})

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

    @detail_route(methods=['POST', ])
    def proposed_decline(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = ProposedDeclineSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            instance.proposed_decline(request, serializer.validated_data)
            serializer = InternalApplicationSerializer(
                instance, context={'request': request})
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

    @detail_route(methods=['post'])
    @renderer_classes((JSONRenderer,))
    def draft(self, request, *args, **kwargs):
        parser = SchemaParser(draft=True)
        try:
            instance = self.get_object()
            parser.save_application_user_data(instance, request, self)
            return redirect(reverse('external'))
        except MissingFieldsException as e:
            return Response({
                'missing': e.error_list},
                status=status.HTTP_400_BAD_REQUEST
            )
        except serializers.ValidationError:
            print(traceback.print_exc())
            raise
        except ValidationError as e:
            raise serializers.ValidationError(repr(e.error_dict))
        except Exception as e:
            print(traceback.print_exc())
        raise serializers.ValidationError(str(e))

    @detail_route(methods=['post'])
    @renderer_classes((JSONRenderer,))
    def officer_comments(self, request, *args, **kwargs):
        try:
            instance = self.get_object()

            with transaction.atomic():
                ApplicationService.process_form(
                    request,
                    instance,
                    request.data,
                    action=ApplicationFormDataRecord.ACTION_TYPE_ASSIGN_COMMENT
                )

            return Response({'success': True})
        except Exception as e:
            print(traceback.print_exc())
        raise serializers.ValidationError(str(e))

    @detail_route(methods=['post'])
    @renderer_classes((JSONRenderer,))
    def form_data(self, request, *args, **kwargs):
        logger.debug('form_data()')
        try:
            instance = self.get_object()
            with transaction.atomic():
                ApplicationService.process_form(
                    request,
                    instance,
                    request.data,
                    action=ApplicationFormDataRecord.ACTION_TYPE_ASSIGN_VALUE
                )

                instance.log_user_action(
                    ApplicationUserAction.ACTION_SAVE_APPLICATION.format(
                        instance.lodgement_number
                    ), request)

            logger.debug('form_data() - successful response')
            return Response({'success': True})

        except MissingFieldsException as e:
            return Response({
                'missing': e.error_list},
                status=status.HTTP_400_BAD_REQUEST
            )
        except ValidationError as e:
            raise serializers.ValidationError(repr(e.error_dict))
        except Exception as e:
            print(traceback.print_exc())
        raise serializers.ValidationError(str(e))

    @detail_route(methods=['get'])
    def select_filtered_species(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            category = instance.licence_category

            filter_str = request.query_params['term']
            tsc_service = TSCSpecieService(HerbieSpecieKMICall())
            data = tsc_service.search_filtered_taxon(filter_str, category)

            return Response(data)

        except serializers.ValidationError:
            print(traceback.print_exc())
            raise
        except ValidationError as e:
            raise serializers.ValidationError(repr(e.error_dict))
        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))

    @detail_route(methods=['post'])
    @renderer_classes((JSONRenderer,))
    def application_officer_save(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            parser = SchemaParser()
            parser.save_application_officer_data(instance, request, self)
            return redirect(reverse('external'))
        except serializers.ValidationError:
            print(traceback.print_exc())
            raise
        except ValidationError as e:
            raise serializers.ValidationError(repr(e.error_dict))
        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))

    @renderer_classes((JSONRenderer,))
    def create(self, request, *args, **kwargs):
        from wildlifecompliance.components.licences.models import (
            WildlifeLicence, LicencePurpose
        )

        try:
            org_applicant = request.data.get('organisation_id')
            proxy_applicant = request.data.get('proxy_id')
            licence_purposes = request.data.get('licence_purposes')
            application_type = request.data.get('application_type')
            customer_pay_method = request.data.get('customer_method_id')

            # Amendment to licence purpose requires the selected activity it
            # belongs to - allows for multiple purposes of same type.
            selected_activity = request.data.get('selected_activity', None)

            # establish the submit type from the payment method.
            CASH = ApplicationInvoice.OTHER_PAYMENT_METHOD_CASH
            NONE = ApplicationInvoice.OTHER_PAYMENT_METHOD_NONE

            if customer_pay_method == CASH:
                submit_type = Application.SUBMIT_TYPE_PAPER
            elif customer_pay_method == NONE:
                submit_type = Application.SUBMIT_TYPE_MIGRATE
            else:
                submit_type = Application.SUBMIT_TYPE_ONLINE

            data = {
                'submitter': request.user.id,
                'org_applicant': org_applicant,
                'proxy_applicant': proxy_applicant,
                'licence_purposes': licence_purposes,
                'application_type': application_type,
                'submit_type': submit_type,
            }

            if not licence_purposes:
                raise serializers.ValidationError(
                    'Please select at least one purpose')

            with transaction.atomic():

                licence_purposes_queryset = LicencePurpose.objects.filter(
                    id__in=licence_purposes
                )
                licence_category = licence_purposes_queryset.first().licence_category
                licence_activities = Application.get_active_licence_activities(
                    request, application_type)
                licence_activity_ids = Application.get_active_licence_activities(
                    request, application_type).values_list('licence_activity_id', flat=True)
                # active_applications are applications linked with licences that have CURRENT or SUSPENDED activities
                active_applications = Application.get_active_licence_applications(request, application_type) \
                    .filter(licence_purposes__licence_category_id=licence_category.id) \
                    .order_by('-id')
                active_current_applications = active_applications.exclude(
                    selected_activities__activity_status=ApplicationSelectedActivity.ACTIVITY_STATUS_SUSPENDED
                )
                # latest_active_licence = WildlifeLicence.objects.filter(
                #     licence_category_id=licence_category.id,
                #     current_application__in=active_applications.values_list('id', flat=True)
                # ).order_by('-id').first()

                # determine licence no from active application for category.
                latest_active_licence = WildlifeLicence.objects.filter(
                    licence_category_id=licence_category.id,
                    id__in=active_applications.values_list('licence_id', flat=True)
                ).order_by('-id').first()

                # Initial validation
                if application_type in [
                    Application.APPLICATION_TYPE_AMENDMENT,
                    Application.APPLICATION_TYPE_RENEWAL,
                    Application.APPLICATION_TYPE_REISSUE,
                ]:
                    # Check that at least one active application exists in this licence category for amendment/renewal
                    if not latest_active_licence:
                        raise serializers.ValidationError(
                            'Cannot create amendment application: active licence not found!')

                    # Ensure purpose ids are in a shared set with the latest current applications purposes
                    # to prevent front-end tampering. Remove any that aren't valid for renew/amendment/reissue.
                    active_current_purposes = active_current_applications.filter(
                        licence_purposes__licence_activity_id__in=licence_activity_ids
                    ).values_list(
                        'licence_purposes__id',
                        flat=True
                    )

                    previous_application = licence_activities.filter(
                        id=selected_activity
                    ).values_list(
                        'application_id',
                        flat=True
                    ).first()
                    data['previous_application'] = previous_application

                    cleaned_purpose_ids = set(active_current_purposes) & set(licence_purposes)
                    data['licence_purposes'] = cleaned_purpose_ids

                if latest_active_licence:
                    # Store currently active licence against application.
                    data['licence'] = latest_active_licence.id

                # Use serializer for external application creation - do not
                # expose unneeded fields.
                serializer = CreateExternalApplicationSerializer(data=data)
                serializer.is_valid(raise_exception=True)
                serializer.save()

                # Pre-fill the ApplicationFormDataRecord table with data from
                # latest current applications.
                # for selected purpose ids
                if application_type in [
                    Application.APPLICATION_TYPE_AMENDMENT,
                    Application.APPLICATION_TYPE_RENEWAL,
                ]:
                    target_application = serializer.instance
                    copied_purpose_ids = []
                    # FIXME: Copying the first licence purpose from list.
                    # duplicates can exist for multi. Correctly select the
                    # required activity and pass in for amend and renewal.
                    for activity in licence_activities:
                        activity_purpose_ids = [
                            p.purpose.id
                            for p in activity.proposed_purposes.all()
                            if p.is_issued
                        ]
                        copy_purpose_ids = list(
                           set(activity_purpose_ids) - set(copied_purpose_ids)
                        )
                        purposes_to_copy = set(
                            cleaned_purpose_ids) & set(copy_purpose_ids)

                        for purpose_id in purposes_to_copy:

                            activity.application.copy_application_purpose_to_target_application(
                                target_application, purpose_id)

                            activity.application.copy_conditions_to_target(
                                target_application,
                                purpose_id,
                            )
                            copied_purpose_ids.append(purpose_id)

                # Set previous_application to the latest active application if
                # exists
                if not serializer.instance.previous_application \
                        and latest_active_licence:
                    serializer.instance.previous_application_id =\
                        latest_active_licence.current_application.id
                    serializer.instance.save()

                # serializer.instance.update_dynamic_attributes()
                ApplicationService.update_dynamic_attributes(
                    serializer.instance)
                response = Response(serializer.data)

            return response

        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))

    def update(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = SaveApplicationSerializer(instance, data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            return Response(serializer.data)
        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))

    def destroy(self, request, *args, **kwargs):
        http_status = status.HTTP_200_OK
        instance = self.get_object()
        if instance.processing_status != Application.PROCESSING_STATUS_DRAFT:
            raise serializers.ValidationError(
                'You cannot discard a submitted application!')

        instance.activities.filter(
            processing_status=ApplicationSelectedActivity.PROCESSING_STATUS_DRAFT
        ).update(
            processing_status=ApplicationSelectedActivity.PROCESSING_STATUS_DISCARDED
        )

        return Response({'processing_status': ApplicationSelectedActivity.PROCESSING_STATUS_DISCARDED
                         }, status=http_status)

    @detail_route(methods=['DELETE', ])
    def discard_activity(self, request, *args, **kwargs):
        http_status = status.HTTP_200_OK
        activity_id = request.GET.get('activity_id')
        instance = self.get_object()

        try:
            activity = instance.activities.get(
                licence_activity_id=activity_id,
                processing_status=ApplicationSelectedActivity.PROCESSING_STATUS_DRAFT
            )
        except ApplicationSelectedActivity.DoesNotExist:
            raise serializers.ValidationError("This activity cannot be discarded at this time.")

        activity.processing_status = ApplicationSelectedActivity.PROCESSING_STATUS_DISCARDED
        activity.save()

        return Response({'processing_status': instance.processing_status}, status=http_status)

    @detail_route(methods=['GET', ])
    def assessment_details(self, request, *args, **kwargs):
        # queryset = self.get_queryset()
        instance = self.get_object()
        queryset = Assessment.objects.filter(application=instance.id)
        licence_activity = self.request.query_params.get(
            'licence_activity', None)
        if licence_activity is not None:
            queryset = queryset.filter(
                licence_activity=licence_activity)
        serializer = AssessmentSerializer(queryset, many=True)
        return Response(serializer.data)

    @list_route(methods=['POST', ])
    def set_application_species(self, request, *args, **kwargs):
        species_ids = request.data.get('field_data')
        if species_ids is not None:
            species_list = ApplicationService.get_licence_species(species_ids)
            return Response({'species': species_list })

        return Response({
            'species': None
        })

    @detail_route(permission_classes=[], methods=['GET'])
    def application_checkout_status(self, request, *args, **kwargs):
        # TODO: may need to re-build this function for Wildlife Licensing (code taken from Parkstay) if required
        try:
            # instance = self.get_object()
            response = {
                'status': 'rejected',
                'error': ''
            }
            # # Check the type of booking
            # if instance.booking_type != 3:
            #    response['error'] = 'This booking has already been paid for'
            #    return Response(response,status=status.HTTP_200_OK)
            # # Check if the time for the booking has elapsed
            # if instance.expiry_time <= timezone.now():
            #     response['error'] = 'This booking has expired'
            #     return Response(response,status=status.HTTP_200_OK)
            # if all is well
            response['status'] = 'approved'
            return Response(response, status=status.HTTP_200_OK)
        except serializers.ValidationError:
            print(traceback.print_exc())
            raise
        except ValidationError as e:
            raise serializers.ValidationError(repr(e.error_dict))
        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))


class ApplicationConditionViewSet(viewsets.ModelViewSet):
    queryset = ApplicationCondition.objects.all()
    serializer_class = ApplicationConditionSerializer

    def get_queryset(self):
        user = self.request.user
        if is_internal(self.request):
            return ApplicationCondition.objects.all()
        elif is_customer(self.request):
            user_orgs = [
                org.id for org in user.wildlifecompliance_organisations.all()]
            user_applications = [application.id for application in Application.objects.filter(
                Q(org_applicant_id__in=user_orgs) | Q(proxy_applicant=user) | Q(submitter=user))]
            return ApplicationCondition.objects.filter(
                Q(application_id__in=user_applications))
        return ApplicationCondition.objects.none()

    @detail_route(methods=['DELETE', ])
    def delete(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            instance.application.log_user_action(
                ApplicationUserAction.ACTION_DELETE_CONDITION.format(
                    instance.licence_purpose.short_name,
                    instance.condition[:256],
                ),
                request
            )
            instance.delete()
            serializer = self.get_serializer(instance)
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
    def update_condition(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data)
            serializer.is_valid(raise_exception=True)
            with transaction.atomic():
                instance = serializer.save()
                instance.application.log_user_action(
                    ApplicationUserAction.ACTION_UPDATE_CONDITION.format(
                        instance.licence_purpose.short_name,
                        instance.condition[:256],
                    ),
                    request
                )
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

    def create(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            with transaction.atomic():
                instance = serializer.save()
                instance.set_source(request.user)
                instance.submit()
                instance.application.log_user_action(
                    ApplicationUserAction.ACTION_CREATE_CONDITION.format(
                        instance.licence_purpose.short_name,
                        instance.condition[:256],
                    ),
                    request
                )
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
    def move_up(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            instance.up()
            instance.save()
            instance.application.log_user_action(
                ApplicationUserAction.ACTION_ORDER_CONDITION_UP.format(
                    instance.condition[:256]), request)
            serializer = self.get_serializer(instance)
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
    def move_down(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            instance.down()
            instance.save()
            instance.application.log_user_action(
                ApplicationUserAction.ACTION_ORDER_CONDITION_DOWN.format(
                    instance.condition[:256]), request)
            serializer = self.get_serializer(instance)
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

class ApplicationSelectedActivityViewSet(viewsets.ModelViewSet):
    queryset = ApplicationSelectedActivity.objects.all()
    serializer_class = ApplicationSelectedActivitySerializer

    def get_queryset(self):
        if is_internal(self.request):
            return ApplicationSelectedActivity.objects.all()
        elif is_customer(self.request):
            return ApplicationSelectedActivity.objects.none()
        return ApplicationSelectedActivity.objects.none()

    @detail_route(methods=['POST', ])
    def process_issuance_document(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            returned_data = process_generic_document(request, instance, document_type="issuance_documents")
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


class ApplicationStandardConditionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ApplicationStandardCondition.objects.all()
    serializer_class = ApplicationStandardConditionSerializer

    def get_queryset(self):
        if is_internal(self.request):
            return ApplicationStandardCondition.objects.all()
        elif is_customer(self.request):
            return ApplicationStandardCondition.objects.none()
        return ApplicationStandardCondition.objects.none()

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        search = request.GET.get('search')
        if search:
            queryset = queryset.filter(text__icontains=search)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class AssessmentPaginatedViewSet(viewsets.ModelViewSet):
    filter_backends = (ApplicationFilterBackend,)
    pagination_class = DatatablesPageNumberPagination
    renderer_classes = (ApplicationRenderer,)
    queryset = Assessment.objects.none()
    serializer_class = DTAssessmentSerializer
    page_size = 10

    def get_queryset(self):
        if is_internal(self.request):
            return Assessment.objects.all()
        elif is_customer(self.request):
            return Assessment.objects.none()
        return Assessment.objects.none()

    @list_route(methods=['GET', ])
    def datatable_list(self, request, *args, **kwargs):
        self.serializer_class = DTAssessmentSerializer

        # Get the assessor groups the current user is member of
        perm_user = PermissionUser(request.user)
        assessor_groups = perm_user.get_wildlifelicence_permission_group(
            'assessor', first=False)

        # For each assessor groups get the assessments
        queryset = self.get_queryset().none()
        for group in assessor_groups:
            queryset = queryset | Assessment.objects.filter(
                assessor_group=group) | Assessment.objects.filter(
                actioned_by=self.request.user)

        queryset = self.filter_queryset(queryset)
        self.paginator.page_size = queryset.count()
        result_page = self.paginator.paginate_queryset(queryset, request)
        serializer = DTAssessmentSerializer(
            result_page, context={'request': request}, many=True)
        return self.paginator.get_paginated_response(serializer.data)


class AssessmentViewSet(viewsets.ModelViewSet):
    queryset = Assessment.objects.all()
    serializer_class = AssessmentSerializer

    def get_queryset(self):
        if is_internal(self.request):
            return Assessment.objects.all()
        elif is_customer(self.request):
            return Assessment.objects.none()
        return Assessment.objects.none()

    @list_route(methods=['GET', ])
    def get_latest_for_application_activity(self, request, *args, **kwargs):
        application_id = request.query_params.get(
            'application_id', None)
        activity_id = request.query_params.get(
            'activity_id', None)
        latest_assessment = Assessment.objects.filter(
            application_id=application_id,
            licence_activity_id=activity_id
        ).exclude(
            status='recalled'
        ).latest('id')
        serializer = AssessmentSerializer(latest_assessment)
        return Response(serializer.data)

    @list_route(methods=['GET', ])
    def user_list(self, request, *args, **kwargs):
        # Get the assessor groups the current user is member of
        perm_user = PermissionUser(request.user)
        assessor_groups = perm_user.get_wildlifelicence_permission_group('assessor', first=False)

        # For each assessor groups get the assessments
        queryset = self.get_queryset().none()
        for group in assessor_groups:
            queryset = queryset | Assessment.objects.filter(
                assessor_group=group)

        serializer = DTAssessmentSerializer(queryset, many=True)
        return Response(serializer.data)

    @renderer_classes((JSONRenderer,))
    def create(self, request, *args, **kwargs):
        try:
            serializer = SaveAssessmentSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            instance = serializer.save()
            instance.generate_assessment(request)
            serializer = self.get_serializer(instance)
            return Response(serializer.data)
        except serializers.ValidationError:
            print(traceback.print_exc())
            raise
        except ValidationError as e:
            if hasattr(e, 'error_dict'):
                raise serializers.ValidationError(repr(e.error_dict))
            else:
                logger.error('AssessmentViewSet.create(): {0}'.format(e))
                # raise serializers.ValidationError(repr(e[0].encode('utf-8')))
                raise serializers.ValidationError(repr(e[0]))
        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))

    @detail_route(methods=['POST', ])
    def remind_assessment(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            instance.remind_assessment(request)
            serializer = self.get_serializer(instance)
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
    def recall_assessment(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            instance.recall_assessment(request)
            serializer = self.get_serializer(instance)
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
    def resend_assessment(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            instance.resend_assessment(request)
            serializer = self.get_serializer(instance)
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

    @detail_route(methods=['PUT', ])
    def update_assessment(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = SimpleSaveAssessmentSerializer(instance, data=self.request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            instance = serializer.save()
            return Response(serializer.data)
        except serializers.ValidationError:
            print(traceback.print_exc())
            raise
        except ValidationError as e:
            if hasattr(e, 'error_dict'):
                raise serializers.ValidationError(repr(e.error_dict))
            else:
                logger.error(
                    'AssessmentViewSet.update_assessment(): {0}'.format(e)
                )
                # raise serializers.ValidationError(repr(e[0].encode('utf-8')))
                raise serializers.ValidationError(repr(e[0]))
        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))


class AssessorGroupViewSet(viewsets.ModelViewSet):
    queryset = ActivityPermissionGroup.objects.none()
    serializer_class = ActivityPermissionGroupSerializer
    renderer_classes = [JSONRenderer, ]

    def get_queryset(self, application=None):
        if is_internal(self.request):
            if application is not None:
                return application.get_permission_groups('assessor')
            return ActivityPermissionGroup.objects.filter(
                permissions__codename='assessor'
            )
        elif is_customer(self.request):
            return ActivityPermissionGroup.objects.none()
        return ActivityPermissionGroup.objects.none()

    @list_route(methods=['POST', ])
    def user_list(self, request, *args, **kwargs):
        app_id = request.data.get('application_id')
        application = Application.objects.get(id=app_id)
        queryset = self.get_queryset(application)
        serializer = self.get_serializer(queryset, many=True)

        return Response(serializer.data)


class AmendmentRequestViewSet(viewsets.ModelViewSet):
    queryset = AmendmentRequest.objects.all()
    serializer_class = AmendmentRequestSerializer

    def get_queryset(self):
        user = self.request.user
        if is_internal(self.request):
            return AmendmentRequest.objects.all()
        elif is_customer(self.request):
            user_orgs = [
                org.id for org in user.wildlifecompliance_organisations.all()]
            user_applications = [application.id for application in Application.objects.filter(
                Q(org_applicant_id__in=user_orgs) | Q(proxy_applicant=user) | Q(submitter=user))]
            return AmendmentRequest.objects.filter(
                Q(application_id__in=user_applications))
        return AmendmentRequest.objects.none()

    def create(self, request, *args, **kwargs):
        try:
            amend_data = self.request.data
            reason = amend_data.pop('reason')
            application_id = amend_data.pop('application')
            text = amend_data.pop('text')
            activity_list = amend_data.pop('activity_list')
            if not activity_list:
                raise serializers.ValidationError('Please select at least one activity to amend!')

            data = {}
            application = Application.objects.get(id=application_id)
            for activity_id in activity_list:
                data = {
                    'application': application_id,
                    'reason': reason,
                    'text': text,
                    'licence_activity': activity_id
                }

                selected_activity = application.get_selected_activity(activity_id)
                if selected_activity.processing_status == ApplicationSelectedActivity.PROCESSING_STATUS_DISCARDED:
                    raise serializers.ValidationError('Selected activity has been discarded by the customer!')

                serializer = self.get_serializer(data=data)
                serializer.is_valid(raise_exception=True)
                instance = serializer.save()
                instance.reason = reason
                instance.generate_amendment(request)

                # Set all proposed purposes back to selected.
                STATUS = \
                  ApplicationSelectedActivityPurpose.PROCESSING_STATUS_SELECTED
                p_ids = [ p.purpose.id \
                    for p in selected_activity.proposed_purposes.all() ]
                selected_activity.set_proposed_purposes_process_status_for(
                    p_ids, STATUS)

            # send email
            send_application_amendment_notification(
                data, application, request)
            serializer = self.get_serializer(instance)
            return Response(serializer.data)
        except serializers.ValidationError:
            print(traceback.print_exc())
            raise
        except ValidationError as e:
            if hasattr(e, 'error_dict'):
                raise serializers.ValidationError(repr(e.error_dict))
            else:
                logger.error(
                    'AmendmentRequestViewSet.create(): {0}'.format(e)
                )
                # raise serializers.ValidationError(repr(e[0].encode('utf-8')))
                raise serializers.ValidationError(repr(e[0]))
        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))


class AmendmentRequestReasonChoicesView(views.APIView):

    renderer_classes = [JSONRenderer, ]

    def get(self, request, format=None):
        choices_list = []
        choices = AmendmentRequest.REASON_CHOICES
        if choices:
            for c in choices:
                choices_list.append({'key': c[0], 'value': c[1]})

        return Response(choices_list)
