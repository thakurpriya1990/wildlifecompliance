# -*- coding: utf-8 -*-
import os

from io import BytesIO

from django.core.files.storage import default_storage
from reportlab.lib import enums
from reportlab.lib.colors import Color
from reportlab.lib.pagesizes import A4
from reportlab.platypus import BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib import colors

from django.conf import settings

#DPAW_HEADER_LOGO = os.path.join(settings.BASE_DIR, 'ledger', 'payments','static', 'payments', 'img','dbca_logo.jpg')
#DPAW_HEADER_LOGO_SM = os.path.join(settings.BASE_DIR, 'ledger', 'payments','static', 'payments', 'img','dbca_logo_small.png')
#BPAY_LOGO = os.path.join(settings.BASE_DIR, 'ledger', 'payments','static', 'payments', 'img', 'BPAY_2012_PORT_BLUE.png')
from wildlifecompliance.components.main.pdf_utils import gap, get_infringement_notice_table

DPAW_HEADER_LOGO = os.path.join(settings.BASE_DIR, 'staticfiles', 'payments', 'img','dbca_logo.jpg')
DPAW_HEADER_LOGO_SM = os.path.join(settings.BASE_DIR, 'staticfiles', 'payments', 'img','dbca_logo_small.png')
BPAY_LOGO = os.path.join(settings.BASE_DIR, 'staticfiles', 'payments', 'img', 'BPAY_2012_PORT_BLUE.png')

HEADER_MARGIN = 10
HEADER_SMALL_BUFFER = 3

PAGE_MARGIN = 20 * mm  # mm?

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
    every_page_frame = Frame(PAGE_MARGIN, PAGE_MARGIN, PAGE_WIDTH - 2 * PAGE_MARGIN, PAGE_HEIGHT - 2 * PAGE_MARGIN, id='EveryPagesFrame',)  # showBoundary=Color(0, 1, 0))
    every_page_frame2 = Frame(PAGE_MARGIN, PAGE_MARGIN, PAGE_WIDTH - 2 * PAGE_MARGIN, PAGE_HEIGHT - 2 * PAGE_MARGIN, id='EveryPagesFrame2',)  # showBoundary=Color(0, 0, 1))
    # every_page_template = PageTemplate(id='EveryPages', frames=[every_page_frame,], onPage=_create_header)
    every_page_template = PageTemplate(id='EveryPages', frames=[every_page_frame,], )
    every_page_template2 = PageTemplate(id='EveryPages2', frames=[every_page_frame2,], )
    doc = BaseDocTemplate(invoice_buffer, pageTemplates=[every_page_template, every_page_template2,], pagesize=A4,)  # showBoundary=Color(1, 0, 0))

    t1 = get_infringement_notice_table(sanction_outcome)

    data_tbl2 = []
    # Notice to alleged offender  (1)
    body = []
    body.append(Paragraph('It is alleged that you have committed the above offence.</p>', styles['Normal']))
    body.append(Paragraph('If you do not want to be prosecuted in court for the offence, pay the modified penalty within 28 days after the date of this notice.', styles['Normal']))
    body.append(Paragraph('How to pay', styles['Normal']))
    body.append(Paragraph('<strong>By post:</strong>Send a cheque or money order (payable to ‘Approved Officer — Biodiversity Conservation Act 2016’) to:', styles['Normal']))
    body.append(Paragraph('Approved Officer — Biodiversity Conservation Act 2016<br />Department of Biodiversity, Conservation and Attractions<br />Locked Bag 104<br />Bentley Delivery Centre WA 6983', styles['Normal']))
    body.append(Spacer(1, 10))
    body.append(Paragraph('<strong>In person:</strong> Pay the cashier at any office of the Department of Biodiversity, Conservation and Attractions, or pay over the telephone by credit card by calling the general telephone number of any office of the Department of Biodiversity, Conservation and Attractions.', styles['Normal']))
    data_tbl2.append([Paragraph('<strong>Notice to alleged offender</strong>', styles['Normal']), body, ''])

    # Notice to alleged offender  (2)
    body = []
    body.append(Paragraph('<strong>If you do not pay</strong> the modified penalty within 28 days, you may be prosecuted or enforcement action may be taken under the Fines, Penalties and Infringement Notices Enforcement Act 1994. Under that Act, some or all of the following action may be taken — your driver’s licence may be suspended; your vehicle licence may be suspended or cancelled; your details may be published on a website; your vehicle may be immobilised or have its number plates removed; your property may be seized and sold.', styles['Normal']))
    body.append(Spacer(1, 10))
    body.append(Paragraph('<strong>If you need more time.</strong> to pay the modified penalty, you can apply for an extension of time by writing to the Approved Officer at the above postal address.', styles['Normal']))
    data_tbl2.append(['', body, ''])

    # Notice to alleged offender  (3)
    body = []
    body.append(Paragraph('<strong>If you want this matter to be dealt with by prosecution in court</strong>, sign here <u>' + gap(80) + '</u> and post this notice to the Approved Officer at the above postal address within 28 days after the date of this notice.', styles['Normal']))
    data_tbl2.append(['', body, ''])

    # Create 2nd table
    invoice_table_style2 = TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        # Notice to alleged offender
        ('SPAN', (0, 0), (0, 2)),
        ('SPAN', (1, 0), (2, 0)),
        ('SPAN', (1, 1), (2, 1)),
        ('SPAN', (1, 2), (2, 2)),
    ])
    col_width = [40*mm, 60*mm, 80*mm,]
    t2 = Table(data_tbl2, style=invoice_table_style2, colWidths=col_width)

    elements = []
    # elements.append(NextPageTemplate('EveryPages2'))
    elements.append(t1)
    elements.append(PageBreak())
    elements.append(t2)

    doc.build(elements)
    return invoice_buffer


def create_infringement_notice_blue(filename, sanction_outcome):
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


