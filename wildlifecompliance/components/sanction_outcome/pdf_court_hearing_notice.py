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


PAGE_MARGIN = 5 * mm
PAGE_WIDTH, PAGE_HEIGHT = A4


def _create_pdf(invoice_buffer, sanction_outcome):
    every_page_frame = Frame(PAGE_MARGIN, PAGE_MARGIN, PAGE_WIDTH - 2 * PAGE_MARGIN, PAGE_HEIGHT - 2 * PAGE_MARGIN, id='EveryPagesFrame', )  #showBoundary=Color(0, 1, 0))
    every_page_template = PageTemplate(id='EveryPages', frames=[every_page_frame,], )
    doc = BaseDocTemplate(invoice_buffer, pageTemplates=[every_page_template, ], pagesize=A4,)  # showBoundary=Color(1, 0, 0))

    # Common
    col_width_head = [85*mm, 25*mm, 85*mm,]
    col_width_details = [27*mm, 27*mm, 71*mm, 30*mm, 36*mm]
    col_width_for_court = [27*mm, 24*mm, 18*mm, 58*mm, 47*mm, 17*mm]
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
    style_tbl_accused_details = TableStyle([
        ('VALIGN', (0, 0), (0, 0), 'MIDDLE'),
        # ('VALIGN', (1, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('SPAN', (1, 0), (4, 0)),
        ('SPAN', (1, 2), (4, 2)),
    ])

    gap_between_tables = 1.5*mm
    elements = []
    elements.append(tbl_head)
    elements.append(tbl_accused_details)
    elements.append(Spacer(0, gap_between_tables))

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


