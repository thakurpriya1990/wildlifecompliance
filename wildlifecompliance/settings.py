import os
import confy
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
confy.read_environment_file(BASE_DIR+"/.env")
os.environ.setdefault("BASE_DIR", BASE_DIR)
from django.core.exceptions import ImproperlyConfigured
from ledger.settings_base import *

os.environ['LEDGER_PRODUCT_CUSTOM_FIELDS'] = "('ledger_description','quantity','price_incl_tax','price_excl_tax','oracle_code')"
os.environ['LEDGER_REFUND_TRANSACTION_CALLBACK_MODULE'] = 'wildlifecompliance:wildlifecompliance.components.applications.api.application_refund_callback'
os.environ['LEDGER_INVOICE_TRANSACTION_CALLBACK_MODULE'] = 'wildlifecompliance:wildlifecompliance.components.applications.api.application_invoice_callback'

ROOT_URLCONF = 'wildlifecompliance.urls'
SITE_ID = 1
SYSTEM_MAINTENANCE_WARNING = env('SYSTEM_MAINTENANCE_WARNING', 24)  # hours

STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles_wc')
SHOW_DEBUG_TOOLBAR = env('SHOW_DEBUG_TOOLBAR', False)
APPEND_SOURCE_TO_RICHTEXT_ADMIN = env('APPEND_SOURCE_TO_RICHTEXT_ADMIN', False)
FILE_UPLOAD_MAX_MEMORY_SIZE = env('FILE_UPLOAD_MAX_MEMORY_SIZE', 2621440) # 2.5MB --> Django Default


if SHOW_DEBUG_TOOLBAR:
#    def get_ip():
#        import subprocess
#        route = subprocess.Popen(('ip', 'route'), stdout=subprocess.PIPE)
#        network = subprocess.check_output(
#            ('grep', '-Po', 'src \K[\d.]+\.'), stdin=route.stdout
#        ).decode().rstrip()
#        route.wait()
#        network_gateway = network + '1'
#        return network_gateway

    def show_toolbar(request):
        return True

    MIDDLEWARE_CLASSES += [
        'debug_toolbar.middleware.DebugToolbarMiddleware',
    ]
    INSTALLED_APPS += (
        'debug_toolbar',
    )
    #INTERNAL_IPS = ('127.0.0.1', 'localhost', get_ip())
    INTERNAL_IPS = ('127.0.0.1', 'localhost')

    # this dict removes check to dtermine if toolbar should display --> works for rks docker container
    DEBUG_TOOLBAR_CONFIG = {
        "SHOW_TOOLBAR_CALLBACK" : show_toolbar,
        'INTERCEPT_REDIRECTS': False,
    }

STATIC_URL = '/static/'

INSTALLED_APPS += [
    'reversion_compare',
    'django.contrib.humanize',
    'bootstrap3',
    'wildlifecompliance',
    'wildlifecompliance.components.main',
    'wildlifecompliance.components.applications',
    'wildlifecompliance.components.organisations',
    'wildlifecompliance.components.licences',
    'wildlifecompliance.components.users',
    'wildlifecompliance.components.returns',
    'wildlifecompliance.components.call_email',
    'wildlifecompliance.components.offence',
    'wildlifecompliance.components.inspection',
    'wildlifecompliance.components.sanction_outcome',
    'wildlifecompliance.components.wc_payments',
    'wildlifecompliance.components.legal_case',
    'wildlifecompliance.components.artifact',
    'taggit',
    'rest_framework',
    'rest_framework_gis',
    'rest_framework_datatables',
    'smart_selects',
    'ckeditor',
]

CKEDITOR_BASEPATH = '/static/ckeditor/ckeditor/'

CKEDITOR_CONFIGS = {
    'default': {
        'toolbar': 'Custom',
        'toolbar_Custom': [
            ['Bold', 'Italic', 'Underline'],
            ['NumberedList', 'BulletedList', '-', 'Outdent', 'Indent', '-', 'JustifyLeft', 'JustifyCenter', 'JustifyRight', 'JustifyBlock'],
            ['Link', 'Unlink'],
            ['RemoveFormat'],
            #[ 'Source']
        ]
    },
    'pdf_config': {
        'toolbar': 'Custom',
        'toolbar_Custom': [
            [ '-', 'Bold', 'Italic' ],
            [ 'Format' ],
            [ 'NumberedList', 'BulletedList' ],
            [ 'Table' ],
            #[ 'Source']
        ]
    },
}

