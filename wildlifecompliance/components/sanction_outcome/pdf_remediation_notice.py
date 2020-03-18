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
from reportlab.platypus import BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, Table, TableStyle,  \
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

from wildlifecompliance.components.main.pdf_utils import gap, SolidLine, get_font_str

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
    ])
    date_str = gap(10) + '/' + gap(10) + '/ 20'
    col_width = [180*mm, ]

    offender = sanction_outcome.get_offender()

    data = []
    p_number = get_font_str(str(offender[0].phone_number) + '(p)') if offender[0].phone_number else ''
    m_number = get_font_str(offender[0].mobile_number + '(m)') if offender[0].mobile_number else ''
    phone_number = ' | '.join(list(filter(None, [p_number, m_number])))
    data.append([[
        Paragraph('Pursuant to the <i>Biodiversity Conservation Act 2016</i>, the CEO considers that you are a person bound by a relevant instrument.<br />'
                           '<strong>Contact details of person to whom this Notice is issued:</strong>', styles['Normal']),
        Paragraph('Full name: ' + get_font_str(offender[0].get_full_name()) + gap(5) + 'Date of Birth: ' + get_font_str(offender[0].dob.strftime('%d/%m/%Y')), styles['Normal']),
        Paragraph('Postal/Residential address: ' + get_font_str(offender[0].residential_address), styles['Normal']),
        Paragraph('Telephone number: ' + phone_number, styles['Normal']),
        Paragraph('Email address: ' + get_font_str(offender[0].email), styles['Normal']),
    ], ])
    data.append([[
        Paragraph('The CEO is of the opinion that you have contravened the relevant instrument listed below:', styles['Normal']),
        Table([
            [Paragraph('<strong>Relevant Instrument</strong>', styles['Normal']), Paragraph('<strong>Reference Number of Instrument/Notice</strong>', styles['Normal'])],
            [Paragraph('Biodiversity Conservation Covenant', styles['Normal']), ''],
            [Paragraph('Environment Pest Notice', styles['Normal']), ''],
            [Paragraph('Habitat Conservation Notice', styles['Normal']), ''],
        ], style=invoice_table_style, rowHeights=[6*mm, 12*mm, 12*mm, 12*mm])
    ], ])
    data.append([[
        Paragraph('You are required to undertake one or more of the following action(s) to comply with the named instrument:', styles['Normal']),
        Paragraph('a) Stop anything that is being done in contravention of the instrument; and<br />'
                  'b) Do anything required by the instrument to be done that has not been done; and<br />'
                  'c) Carry out work that is necessary to remedy anything done in contravention of the instrument; and<br />'
                  'd) Do anything incidental to action referred to in (a), (b), or (c) above', styles['Normal'])
    ], ])

    # Actions
    actions = []
    actions.append(Paragraph('List the remedial actions necessary to afford compliance with the relevant instrument:', styles['Normal']))
    for ra in sanction_outcome.remediation_actions.all():
        actions.append(Paragraph(get_font_str(ra.action), styles['Normal']))
    data.append([actions,])
    data.append([[
        Paragraph('<strong>IMPORTANT</strong>: You must comply with the remediation action(s) listed above within the period specified in this notice.', styles['Normal']),
        Paragraph('If you do not comply within the specified period, the CEO may take any necessary remedial action and may recover the reasonable costs incurred in taking remedial action from you, as a person(s) bound by the relevant instrument, in a court of competent jurisdiction as a debt to the State.', styles['Normal']),
        Paragraph('Postal Address of the CEO:<br />Department of Biodiversity, Conservation and Attractions<br />Locked Bag 104<br />Bentley Delivery Centre WA 6983', styles['Normal']),
    ], ])
    data.append([[
        Paragraph('<strong>Notes:</strong>:', styles['Normal']),
        Paragraph('A separate Remediation Notice must be issued to each person bound by the instrument.:', styles['Normal'], bulletText='-'),
        Paragraph('For the purpose of taking remedial action a wildlife officer may enter on land with or without vehicles, plant or equipment and remain on that land for as long as is necessary to complete the remedial action.', styles['Normal'], bulletText='-'),
        Paragraph('A wildlife officer must not exercise a power to enter unless they first obtain the consent of the owner or occupier of the land, or the owner/occupier has been given reasonable notice of the proposed entry and has not objected to the entry, or the entry is in accordance with an entry warrant. Section 202 of the Biodiversity Conservation Act 2016 applies. (Occupiers Rights)', styles['Normal'], bulletText='-',)
    ], ])

    t1 = Table(data, style=invoice_table_style, colWidths=col_width, rowHeights=[60*mm, 60*mm, 40*mm, 90*mm, 60*mm, 60*mm,])

    # Append tables to the elements to build
    gap_between_tables = 1.5*mm
    elements = []
    elements.append(dbca_logo)
    elements.append(title_remediation_notice)
    elements.append(t1)

    doc.build(elements)
    return invoice_buffer


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

        invoice_buffer.close()

        return document
