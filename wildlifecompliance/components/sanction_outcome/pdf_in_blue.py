# -*- coding: utf-8 -*-
import os

from decimal import Decimal as D
from io import BytesIO

from django.core.files.storage import default_storage
from oscar.templatetags.currency_filters import currency
from reportlab.lib import enums
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

PAGE_MARGIN = 30
PAGE_TOP_MARGIN = 200

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


# class Remittance(Flowable):
#     def __init__(self,current_x,current_y,invoice):
#         Flowable.__init__(self)
#         self.current_x = current_x
#         self.current_y = current_y
#         self.invoice = invoice
#
#     def __repr__(self):
#         return 'remittance'
#
#     def __logo_line(self):
#         canvas = self.canv
#         current_y, current_x = self.current_y, self.current_x
#         canvas.setFont(DEFAULT_FONTNAME, MEDIUM_FONTSIZE)
#         dpaw_header_logo = ImageReader(DPAW_HEADER_LOGO_SM)
#
#         dpaw_header_logo_size = dpaw_header_logo.getSize()
#         canvas.drawImage(dpaw_header_logo, HEADER_MARGIN, current_y - (dpaw_header_logo_size[1]/1.8),height=dpaw_header_logo_size[1]/1.8, mask='auto', width=dpaw_header_logo_size[0]/1.8)
#
#         current_y = -20
#         canvas.setFont(BOLD_FONTNAME, MEDIUM_FONTSIZE)
#         canvas.drawRightString(current_x * 45,current_y,'Remittance Advice')
#
#         current_y -= 20
#         canvas.setFont(DEFAULT_FONTNAME, MEDIUM_FONTSIZE)
#         canvas.drawString(current_x * 27,current_y,'PLEASE DETACH AND RETURN WITH YOUR PAYMENT')
#
#         current_y -= 20
#         canvas.setFont(DEFAULT_FONTNAME, MEDIUM_FONTSIZE)
#         canvas.drawString(current_x, current_y, 'ABN: 38 052 249 024')
#         self.current_y = current_y
#
#     def __payment_line(self):
#         canvas = self.canv
#         current_y, current_x = self.current_y, self.current_x
#         bpay_logo = ImageReader(BPAY_LOGO)
#         #current_y -= 40
#         # Pay By Cheque
#         cheque_x = current_x + 4 * inch
#         cheque_y = current_y -30
#         canvas.setFont(BOLD_FONTNAME, MEDIUM_FONTSIZE)
#         canvas.drawString(cheque_x, cheque_y, 'Pay By Cheque:')
#         canvas.setFont(DEFAULT_FONTNAME, 9)
#         cheque_y -= 15
#         canvas.drawString(cheque_x, cheque_y, 'Make cheque payable to: Department of Biodiversity, Conservation and Attractions')
#         cheque_y -= 15
#         canvas.drawString(cheque_x, cheque_y, 'Mail to: Department of Biodiversity, Conservation and Attractions')
#         cheque_y -= 15
#         canvas.drawString(cheque_x + 32, cheque_y, 'Locked Bag 30')
#         cheque_y -= 15
#         canvas.drawString(cheque_x + 32, cheque_y, 'Bentley Delivery Centre WA 6983')
#         if settings.BPAY_ALLOWED:
#             # Outer BPAY Box
#             canvas.rect(current_x,current_y - 25,2.3*inch,-1.2*inch)
#             canvas.setFillColorCMYK(0.8829,0.6126,0.0000,0.5647)
#             # Move into bpay box
#             current_y += 5
#             box_pos = current_x + 0.1 * inch
#             bpay_logo_size = bpay_logo.getSize()
#             canvas.drawImage(bpay_logo, box_pos, current_y - (bpay_logo_size[1]/12 * 1.7), height= bpay_logo_size[1]/12,width=bpay_logo_size[0]/12, mask='auto')
#             # Create biller information box
#             biller_x = box_pos + bpay_logo_size[0]/12 + 1
#             canvas.rect(biller_x,(current_y - (bpay_logo_size[1]/12 * 1.7)) + 3,1.65*inch,(bpay_logo_size[1]/12)-5)
#             # Bpay info
#             canvas.setFont(BOLD_FONTNAME, MEDIUM_FONTSIZE)
#             info_y = ((current_y - (bpay_logo_size[1]/12 * 1.7)) + 3) + (0.35 * inch)
#             canvas.drawString(biller_x + 5, info_y, 'Biller Code: {}'.format(self.invoice.biller_code))
#             canvas.drawString(biller_x + 5, info_y - 20, 'Ref: {}'.format(self.invoice.reference))
#             # Bpay Info string
#             canvas.setFont(BOLD_FONTNAME,SMALL_FONTSIZE)
#             canvas.drawString(box_pos, info_y - 0.55 * inch, 'Telephone & Internet Banking - BPAY')
#             canvas.setFont(DEFAULT_FONTNAME,6.5)
#             canvas.drawString(box_pos, info_y - 0.65 * inch, 'Contact your bank or financial institution to make')
#             canvas.drawString(box_pos, info_y - 0.75 * inch, 'this payment from your cheque, savings, debit or')
#             canvas.drawString(box_pos, info_y - 0.85 * inch, 'transaction account. More info: www.bpay.com.au')
#
#         self.current_y = current_y
#
#     def __footer_line(self):
#         canvas = self.canv
#         current_y, current_x = self.current_y, self.current_x
#         current_y -= 2 * inch
#         canvas.setFont(DEFAULT_FONTNAME, LARGE_FONTSIZE)
#         canvas.setFillColor(colors.black)
#         canvas.drawString(current_x, current_y, 'Invoice Number')
#         canvas.drawString(PAGE_WIDTH/4, current_y, 'Invoice Date')
#         canvas.drawString((PAGE_WIDTH/4) * 2, current_y, 'GST included')
#         canvas.drawString((PAGE_WIDTH/4) * 3, current_y, 'Invoice Total')
#         current_y -= 20
#         canvas.setFont(DEFAULT_FONTNAME, MEDIUM_FONTSIZE)
#         # canvas.drawString(current_x, current_y, self.invoice.reference)
#         # canvas.drawString(PAGE_WIDTH/4, current_y, self.invoice.created.strftime(DATE_FORMAT))
#         # canvas.drawString((PAGE_WIDTH/4) * 2, current_y, currency(self.invoice.amount - calculate_excl_gst(self.invoice.amount)))
#         # canvas.drawString((PAGE_WIDTH/4) * 3, current_y, currency(self.invoice.amount))
#
#     def draw(self):
#         if settings.BPAY_ALLOWED:
#             self.__logo_line()
#             self.__payment_line()
#         self.__footer_line()


