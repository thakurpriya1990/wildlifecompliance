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
#from wildlifecompliance.components.legal_case.models import (
 #       LegalCase,
  #      )

PAGE_MARGIN = 5 * mm
PAGE_WIDTH, PAGE_HEIGHT = A4


def _create_pdf(invoice_buffer, legal_case, request_data):
    # 'report' variable set according to whether document_type is 'brief_of_evidence' or 'prosecution_brief'
    # 'report_document_artifacts' variable set according to whether document_type is 'brief_of_evidence' or 'prosecution_brief'
    document_type = request_data.get('document_type')
    include_statement_of_facts = request_data.get('include_statement_of_facts')
    include_case_information_form = request_data.get('include_case_information_form')
    include_offences_offenders_roi = request_data.get('include_offences_offenders_roi')
    include_witness_officer_other_statements = request_data.get('include_witness_officer_other_statements')
    include_physical_artifacts = request_data.get('include_physical_artifacts')
    include_document_artifacts = request_data.get('include_document_artifacts')
    report = None
    report_document_artifacts = None
    if document_type == 'brief_of_evidence':
        report = legal_case.brief_of_evidence
        report_document_artifacts = legal_case.briefofevidencedocumentartifacts_set.all()
    elif document_type == 'prosecution_brief':
        report = legal_case.prosecution_brief
        report_document_artifacts = legal_case.prosecutionbriefdocumentartifacts_set.all()

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

    # Details of alleged offence
    #rowHeights = [6*mm, 6*mm, 6*mm, 30*mm, 6*mm]
    #style_tbl_details = TableStyle([
    #    ('VALIGN', (0, 0), (0, 0), 'TOP'),
    #    ('VALIGN', (1, 0), (-1, -1), 'MIDDLE'),
    #    ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
    #    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
    #    ('SPAN', (0, 0), (0, 4)),
    #    ('SPAN', (2, 0), (4, 0)),
    #    ('SPAN', (2, 1), (4, 1)),
    #    ('SPAN', (2, 2), (4, 2)),
    #    ('SPAN', (2, 3), (4, 3)),
    #    ('SPAN', (2, 4), (4, 4)),
    #])
    data = []
    data.append([
        Paragraph('<strong>Details of alleged offence</strong><br />'
                  '<i><font size="' + str(FONT_SIZE_S) + '">[This description must comply with the CPA Schedule 1 clause 5.]</font></i>', styles['Normal']),
        Paragraph('Accused', styles['Normal']),
        '',
        '',
        '',
    ])
    data.append(['', Paragraph('Date or period', styles['Normal']), '', '', ''])
    data.append(['', Paragraph('Place', styles['Normal']), '', '', ''])
    data.append(['', Paragraph('Description', styles['Normal']), '', '', ''])
    data.append(['', Paragraph('Written law', styles['Normal']), '', '', ''])
    #tbl_details = Table(data, style=style_tbl_details, colWidths=col_width_details, rowHeights=rowHeights)
    tbl_statement = Table(data, style=style_tbl_details, colWidths=col_width_details, rowHeights=rowHeights)



    # Append tables to the elements to build
    gap_between_tables = 1.5*mm
    elements = []
    #elements.append(tbl_head)
    elements.append(tbl_statement)
    #elements.append(Spacer(0, gap_between_tables))
    #elements.append(tbl_notice)
    #elements.append(Spacer(0, gap_between_tables))
    #elements.append(tbl_accused)
    #elements.append(Spacer(0, gap_between_tables))
    #elements.append(tbl_prosecutor)
    #elements.append(Spacer(0, gap_between_tables))
    #elements.append(tbl_for_court)
    #elements.append(PageBreak())
    #elements.append(tbl_for_court_number)
    #elements.append(Spacer(0, gap_between_tables))
    #elements.append(tbl_above)
    #elements.append(Spacer(0, gap_between_tables))
    #elements.append(tbl_below)

    doc.build(elements)
    return invoice_buffer


def gap(num):
    ret = ''
    for i in range(num):
        ret = ret + '&nbsp;'
    return ret


def create_document_pdf_bytes(legal_case, request_data):
    with BytesIO() as invoice_buffer:
        _create_pdf(invoice_buffer, legal_case, request_data)
        document_type = request_data.get('document_type')
        filename = document_type + '_' + legal_case.number + '.pdf'

        # Get the value of the BytesIO buffer
        value = invoice_buffer.getvalue()

        # START: Save the pdf file to the database
        ## delete existing document
        document = None
        path = 'wildlifecompliance/{}/{}/generated_documents/{}'.format(legal_case._meta.model_name, legal_case.id, filename)
        document_exists = default_storage.exists(path)
        if document_exists:
            print("delete " + path)
            # delete file
            default_storage.delete(path)
        document, created = legal_case.generated_documents.get_or_create(name=filename)
        stored_file = default_storage.save(path, invoice_buffer)
        document._file = stored_file
        # save file object
        document.save()

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