if APPEND_SOURCE_TO_RICHTEXT_ADMIN:
    CKEDITOR_CONFIGS['pdf_config']['toolbar_Custom'].append(['Source'])


ADD_REVERSION_ADMIN = True

# maximum number of days allowed for a booking
WSGI_APPLICATION = 'wildlifecompliance.wsgi.application'

REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
        'rest_framework_datatables.renderers.DatatablesRenderer',
    ),
    'DEFAULT_FILTER_BACKENDS': (
        'rest_framework_datatables.filters.DatatablesFilterBackend',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework_datatables.pagination.DatatablesPageNumberPagination',
    'PAGE_SIZE': 50,
}

USE_DJANGO_JQUERY=True

if env('EMAIL_INSTANCE') is not None and env('EMAIL_INSTANCE','') != 'PROD':
    REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES'] += ('rest_framework.renderers.BrowsableAPIRenderer',)

MIDDLEWARE_CLASSES += [
    'wildlifecompliance.middleware.FirstTimeNagScreenMiddleware',
    'wildlifecompliance.middleware.CacheControlMiddleware',
]

LATEX_GRAPHIC_FOLDER = os.path.join(BASE_DIR,"templates","latex","images")

TEMPLATES[0]['DIRS'].append(
    os.path.join(
        BASE_DIR,
        'wildlifecompliance',
        'templates'))
TEMPLATES[0]['DIRS'].append(
    os.path.join(
        BASE_DIR,
        'wildlifecompliance',
        'components',
        'organisations',
        'templates'))
TEMPLATES[0]['DIRS'].append(
    os.path.join(
        BASE_DIR,
        'wildlifecompliance',
        'components',
        'emails',
        'templates'))
del BOOTSTRAP3['css_url']
#BOOTSTRAP3 = {
#    'jquery_url': '//static.dbca.wa.gov.au/static/libs/jquery/2.2.1/jquery.min.js',
#    'base_url': '//static.dbca.wa.gov.au/static/libs/twitter-bootstrap/3.3.6/',
#    'css_url': None,
#    'theme_url': None,
#    'javascript_url': None,
#    'javascript_in_head': False,
#    'include_jquery': False,
#    'required_css_class': 'required-form-field',
#    'set_placeholder': False,
#}
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': os.path.join(BASE_DIR, 'wildlifecompliance', 'cache'),
    }
}
CRON_CLASSES = [
    'wildlifecompliance.cron.OracleIntegrationCronJob',
]

# Additional logging for wildlifecompliance
LOGGING['handlers']['application_checkout'] = {
    'level': 'INFO',
    'class': 'logging.handlers.RotatingFileHandler',
    'filename': os.path.join(
        BASE_DIR,
        'logs',
        'wildlifecompliance_application_checkout.log'),
    'formatter': 'verbose',
    'maxBytes': 5242880}
LOGGING['loggers']['application_checkout'] = {
    'handlers': ['application_checkout'],
    'level': 'INFO'
}
# Additional logging for securebase manager.
LOGGING['handlers']['securebase_manager'] = {
    'level': 'INFO',
    'class': 'logging.handlers.RotatingFileHandler',
    'filename': os.path.join(
        BASE_DIR,
        'logs',
        'securebase_manager.log'),
    'formatter': 'verbose',
    'maxBytes': 5242880}
LOGGING['loggers']['securebase_manager'] = {
    'handlers': ['securebase_manager'],
    'level': 'INFO'
}
# # Additional logging for compliancemanagement
# LOGGING['handlers']['compliancemanagement'] = {
#     'level': 'INFO',
#     'class': 'logging.handlers.RotatingFileHandler',
#     'filename': os.path.join(
#         BASE_DIR,
#         'logs',
#         'wildlifecompliance_compliancemanagement.log'),
#     'formatter': 'verbose',
#     'maxBytes': 5242880}
# LOGGING['loggers']['compliancemanagement'] = {
#     'handlers': ['compliancemanagement'],
#     'level': 'INFO'
# }
print(BASE_DIR)
STATICFILES_DIRS.append(
    os.path.join(
        os.path.join(
            BASE_DIR,
            'wildlifecompliance',
            'static')))
