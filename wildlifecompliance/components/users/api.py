import re
import traceback
from django.db.models import Q
from django.db import transaction
from django.http import HttpResponse
from django.core.exceptions import ValidationError
from rest_framework import viewsets, serializers, views, status
#from rest_framework.decorators import detail_route, list_route
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
from ledger.accounts.models import EmailUser, Address, Profile, EmailIdentity, EmailUserAction
from django.contrib.auth.models import Permission, ContentType
from datetime import datetime
from django_countries import countries
from wildlifecompliance.components.applications.models import Application
from wildlifecompliance.components.applications.email import send_id_updated_notification
from wildlifecompliance.components.call_email.serializers import SaveEmailUserSerializer, SaveUserAddressSerializer
from wildlifecompliance.components.organisations.models import (
    OrganisationRequest, Organisation
)
from wildlifecompliance.components.main.models import Region, District
from wildlifecompliance.components.users.models import (
        #CompliancePermissionGroup, 
        ComplianceManagementUserPreferences,
        )
from wildlifecompliance.helpers import (
        is_customer, is_internal, is_compliance_management_callemail_readonly_user,
        is_compliance_management_volunteer, is_compliance_management_readonly_user, 
        is_compliance_management_callemail_readonly_user, prefer_compliance_management,
        )
from wildlifecompliance.components.users.serializers import (
    UserSerializer,
    DTUserSerializer,
    UserProfileSerializer,
    UserAddressSerializer,
    PersonalSerializer,
    ContactSerializer,
    EmailIdentitySerializer,
    EmailUserActionSerializer,
    MyUserDetailsSerializer,
    #CompliancePermissionGroupSerializer,
    ComplianceUserDetailsSerializer,
    #CompliancePermissionGroupDetailedSerializer,
    ComplianceUserDetailsOptimisedSerializer,
    #CompliancePermissionGroupMembersSerializer,
    UpdateComplianceManagementUserPreferencesSerializer,
    ComplianceManagementSaveUserSerializer,
    ComplianceManagementUserSerializer,
    ComplianceManagementSaveUserAddressSerializer,
    FirstTimeUserSerializer,
)
from wildlifecompliance.components.organisations.serializers import (
    OrganisationRequestDTSerializer,
)

from rest_framework_datatables.pagination import DatatablesPageNumberPagination
from rest_framework_datatables.filters import DatatablesFilterBackend
from rest_framework_datatables.renderers import DatatablesRenderer
from django.urls import reverse
from django.shortcuts import render, redirect, get_object_or_404
from rest_framework.decorators import (
    detail_route,
    list_route,
    renderer_classes,
    parser_classes,
    api_view
)
from django.core.cache import cache
from wildlifecompliance.components.main.process_document import process_generic_document
#from wildlifecompliance.components.main.utils import retrieve_department_users


def generate_dummy_email(first_name, last_name):
    e = EmailUser(first_name=first_name, last_name=last_name)
    email_address = e.get_dummy_email().strip().strip('.').lower()
    email_address = re.sub(r'\.+', '.', email_address)
    email_address = re.sub(r'\s+', '_', email_address)
    return email_address


class IsComplianceManagementCallEmailReadonlyUser(views.APIView):
    renderer_classes = [JSONRenderer,]
    def get(self, request, format=None):
        user = False
        if is_compliance_management_callemail_readonly_user(request):
            user = True
        return Response({"compliance_management_callemail_readonly_user": user})


class GetCountries(views.APIView):
    renderer_classes = [JSONRenderer,]
    def get(self, request, format=None):
        country_list = []
        for country in list(countries):
            country_list.append({"name": country.name, "code": country.code})
        return Response(country_list)


#class DepartmentUserList(views.APIView):
#    renderer_classes = [JSONRenderer,]
#    def get(self, request, format=None):
#        data = cache.get('department_users')
#        if not data:
#            retrieve_department_users()
#            data = cache.get('department_users')
#        return Response(data)
#
#        #serializer  = UserSerializer(request.user)


