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
    KeepTogether, PageBreak, Flowable, NextPageTemplate, FrameBreak
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

#DPAW_HEADER_LOGO = os.path.join(settings.BASE_DIR, 'ledger', 'payments','static', 'payments', 'img','dbca_logo.jpg')
#DPAW_HEADER_LOGO_SM = os.path.join(settings.BASE_DIR, 'ledger', 'payments','static', 'payments', 'img','dbca_logo_small.png')
#BPAY_LOGO = os.path.join(settings.BASE_DIR, 'ledger', 'payments','static', 'payments', 'img', 'BPAY_2012_PORT_BLUE.png')
DPAW_HEADER_LOGO = os.path.join(settings.BASE_DIR, 'staticfiles', 'payments', 'img','dbca_logo.jpg')
DPAW_HEADER_LOGO_SM = os.path.join(settings.BASE_DIR, 'staticfiles', 'payments', 'img','dbca_logo_small.png')
BPAY_LOGO = os.path.join(settings.BASE_DIR, 'staticfiles', 'payments', 'img', 'BPAY_2012_PORT_BLUE.png')

HEADER_MARGIN = 10
HEADER_SMALL_BUFFER = 3

PAGE_MARGIN = 20 * mm

PAGE_WIDTH, PAGE_HEIGHT = A4

DEFAULT_FONTNAME = 'Helvetica'
BOLD_FONTNAME = 'Helvetica-Bold'

VERY_LARGE_FONTSIZE = 14
LARGE_FONTSIZE = 12
MEDIUM_FONTSIZE = 10
SMALL_FONTSIZE = 8

PARAGRAPH_BOTTOM_MARGIN = 5

SECTION_BUFFER_HEIGHT = 10

DATE_FORMAT = '%d/%m/%Y'

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name='InfoTitleLargeCenter', fontName=BOLD_FONTNAME, fontSize=LARGE_FONTSIZE,
                          spaceAfter=PARAGRAPH_BOTTOM_MARGIN, alignment=enums.TA_CENTER))
styles.add(ParagraphStyle(name='InfoTitleVeryLargeCenter', fontName=BOLD_FONTNAME, fontSize=VERY_LARGE_FONTSIZE,
                          spaceAfter=PARAGRAPH_BOTTOM_MARGIN * 2, alignment=enums.TA_CENTER))
styles.add(ParagraphStyle(name='InfoTitleLargeLeft', fontName=BOLD_FONTNAME, fontSize=LARGE_FONTSIZE,
                          spaceAfter=PARAGRAPH_BOTTOM_MARGIN, alignment=enums.TA_LEFT,
                          leftIndent=PAGE_WIDTH / 10, rightIndent=PAGE_WIDTH / 10))
styles.add(ParagraphStyle(name='InfoTitleLargeRight', fontName=BOLD_FONTNAME, fontSize=LARGE_FONTSIZE,
                          spaceAfter=PARAGRAPH_BOTTOM_MARGIN, alignment=enums.TA_RIGHT,
                          rightIndent=PAGE_WIDTH / 10))
styles.add(ParagraphStyle(name='BoldLeft', fontName=BOLD_FONTNAME, fontSize=MEDIUM_FONTSIZE, alignment=enums.TA_LEFT))
styles.add(ParagraphStyle(name='BoldRight', fontName=BOLD_FONTNAME, fontSize=MEDIUM_FONTSIZE, alignment=enums.TA_RIGHT))
styles.add(ParagraphStyle(name='Center', alignment=enums.TA_CENTER))
styles.add(ParagraphStyle(name='Left', alignment=enums.TA_LEFT))
styles.add(ParagraphStyle(name='Right', alignment=enums.TA_RIGHT))
styles.add(ParagraphStyle(name='LongString', alignment=enums.TA_LEFT,wordWrap='CJK'))