DEV_STATIC = env('DEV_STATIC', False)
DEV_STATIC_URL = env('DEV_STATIC_URL')
DEV_APP_BUILD_URL = env('DEV_APP_BUILD_URL')  # URL of the Dev app.js served by webpack & express
#BUILD_TAG = env('BUILD_TAG', '0.0.0')  # URL of the Dev app.js served by webpack & express

RAND_HASH = ''
if os.path.isdir(BASE_DIR+'/.git/') is True:
    RAND_HASH = os.popen('cd  '+BASE_DIR+' ; git log -1 --format=%H').read()
if not len(RAND_HASH):
    RAND_HASH = os.popen('cat /app/rand_hash').read()
if len(RAND_HASH) == 0:
    print ("ERROR: No rand hash provided")

if DEV_STATIC and not DEV_STATIC_URL:
    raise ImproperlyConfigured(
        'If running in DEV_STATIC, DEV_STATIC_URL has to be set')
DATA_UPLOAD_MAX_NUMBER_FIELDS = None

# Department details
SYSTEM_NAME = env('SYSTEM_NAME', 'Wildlife Licensing System')
SYSTEM_EMAIL = env('SYSTEM_EMAIL', 'wildlifelicensing@dbca.wa.gov.au')

WC_PAYMENT_SYSTEM_ID = env('WC_PAYMENT_SYSTEM_ID', 'S566')
WC_PAYMENT_SYSTEM_PREFIX = env('PAYMENT_SYSTEM_PREFIX', WC_PAYMENT_SYSTEM_ID.replace('S', '0'))
PS_PAYMENT_SYSTEM_ID = WC_PAYMENT_SYSTEM_ID
WC_PAYMENT_SYSTEM_URL_PDF = env('WC_PAYMENT_SYSTEM_URL_PDF', '/ledger/payments/invoice-pdf/')
WC_PAYMENT_SYSTEM_URL_INV = env('WC_PAYMENT_SYSTEM_URL_INV', '/ledger/payments/invoice/')

COLS_ADMIN_GROUP = env('COLS_ADMIN_GROUP', 'COLS Admin')
if not VALID_SYSTEMS:
    VALID_SYSTEMS = [WC_PAYMENT_SYSTEM_ID]
DEP_URL = env('DEP_URL', 'www.dbca.wa.gov.au')
DEP_PHONE = env('DEP_PHONE', '(08) 9219 9831')
DEP_FAX = env('DEP_FAX', '(08) 9423 8242')
DEP_POSTAL = env(
    'DEP_POSTAL',
    'Locked Bag 104, Bentley Delivery Centre, Western Australia 6983')
DEP_NAME = env(
    'DEP_NAME',
    'Department of Biodiversity, Conservation and Attractions')
DEPT_DOMAINS = env('DEPT_DOMAINS', ['dpaw.wa.gov.au', 'dbca.wa.gov.au'])
SITE_PREFIX = env('SITE_PREFIX')
SITE_DOMAIN = env('SITE_DOMAIN')
SITE_URL = env('SITE_URL', 'https://' + SITE_PREFIX + '.' + SITE_DOMAIN)
SITE_URL_WLC = env('SITE_URL_WLC')
GROUP_PREFIX = env('GROUP_PREFIX', 'Wildlife Compliance')
COMPLIANCE_GROUP_PREFIX = env('COMPLIANCE_GROUP_PREFIX', 'Compliance Management')
EXT_USER_API_ROOT_URL = env('EXT_USER_API_ROOT_URL', None)
EXCEL_OUTPUT_PATH = env('EXCEL_OUTPUT_PATH')
ALLOW_EMAIL_ADMINS = env('ALLOW_EMAIL_ADMINS', False)  # Allows internal pages to be accessed via email authentication
SYSTEM_APP_LABEL = env('SYSTEM_APP_LABEL', 'wildlifecompliance')  # global app_label for group permissions filtering
RENEWAL_PERIOD_DAYS = env('RENEWAL_PERIOD_DAYS', 30)
GEOCODING_ADDRESS_SEARCH_TOKEN = env('GEOCODING_ADDRESS_SEARCH_TOKEN', 'ACCESS_TOKEN_NOT_FOUND')
DOT_EMAIL_ADDRESS = env('DOT_EMAIL_ADDRESS')

