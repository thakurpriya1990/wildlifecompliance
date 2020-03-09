from __future__ import unicode_literals

import json
from collections import OrderedDict

from django import forms
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.paginator import Page
from django.http.multipartparser import parse_header
from django.template import Template, loader
from django.test.client import encode_multipart
from django.utils import six

from rest_framework import VERSION, exceptions, serializers, status
from rest_framework.compat import (
    INDENT_SEPARATORS, LONG_SEPARATORS, SHORT_SEPARATORS, coreapi,
    template_render
)
from rest_framework.exceptions import ParseError
from rest_framework.request import is_form_media_type, override_method
from rest_framework.settings import api_settings
from rest_framework.utils import encoders
from rest_framework.utils.breadcrumbs import get_breadcrumbs
from rest_framework.utils.field_mapping import ClassLookupDict
from rest_framework.renderers import BaseRenderer


class PDFRenderer(BaseRenderer):
    media_type = 'application/pdf'
    format = 'pdf'
    render_style = 'binary'

    def render(self, data, media_type=None, renderer_context=None):
        import ipdb; ipdb.set_trace();
        print("this is the pdfrenderer")
        return data.encode(self.charset)

