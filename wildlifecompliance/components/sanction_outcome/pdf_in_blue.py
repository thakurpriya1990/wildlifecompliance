# -*- coding: utf-8 -*-
import os

from decimal import Decimal as D
from io import BytesIO

from django.core.files.storage import default_storage
from oscar.templatetags.currency_filters import currency
from reportlab.lib import enums
from reportlab.lib.colors import Color
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


class FlowableRect(Flowable):
    def __init__(self, width, height):
        Flowable.__init__(self)
        self.width = width
        self.height = height

    def draw(self):
        self.canv.setFont('Times-Roman', 12)
        self.canv.drawString(0, 5, 'Is this a 2nd or subsequent offence? Yes')
        self.canv.rect(197, 4, self.width, self.height, fill=0)
        self.canv.drawString(220, 5, 'No')
        self.canv.rect(237, 4, self.width, self.height, fill=0)

    def wrap(self, *args):
        return 0, 18


class SolidLine(Flowable):

    def __init__(self, width, height=0):
        Flowable.__init__(self)
        self.width = width
        self.height = height

    def wrap(self, *args):
        return 0, 25

    def __repr__(self):
        return 'Line {}'.format(self.width)

    def draw(self):
        self.canv.line(5, self.height + 5, self.width, self.height + 5)


class BrokenLine(Flowable):

    def __init__(self, width, height=0):
        Flowable.__init__(self)
        self.width = width
        self.height = height

    def __repr__(self):
        return 'Line {}'.format(self.width)

    def draw(self):
        self.canv.setDash(3,3)
        self.canv.line(0, self.height, self.width, self.height)
        # f = self.canv.getAvailableFonts()
        # pass