class GetMyUserDetails(views.APIView):
    renderer_classes = [JSONRenderer, ]

    def get(self, request, format=None):
        serializer = MyUserDetailsSerializer(request.user, context={'request': request})
        return Response(serializer.data)


class GetComplianceUserDetails(views.APIView):
    renderer_classes = [JSONRenderer, ]

    def get(self, request, format=None):
        serializer = ComplianceUserDetailsSerializer(request.user, context={'request': request})
        returned_data = serializer.data
        if returned_data.get('id'):
            user_id = returned_data.get('id')
            user = EmailUser.objects.get(id=user_id)
        returned_data.update({'is_internal': is_internal(request)})
        returned_data.update({'is_volunteer': is_compliance_management_volunteer(request)})
        returned_data.update({'is_readonly_user': is_compliance_management_readonly_user(request)})
        returned_data.update({'is_callemail_readonly_user': is_compliance_management_callemail_readonly_user(request)})
        return Response(returned_data)


class GetUser(views.APIView):
    renderer_classes = [JSONRenderer, ]

    def get(self, request, format=None):
        serializer = PersonalSerializer(request.user)
        return Response(serializer.data)


class IsNewUser(views.APIView):
    def get(self, request, format=None):
        is_new = 'False'
        try:
            is_new = request.session['is_new']
        except BaseException:
            pass
        return HttpResponse(is_new)


class UserProfileCompleted(views.APIView):
    def get(self, request, format=None):
        request.session['is_new'] = False
        request.session['new_to_wildlifecompliance'] = False
        return HttpResponse('OK')


