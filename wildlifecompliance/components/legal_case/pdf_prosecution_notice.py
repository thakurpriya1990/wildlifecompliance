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

from wildlifecompliance.components.main.pdf_utils import OffsetTable, get_font_str

PAGE_MARGIN = 5 * mm
PAGE_WIDTH, PAGE_HEIGHT = A4


def _create_pdf(invoice_buffer, legal_case, offenders):
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
    elements = []
    for offender in offenders:

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
                              '<strong><font size="' + str(FONT_SIZE_L) + '">PROSECUTION NOTICE</font></strong><br />'
                              '<i>Criminal Procedure Act 2004</i><br />'
                              'Criminal Procedure Regulations 2005 - Form 3', styles['Centre']),]], style=style_tbl_left)
        data_right = Table([
            [Paragraph('Court number', styles['Normal']), ''],
            [Paragraph('Magistrates court at', styles['Normal']), ''],
            [Paragraph('Date lodged', styles['Normal']), ''],
        ], style=style_tbl_right, rowHeights=[7.8*mm, 7.8*mm, 7.8*mm,])
        tbl_head = Table([[data_left, '', data_right]], style=invoice_table_style, colWidths=col_width_head, )

        # Details of alleged offence
        rowHeights = [6*mm, 6*mm, 6*mm, 30*mm, 6*mm]
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
            Paragraph('<strong>Details of alleged offence</strong><br />'
                      '<i><font size="' + str(FONT_SIZE_S) + '">[This description must comply with the CPA Schedule 1 clause 5.]</font></i>', styles['Normal']),
            Paragraph('Accused', styles['Normal']),
            Paragraph(get_font_str(offender.person.get_full_name()), styles['Normal']),
            '',
            '',
        ])
        data.append(['', Paragraph('Date or period', styles['Normal']), '', '', ''])
        data.append(['', Paragraph('Place', styles['Normal']), '', '', ''])
        data.append(['', Paragraph('Description', styles['Normal']), '', '', ''])
        data.append(['', Paragraph('Written law', styles['Normal']), '', '', ''])
        tbl_details = Table(data, style=style_tbl_details, colWidths=col_width_details, rowHeights=rowHeights)

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
        rowHeights = [4.5*mm, 6*mm, 6*mm]
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
            Paragraph('<i><font size="' + str(FONT_SIZE_S) + '">[This description must comply with the CPA Schedule 1 clause 4.]</font></i>', styles['Normal']),
            '',
            '',
            '',
        ])
        data.append([
            '',
            Paragraph('Date of Birth', styles['Normal']),
            'DOB?',
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
        tbl_accused = Table(data, style=style_tbl_accused, colWidths=col_width_details, rowHeights=rowHeights)

        # Prosecutor
        rowHeights = [4.5*mm, 6*mm, 6*mm, 6*mm, 15*mm, 4.5*mm, 15*mm, 6*mm]
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
            Paragraph('<i><font size="' + str(FONT_SIZE_S) + '">[Identify the prosecutor in accordance with the CPA Schedule 1 clause 3.]</font></i>', styles['Normal']),
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
            Paragraph('<i><font size="' + str(FONT_SIZE_S) + '">[A witness may not be needed. See the CPA section 23.]</font></i>', styles['Normal']),
            '',
            '',
        ])
        data.append([
            '',
            '',
            Paragraph('<font size="' + str(FONT_SIZE_S) + '">Justice of the Peace or Prescribed Court Officer</font>', styles['Normal']),
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
        tbl_prosecutor = Table(data, style=style_tbl_prosecutor, colWidths=col_width_details, rowHeights=rowHeights)

        # For Court Use Only
        rowHeights_court = [6*mm, 10*mm, 6*mm, 6*mm, 6*mm, 6*mm, 6*mm, 6*mm, 6*mm, 6*mm, 23*mm, 17*mm]
        style_tbl_for_court = TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('VALIGN', (3, 11), (5, 11), 'BOTTOM'),
            ('VALIGN', (0, 10), (2, 11), 'TOP'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('SPAN', (0, 0), (5, 0)),
            ('SPAN', (3, 1), (4, 1)),
            ('SPAN', (3, 2), (4, 2)),
            ('SPAN', (3, 3), (4, 3)),
            ('SPAN', (3, 4), (4, 4)),
            ('SPAN', (3, 5), (4, 5)),
            ('SPAN', (3, 6), (4, 6)),
            ('SPAN', (1, 7), (2, 7)),  # Guilty / not guilty
            ('SPAN', (1, 8), (2, 8)),
            ('SPAN', (1, 9), (2, 9)),  # Convicted / acquitted
            ('SPAN', (3, 7), (5, 10)),  # Penalty and other orders
            ('SPAN', (4, 11), (5, 11)),
            ('SPAN', (0, 10), (2, 11)),  # <== This has a bug...?
        ])
        data = []
        data.append([
            Paragraph('<i>For Court User Only</i>', styles['Bold']),
            '', '', '', '', ''])
        data.append([
            Paragraph('Date', styles['Centre']),
            Paragraph('Appearance by accused', styles['Centre']),
            Paragraph('Counsel', styles['Centre']),
            Paragraph('Record of court proceedings', styles['Centre']),
            '',
            Paragraph('Judicial officer', styles['Centre']),
        ])
        data.append(['', Paragraph('Y / N', styles['Bold']), '', '', '', ''])
        data.append(['', Paragraph('Y / N', styles['Bold']), '', '', '', ''])
        data.append(['', Paragraph('Y / N', styles['Bold']), '', '', '', ''])
        data.append(['', Paragraph('Y / N', styles['Bold']), '', '', '', ''])
        data.append(['', Paragraph('Y / N', styles['Bold']), '', '', '', ''])
        data.append([
            Paragraph('Plea', styles['Bold']),
            Paragraph('Guilty / not guilty', styles['Bold']),
            '',
            [Paragraph('Penalty and other orders', styles['Centre']),
             Paragraph('<strong>Fine</strong>', styles['Normal']),
             Paragraph('<strong>Costs</strong>', styles['Normal']),
             Paragraph('<strong>Other</strong>', styles['Normal'])],
            '',
            '',
        ])
        data.append([
            Paragraph('Date of plea', styles['Bold']),
            '', '', '', '', '',
        ])
        data.append([
            Paragraph('<strong>Judgement</strong>', styles['Centre']),
            Paragraph('<strong>Conficted / acquitted</strong>', styles['Centre']),
            '', '', '', '',
        ])
        data.append([Paragraph('<strong>Victim impact statement available</strong>', styles['Centre']), '', '', '', '', ''])
        data.append([
            '',
            '',
            '',
            Paragraph('<strong>Judicial officer</strong>', styles['Centre']),
            Paragraph('<strong>Date:</strong>', styles['Normal']),
            '',
        ])
        tbl_for_court = Table(data, style=style_tbl_for_court, colWidths=col_width_for_court, rowHeights=rowHeights_court)

        #############
        # PageBreak #
        #############

        # Court Number
        rowHeights = [10*mm,]
        col_width_court_number = [30*mm, 70*mm,]
        style_tbl_for_court_number = TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ])
        data = []
        data.append([Paragraph('Court number', styles['Normal']), ''])
        tbl_for_court_number = OffsetTable(data, x_offset=45.5 * mm, style=style_tbl_for_court_number, colWidths=col_width_court_number, rowHeights=rowHeights)

        # Table above
        style_array = [
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ]
        for row_num in range(0, 29):
            style_array.append(('SPAN', (3, row_num), (4, row_num)))
        style_tbl_above = TableStyle(style_array)
        data = []
        data.append([
            Paragraph('Date', styles['Centre']),
            Paragraph('Appearance by accused', styles['Centre']),
            Paragraph('Counsel', styles['Centre']),
            Paragraph('Record of court proceedings', styles['Centre']),
            '',
            Paragraph('Judicial officer', styles['Centre']),
        ])
        for row_num in range(0, 28):
            data.append(['', Paragraph('<strong>Y / N</strong>', styles['Centre']), '', '', '', ''])
        tbl_above = Table(data, style=style_tbl_above, colWidths=col_width_for_court)

        # Table below
        style_array = [
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ]
        for row_num in range(0, 8):
            style_array.append(('SPAN', (2, row_num), (5, row_num)))
        style_tbl_below = TableStyle(style_array)
        data = []
        data.append([
            Paragraph('Date', styles['Centre']),
            Paragraph('Clerk\'s Initial', styles['Centre']),
            Paragraph('Registry record', styles['Centre']),
            '',
            '',
            '',
        ])
        for row_num in range(0, 7):
            data.append(['', '', '', '', '', ''])
        tbl_below = Table(data, style=style_tbl_below, colWidths=col_width_for_court, rowHeights=8.5*mm)

        # Append tables to the elements to build
        gap_between_tables = 1.5*mm
        elements.append(tbl_head)
        elements.append(tbl_details)
        elements.append(Spacer(0, gap_between_tables))
        elements.append(tbl_notice)
        elements.append(Spacer(0, gap_between_tables))
        elements.append(tbl_accused)
        elements.append(Spacer(0, gap_between_tables))
        elements.append(tbl_prosecutor)
        elements.append(Spacer(0, gap_between_tables))
        elements.append(tbl_for_court)
        elements.append(PageBreak())
        elements.append(tbl_for_court_number)
        elements.append(Spacer(0, gap_between_tables))
        elements.append(tbl_above)
        elements.append(Spacer(0, gap_between_tables))
        elements.append(tbl_below)

    doc.build(elements)
    return invoice_buffer


def create_prosecution_notice_pdf_bytes(filename, legal_case):
    with BytesIO() as invoice_buffer:
        _create_pdf(invoice_buffer, legal_case)

        # Get the value of the BytesIO buffer
        value = invoice_buffer.getvalue()

        # START: Save the pdf file to the database
        document = legal_case.documents.create(name=filename)
        path = default_storage.save('wildlifecompliance/{}/{}/documents/{}'.format(legal_case._meta.model_name, legal_case.id, filename), invoice_buffer)
        document._file = path
        document.save()
        # END: Save

        invoice_buffer.close()

        return document