# def _create_header(canvas, doc, draw_page_number=True):
#     canvas.saveState()
#     canvas.setTitle('Invoice')
#     canvas.setFont(BOLD_FONTNAME, LARGE_FONTSIZE)
#
#     current_y = PAGE_HEIGHT - HEADER_MARGIN
#
#     dpaw_header_logo = ImageReader(DPAW_HEADER_LOGO)
#     dpaw_header_logo_size = dpaw_header_logo.getSize()
#     canvas.drawImage(dpaw_header_logo, PAGE_WIDTH / 3, current_y - (dpaw_header_logo_size[1]/2),width=dpaw_header_logo_size[0]/2, height=dpaw_header_logo_size[1]/2, mask='auto')
#
#     current_y -= 70
#     canvas.drawCentredString(PAGE_WIDTH / 2, current_y - LARGE_FONTSIZE, 'INFRINGEMENT NOTICE')
#
#     current_y -= 20
#     canvas.drawCentredString(PAGE_WIDTH / 2, current_y - LARGE_FONTSIZE, 'ABN: 38 052 249 024')
#
#     # Invoice address details
#     invoice_details_offset = 37
#     current_y -= 20
#     # invoice = doc.invoice
#     sanction_outcome = doc.sanction_outcome
#     canvas.setFont(BOLD_FONTNAME, SMALL_FONTSIZE)
#     current_x = PAGE_MARGIN + 5
#     canvas.drawString(current_x, current_y - (SMALL_FONTSIZE + HEADER_SMALL_BUFFER), sanction_outcome.get_offender()[0].get_full_name())
#     # canvas.drawString(current_x, current_y - (SMALL_FONTSIZE + HEADER_SMALL_BUFFER), invoice.owner.get_full_name())
#     # canvas.drawString(current_x, current_y - (SMALL_FONTSIZE + HEADER_SMALL_BUFFER) * 2,invoice.owner.username)
#     current_x += 452
#     #write Invoice details
#     canvas.drawString(current_x, current_y - (SMALL_FONTSIZE + HEADER_SMALL_BUFFER),'Date')
#     # canvas.drawString(current_x + invoice_details_offset, current_y - (SMALL_FONTSIZE + HEADER_SMALL_BUFFER),invoice.created.strftime(DATE_FORMAT))
#     canvas.drawString(current_x, current_y - (SMALL_FONTSIZE + HEADER_SMALL_BUFFER) * 2, 'Page')
#     canvas.drawString(current_x + invoice_details_offset, current_y - (SMALL_FONTSIZE + HEADER_SMALL_BUFFER) * 2, str(canvas.getPageNumber()))
#     canvas.drawRightString(current_x + 20, current_y - (SMALL_FONTSIZE + HEADER_SMALL_BUFFER) * 3, 'Invoice Number')
#     # canvas.drawString(current_x + invoice_details_offset, current_y - (SMALL_FONTSIZE + HEADER_SMALL_BUFFER) * 3, invoice.reference)
#     canvas.drawRightString(current_x + 20, current_y - (SMALL_FONTSIZE + HEADER_SMALL_BUFFER) * 4, 'Total (AUD)')
#     # canvas.drawString(current_x + invoice_details_offset, current_y - (SMALL_FONTSIZE + HEADER_SMALL_BUFFER) * 4, currency(invoice.amount))
#     canvas.drawRightString(current_x + 20, current_y - (SMALL_FONTSIZE + HEADER_SMALL_BUFFER) * 5, 'GST included (AUD)')
#     # canvas.drawString(current_x + invoice_details_offset, current_y - (SMALL_FONTSIZE + HEADER_SMALL_BUFFER) * 5, currency(invoice.amount - calculate_excl_gst(invoice.amount)))
#     canvas.drawRightString(current_x + 20, current_y - (SMALL_FONTSIZE + HEADER_SMALL_BUFFER) * 6, 'Paid (AUD)')
#     # canvas.drawString(current_x + invoice_details_offset, current_y - (SMALL_FONTSIZE + HEADER_SMALL_BUFFER) * 6, currency(invoice.payment_amount))
#     canvas.drawRightString(current_x + 20, current_y - (SMALL_FONTSIZE + HEADER_SMALL_BUFFER) * 7, 'Outstanding (AUD)')
#     # canvas.drawString(current_x + invoice_details_offset, current_y - (SMALL_FONTSIZE + HEADER_SMALL_BUFFER) * 7, currency(invoice.balance))
#     canvas.restoreState()