# Details for Threathened Species and Communities server.
TSC_URL = env('TSC_URL', 'https://tsc.dbca.wa.gov.au')
TSC_AUTH = env('TSC_AUTH', 'NO_AUTH')
CRON_RUN_AT_TIMES = env('CRON_RUN_AT_TIMES', '02:05')

if env('CONSOLE_EMAIL_BACKEND', False):
   EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
# if DEBUG:
#     EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
#

SO_TYPE_INFRINGEMENT_NOTICE = 'infringement_notice'
SO_TYPE_CAUTION_NOTICE = 'caution_notice'
SO_TYPE_LETTER_OF_ADVICE = 'letter_of_advice'
SO_TYPE_REMEDIATION_NOTICE = 'remediation_notice'

SO_TYPE_CHOICES = (
    (SO_TYPE_INFRINGEMENT_NOTICE, 'Infringement Notice'),
    (SO_TYPE_CAUTION_NOTICE, 'Caution Notice'),
    (SO_TYPE_LETTER_OF_ADVICE, 'Letter of Advice'),
    (SO_TYPE_REMEDIATION_NOTICE, 'Remediation Notice'),
)
HEAD_OFFICE_NAME=env('HEAD_OFFICE_NAME', 'KENSINGTON')
HTTP_HOST_FOR_TEST = env('HTTP_HOST_FOR_TEST', 'localhost:8123')

GROUP_CALL_EMAIL_TRIAGE = "call_email_triage"
GROUP_OFFICER = "officer"
GROUP_MANAGER = "manager"
GROUP_VOLUNTEER = "volunteer"
GROUP_INFRINGEMENT_NOTICE_COORDINATOR = "infringement_notice_coordinator"
GROUP_PROSECUTION_COORDINATOR = "prosecution_coordinator"
GROUP_PROSECUTION_MANAGER = "prosecution_manager"
GROUP_PROSECUTION_COUNCIL = "prosecution_council"
GROUP_COMPLIANCE_MANAGEMENT_READ_ONLY = "compliance_management_read_only"
GROUP_COMPLIANCE_MANAGEMENT_CALL_EMAIL_READ_ONLY = "compliance_management_call_email_read_only"
GROUP_COMPLIANCE_MANAGEMENT_APPROVED_EXTERNAL_USER = "compliance_management_approved_external_user"
GROUP_COMPLIANCE_ADMIN = "compliance_admin"
GROUP_LICENSING_ADMIN = "licensing_admin"
GROUP_NAME_CHOICES = (
    (GROUP_CALL_EMAIL_TRIAGE, "Call Email Triage"),
    (GROUP_OFFICER, "Officer"),
    (GROUP_MANAGER, "Manager"),
    (GROUP_VOLUNTEER, "Volunteer"),
    (GROUP_INFRINGEMENT_NOTICE_COORDINATOR, "Infringement Notice Coordinator"),
    (GROUP_PROSECUTION_COORDINATOR, "Prosecution Notice Coordinator"),
    (GROUP_PROSECUTION_MANAGER, "Prosecution Manager"),
    (GROUP_PROSECUTION_COUNCIL, "Prosecution Council"),
    (GROUP_COMPLIANCE_MANAGEMENT_READ_ONLY, "Compliance Management Read Only"),
    (GROUP_COMPLIANCE_MANAGEMENT_CALL_EMAIL_READ_ONLY, "Compliance Management Call Email Read Only"),
    (GROUP_COMPLIANCE_MANAGEMENT_APPROVED_EXTERNAL_USER, "Compliance Management Approved External User"),
    (GROUP_COMPLIANCE_ADMIN, "Compliance Admin"),
    (GROUP_LICENSING_ADMIN, "Licensing Admin"),
)

AUTH_GROUP_COMPLIANCE_BUSINESS_ADMIN = 'Wildlife Compliance - Compliance Business Admin'
CUSTOM_AUTH_GROUPS = [
    AUTH_GROUP_COMPLIANCE_BUSINESS_ADMIN,
    ]
