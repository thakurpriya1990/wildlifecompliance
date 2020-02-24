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

    # Table
    invoice_table_style = TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('VALIGN', (1, 3), (1, 3), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('SPAN', (1, 1), (2, 1)),
        ('SPAN', (0, 2), (0, 3)),
        ('SPAN', (1, 4), (2, 4)),
        ('SPAN', (1, 5), (2, 5)),
        ('SPAN', (1, 6), (2, 6)),
        ('SPAN', (1, 7), (2, 7)),
        ('SPAN', (1, 8), (2, 8)),
    ])
    date_str = gap(10) + '/' + gap(10) + '/'
    col_width = [30*mm, 125*mm, 25*mm, ]

    data = []
    data.append([
        Paragraph('<strong>Western Australia</strong>', styles['Normal']),
        Paragraph('<i>Biodiversity Conservation Act 2016</i><br /><strong>Obtaining Records and Directions</strong>', styles['Normal']),
        Paragraph('<strong>No.</strong>', styles['Normal']),
    ])
    data.append([
        Paragraph('<strong>To</strong>', styles['Normal']),
        [
            Paragraph('Given names:', styles['Normal']),
            Paragraph('Surname:', styles['Normal']),
            Spacer(0, 3*mm),
        ],
        '',
    ])
    data.append([
        Paragraph('<strong>Address</strong>', styles['Normal']),
        [
            Paragraph('No and Street:', styles['Normal']),
            Paragraph('Town/Suburb:', styles['Normal']),
            Spacer(0, 3*mm)
        ],
        Paragraph('Post Code', styles['Normal']),
    ])
    data.append(([
        '',
        Paragraph('Date of Birth' + date_str, styles['Normal']),
        [
            Paragraph('Gender:', styles['Normal']),
            Paragraph('M' + gap(3) + 'F' + gap(3) + 'U', styles['Normal']),
        ],
    ]))
    data.append([
        Paragraph('<strong>Direction<br /><br />* Delete as appropriate.<br /><br /># Enter details of direction given.</strong>', styles['Normal']),
        [Paragraph('Under the <strong><i>Biodiversity Conservation Act 2016 s204(2) (a), (b), (d)*</i></strong>, I direct you to - #<br />', styles['Normal']),
         Spacer(0, 20*mm),
         Paragraph('Under the <strong><i>Biodiversity Conservation Act 2016 s205(2)</i></strong>, I direct you to - #', styles['Normal']),
         Spacer(0, 20*mm),
         ],
        '',
    ])
    data.append([
        Paragraph('<strong>Warning</strong>', styles['Normal']),
        Paragraph('<strong>If you do not obey this direction you may be liable to a fine of $10,000.00.</strong>', styles['Normal']),
        '',
    ])
    data.append([
        Paragraph('<strong>Issuing officer’s signature and details</strong>', styles['Normal']),
        [
            Paragraph('I issue this direction on this date and at this time Date:' + date_str + '<br />' + gap(77) + 'Time:' + gap(10) + 'am / pm', styles['Normal']),
            Paragraph('Name and AO Number:', styles['Normal']),
            Paragraph('Signature', styles['Normal']),
            Paragraph('District/Region:', styles['Normal']),
            Spacer(0, 3 * mm),
        ],
        '',
    ])
    data.append([
        Paragraph('<strong>Witnessing officer</strong>', styles['Normal']),
        [
            Paragraph('Name and AO Number:', styles['Normal']),
            Paragraph('Signature', styles['Normal']),
            Paragraph('District/Region:', styles['Normal']),
            Spacer(0, 3 * mm),
        ],
        '',
    ])
    data.append([
        Paragraph('<strong>Recipient\'s signature [Optional]</strong>', styles['Normal']),
        Paragraph('I acknowledge receiving this direction. I understand what it says', styles['Normal']),
        ''
    ])
    t1 = Table(data, style=invoice_table_style, colWidths=col_width, )

    # Table 2
    col_width = [30*mm, 150*mm, ]
    col_width_internal = [15*mm, 130*mm, ]
    invoice_table_style = TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('BACKGROUND', (0, 0), (1, 0), (0.8, 0.8, 0.8)),
        ('SPAN', (0, 0), (1, 0)),
        ('SPAN', (0, 1), (1, 1)),
        ('BACKGROUND', (0, 5), (1, 5), (0.8, 0.8, 0.8)),
        ('SPAN', (0, 5), (1, 5)),
        ('SPAN', (0, 6), (1, 6)),
    ])
    data = []
    data.append([
        Paragraph('<strong>Section 204 - Obtaining records:</strong>', styles['Centre']),
        '',
    ])
    data.append([
        Paragraph('For inspection purposes a wildlife officer may do one or more of the following -', styles['Centre']),
        '',
    ])
    tbl_style_internal = TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
    ])
    data.append([
        Paragraph('s204(2)(a)', styles['Normal']),
        Table([[
            Paragraph('a)', styles['Right']),
            Paragraph('direct a person who has the custody or control of a record to give the wildlife officer the record or a copy of it;', styles['Normal']),
        ]], style=tbl_style_internal, colWidths=col_width_internal),
    ])
    data.append([
        Paragraph('s204(2)(b)', styles['Normal']),
        Table([[
            Paragraph('b)', styles['Right']),
            Paragraph('direct a person who has the custody or control of a record, computer or thing to make or print out a copy of the record or to operate the computer or thing;', styles['Normal']),
        ]], style=tbl_style_internal, colWidths=col_width_internal),
    ])
    data.append([
        Paragraph('s204(2)(d)', styles['Normal']),
        Table([[
            Paragraph('d)', styles['Right']),
            Paragraph('direct a person who is or appears to be in control of a record that the wildlife officer reasonably suspects is a relevant record to give the wildlife officer a translation, code, password or other information necessary to gain access to or interpret and understand the record.', styles['Normal']),
        ]], style=tbl_style_internal, colWidths=col_width_internal),
    ])
    data.append([
        Paragraph('<strong>Section 205 - Directions</strong>', styles['Centre']),
        '',
    ])
    data.append([
        Paragraph('A wildlife officer may do one or more of the following -', styles['Centre']),
        '',
    ])
    data.append([
        Paragraph('s205(2)(a)(i)<br />s205(2)(a)(ii)', styles['Normal']),
        [ Paragraph('For inspection purposes direct an occupier of a place or vehicle, or a person who is or appears to be in possession or control of a thing, to give to the wildlife officer, orally or in writing -', styles['Normal']),
            Table([
                [
                    Paragraph('(i)', styles['Right']),
                    Paragraph(
                        'any information in the person’s possession or control as to the name and address of the owner of the place, vehicle or thing; and',
                        styles['Normal']),
                ],
                [
                    Paragraph('(ii)', styles['Right']),
                    Paragraph(
                        'any other information in the person’s possession or control that is relevant to an inspection',
                        styles['Normal']),
                ],
            ], style=tbl_style_internal, colWidths=col_width_internal),
        ],
    ])
    data.append([
        Paragraph('s205(2)(b)', styles['Normal']),
        Paragraph('For inspection purposes direct a person who is or appears to be in possession or control of an organism or potential carrier to give the wildlife officer any information in the person’s possession or control as to the name and address of any person from whom the organism or potential carrier or to whom a similar organism or potential carrier has been supplied;', styles['Normal']),
    ])
    data.append([
        Paragraph('s205(2)(c)', styles['Normal']),
        Paragraph('For inspection purposes direct an occupier of a place or vehicle to answer questions;', styles['Normal']),
    ])
    data.append([
        Paragraph('s205(2)(d)', styles['Normal']),
        Paragraph('For inspection purposes direct an occupier of a place or vehicle to produce a specified thing or a thing of a specified kind;', styles['Normal']),
    ])
    data.append([
        Paragraph('s205(2)(e)', styles['Normal']),
        Paragraph('For inspection purposes direct an occupier of a place or vehicle to open or unlock any thing in or on the place or vehicle to which the wildlife officer requires access;', styles['Normal']),
    ])
    data.append([
        Paragraph('s205(2)(f)', styles['Normal']),
        Paragraph('Direct an occupier of a place or vehicle to give the wildlife officer a plan, or access to a plan, of the place or vehicle;', styles['Normal']),
    ])
    data.append([
        Paragraph('s205(2)(g)', styles['Normal']),
        Paragraph('Direct an occupier of a place or vehicle, or a person who is or appears to be in possession or control of a thing, to give the wildlife officer any assistance that the wildlife officer reasonably needs to carry out the wildlife officer’s functions in relation to the place, vehicle or thing;', styles['Normal']),
    ])
    data.append([
        Paragraph('s205(2)(h)', styles['Normal']),
        Paragraph('Direct an occupier of a vehicle to move the vehicle to a specified place for inspection or treatment;', styles['Normal']),
    ])
    data.append([
        Paragraph('s205(2)(i)', styles['Normal']),
        Paragraph('direct a person who is or could be carrying an organism or potential carrier to go to a specified place for inspection or treatment;', styles['Normal']),
    ])
    data.append([
        Paragraph('s205(2)(j)', styles['Normal']),
        Paragraph('Direct a person who is or appears to be in control of a consignment of goods or a potential carrier to move the consignment or potential carrier to a specified place for inspection or treatment;', styles['Normal']),
    ])
    data.append([
        Paragraph('s205(2)(k)', styles['Normal']),
        Paragraph('Direct a person who is or appears to be in control of an organism to do anything necessary to identify the organism;', styles['Normal']),
    ])
    data.append([
        Paragraph('s205(2)(l)', styles['Normal']),
        Paragraph('Direct a person who is or appears to be in control of an animal to restrain, muster, round up, yard, draft or otherwise move or handle the animal or to remove the animal to a specified place for inspection or treatment;', styles['Normal']),
    ])
    data.append([
        Paragraph('s205(2)(m)', styles['Normal']),
        Paragraph('Direct a person who is or appears to be in control of any goods, vehicle, package or container to label it;', styles['Normal']),
    ])
    data.append([
        Paragraph('s205(2)(n)', styles['Normal']),
        Paragraph('Direct a person who is or appears to be in control of an organism, potential carrier or other thing prohibited, controlled, regulated or managed under this Act to keep that organism, potential carrier or other thing in the possession of that person until further directed by the wildlife officer;', styles['Normal']),
    ])
    data.append([
        Paragraph('s205(2)(o)', styles['Normal']),
        Paragraph('Direct a person who is or appears to be in control of an organism, potential carrier or other thing prohibited, controlled, regulated or managed under this Act to leave that organism, potential carrier or other thing at a specified place until further directed by the wildlife officer.', styles['Normal']),
    ])
    t2 = Table(data, style=invoice_table_style, colWidths=col_width, )


    # Append tables to the elements to build
    elements = []
    elements.append(dbca_logo)
    elements.append(Spacer(0, 5*mm))
    elements.append(t1)
    elements.append(PageBreak())
    elements.append(Spacer(0, 10*mm))
    elements.append(t2)

    doc.build(elements)
    return invoice_buffer


def gap(num):
    ret = ''
    for i in range(num):
        ret = ret + '&nbsp;'
    return ret


def create_letter_of_advice_pdf_bytes(filename, sanction_outcome):
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