def _create_pdf(invoice_buffer, sanction_outcome):
    every_page_frame = Frame(PAGE_MARGIN, PAGE_MARGIN, PAGE_WIDTH - 2 * PAGE_MARGIN, PAGE_HEIGHT - 2 * PAGE_MARGIN, id='EveryPagesFrame', showBoundary=Color(0, 1, 0))
    every_page_frame2 = Frame(PAGE_MARGIN, PAGE_MARGIN, PAGE_WIDTH - 2 * PAGE_MARGIN, PAGE_HEIGHT - 2 * PAGE_MARGIN, id='EveryPagesFrame2', showBoundary=Color(0, 0, 1))
    # every_page_template = PageTemplate(id='EveryPages', frames=[every_page_frame,], onPage=_create_header)
    every_page_template = PageTemplate(id='EveryPages', frames=[every_page_frame,], )
    every_page_template2 = PageTemplate(id='EveryPages2', frames=[every_page_frame2,], )
    doc = BaseDocTemplate(invoice_buffer, pageTemplates=[every_page_template, every_page_template2,], pagesize=A4,)  # showBoundary=Color(1, 0, 0))

    col_width = [40*mm, 60*mm, 80*mm,]

    # SPAN (col, row)
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
        ('SPAN', (0, 8), (0, 11)),
        ('SPAN', (1, 8), (2, 8)),
        ('SPAN', (1, 9), (2, 9)),
        ('SPAN', (1, 10), (2, 10)),
        ('SPAN', (1, 11), (2, 11)),

        # Officer issuing notice
        ('SPAN', (0, 12), (0, 14)),
        ('SPAN', (1, 12), (2, 12)),
        ('SPAN', (1, 13), (2, 13)),
        ('SPAN', (1, 14), (2, 14)),

        # Date
        ('SPAN', (1, 15), (2, 15)),
    ])

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


    date_str = gap(10) + '/' + gap(10) + '/ 20'
    rect = FlowableRect(10, 10)

    styles = StyleSheet1()
    styles.add(ParagraphStyle(name='Normal',
                              fontName='Times-Roman',
                              fontSize=12,
                              spaceBefore=7,  # space before paragraph
                              spaceAfter=7,   # space after paragraph
                              leading=16))       # space between lines
    styles.add(ParagraphStyle(name='BodyText',
                              parent=styles['Normal'],
                              spaceBefore=6))
    styles.add(ParagraphStyle(name='Italic',
                              parent=styles['BodyText'],
                              fontName='Times-Italic'))
    styles.add(ParagraphStyle(name='Bold',
                              parent=styles['BodyText'],
                              fontName='Times-Bold'))
    # styles = getSampleStyleSheet()
    data = []
    data.append([Paragraph('<i>Biodiversity Conservation Act 2016</i><br /><strong>Infringement Notice</strong>', styles['Normal']),
              '',
              Paragraph(u'Infringement<br />notice no. <font face="Helvetica"><strong>' + sanction_outcome.lodgement_number + u'</strong></font>', styles['Normal'])])

    # Alleged offender
    data.append([Paragraph('Alleged offender', styles['Bold']), Paragraph('Name: Family name', styles['Normal']), ''])
    data.append(['', Paragraph(gap(12) + 'Given names', styles['Normal']), ''])
    data.append(['', Paragraph(gap(12) + 'Date of Birth', styles['Normal']), ''])
    data.append(['', [Paragraph('<strong>or</strong><br />Body corporate name', styles['Normal']), Spacer(1, 25)], ''])
    data.append(['', [Paragraph('Address', styles['Normal']), Spacer(1, 25), Paragraph('Postcode', styles['Normal'])], ''])

    # When
    data.append([Paragraph('When', styles['Bold']), Paragraph('Date' + date_str + gap(5) + 'Time' + gap(10) + 'am/pm', styles['Normal']), ''])

    # Where
    data.append([Paragraph('Where', styles['Bold']), [Paragraph('Location of offence', styles['Normal']), Spacer(1, 25)], ''])

    # Alleged offence
    data.append([Paragraph('Alleged offence', styles['Bold']),
                 [
                     Paragraph('Description of offence', styles['Normal']),
                     SolidLine(370, 0),
                     SolidLine(370, 0),
                     SolidLine(370, 0),
                     SolidLine(370, 0),
                     SolidLine(370, 0),
                 ],
                 ''])  # row index: 8
    # data.append(['', rect, ''])
    data.append(['', rect, ''])
    data.append(['', [Paragraph('Biodiversity Conservation Act 2016 s.', styles['Normal']),
                      Paragraph('or', styles['Normal']),
                      Paragraph('Biodiversity Conservation Regulations 2018 r.', styles['Normal'])], ''])
    data.append(['', Paragraph('Modified penalty: $', styles['Normal']), ''])

    # Officer issuing notice
    data.append([Paragraph('Officer issuing notice', styles['Bold']), Paragraph('Name', styles['Normal']), ''])  # row index: 12
    data.append(['', Paragraph('Signature', styles['Normal']), ''])
    data.append(['', Paragraph('Officer no.', styles['Normal']), ''])

    # Date
    data.append([Paragraph('Date', styles['Bold']), Paragraph('Date of notice:' + date_str, styles['Normal']), ''])

    # Create 1st table
    t1 = Table(data, style=invoice_table_style, colWidths=col_width)

    data_tbl2 = []
    # Notice to alleged offender  (1)
    body = []
    body.append(Paragraph('It is alleged that you have committed the above offence.</p>', styles['Normal']))
    body.append(Paragraph('If you do not want to be prosecuted in court for the offence, pay the modified penalty within 28 days after the date of this notice.', styles['Normal']))
    body.append(Paragraph('How to pay', styles['Bold']))
    body.append(Paragraph('<strong>By post:</strong>Send a cheque or money order (payable to ‘Approved Officer — Biodiversity Conservation Act 2016’) to:', styles['Normal']))
    body.append(Paragraph('Approved Officer — Biodiversity Conservation Act 2016<br />Department of Biodiversity, Conservation and Attractions<br />Locked Bag 104<br />Bentley Delivery Centre WA 6983', styles['Normal']))
    body.append(Spacer(1, 10))
    body.append(Paragraph('<strong>In person:</strong> Pay the cashier at any office of the Department of Biodiversity, Conservation and Attractions, or pay over the telephone by credit card by calling the general telephone number of any office of the Department of Biodiversity, Conservation and Attractions.', styles['Normal']))
    data_tbl2.append([Paragraph('Notice to alleged offender', styles['Bold']), body, ''])

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
    t2 = Table(data_tbl2, style=invoice_table_style2, colWidths=col_width)

    elements = []
    # elements.append(NextPageTemplate('EveryPages2'))
    elements.append(t1)
    elements.append(PageBreak())
    elements.append(t2)

    doc.build(elements)
    return invoice_buffer


def gap(num):
    ret = ''
    for i in range(num):
        ret = ret + '&nbsp;'
    return ret


def create_in_pdf_bytes(filename, sanction_outcome):
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


