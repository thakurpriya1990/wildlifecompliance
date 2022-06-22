import logging
from django.conf import settings
from django.contrib import admin
from django.conf.urls import url, include
from django.views.generic.base import TemplateView, RedirectView
from django.conf.urls.static import static
from rest_framework import routers

from wildlifecompliance import views
from wildlifecompliance.components.returns.views import (
    ReturnSuccessView,
    ReturnSheetSuccessView,
)
from wildlifecompliance.components.applications.views import (
    ApplicationSuccessView,
    LicenceFeeSuccessView,
)
from wildlifecompliance.admin import wildlifecompliance_admin_site

from wildlifecompliance.components.main.views import (
        SearchKeywordsView,
        SearchReferenceView,
        SearchWeakLinksView,
        CreateWeakLinkView,
        RemoveWeakLinkView,
        GeocodingAddressSearchTokenView,
        SystemPreferenceView,
        )
from wildlifecompliance.components.applications import views as application_views
from wildlifecompliance.components.users import api as users_api
from wildlifecompliance.components.organisations import api as org_api
from wildlifecompliance.components.applications import api as application_api
from wildlifecompliance.components.licences import api as licence_api
from wildlifecompliance.components.returns import api as return_api
from wildlifecompliance.components.wc_payments.views import DeferredInvoicingView, DeferredInvoicingPreviewView
from wildlifecompliance.management.permissions_manager import CollectorManager
from wildlifecompliance.components.call_email import api as call_email_api
from wildlifecompliance.components.offence import api as offence_api
from wildlifecompliance.components.inspection import api as inspection_api
from wildlifecompliance.components.sanction_outcome import api as sanction_outcome_api
from wildlifecompliance.components.main import api as main_api
from wildlifecompliance.components.wc_payments import views as payment_views
from wildlifecompliance.components.legal_case import api as legal_case_api
from wildlifecompliance.components.artifact import api as artifact_api

from wildlifecompliance.management.default_data_manager import DefaultDataManager
from wildlifecompliance.utils import are_migrations_running

from ledger.urls import urlpatterns as ledger_patterns

logger = logging.getLogger(__name__)

# API patterns
router = routers.DefaultRouter()
router.register(r'application', application_api.ApplicationViewSet)
router.register(r'application_selected_activity', application_api.ApplicationSelectedActivityViewSet)
router.register(r'application_paginated',
                application_api.ApplicationPaginatedViewSet)
router.register(r'application_conditions',
                application_api.ApplicationConditionViewSet)
router.register(r'application_standard_conditions',
                application_api.ApplicationStandardConditionViewSet)
router.register(r'assessment', application_api.AssessmentViewSet)
router.register(r'assessment_paginated',
                application_api.AssessmentPaginatedViewSet)
router.register(r'amendment', application_api.AmendmentRequestViewSet)
router.register(r'assessor_group', application_api.AssessorGroupViewSet)
router.register(r'licences', licence_api.LicenceViewSet)
router.register(r'licences_paginated', licence_api.LicencePaginatedViewSet)
router.register(r'licences_class', licence_api.LicenceCategoryViewSet)
router.register(r'licence_available_purposes',
                licence_api.UserAvailableWildlifeLicencePurposesViewSet)
router.register(r'returns', return_api.ReturnViewSet)
router.register(r'returns_paginated', return_api.ReturnPaginatedViewSet)
router.register(r'returns_amendment', return_api.ReturnAmendmentRequestViewSet)
router.register(r'return_types', return_api.ReturnTypeViewSet)
router.register(r'organisations', org_api.OrganisationViewSet)
router.register(r'organisations_compliancemanagement', org_api.OrganisationComplianceManagementViewSet)
router.register(r'organisations_paginated',
                org_api.OrganisationPaginatedViewSet)
router.register(r'organisation_requests', org_api.OrganisationRequestsViewSet)
router.register(r'organisation_requests_paginated',
                org_api.OrganisationRequestsPaginatedViewSet)