def _create_pdf(invoice_buffer, sanction_outcome):
    every_page_frame = Frame(PAGE_MARGIN, PAGE_MARGIN, PAGE_WIDTH - 2 * PAGE_MARGIN, PAGE_HEIGHT - 2 * PAGE_MARGIN, id='EveryPagesFrame', showBoundary=Color(0, 1, 0))
    every_page_template = PageTemplate(id='EveryPages', frames=[every_page_frame,], )
    doc = BaseDocTemplate(invoice_buffer, pageTemplates=[every_page_template, ], pagesize=A4,)  # showBoundary=Color(1, 0, 0))

    # Common
    col_width_details = [25*mm, 25*mm, 71*mm, 25*mm, 40*mm]

    styles = StyleSheet1()
    styles.add(ParagraphStyle(name='Normal',
                              fontName='Helvetica',
                              fontSize=9,
                              spaceBefore=7,  # space before paragraph
                              spaceAfter=7,   # space after paragraph
                              leading=12))       # space between lines
    styles.add(ParagraphStyle(name='BodyText',
                              parent=styles['Normal'],
                              spaceBefore=6))
    styles.add(ParagraphStyle(name='Italic',
                              parent=styles['BodyText'],
                              fontName='Times-Italic'))
    styles.add(ParagraphStyle(name='Bold',
                              parent=styles['BodyText'],
                              fontName='Times-Bold'))
    styles.add(ParagraphStyle(name='Right',
                              parent=styles['BodyText'],
                              alignment=TA_RIGHT))
    styles.add(ParagraphStyle(name='Centre',
                              parent=styles['BodyText'],
                              alignment=TA_CENTER))

    # Head (col, row)
    invoice_table_style = TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0, colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
    ])
    style_tbl_left = TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
    ])
    style_tbl_right = TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
    ])
    col_width_head = [85*mm, 20*mm, 85*mm,]
    data_left = Table([[Paragraph('MAGISTRATES COURT of WESTERN<br />'
                          'AUSTRALIA<br />'
                          '<strong>PROSECUTION NOTICE</strong><br />'
                          '<i>Criminal Procedure Act 2004</i><br />'
                          'Criminal Procedure Regulations 2005 - Form 3', styles['Centre']),]], style=style_tbl_left)
    data_right = Table([
        [Paragraph('Court number', styles['Normal']), ''],
        [Paragraph('Magistrates court at', styles['Normal']), ''],
        [Paragraph('Date lodged', styles['Normal']), ''],
    ], style=style_tbl_right, rowHeights=[7.5*mm, 7.5*mm, 7.5*mm,])
    tbl_head = Table([[data_left, '', data_right]], style=invoice_table_style, colWidths=col_width_head, )

    # Details of alleged offence
    style_tbl_details = TableStyle([
        ('VALIGN', (0, 0), (0, 0), 'TOP'),
        ('VALIGN', (1, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('SPAN', (0, 0), (0, 4)),
        ('SPAN', (2, 0), (4, 0)),
        ('SPAN', (2, 1), (4, 1)),
        ('SPAN', (2, 2), (4, 2)),
        ('SPAN', (2, 3), (4, 3)),
        ('SPAN', (2, 4), (4, 4)),
    ])
    data = []
    data.append([
        Paragraph('<strong>Details of alleged offence</strong><br /><i>[This description must comply with the CPA Schedule 1 clause 5.]</i>', styles['Normal']),
        Paragraph('Accused', styles['Normal']),
        '',
        '',
        '',
    ])
    data.append(['', Paragraph('Date or period', styles['Normal']), '', '', ''])
    data.append(['', Paragraph('Place', styles['Normal']), '', '', ''])
    data.append(['', Paragraph('Description', styles['Normal']), '', '', ''])
    data.append(['', Paragraph('Written law', styles['Normal']), '', '', ''])
    tbl_details = Table(data, style=style_tbl_details, colWidths=col_width_details)

    # Notice to accused
    style_tbl_notice = TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('SPAN', (1, 0), (4, 0)),
    ])
    data = []
    data.append([
        Paragraph('<strong>Notice to accused</strong>', styles['Normal']),
        Paragraph('You are charged with the offence described above, or the offences described in any attachment to this notice. The charge(s) will be dealt with by the above court.', styles['Normal']),
        '',
        '',
        '',
    ])
    tbl_notice = Table(data, style=style_tbl_notice, colWidths=col_width_details)

    # Accused's Details
    style_tbl_accused = TableStyle([
        ('VALIGN', (0, 0), (0, -1), 'TOP'),
        ('VALIGN', (1, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('SPAN', (0, 0), (0, 2)),
        ('SPAN', (1, 0), (4, 0)),
        ('SPAN', (3, 1), (4, 1)),
        ('SPAN', (2, 2), (4, 2)),
    ])
    data = []
    data.append([
        Paragraph('<strong>Accused\'s Details</strong>', styles['Normal']),
        Paragraph('<i>[This description must comply with the CPA Schedule 1 clause 4.]</i>', styles['Normal']),
        '',
        '',
        '',
    ])
    data.append([
        '',
        Paragraph('Date of Birth', styles['Normal']),
        '',
        Paragraph('Male / Female', styles['Normal']),
        '',
    ])
    data.append([
        '',
        Paragraph('Address', styles['Normal']),
        '',
        '',
        '',
    ])
    tbl_accused = Table(data, style=style_tbl_accused, colWidths=col_width_details)

    # Prosecutor
    style_tbl_prosecutor = TableStyle([
        ('VALIGN', (0, 0), (0, -1), 'TOP'),
        ('VALIGN', (1, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (2, 6), (-1, 6), 'BOTTOM'),
        ('SPAN', (0, 0), (0, 1)),  # col: Prosecutor
        ('SPAN', (0, 2), (0, 6)),  # col: Person issuing this notice
        ('SPAN', (1, 5), (1, 6)),  # col: Witness's signature
        ('SPAN', (1, 0), (4, 0)),
        ('SPAN', (1, 1), (4, 1)),
        ('SPAN', (2, 4), (4, 4)),
        ('SPAN', (2, 5), (4, 5)),
        ('SPAN', (2, 6), (4, 6)),
        ('SPAN', (1, 7), (4, 7)),
    ])
    data = []
    data.append([
        Paragraph('<strong>Prosecutor</strong>', styles['Normal']),
        Paragraph('<i>[Identify the prosecutor in accordance with the CPA Schedule 1 clause 3.]</i>', styles['Normal']),
        '',
        '',
        '',
    ])
    data.append([
        '',
        '',
        '',
        '',
        '',
    ])
    data.append([
        Paragraph('<strong>Person issuing this notice</strong>', styles['Normal']),
        Paragraph('Full name', styles['Normal']),
        '',
        Paragraph('official title', styles['Normal']),
        '',
    ])
    data.append([
        '',
        Paragraph('Work address', styles['Normal']),
        '',
        Paragraph('Work telephone', styles['Normal']),
        '',
    ])
    data.append([
        '',
        Paragraph('Signature', styles['Normal']),
        '',
        '',
        '',
    ])
    data.append([
        '',
        Paragraph('Witness\'s Signature', styles['Normal']),
        Paragraph('<i>[A witness may not be needed. See the CPA section 23.]</i>', styles['Normal']),
        '',
        '',
    ])
    data.append([
        '',
        '',
        Paragraph('Justice of the Peace or Prescribed Court Officer', styles['Normal']),
        '',
        '',
    ])
    data.append([
        Paragraph('<strong>Date</strong>', styles['Normal']),
        Paragraph('This prosecution notice is signed on', styles['Normal']),
        '',
        '',
        '',
    ])
    tbl_prosecutor = Table(data, style=style_tbl_prosecutor, colWidths=col_width_details)

    # Append tables to the elements to build
    gap_between_tables = 1.5*mm
    elements = []
    elements.append(tbl_head)
    elements.append(tbl_details)
    elements.append(Spacer(0, gap_between_tables))
    elements.append(tbl_notice)
    elements.append(Spacer(0, gap_between_tables))
    elements.append(tbl_accused)
    elements.append(Spacer(0, gap_between_tables))
    elements.append(tbl_prosecutor)
    doc.build(elements)
    return invoice_buffer


def gap(num):
    ret = ''
    for i in range(num):
        ret = ret + '&nbsp;'
    return ret


def create_prosecution_notice_pdf_bytes(filename, sanction_outcome):
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


