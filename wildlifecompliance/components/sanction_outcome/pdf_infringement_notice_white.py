# -*- coding: utf-8 -*-
from io import BytesIO
from django.core.files.storage import default_storage
from reportlab.lib import enums, colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.platypus import BaseDocTemplate, PageTemplate, Frame, PageBreak, Paragraph, Spacer, TableStyle, Table, \
    Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle, StyleSheet1
from wildlifecompliance.components.sanction_outcome.pdf_infringement_notice_blue import BOLD_FONTNAME, LARGE_FONTSIZE, \
    VERY_LARGE_FONTSIZE, MEDIUM_FONTSIZE, PAGE_MARGIN, PAGE_WIDTH, \
    PARAGRAPH_BOTTOM_MARGIN, PAGE_HEIGHT, DPAW_HEADER_LOGO
from wildlifecompliance.components.main.pdf_utils import get_infringement_notice_table, BrokenLine, SolidLine, gap, \
    YesNoCheckbox, ParagraphCheckbox, get_font_str

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
    MARGIN_TOP = 5
    MARGIN_BOTTOM = 5
    every_page_frame = Frame(PAGE_MARGIN, MARGIN_TOP, PAGE_WIDTH - 2 * PAGE_MARGIN, PAGE_HEIGHT - (MARGIN_TOP + MARGIN_BOTTOM), id='EveryPagesFrame',)  # showBoundary=Color(0, 1, 0))
    # every_page_frame2 = Frame(PAGE_MARGIN, PAGE_MARGIN, PAGE_WIDTH - 2 * PAGE_MARGIN, PAGE_HEIGHT - 2 * PAGE_MARGIN, id='EveryPagesFrame2',)  # showBoundary=Color(0, 0, 1))
    every_page_template = PageTemplate(id='EveryPages', frames=[every_page_frame,], )
    # every_page_template2 = PageTemplate(id='EveryPages2', frames=[every_page_frame2,], )
    doc = BaseDocTemplate(invoice_buffer, pageTemplates=[every_page_template, ], pagesize=A4,)  # showBoundary=Color(1, 0, 0))
    # doc = BaseDocTemplate(invoice_buffer, pageTemplates=[every_page_template, every_page_template2,], pagesize=A4,)  # showBoundary=Color(1, 0, 0))

    # Logo
    dpaw_header_logo = ImageReader(DPAW_HEADER_LOGO)
    dpaw_header_logo_size = dpaw_header_logo.getSize()
    width = dpaw_header_logo_size[0]/2
    height = dpaw_header_logo_size[1]/2
    dbca_logo = Image(DPAW_HEADER_LOGO, width=width, height=height)

    # 1st page
    t1 = get_infringement_notice_table(sanction_outcome)

    # 2nd page
    title_evidential_notes = Paragraph('<strong>EVIDENTIAL NOTES:</strong>', styles['Normal'])

    # table
    col_width = [40*mm, 35*mm, 22*mm, 31*mm, 37*mm, ]
    invoice_table_style = TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('SPAN', (1, 0), (4, 0)),
        ('SPAN', (1, 1), (4, 1)),
        ('SPAN', (1, 2), (4, 2)),
        ('SPAN', (1, 3), (4, 3)),
        ('SPAN', (2, 5), (3, 5)),
        ('SPAN', (2, 6), (4, 6)),
    ])
    data = []
    rego = sanction_outcome.registration_number if sanction_outcome.registration_number else ''
    data.append([
        Paragraph('<strong>Registration number<br />vehicle/vessel:</strong>', styles['Normal']),
        Paragraph(get_font_str(rego), styles['Normal']),
        '', '', '',
    ])
    data.append([
        Paragraph('<strong>Make:</strong>', styles['Normal']),
        '', '', '', '',
    ])
    data.append([
        Paragraph('<strong>Model:</strong>', styles['Normal']),
        '', '', '', '',
    ])
    data.append([
        Paragraph('<strong>Type: i.e SUV etc</strong>', styles['Normal']),
        '', '', '', '',
    ])

    data.append([
        Paragraph('<strong>Photograph(s) taken:</strong>', styles['Normal']),
        YesNoCheckbox(11, 11, fontName='Helvetica'),
        Paragraph('<strong>Attached:</strong>', styles['Normal']),
        YesNoCheckbox(11, 11, fontName='Helvetica'),
        Paragraph('<strong>Number:</strong>', styles['Normal']),
    ])
    data.append([
        Paragraph('<strong>Gender:<br />Tick relevant box</strong>', styles['Normal']),
        ParagraphCheckbox('Male', styles['Normal'],),
        ParagraphCheckbox('Female', styles['Normal'], ),
        '',
        ParagraphCheckbox('Other/unknown', styles['Normal'], ),
    ])
    data.append([
        Paragraph('<strong>Identification<br />produced:</strong>', styles['Normal']),
        YesNoCheckbox(11, 11, fontName='Helvetica'),
        Paragraph('<strong>If Yes, provide details:</strong>', styles['Normal']),
        '', '',
    ])
    t2 = Table(data, style=invoice_table_style, colWidths=col_width)

    title_original_notes = Paragraph('<strong>ORIGINAL NOTES OF INCIDENT:</strong>', styles['Normal'])

    elements = []
    elements.append(dbca_logo)
    elements.append(t1)
    elements.append(PageBreak())
    elements.append(dbca_logo)
    elements.append(title_evidential_notes)
    elements.append(Spacer(0, 5*mm))
    elements.append(t2)
    elements.append(Spacer(0, 5*mm))
    elements.append(title_original_notes)
    for i in range(0, 23):
        elements.append(SolidLine(440, 0, dashed=True, wrap_height=20))
    elements.append(Spacer(0, 10*mm))
    elements.append(Paragraph('<strong>Signature:</strong>' + gap(50) + '<strong>Date:</strong>', styles['Normal']))

    doc.build(elements)
    return invoice_buffer


def create_infringement_notice_white(filename, sanction_outcome):
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