router.register(r'organisation_contacts', org_api.OrganisationContactViewSet)
router.register(r'my_organisations', org_api.MyOrganisationsViewSet)
router.register(r'users', users_api.UserViewSet)
router.register(r'compliance_management_users', users_api.ComplianceManagementUserViewSet)
router.register(r'users_paginated', users_api.UserPaginatedViewSet)
router.register(r'profiles', users_api.ProfileViewSet)
router.register(r'my_profiles', users_api.MyProfilesViewSet)
router.register(r'emailidentities', users_api.EmailIdentityViewSet)
router.register(r'call_email', call_email_api.CallEmailViewSet)
router.register(r'call_email_location', call_email_api.LocationViewSet)
router.register(r'classification', call_email_api.ClassificationViewSet)
router.register(r'lov_collection', call_email_api.LOVCollectionViewSet)
router.register(r'report_types', call_email_api.ReportTypeViewSet)
router.register(r'location', call_email_api.LocationViewSet)
router.register(r'referrers', call_email_api.ReferrerViewSet)
router.register(r'search_user', call_email_api.EmailUserViewSet)
router.register(r'search_alleged_offences', offence_api.SearchSectionRegulation)
router.register(r'search_organisation', offence_api.SearchOrganisation)
router.register(r'map_layers', call_email_api.MapLayerViewSet)
#router.register(r'compliancepermissiongroup', users_api.CompliancePermissionGroupViewSet)
#router.register(r'region_district', users_api.RegionDistrictViewSet)
router.register(r'regions', main_api.RegionViewSet)
router.register(r'districts', main_api.DistrictViewSet)
router.register(r'legal_case_priorities', legal_case_api.LegalCasePriorityViewSet)
router.register(r'inspection_types', inspection_api.InspectionTypeViewSet)
router.register(r'call_email_paginated', call_email_api.CallEmailPaginatedViewSet)
router.register(r'inspection', inspection_api.InspectionViewSet)
router.register(r'inspection_paginated', inspection_api.InspectionPaginatedViewSet)
router.register(r'sanction_outcome', sanction_outcome_api.SanctionOutcomeViewSet)
router.register(r'sanction_outcome_paginated', sanction_outcome_api.SanctionOutcomePaginatedViewSet)
router.register(r'remediation_action', sanction_outcome_api.RemediationActionViewSet)
router.register(r'offence', offence_api.OffenceViewSet)
router.register(r'offence_paginated', offence_api.OffencePaginatedViewSet)
router.register(r'temporary_document', main_api.TemporaryDocumentCollectionViewSet)
router.register(r'legal_case', legal_case_api.LegalCaseViewSet)
router.register(r'legal_case_paginated', legal_case_api.LegalCasePaginatedViewSet)
router.register(r'document_artifact', artifact_api.DocumentArtifactViewSet)
router.register(r'artifact', artifact_api.ArtifactViewSet)
router.register(r'artifact_paginated', artifact_api.ArtifactPaginatedViewSet)
router.register(r'physical_artifact', artifact_api.PhysicalArtifactViewSet)
router.register(r'physical_artifact_types', artifact_api.PhysicalArtifactTypeViewSet)
router.register(r'disposal_methods', artifact_api.PhysicalArtifactDisposalMethodViewSet)

router.register(
    r'schema_masterlist',
    main_api.SchemaMasterlistViewSet
)
router.register(
    r'schema_masterlist_paginated', main_api.SchemaMasterlistPaginatedViewSet)
router.register(
    r'schema_purpose', main_api.SchemaPurposeViewSet)
router.register(
    r'schema_purpose_paginated', main_api.SchemaPurposePaginatedViewSet)
router.register(
    r'schema_group', main_api.SchemaGroupViewSet)
router.register(
    r'schema_group_paginated', main_api.SchemaGroupPaginatedViewSet)
router.register(
    r'schema_question', main_api.SchemaQuestionViewSet)
router.register(
    r'schema_question_paginated', main_api.SchemaQuestionPaginatedViewSet)

