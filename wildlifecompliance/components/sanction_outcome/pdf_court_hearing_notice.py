# -*- coding: utf-8 -*-
import os

from decimal import Decimal as D
from io import BytesIO

from django.core.files.storage import default_storage
from ledger.payments.pdf import BrokenLine
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


PAGE_MARGIN = 5 * mm
PAGE_WIDTH, PAGE_HEIGHT = A4


class ParagraphOffeset(Paragraph, object):

    def __init__(self, text, style, bulletText=None, frags=None, caseSensitive=1, encoding='utf8', x_offset=0, y_offset=0):
        self.x_offset = x_offset
        self.y_offset = y_offset
        super(ParagraphOffeset, self).__init__(text, style, bulletText, frags, caseSensitive, encoding)

    def drawOn(self, canvas, x, y, _sW=0):
        x = x + self.x_offset
        y = y + self.y_offset
        super(ParagraphOffeset, self).drawOn(canvas, x, y, _sW)


def _create_pdf(invoice_buffer, sanction_outcome):
    every_page_frame = Frame(PAGE_MARGIN, PAGE_MARGIN, PAGE_WIDTH - 2 * PAGE_MARGIN, PAGE_HEIGHT - 2 * PAGE_MARGIN, id='EveryPagesFrame', )  #showBoundary=Color(0, 1, 0))
    every_page_template = PageTemplate(id='EveryPages', frames=[every_page_frame,], )
    doc = BaseDocTemplate(invoice_buffer, pageTemplates=[every_page_template, ], pagesize=A4,)  # showBoundary=Color(1, 0, 0))

    # Common
    col_width_head = [85*mm, 25*mm, 85*mm,]
    col_width_details = [28*mm, 28*mm, 71*mm, 23*mm, 41*mm]
    FONT_SIZE_L = 11
    FONT_SIZE_M = 10
    FONT_SIZE_S = 8

    styles = StyleSheet1()
    styles.add(ParagraphStyle(name='Normal',
                              fontName='Helvetica',
                              fontSize=FONT_SIZE_M,
                              spaceBefore=2,  # space before paragraph
                              spaceAfter=2,   # space after paragraph
                              leading=11))       # space between lines
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

    # Header small text
    header_small_text_p1 = ParagraphOffeset('<font size="' + str(FONT_SIZE_S) + '">Copy to be attached to court copy of prosecution notice</font>',
                                            styles['Right'],
                                            x_offset=-3*mm, y_offset=0)

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
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
    ])
    data_left = Table([[Paragraph('MAGISTRATES COURT of WESTERN<br />'
                          'AUSTRALIA<br />'
                          '<strong><font size="' + str(FONT_SIZE_L) + '">COURT HEARING NOTICE</font></strong><br />'
                          '<i>Criminal Procedure Act 2004</i><br />'
                          'Criminal Procedure Regulations 2005 - Form 5', styles['Centre']),]], style=style_tbl_left)
    data_right = Table([
        [Paragraph('Court number', styles['Normal']), ''],
        [Paragraph('Magistrates court at', styles['Normal']), ''],
    ], style=style_tbl_right, rowHeights=[7.8*mm, 15.6*mm, ])
    tbl_head = Table([[data_left, '', data_right]], style=invoice_table_style, colWidths=col_width_head, )

    # Accused's Details, etc
    rowHeights = [6*mm, 6*mm, 6*mm, 30*mm, 6*mm]
    style_tbl_accused_details = TableStyle([
        ('VALIGN', (0, 0), (0, 0), 'MIDDLE'),
        # ('VALIGN', (1, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('SPAN', (0, 0), (0, 1)),
        ('SPAN', (2, 0), (4, 0)),
        ('SPAN', (2, 1), (4, 1)),
    ])
    data = []
    data.append([
        Paragraph('<strong>Accused\'s Details</strong><br />', styles['Normal']),
        Paragraph('Full name', styles['Normal']),  # ,
        '', '', '',
    ])
    data.append([
        '',
        Paragraph('Address', styles['Normal']),
        '', '', '',
    ])
    tbl_accused_details = Table(data, style=style_tbl_accused_details, colWidths=col_width_details, )  # rowHeights=rowHeights)

    # Hearing details, etc
    style_tbl_hearing_details = TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('SPAN', (1, 0), (4, 0)),
        ('SPAN', (1, 2), (4, 2)),
    ])
    data = []
    data.append([
        Paragraph('<strong>Hearing details</strong>', styles['Normal']),
        Paragraph('The charge(s) in the attached prosecution notice dated [insert date]<br />will be first dealt with by the above court at the time, date and place stated below.', styles['Normal']),
        '', '', '',
    ])
    data.append([
        Paragraph('<strong>Date and time</strong>', styles['Normal']),
        Paragraph('Date', styles['Normal']),
        '',
        Paragraph('Time', styles['Normal']),
        '',
    ])
    data.append([
        Paragraph('<strong>Place</strong>', styles['Normal']),
        '', '', '', '',
    ])
    tbl_hearing_details = Table(data, style=style_tbl_hearing_details, colWidths=col_width_details, )  # rowHeights=rowHeights)

    # Notice to accused
    col_width_notice_to_accused = [28*mm, 163*mm, ]
    style_tbl_notice_to_accused = TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
    ])
    data = []
    data.append([
        Paragraph('<strong>Notice to accused</strong>', styles['Normal']),
        Paragraph('<strong>Your options are set out below. You should read them carefully.</strong><br />If you do not know what to do, you should get advice from a lawyer, the Legal Aid Commission or the Aboriginal Legal Service. If you will need an interpreter in court, please contact the court', styles['Normal']),
    ])
    data.append([
        Paragraph('<strong>Options</strong>', styles['Normal']),
        Paragraph('1. You can attend the above hearing. <br />'
                  '2. You can do nothing. <br />'
                  '3. You can plead not guilty in writing. <br />'
                  '4. You can plead guilty in writing. <br />'
                  '<strong>Options 2, 3 and 4 are explained below.</strong>', styles['Normal']),
    ])
    data.append([
        [
            Paragraph('<strong>Doing nothing</strong>', styles['Normal']),
            Spacer(0, 5*mm),
            Paragraph('<strong>[Options 2]</strong>', styles['Normal']),
        ],
        [
            Paragraph('If you do not appear at the above hearing and you do not send the court a written plea in time, the court may determine the charge(s) at the above hearing in your absence.', styles['Normal']),
            Paragraph('In some cases the court can take as proved any allegation in the attached prosecution notice without hearing evidence.', styles['Normal']),
            Paragraph('The court may decide to summons you to court or have you arrested and brought before the court.', styles['Normal']),
            Paragraph('If the court finds you guilty, it may fine you and order you to pay court costs and the prosecutor’s costs.', styles['Normal']),
        ],
    ])
    data.append([
        [
            Paragraph('<strong>Pleading not guilty in writing</strong>', styles['Normal']),
            Spacer(0, 5 * mm),
            Paragraph('<strong>[Option 3]</strong>', styles['Normal']),
        ],
        [
            Paragraph('Pleading <u>not guilty</u> to a charge in the prosecution notice means you do not admit the charge.', styles['Normal']),
            Paragraph('If you send the court a written plea of <u>not guilty</u>, you need not attend the above hearing. If the court receives your written plea in time it will send you a notice of another hearing, at which the court will deal with the charge(s) (in your absence if you are not there) and hear any evidence you wish to give and any witnesses you call.', styles['Normal']),
            Paragraph('To send the court a written plea of not guilty, fill out page 2 of this form and send page 2 to the address on it at least three days before the above hearing date.', styles['Normal']),
        ],
    ])
    data.append([
        [
            Paragraph('<strong>Pleading guilty in writing</strong>', styles['Normal']),
            Spacer(0, 5 * mm),
            Paragraph('[Option 4]', styles['Normal']),
        ],
        [
            Paragraph('Pleading <u>guilty</u> to a charge in the prosecution notice means you admit the charge.', styles['Normal']),
            Paragraph('If you send the court a written plea of <u>guilty</u>, you need not attend the above hearing unless you want to tell the court something.', styles['Normal']),
            Paragraph('If the court receives your written plea in time it will deal with the charge(s) at the above hearing (in your absence if you are not there) and may fine you and order you to pay court costs and the prosecutor’s costs.', styles['Normal']),
            Paragraph('To send the court a written plea of guilty, fill out page 2 of this form, include any written explanation or information you want the court to consider, and send it all to the address on the form at least three days before the above hearing date.', styles['Normal']),
            Paragraph('The court might not accept your plea of guilty if what you tell the court suggests you do not admit the charge. If that happens you will be notified.', styles['Normal']),
        ],
    ])
    tbl_notice_to_accused = Table(data, style=style_tbl_notice_to_accused, colWidths=col_width_notice_to_accused)

    # Issuing details
    col_width_issuing_details = col_width_notice_to_accused
    style_tbl_issuing_details = TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
    ])
    data = []
    data.append([
        Paragraph('<strong>Issuing details</strong>', styles['Normal']),
        [
            Paragraph('This notice is issued on [date]', styles['Normal']),
            Spacer(0, 8*mm),
            BrokenLine(50*mm),
            Paragraph('<i>[Title of person issuing notice]</i>', styles['Normal']),
        ]
    ])
    tbl_issuing_details = Table(data, style=style_tbl_issuing_details, colWidths=col_width_issuing_details)

    # Service details
    col_width_service_details = col_width_notice_to_accused
    style_tbl_service_details = TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('SPAN', (0, 0), (0, 1))
    ])
    data = []
    data.append([
        [
            Paragraph('<strong>Service details</strong>', styles['Normal']),
            Spacer(0, 5 * mm),
            Paragraph('[*Police only]', styles['Normal']),
        ],
        Paragraph('<i>[Service must be in one of the manners in the CPA Schedule 2 clauses 2, 3 or 4 (see s. 33(3)). Insert here whichever manner of service was used.]</i>', styles['Normal'])
    ])
    tbl_style_internal = TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ])
    data.append([
        '',
        [
            Paragraph('On' + gap(30) + '20' + gap(10) + ', the accused was served with a copy of this notice and the prosecution notice referred to above in the following manner:', styles['Normal']),
            Table([
                [Paragraph('Name of server:', styles['Normal']), Paragraph('*Registered No:', styles['Normal'])],
                [Paragraph('Signature:', styles['Normal']), Paragraph(gap(1) + 'Station:', styles['Normal'])],
            ], style=tbl_style_internal, rowHeights=[8*mm, 8*mm, ])
        ]
    ])
    tbl_service_details = Table(data, style=style_tbl_service_details, colWidths=col_width_service_details)

    gap_between_tables = 1.5*mm
    elements = []
    elements.append(header_small_text_p1)
    elements.append(tbl_head)
    elements.append(tbl_accused_details)
    elements.append(Spacer(0, gap_between_tables))
    elements.append(tbl_hearing_details)
    elements.append(Spacer(0, gap_between_tables))
    elements.append(tbl_notice_to_accused)
    elements.append(Spacer(0, gap_between_tables))
    elements.append(tbl_issuing_details)
    elements.append(Spacer(0, gap_between_tables))
    elements.append(tbl_service_details)

    doc.build(elements)
    return invoice_buffer


def gap(num):
    ret = ''
    for i in range(num):
        ret = ret + '&nbsp;'
    return ret


def create_court_hearing_notice_pdf_bytes(filename, sanction_outcome):
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


class OffsetTable(Table, object):

    def __init__(self, data, colWidths=None, rowHeights=None, style=None,
                 repeatRows=0, repeatCols=0, splitByRow=1, emptyTableAction=None, ident=None,
                 hAlign=None, vAlign=None, normalizedData=0, cellStyles=None, rowSplitRange=None,
                 spaceBefore=None, spaceAfter=None, longTableOptimize=None, minRowHeights=None, x_offset=0, y_offset=0):
        self.x_offset = x_offset
        self.y_offset = y_offset
        super(OffsetTable, self).__init__(data, colWidths, rowHeights, style,
                                          repeatRows, repeatCols, splitByRow, emptyTableAction, ident,
                                          hAlign, vAlign, normalizedData, cellStyles, rowSplitRange,
                                          spaceBefore, spaceAfter, longTableOptimize, minRowHeights)

    def drawOn(self, canvas, x, y, _sW=0):
        x = x + self.x_offset
        y = y + self.y_offset
        super(OffsetTable, self).drawOn(canvas, x, y, _sW)


