# -*- coding: utf-8 -*-
from io import BytesIO
from django.core.files.storage import default_storage
from reportlab.lib import enums
from reportlab.lib.pagesizes import A4
from reportlab.platypus import BaseDocTemplate, PageTemplate, Frame, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle, StyleSheet1
from wildlifecompliance.components.sanction_outcome.pdf_infringement_notice_blue import BOLD_FONTNAME, LARGE_FONTSIZE, VERY_LARGE_FONTSIZE, MEDIUM_FONTSIZE, PAGE_MARGIN, PAGE_WIDTH, \
    PARAGRAPH_BOTTOM_MARGIN, PAGE_HEIGHT
from wildlifecompliance.components.main.pdf_utils import get_infringement_notice_table

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
    every_page_template = PageTemplate(id='EveryPages', frames=[every_page_frame,], )
    every_page_template2 = PageTemplate(id='EveryPages2', frames=[every_page_frame2,], )
    doc = BaseDocTemplate(invoice_buffer, pageTemplates=[every_page_template, every_page_template2,], pagesize=A4,)  # showBoundary=Color(1, 0, 0))

    t1 = get_infringement_notice_table(sanction_outcome)

    elements = []
    elements.append(t1)
    elements.append(PageBreak())

    doc.build(elements)
    return invoice_buffer


def create_infringement_notice_yellow(filename, sanction_outcome):
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