api_patterns = [url(r'^api/my_user_details/$',
                    users_api.GetMyUserDetails.as_view(),
                    name='get-my-user-details'),
                url(r'^api/is_compliance_management_callemail_readonly_user$', 
                    users_api.IsComplianceManagementCallEmailReadonlyUser.as_view(), 
                    name='is-compliance-manegement-callemail-readonly-user'),
                url(r'^api/allocated_group_members$', 
                    main_api.AllocatedGroupMembers.as_view(), 
                    name='allocated-group-members'),
                url(r'^api/countries$', 
                    users_api.GetCountries.as_view(), 
                    name='get-countries'),
                url(r'^api/staff_member_lookup$', 
                    users_api.StaffMemberLookup.as_view(), 
                    name='staff-member-lookup'),
                #url(r'^api/department_users$',
                 #   users_api.DepartmentUserList.as_view(),
                  #  name='department-users-list'),
                url(r'^api/my_compliance_user_details/$',
                    users_api.GetComplianceUserDetails.as_view(),
                    name='get-my-compliance-user-details'),
                url(r'^api/is_new_user/$',
                    users_api.IsNewUser.as_view(),
                    name='is-new-user'),
                url(r'^api/user_profile_completed/$',
                    users_api.UserProfileCompleted.as_view(),
                    name='get-user-profile-completed'),
                url(r'^api/amendment_request_reason_choices',
                    application_api.AmendmentRequestReasonChoicesView.as_view(),
                    name='amendment_request_reason_choices'),
                url(r'^api/return_amendment_request_reason_choices',
                    return_api.ReturnAmendmentRequestReasonChoicesView.as_view(),
                    name='return_amendment_request_reason_choices'),
                url(r'^api/empty_list/$',
                    application_api.GetEmptyList.as_view(),
                    name='get-empty-list'),
                url(r'^api/organisation_access_group_members',
                    org_api.OrganisationAccessGroupMembers.as_view(),
                    name='organisation-access-group-members'),
                url(r'^api/search_keywords',
                    SearchKeywordsView.as_view(),
                    name='search_keywords'),
                url(r'^api/search_reference',
                    SearchReferenceView.as_view(),
                    name='search_reference'),
                url(r'^api/search_weak_links',
                    SearchWeakLinksView.as_view(),
                    name='search_weak_links'),
                url(r'^api/create_weak_link',
                    CreateWeakLinkView.as_view(),
                    name='create_weak_link'),
                url(r'^api/remove_weak_link',
                    RemoveWeakLinkView.as_view(),
                    name='remove_weak_link'),
                url(r'^api/geocoding_address_search_token',
                    GeocodingAddressSearchTokenView.as_view(),
                    name='geocoding_address_search_token'),
                url(r'^api/system_preference',
                    SystemPreferenceView.as_view(),
                    name='system_preference'),
                url(r'^api/',
                    include(router.urls))]

