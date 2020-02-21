# -*- coding: utf-8 -*-
import os

from decimal import Decimal as D
from io import BytesIO

from django.core.files.storage import default_storage
from oscar.templatetags.currency_filters import currency
from reportlab.lib import enums
from reportlab.lib.colors import Color
from reportlab.lib.enums import TA_RIGHT, TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.platypus import BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, Table, TableStyle, ListFlowable, \
    KeepTogether, PageBreak, Flowable, NextPageTemplate, FrameBreak, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle, StyleSheet1
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen.canvas import Canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.lib.units import inch, mm
from reportlab.lib import colors

from django.core.files import File
from django.conf import settings

from ledger.accounts.models import Document
from ledger.checkout.utils import calculate_excl_gst

from wildlifecompliance.components.sanction_outcome.pdf import BrokenLine
from wildlifecompliance.components.sanction_outcome.pdf_in_blue import SolidLine

PAGE_WIDTH, PAGE_HEIGHT = A4
DEFAULT_FONTNAME = 'Helvetica'
BOLD_FONTNAME = 'Helvetica-Bold'

DPAW_HEADER_LOGO = os.path.join(settings.BASE_DIR, 'staticfiles', 'payments', 'img','dbca_logo.jpg')
DPAW_HEADER_LOGO_SM = os.path.join(settings.BASE_DIR, 'staticfiles', 'payments', 'img','dbca_logo_small.png')
BPAY_LOGO = os.path.join(settings.BASE_DIR, 'staticfiles', 'payments', 'img', 'BPAY_2012_PORT_BLUE.png')
HEADER_MARGIN = 10
HEADER_SMALL_BUFFER = 3
PAGE_TOP_MARGIN = 200
VERY_LARGE_FONTSIZE = 14
LARGE_FONTSIZE = 12
MEDIUM_FONTSIZE = 10
SMALL_FONTSIZE = 8
PARAGRAPH_BOTTOM_MARGIN = 5
SECTION_BUFFER_HEIGHT = 10
DATE_FORMAT = '%d/%m/%Y'


def _create_pdf(invoice_buffer, sanction_outcome):
    PAGE_MARGIN = 5 * mm
    page_frame_1 = Frame(PAGE_MARGIN, PAGE_MARGIN, PAGE_WIDTH - 2 * PAGE_MARGIN, PAGE_HEIGHT - 2 * PAGE_MARGIN, id='PagesFrame1', )  #showBoundary=Color(0, 1, 0))
    page_template_1 = PageTemplate(id='Page1', frames=[page_frame_1, ], )
    doc = BaseDocTemplate(invoice_buffer, pageTemplates=[page_template_1, ], pagesize=A4,)  # showBoundary=Color(1, 0, 0))

    # Common
    FONT_SIZE_L = 11
    FONT_SIZE_M = 10
    FONT_SIZE_S = 8

    styles = StyleSheet1()
    styles.add(ParagraphStyle(name='Normal',
                              fontName='Helvetica',
                              fontSize=FONT_SIZE_M,
                              spaceBefore=7,  # space before paragraph
                              spaceAfter=7,   # space after paragraph
                              leading=12))       # space between lines
    styles.add(ParagraphStyle(name='BodyText',
                              parent=styles['Normal'],
                              spaceBefore=6))
    styles.add(ParagraphStyle(name='Italic',
                              parent=styles['BodyText'],
                              fontName='Helvetica-Italic'))
    styles.add(ParagraphStyle(name='Bold',
                              parent=styles['BodyText'],
                              fontName='Helvetica-Bold',
                              alignment = TA_CENTER))
    styles.add(ParagraphStyle(name='Right',
                              parent=styles['BodyText'],
                              alignment=TA_RIGHT))
    styles.add(ParagraphStyle(name='Centre',
                              parent=styles['BodyText'],
                              alignment=TA_CENTER))

    # Logo
    dpaw_header_logo = ImageReader(DPAW_HEADER_LOGO)
    dpaw_header_logo_size = dpaw_header_logo.getSize()
    width = dpaw_header_logo_size[0]/2
    height = dpaw_header_logo_size[1]/2
    dbca_logo = Image(DPAW_HEADER_LOGO, width=width, height=height)

    # Title
    title_remediation_notice = Paragraph('<font size="' + str(FONT_SIZE_L) + '"><strong>REMEDIATION NOTICE</strong></font>', styles['Centre'])

    # Table
    invoice_table_style = TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),

        ('SPAN', (0, 0), (1, 0)),

        # Alleged offender
        ('SPAN', (0, 1), (0, 5)),
        ('SPAN', (1, 1), (2, 1)),
        ('SPAN', (1, 2), (2, 2)),
        ('SPAN', (1, 3), (2, 3)),
        ('SPAN', (1, 4), (2, 4)),
        ('SPAN', (1, 5), (2, 5)),

        # When
        ('SPAN', (1, 6), (2, 6)),

        # Where
        ('SPAN', (1, 7), (2, 7)),

        # Alleged offence
        ('SPAN', (0, 8), (0, 9)),
        ('SPAN', (1, 8), (2, 8)),
        # ('SPAN', (1, 9), (2, 9)),
        ('SPAN', (1, 9), (2, 9)),
        # ('SPAN', (1, 10), (2, 10)),

        # Officer issuing notice
        ('SPAN', (0, 10), (0, 12)),
        ('SPAN', (1, 10), (2, 10)),
        ('SPAN', (1, 11), (2, 11)),
        ('SPAN', (1, 12), (2, 12)),

        # Date
        ('SPAN', (1, 13), (2, 13)),

        # Notice to alleged offender
        ('SPAN', (1, 14), (2, 14)),
    ])
    date_str = gap(10) + '/' + gap(10) + '/ 20'
    col_width = [40*mm, 60*mm, 80*mm, ]

    data = []
    data.append([Paragraph('<i>Biodiversity Conservation Act 2016</i><br /><strong><font size="' + str(FONT_SIZE_L) + '">Caution Notice</font></strong>', styles['Normal']),
                 '',
                 Paragraph(u'Caution<br />notice no. <font face="Helvetica"><strong>' + sanction_outcome.lodgement_number + u'</strong></font>', styles['Normal'])])


    # Append tables to the elements to build
    gap_between_tables = 1.5*mm
    elements = []
    elements.append(dbca_logo)
    elements.append(title_remediation_notice)

    doc.build(elements)
    return invoice_buffer


def gap(num):
    ret = ''
    for i in range(num):
        ret = ret + '&nbsp;'
    return ret


def create_remediation_notice_pdf_bytes(filename, sanction_outcome):
    with BytesIO() as invoice_buffer:
        _create_pdf(invoice_buffer, sanction_outcome)

        # Get the value of the BytesIO buffer
        value = invoice_buffer.getvalue()

        # START: Save the pdf file to the database
        document = sanction_outcome.documents.create(name=filename)
        path = default_storage.save('wildlifecompliance/{}/{}/documents/{}'.format(sanction_outcome._meta.model_name, sanction_outcome.id, filename), invoice_buffer)
        document._file = path
        document.save()
        # END: Save

        return document


class DbcaLogo(Image, object):

    def __init__(self, filename, x_offset=0, y_offset=0, width=None, height=None, kind='direct', mask="auto", lazy=1, hAlign='CENTER'):
        self.x_offset = x_offset
        self.y_offset = y_offset
        super(DbcaLogo, self).__init__(filename, width, height, kind, mask, lazy, hAlign)