def _create_invoice(invoice_buffer, sanction_outcome):
    every_page_frame = Frame(PAGE_MARGIN, PAGE_MARGIN, PAGE_WIDTH - 2 * PAGE_MARGIN,
                             PAGE_HEIGHT - 2 * PAGE_MARGIN, id='EveryPagesFrame', showBoundary=0)
    # every_page_template = PageTemplate(id='EveryPages', frames=[every_page_frame,], onPage=_create_header)
    every_page_template = PageTemplate(id='EveryPages', frames=[every_page_frame,],)
    doc = BaseDocTemplate(invoice_buffer, pageTemplates=[every_page_template], pagesize=A4)

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
              Paragraph('Infringement<br />notice no.', styles['Normal'])])

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
                     Paragraph('<u>' + gap(127) + '</u>', styles['Normal']),
                     Paragraph('<u>' + gap(127) + '</u>', styles['Normal']),
                     Paragraph('<u>' + gap(127) + '</u>', styles['Normal']),
                     Paragraph('<u>' + gap(127) + '</u>', styles['Normal']),
                     Paragraph('<u>' + gap(127) + '</u>', styles['Normal']),
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
        _create_invoice(invoice_buffer, sanction_outcome)

        # Get the value of the BytesIO buffer
        value = invoice_buffer.getvalue()

        # START: Save the pdf file to the database
        document = sanction_outcome.documents.create(name=filename)
        path = default_storage.save('wildlifecompliance/{}/{}/documents/{}'.format(sanction_outcome._meta.model_name, sanction_outcome.id, filename), invoice_buffer)
        document._file = path
        document.save()
        # END: Save

        return document