# URL Patterns
urlpatterns = [
    url(r'contact-us/$',
        TemplateView.as_view(
            template_name="wildlifecompliance/contact_us.html"),
        name='wc_contact'),
    url(
        r'further-info/$',
        RedirectView.as_view(
            url='https://www.dpaw.wa.gov.au/plants-and-animals/licences-and-permits'),
        name='wc_further_info'),
    url(r'^admin/', wildlifecompliance_admin_site.urls),
    url(r'^ledger/admin/', admin.site.urls, name='ledger_admin'),
    url(r'^chaining/', include('smart_selects.urls')),
    url(r'', include(api_patterns)),
    url(r'^$', views.WildlifeComplianceRoutingView.as_view(), name='wc_home'),
    url(r'^internal/', views.InternalView.as_view(), name='internal'),
    url(r'^external/', views.ExternalView.as_view(), name='external'),
    url(r'^external/application/(?P<application_pk>\d+)/$', views.ExternalApplicationView.as_view(), name='external-application-detail'),
    url(r'^external/return/(?P<return_pk>\d+)/$', views.ExternalReturnView.as_view(), name='external-return-detail'),
    url(r'^firsttime/$', views.first_time, name='first_time'),
    url(r'^account/$', views.ExternalView.as_view(), name='manage-account'),
    url(r'^profiles/', views.ExternalView.as_view(), name='manage-profiles'),
    # url(r'^external/organisations/manage/$', views.ExternalView.as_view(), name='manage-org'),
    url(r'^application/$',
        application_views.ApplicationView.as_view(),
        name='application'),
    # url(r'^organisations/(?P<pk>\d+)/confirm-delegate-access/(?P<uid>[0-9A-Za-z]+)-(?P<token>.+)/$',
    #     views.ConfirmDelegateAccess.as_view(), name='organisation_confirm_delegate_access'),
    url('^healthcheck/', views.HealthCheckView.as_view(), name='health_check'),

    # following url is defined so that to include url path when sending
    # call_email emails to users
    url(r'^internal/call_email/(?P<call_email_id>\d+)/$', views.ApplicationView.as_view(),
        name='internal-call-email-detail'),
    # following url is defined so that to include url path when sending
    # artifact emails to users
    url(r'^internal/object/(?P<artifact_id>\d+)/$', views.ApplicationView.as_view(),
        name='internal-artifact-detail'),

    # following url is defined so that to include url path when sending
    # inspection emails to users
    url(r'^internal/inspection/(?P<inspection_id>\d+)/$', views.ApplicationView.as_view(),
        name='internal-inspection-detail'),

    # following url is defined so that to include url path when sending
    # sanction outcome emails to users
    url(r'^internal/sanction_outcome/(?P<sanction_outcome_id>\d+)/$', views.ApplicationView.as_view(), name='internal-sanction-outcome-detail'),

    url(r'^internal/offence/(?P<offence_id>\d+)/$', views.ApplicationView.as_view(), name='internal-offence-detail'),

    # following url is defined so that to include url path when sending
    # inspection emails to users
    url(r'^internal/legal_case/(?P<legal_case_id>\d+)/$', views.ApplicationView.as_view(),
        name='internal-legal-case-detail'),
    url(r'^internal/application/(?P<application_pk>\d+)/$', views.ApplicationView.as_view(),
        name='internal-application-detail'),
    url(r'^application_submit/submit_with_invoice/',
        ApplicationSuccessView.as_view(),
        name='external-application-success-invoice'),
    url(r'^application/finish_licence_fee_payment/',
        LicenceFeeSuccessView.as_view(),
        name='external-licence-fee-success-invoice'),
    url(r'^returns_submit/submit_with_invoice/',
        ReturnSuccessView.as_view(),
        name='external-returns-success-invoice'),
    url(r'^returns/finish_sheet_fee_payment/',
        ReturnSheetSuccessView.as_view(),
        name='external-sheet-success-invoice'),

    # url(r'^export/xls/$', application_views.export_applications, name='export_applications'),
    url(r'^export/pdf/$', application_views.pdflatex, name='pdf_latex'),
    url(r'^mgt-commands/$',
        views.ManagementCommandsView.as_view(),
        name='mgt-commands'),

    # payment related urls
    url(r'^infringement_penalty/(?P<sanction_outcome_id>\d+)/$', payment_views.InfringementPenaltyView.as_view(), name='infringement_penalty'),
    url(r'^success/fee/$', payment_views.InfringementPenaltySuccessView.as_view(), name='penalty_success'),

    # For 'Record Payment'
    url(r'^payment_deferred/(?P<sanction_outcome_pk>\d+)/$', DeferredInvoicingView.as_view(), name='deferred_invoicing'),
    url(r'^preview_deferred/(?P<sanction_outcome_pk>\d+)/$', DeferredInvoicingPreviewView.as_view(), name='preview_deferred_invoicing'),

    # Reports
    url(r'^api/oracle_job$',main_api.OracleJob.as_view(), name='get-oracle'),
    #url(r'^api/oracle_job$',main_api.OracleJob.as_view(), name='get-oracle'),
    url(r'^api/reports/booking_settlements$', main_api.BookingSettlementReportView.as_view(),name='booking-settlements-report'),

    # history comparison.
    url(r'^history/application/(?P<pk>\d+)/$',
        application_views.ApplicationHistoryCompareView.as_view(),
        name='application-history'),

    url(r'^preview/licence-pdf/(?P<application_pk>\d+)',application_views.PreviewLicencePDFView.as_view(), name='preview_licence_pdf'),

    url(r'^securebase-view/',views.SecureBaseView.as_view(), name='securebase-view'),
    url(r'^api/person_org_lookup$', users_api.GetPersonOrg.as_view(), name='get-person-org'),

] + ledger_patterns

if not are_migrations_running():
    DefaultDataManager()
    CollectorManager()

# whitenoise
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.SHOW_DEBUG_TOOLBAR:
    import debug_toolbar
    urlpatterns = [
        url('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