class ProfileViewSet(viewsets.ModelViewSet):
    queryset = Profile.objects.all()
    serializer_class = UserProfileSerializer

    def get_queryset(self):
        user = self.request.user
        if is_internal(self.request):
            return Profile.objects.all()
        elif is_customer(self.request):
            return Profile.objects.filter(user=user)
        return Profile.objects.none()

    @detail_route(methods=['POST', ])
    def update_profile(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = UserProfileSerializer(instance, data=request.data)
            serializer.is_valid(raise_exception=True)
            instance = serializer.save()
            serializer = UserSerializer(instance)
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


class MyProfilesViewSet(viewsets.ModelViewSet):
    queryset = Profile.objects.all()
    serializer_class = UserProfileSerializer

    def get_queryset(self):
        queryset = self.queryset
        query_set = queryset.filter(user=self.request.user)
        return query_set


class UserFilterBackend(DatatablesFilterBackend):

    def filter_queryset(self, request, queryset, view):
        """
        Custom filters
        """
        character_flagged = request.GET.get('character_flagged')
        dob = request.GET.get('dob')

        if queryset.model is EmailUser:
            # apply user selected filters
            character_flagged = character_flagged if character_flagged else 'all'
            if character_flagged.lower() != 'all':
                queryset = queryset.filter(character_flagged=character_flagged)
            if dob:
                queryset = queryset.filter(dob=datetime.strptime(dob, '%Y-%m-%d').date())

        queryset = super(UserFilterBackend, self).filter_queryset(request, queryset, view).distinct()
        total_count = queryset.count()
        setattr(view, '_datatables_total_count', total_count)
        return queryset


class UserRenderer(DatatablesRenderer):
    def render(self, data, accepted_media_type=None, renderer_context=None):
        if 'view' in renderer_context and hasattr(renderer_context['view'], '_datatables_total_count'):
            data['recordsTotal'] = renderer_context['view']._datatables_total_count
        return super(UserRenderer, self).render(data, accepted_media_type, renderer_context)


class UserPaginatedViewSet(viewsets.ModelViewSet):
    filter_backends = (UserFilterBackend,)
    pagination_class = DatatablesPageNumberPagination
    renderer_classes = (UserRenderer,)
    queryset = EmailUser.objects.none()
    serializer_class = DTUserSerializer
    page_size = 10

    def get_queryset(self):
        if is_internal(self.request):
            return EmailUser.objects.all()
        return EmailUser.objects.none()

    @list_route(methods=['GET', ])
    def datatable_list(self, request, *args, **kwargs):
        self.serializer_class = DTUserSerializer
        queryset = self.get_queryset()
        queryset = self.filter_queryset(queryset)
        self.paginator.page_size = queryset.count()
        result_page = self.paginator.paginate_queryset(queryset, request)
        serializer = DTUserSerializer(result_page, context={'request': request}, many=True)
        return self.paginator.get_paginated_response(serializer.data)


class UserViewSet(viewsets.ModelViewSet):
    queryset = EmailUser.objects.all()
    serializer_class = UserSerializer

    def get_queryset(self):
        """
        Optionally restrict the query if the following parameters are in the URL:
                - first_name
                - last_name
                - dob
                - email
        """
        user = self.request.user
        if is_internal(self.request):
            queryset = EmailUser.objects.all()
        elif is_customer(self.request):
            queryset = EmailUser.objects.filter(id=user.id)
        else:
            queryset = EmailUser.objects.none()
        first_name = self.request.query_params.get('first_name', None)
        last_name = self.request.query_params.get('last_name', None)
        dob = self.request.query_params.get('dob', None)
        email = self.request.query_params.get('email', None)
        if first_name is not None:
            queryset = queryset.filter(first_name__iexact=first_name)
        if last_name is not None:
            queryset = queryset.filter(last_name__iexact=last_name)
        if email is not None:
            queryset = queryset.filter(email__iexact=email)
        if dob is not None and dob is not u'':
            queryset = queryset.filter(dob=dob)
        return queryset

    @detail_route(methods=['GET'])
    @renderer_classes((JSONRenderer,))
    def get_intelligence_text(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            intelligence_text = ""
            preference_qs = ComplianceManagementUserPreferences.objects.filter(email_user=instance)
            if preference_qs:
                intelligence_text = preference_qs[0].intelligence_information_text
            return Response({"intelligence_text": intelligence_text})

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
    def save_intelligence_text(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            intelligence_text = request.data.get('intelligence_text')
            preference, created = ComplianceManagementUserPreferences.objects.get_or_create(email_user=instance)
            preference.intelligence_information_text = intelligence_text
            preference.save()
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
    def process_intelligence_document(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            # process docs
            returned_data = process_generic_document(request, instance, 'intelligence_document')
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


    @detail_route(methods=['GET', ])
    def action_log(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            qs = instance.action_logs.all()
            serializer = EmailUserActionSerializer(qs, many=True)
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
    def profiles(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = UserProfileSerializer(
                instance.profiles.all(), many=True)
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
    def update_personal(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = PersonalSerializer(instance, data=request.data)
            serializer.is_valid(raise_exception=True)
            with transaction.atomic():
                instance = serializer.save()
                instance.log_user_action(
                    EmailUserAction.ACTION_PERSONAL_DETAILS_UPDATE.format(
                        '{} {} ({})'.format(
                            instance.first_name,
                            instance.last_name,
                            instance.email)),
                    request)
            serializer = UserSerializer(instance)
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
    def update_contact(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
                instance = self.get_object()
                serializer = ContactSerializer(instance, data=request.data)
                serializer.is_valid(raise_exception=True)
                instance = serializer.save()
                instance.log_user_action(
                    EmailUserAction.ACTION_CONTACT_DETAILS_UPDATE.format(
                        '{} {} ({})'.format(
                            instance.first_name,
                            instance.last_name,
                            instance.email)),
                    request)

            serializer = FirstTimeUserSerializer(
                instance, context={'request': request}
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

    @detail_route(methods=['POST', ])
    def update_address(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = UserAddressSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            address, created = Address.objects.get_or_create(
                # line1=serializer.validated_data['line1'],
                locality=serializer.validated_data['locality'],
                state=serializer.validated_data['state'],
                country=serializer.validated_data['country'],
                postcode=serializer.validated_data['postcode'],
                user=instance
            )
            address.line1 = serializer.validated_data['line1']
            instance.residential_address = address
            with transaction.atomic():
                address.save()
                instance.save()
                instance.log_user_action(
                    EmailUserAction.ACTION_POSTAL_ADDRESS_UPDATE.format(
                        '{} {} ({})'.format(
                            instance.first_name,
                            instance.last_name,
                            instance.email)),
                    request)
            serializer = FirstTimeUserSerializer(
                instance, context={'request': request}
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

    @detail_route(methods=['POST', ])
    def upload_id(self, request, *args, **kwargs):
        from wildlifecompliance.management.securebase_manager import (
            SecureBaseUtils
        )
        try:
            instance = self.get_object()
            SecureBaseUtils.timestamp_id_request(request)
            instance.upload_identification(request)
            with transaction.atomic():
                instance.save()
                instance.log_user_action(
                    EmailUserAction.ACTION_ID_UPDATE.format(
                        '{} {} ({})'.format(
                            instance.first_name,
                            instance.last_name,
                            instance.email)),
                    request)
                # For any of the submitter's applications that have requested ID update,
                # email the assigned officer
                applications = instance.wildlifecompliance_applications.filter(
                    submitter=instance,
                    id_check_status=Application.ID_CHECK_STATUS_AWAITING_UPDATE,
                    org_applicant=None,
                    proxy_applicant=None
                ).exclude(customer_status__in=(
                    Application.CUSTOMER_STATUS_ACCEPTED,
                    Application.CUSTOMER_STATUS_DECLINED)
                ).order_by('id')

                if applications:

                    officers = applications[0].licence_officers
                    if applications[0].is_assigned:
                        officers = [applications[0].assigned_officer]

                    send_id_updated_notification(
                        instance, applications, officers, request
                    )

                # assigned_officers = [application.assigned_officer.email
                #                      for application
                #                      in applications
                #                      if application.assigned_officer]
                # remove duplicate email addresses from assigned_officers list
                # assigned_officers = list(dict.fromkeys(assigned_officers))
                # if len(assigned_officers) > 0:
                #     send_id_updated_notification(instance, applications, assigned_officers, request)
            serializer = UserSerializer(instance, partial=True)
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
    def pending_org_requests(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = OrganisationRequestDTSerializer(
                instance.organisationrequest_set.filter(
                    status=OrganisationRequest.ORG_REQUEST_STATUS_WITH_ASSESSOR),
                many=True,
                context={'request': request})
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

    @list_route(methods=['POST', ])
    def create_new_person(self, request, *args, **kwargs):
        print("create_new_person")
        with transaction.atomic():
            try:
                email_user_id_requested = request.data.get('id', {})
                email_address = request.data.get('email', '')
                if not email_address:
                    first_name = request.data.get('first_name', '')
                    last_name = request.data.get('last_name', '')
                    email_address = generate_dummy_email(first_name, last_name)

                if email_user_id_requested:
                    email_user_instance = EmailUser.objects.get(id=email_user_id_requested)
                    email_user_instance.email = email_address
                else:
                    email_user_instance = EmailUser.objects.create_user(email_address, '')
                    request.data.update({'email': email_address})

                email_user_serializer = SaveEmailUserSerializer(
                    email_user_instance,
                    data=request.data,
                    partial=True)

                if email_user_serializer.is_valid(raise_exception=True):
                    email_user_serializer.save()

                    # Residential address
                    # UPDATE user_id of residential address in order to save the residential address
                    request.data['residential_address'].update({'user_id': email_user_serializer.data['id']})
                    residential_address_id_requested = request.data.get('residential_address', {}).get('id', {})
                    if residential_address_id_requested:
                        residential_address_instance = Address.objects.get(id=residential_address_id_requested)
                        address_serializer = SaveUserAddressSerializer(
                            instance=residential_address_instance,
                            data=request.data['residential_address'],
                            partial=True)
                    else:
                        address_serializer = SaveUserAddressSerializer(
                            data=request.data['residential_address'],
                            partial=True)
                    if address_serializer.is_valid(raise_exception=True):
                        address_serializer.save()

                    # Update relation between email_user and residential_address
                    request.data.update({'residential_address_id': address_serializer.data['id']})
                    email_user = EmailUser.objects.get(id=email_user_serializer.instance.id)
                    email_user_serializer = SaveEmailUserSerializer(email_user, request.data)
                    if email_user_serializer.is_valid():
                        email_user_serializer.save()

            except serializers.ValidationError:
                print(traceback.print_exc())
                raise
            except ValidationError as e:
                print(traceback.print_exc())
                raise serializers.ValidationError(repr(e.error_dict))
            except Exception as e:
                print(traceback.print_exc())
                raise serializers.ValidationError(str(e))

        email_user = EmailUser.objects.get(id=email_user_serializer.instance.id)
        email_user_serializer = UserSerializer(email_user,)
        return Response(
            email_user_serializer.data,
            status=status.HTTP_201_CREATED,
            headers=self.get_success_headers(email_user_serializer.data)
        )

    @detail_route(methods=['POST', ])
    def update_system_preference(self, request, *args, **kwargs):
        with transaction.atomic():
            try:
                prefer_compliance_management = request.data.get('prefer_compliance_management', False)
                user_instance = self.get_object()
                system_preference_instance = ComplianceManagementUserPreferences.objects.get(email_user_id=user_instance.id)
                serializer = UpdateComplianceManagementUserPreferencesSerializer(
                        system_preference_instance,
                        data={
                            'email_user_id': user_instance.id, 
                            'prefer_compliance_management': prefer_compliance_management
                            }
                        )
                serializer.is_valid(raise_exception=True)
                serializer.save()
                return redirect('/')
            except serializers.ValidationError:
                print(traceback.print_exc())
                raise
            except ValidationError as e:
                print(traceback.print_exc())
                raise serializers.ValidationError(repr(e.error_dict))
            except Exception as e:
                print(traceback.print_exc())
                raise serializers.ValidationError(str(e))

class ComplianceManagementUserViewSet(viewsets.ModelViewSet):
    queryset = EmailUser.objects.all()
    serializer_class = UserSerializer
    renderer_classes = [JSONRenderer, ]

    def get_queryset(self):
        """
        Optionally restrict the query if the following parameters are in the URL:
                - first_name
                - last_name
                - dob
                - email
        """
        user = self.request.user
        if is_internal(self.request):
            queryset = EmailUser.objects.all()
        elif is_customer(self.request):
            queryset = EmailUser.objects.filter(id=user.id)
        else:
            queryset = EmailUser.objects.none()
        first_name = self.request.query_params.get('first_name', None)
        last_name = self.request.query_params.get('last_name', None)
        dob = self.request.query_params.get('dob', None)
        email = self.request.query_params.get('email', None)
        if first_name is not None:
            queryset = queryset.filter(first_name__iexact=first_name)
        if last_name is not None:
            queryset = queryset.filter(last_name__iexact=last_name)
        if email is not None:
            queryset = queryset.filter(email__iexact=email)
        if dob is not None and dob is not u'':
            queryset = queryset.filter(dob=dob)
        return queryset

    def create(self, request, *args, **kwargs):
        print("cm user create")
        print(request.data)
        with transaction.atomic():
            try:
                request_data = request.data
                
                email_address = request.data.get('email', '')
                if not email_address:
                    first_name = request.data.get('first_name', '')
                    last_name = request.data.get('last_name', '')
                    email_address = generate_dummy_email(first_name, last_name)
                    request_data.update({'email': email_address})
                
                email_user_instance = EmailUser.objects.create_user(email_address, '')
                res = self.update_person(request, instance=email_user_instance)
                return res
                #print("user_serializer_data")
                #print(type(user_serializer_data))
                #print(user_serializer_data)
               # return Response(
               #     user_serializer_data,
               #     status=status.HTTP_201_CREATED,
               #     #headers=self.get_success_headers(user_serializer.data)
               # )

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
    #@renderer_classes((JSONRenderer,))
    def update_person(self, request, instance=None, *args, **kwargs):
        print("cm user update")
        print(request.data)
        with transaction.atomic():
            try:
                if not instance:
                    instance = self.get_object()
                request_data = request.data
                
                email_address = request.data.get('email', '')
                if not email_address:
                    first_name = request.data.get('first_name', '')
                    last_name = request.data.get('last_name', '')
                    email_address = generate_dummy_email(first_name, last_name)
                    request_data.update({'email': email_address})
                
                residential_address_data = request_data.get('residential_address')
                # residential address
                if instance.residential_address:
                    print("update existing address")
                    #residential_address_instance = Address.objects.get(
                     #       id=instance.residential_address.id)
                    address_serializer = ComplianceManagementSaveUserAddressSerializer(
                            instance.residential_address, 
                            data=residential_address_data)
                    address_serializer.is_valid(raise_exception=True)
                    if address_serializer.is_valid:
                        saved_address = address_serializer.save()
                        request_data.update({'residential_address_id': saved_address.id})

                elif residential_address_data:
                    print("create address")
                    print(residential_address_data)
                    residential_address_data.update({'user_id': instance.id})
                    address_serializer = ComplianceManagementSaveUserAddressSerializer(
                            data=residential_address_data)
                    address_serializer.is_valid(raise_exception=True)
                    if address_serializer.is_valid:
                        saved_address = address_serializer.save()
                        print("saved_address")
                        print(saved_address)
                        request_data.update({'residential_address_id': saved_address.id})

                # now save EmailUser with residential_address_id, if it exists
                print("request_data")
                print(request_data)
                user_serializer = ComplianceManagementSaveUserSerializer(
                        instance=instance, 
                        data=request_data)
                user_serializer.is_valid(raise_exception=True)
                if user_serializer.is_valid:
                    saved_email_user = user_serializer.save()
                    email_user_refresh = EmailUser.objects.get(id=saved_email_user.id)
                    #return_serializer = UserSerializer(instance=instance)
                    print("email_user_refresh.residential_address")
                    print(email_user_refresh.residential_address)
                    return_serializer = ComplianceManagementUserSerializer(instance=email_user_refresh)
                    
                    return Response(
                        return_serializer.data,
                        status=status.HTTP_201_CREATED,
                        headers=self.get_success_headers(user_serializer.data)
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


class EmailIdentityViewSet(viewsets.ModelViewSet):
    queryset = EmailIdentity.objects.all()
    serializer_class = EmailIdentitySerializer

    def get_queryset(self):
        """
        Optionally restrict the query if the following parameters are in the URL:
                - email
        """
        user = self.request.user
        if is_internal(self.request):
            queryset = EmailIdentity.objects.all()
        elif is_customer(self.request):
            queryset = user.emailidentity_set.all()
        else:
            queryset = EmailIdentity.objects.none()
        email = self.request.query_params.get('email', None)
        exclude_user = self.request.query_params.get('exclude_user', None)
        if email is not None:
            queryset = queryset.filter(email__iexact=email)
        if exclude_user is not None:
            queryset = queryset.exclude(user=exclude_user)
        return queryset

#class CompliancePermissionGroupViewSet(viewsets.ModelViewSet):
#    queryset = CompliancePermissionGroup.objects.none()
#    serializer_class = CompliancePermissionGroupSerializer
#    renderer_classes = [JSONRenderer, ]
#
#    def get_queryset(self):
#        if is_internal(self.request):
#            return CompliancePermissionGroup.objects.all()
#        elif is_customer(self.request):
#            return CompliancePermissionGroup.objects.none()
#        return CompliancePermissionGroup.objects.none()
#
#    @list_route(methods=['GET', ])
#    def get_officers(self, request, *args, **kwargs):
#        try:
#            officers = EmailUser.objects.filter(groups__in=CompliancePermissionGroup.objects.filter(permissions__in=Permission.objects.filter(codename='officer')))
#            serializer = ComplianceUserDetailsOptimisedSerializer(officers, many=True)
#            return Response(serializer.data)
#        except serializers.ValidationError:
#            print(traceback.print_exc())
#            raise
#        except ValidationError as e:
#            print(traceback.print_exc())
#            raise serializers.ValidationError(repr(e.error_dict))
#        except Exception as e:
#            print(traceback.print_exc())
#            raise serializers.ValidationError(str(e))
#
#    @list_route(methods=['POST'])
#    def get_users(self, request, *args, **kwargs):
#        try:
#            users = (EmailUser.objects.filter(id__in=request.data.get('user_list')))
#            serializer = ComplianceUserDetailsOptimisedSerializer(users, many=True)
#            return Response(serializer.data)
#        except serializers.ValidationError:
#            print(traceback.print_exc())
#            raise
#        except ValidationError as e:
#            print(traceback.print_exc())
#            raise serializers.ValidationError(repr(e.error_dict))
#        except Exception as e:
#            print(traceback.print_exc())
#            raise serializers.ValidationError(str(e))
#
#    @list_route(methods=['GET', ])
#    def get_detailed_list(self, request, *args, **kwargs):
#        try:
#            serializer = CompliancePermissionGroupDetailedSerializer(
#                CompliancePermissionGroup.objects.all(), 
#                many=True
#                )
#            return Response(serializer.data)
#        except serializers.ValidationError:
#            print(traceback.print_exc())
#            raise
#        except ValidationError as e:
#            print(traceback.print_exc())
#            raise serializers.ValidationError(repr(e.error_dict))
#        except Exception as e:
#            print(traceback.print_exc())
#            raise serializers.ValidationError(str(e))
#
#    @list_route(methods=['POST', ])
#    def get_compliance_group_by_region_district(self, request, *args, **kwargs):
#        try:
#            instance = self.get_object()
#            group_permission = request.data.get('group_permission')
#            compliance_content_type = ContentType.objects.get(model="compliancepermissiongroup")
#            permission = Permission.objects.filter(codename=group_permission).filter(content_type_id=compliance_content_type.id).first()
#            group = CompliancePermissionGroup.objects.filter(region_district=instance).filter(permissions=permission).first()
#            print(group)
#
#            allocated_group = [{
#                'email': '',
#                'first_name': '',
#                'full_name': '',
#                'id': None,
#                'last_name': '',
#                'title': '',
#                }]
#            #serializer = ComplianceUserDetailsOptimisedSerializer(group.members, many=True)
#            serializer = CompliancePermissionGroupMembersSerializer(instance=group)
#            print(serializer.data)
#            for member in serializer.data['members']:
#                allocated_group.append(member)
#
#            return Response(data={'allocated_group': allocated_group, 'group_id': group.id})
#        except serializers.ValidationError:
#            print(traceback.print_exc())
#            raise
#        except ValidationError as e:
#            print(traceback.print_exc())
#            raise serializers.ValidationError(repr(e.error_dict))
#        except Exception as e:
#            print(traceback.print_exc())
#            raise serializers.ValidationError(str(e))

#class RegionDistrictViewSet(viewsets.ModelViewSet):
#    queryset = RegionDistrict.objects.all()
#    serializer_class = RegionDistrictSerializer
#    renderer_classes = [JSONRenderer, ]
#
#    def get_queryset(self):
#        # import ipdb; ipdb.set_trace()
#        user = self.request.user
#        if is_internal(self.request):
#            return RegionDistrict.objects.all()
#        elif is_customer(self.request):
#            return RegionDistrict.objects.none()
#        return RegionDistrict.objects.none()
#    
#    @list_route(methods=['GET', ])
#    def get_regions(self, request, *args, **kwargs):
#        try:
#            serializer = RegionDistrictSerializer(
#                RegionDistrict.objects.filter(region=None), 
#                many=True
#                )
#            print(serializer.data)
#            return Response(serializer.data)
#        except serializers.ValidationError:
#            print(traceback.print_exc())
#            raise
#        except ValidationError as e:
#            print(traceback.print_exc())
#            raise serializers.ValidationError(repr(e.error_dict))
#        except Exception as e:
#            print(traceback.print_exc())
#            raise serializers.ValidationError(str(e))
#
#    @detail_route(methods=['GET', ])
#    def get_region_districts(self, request, *args, **kwargs):
#        try:
#            instance = self.get_object()
#            serializer = RegionDistrictSerializer(
#                instance.districts.all(), many=True)
#            return Response(serializer.data)
#        except serializers.ValidationError:
#            print(traceback.print_exc())
#            raise
#        except ValidationError as e:
#            print(traceback.print_exc())
#            raise serializers.ValidationError(repr(e.error_dict))
#        except Exception as e:
#            print(traceback.print_exc())
#            raise serializers.ValidationError(str(e))
#
#    @detail_route(methods=['POST', ])
#    def get_compliance_group_by_region_district(self, request, *args, **kwargs):
#        try:
#            instance = self.get_object()
#            group_permission = request.data.get('group_permission')
#            compliance_content_type = ContentType.objects.get(model="compliancepermissiongroup")
#            permission = Permission.objects.filter(codename=group_permission).filter(content_type_id=compliance_content_type.id).first()
#            group = CompliancePermissionGroup.objects.filter(region_district=instance).filter(permissions=permission).first()
#            print(group)
#
#            allocated_group = [{
#                'email': '',
#                'first_name': '',
#                'full_name': '',
#                'id': None,
#                'last_name': '',
#                'title': '',
#                }]
#            #serializer = ComplianceUserDetailsOptimisedSerializer(group.members, many=True)
#            serializer = CompliancePermissionGroupMembersSerializer(instance=group)
#            print(serializer.data)
#            for member in serializer.data['members']:
#                allocated_group.append(member)
#
#            return Response(data={'allocated_group': allocated_group, 'group_id': group.id})
#        except serializers.ValidationError:
#            print(traceback.print_exc())
#            raise
#        except ValidationError as e:
#            print(traceback.print_exc())
#            raise serializers.ValidationError(repr(e.error_dict))
#        except Exception as e:
#            print(traceback.print_exc())
#            raise serializers.ValidationError(str(e))

class GetPersonOrg(views.APIView):
    renderer_classes = [JSONRenderer,]

    def get(self, request, format=None):
        search_term = request.GET.get('term', '')
        if search_term:
            data_transform = []
            user_data = EmailUser.objects.filter(
                Q(first_name__icontains=search_term) |
                Q(last_name__icontains=search_term) |
                Q(email__icontains=search_term)
            )[:10]
            for email_user in user_data:
                if email_user.dob:
                    text = '{} {} (DOB: {})'.format(email_user.first_name, email_user.last_name, email_user.dob)
                else:
                    text = '{} {}'.format(email_user.first_name, email_user.last_name)

                #serializer = EmailUserAppViewSerializer(email_user)
                #email_user_data = serializer.data
                email_user_data = {}
                email_user_data['text'] = text
                email_user_data['entity_type'] = 'user'
                email_user_data['id'] = email_user.id
                data_transform.append(email_user_data)
            org_data = Organisation.objects.filter(
                Q(organisation__name__icontains=search_term) |
                Q(organisation__abn__icontains=search_term) |
                Q(organisation__trading_name__icontains=search_term)
            )[:10]
            for org in org_data:
                text = '{} (ABN: {})'.format(org.name, org.abn)
                data = {}
                data['text'] = text
                data['entity_type'] = 'org'
                data['id'] = org.id
                data_transform.append(data)
            ## order results
            data_transform.sort(key=lambda item: item.get("id"))
            return Response({"results": data_transform})
        return Response()


class StaffMemberLookup(views.APIView):
    renderer_classes = [JSONRenderer,]

    def get(self, request, format=None):
        search_term = request.GET.get('term', '')
        if search_term:
            data_transform = []
            user_data = EmailUser.objects.filter(is_staff=True).filter(
                Q(first_name__icontains=search_term) |
                Q(last_name__icontains=search_term) |
                Q(email__icontains=search_term)
            )[:10]
            for email_user in user_data:
                if email_user.dob:
                    text = '{} {} (DOB: {})'.format(email_user.first_name, email_user.last_name, email_user.dob)
                else:
                    text = '{} {}'.format(email_user.first_name, email_user.last_name)

                email_user_data = {}
                email_user_data['text'] = text
                email_user_data['id'] = email_user.id
                data_transform.append(email_user_data)
            return Response({"results": data_transform})
        return Response()

