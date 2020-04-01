# -*- coding: utf-8 -*-

from io import BytesIO

from django.core.files.storage import default_storage
from django.http import HttpResponse
from ledger.payments.pdf import BrokenLine
from reportlab.lib.colors import red, green, blue
from reportlab.lib.enums import TA_RIGHT, TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.platypus import BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import ParagraphStyle, StyleSheet1
from reportlab.lib.units import mm
from reportlab.lib import colors

from wildlifecompliance.components.main.pdf_utils import gap, ParagraphOffeset, ParagraphCheckbox, get_font_str

PAGE_MARGIN = 5 * mm
PAGE_WIDTH, PAGE_HEIGHT = A4


def _create_pdf(invoice_buffer, legal_case, offenders):
    every_page_frame = Frame(PAGE_MARGIN, PAGE_MARGIN, PAGE_WIDTH - 2 * PAGE_MARGIN, PAGE_HEIGHT - 2 * PAGE_MARGIN, id='EveryPagesFrame', )  #showBoundary=Color(0, 1, 0))
    every_page_template = PageTemplate(id='EveryPages', frames=[every_page_frame,], )
    doc = BaseDocTemplate(invoice_buffer, pageTemplates=[every_page_template, ], pagesize=A4,)  # showBoundary=Color(1, 0, 0))

    # Common
    col_width_head = [95*mm, 15*mm, 85*mm,]
    col_width_details = [28*mm, 28*mm, 71*mm, 23*mm, 41*mm]
    FONT_SIZE_L = 12
    FONT_SIZE_M = 10
    FONT_SIZE_S = 8
    topLeftTableRowHeights = [23.5*mm, ]
    topRightTableRowHeights = [7.8*mm, 15.6*mm, ]

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

    elements = []
    for offender in offenders:

        ###
        # 1st page
        ###

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
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ])
        style_tbl_right = TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ])
        data_left = Table([
            [Paragraph('MAGISTRATES COURT of WESTERN<br />'
                       'AUSTRALIA<br />'
                       '<strong><font size="' + str(FONT_SIZE_L) + '">COURT HEARING NOTICE</font></strong><br />'
                       '<i>Criminal Procedure Act 2004</i><br />'
                       'Criminal Procedure Regulations 2005 - Form 5', styles['Centre']),]
        ], style=style_tbl_left, rowHeights=topLeftTableRowHeights)
        data_right = Table([
            [Paragraph('Court number', styles['Normal']), ''],
            [Paragraph('Magistrates court at', styles['Normal']), ''],
        ], style=style_tbl_right, rowHeights=topRightTableRowHeights)
        tbl_head = Table([[data_left, '', data_right]], style=invoice_table_style, colWidths=col_width_head, )

        # Accused's Details, etc
        rowHeights = [6*mm, 6*mm, 6*mm, 30*mm, 6*mm]
        style_tbl_accused_details = TableStyle([
            ('VALIGN', (0, 0), (0, 0), 'MIDDLE'),
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
            Paragraph(get_font_str(offender.person.last_name), styles['Normal']),
            '',
            '',
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
            ('VALIGN', (0, 0), (0, -1), 'TOP'),
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
                      '3. You can plead <u>not guilty</u> in writing. <br />'
                      '4. You can plead <u>guilty</u> in writing. <br />'
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

        ###
        # 2nd page
        ###
        # Head (col, row)
        data_left_p2 = Table([
            [Paragraph('MAGISTRATES COURT of WESTERN<br />'
                       'AUSTRALIA<br />'
                       '<strong><font size="' + str(FONT_SIZE_L) + '">WRITTEN PLEA BY ACCUSED</font></strong><br />'
                       '<i>Criminal Procedure Act 2004</i><br />'
                       'Criminal Procedure Regulations 2005 - Form 5 page 2', styles['Centre']),]
        ], style=style_tbl_left, rowHeights=topLeftTableRowHeights)
        data_right_p2 = Table([
            [Paragraph('Court number', styles['Normal']), ''],
            [Paragraph('Magistrates court at', styles['Normal']), ''],
        ], style=style_tbl_right, rowHeights=topRightTableRowHeights)
        tbl_head_p2 = Table([[data_left_p2, '', data_right_p2]], style=invoice_table_style, colWidths=col_width_head, )

        # Accused's Details
        # This is common among the pages

        # Accused's plea
        col_width_p2 = [28*mm, 28*mm, 71*mm, 23*mm, 41*mm]
        tbl_style_p2 = (
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('VALIGN', (0, 0), (0, -1), 'TOP'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('SPAN', (1, 0), (4, 0)),
            ('SPAN', (1, 1), (4, 1)),
            ('SPAN', (1, 2), (4, 2)),
            ('SPAN', (1, 3), (4, 3)),
            ('SPAN', (1, 4), (4, 4)),
            ('SPAN', (1, 5), (4, 5)),
            ('SPAN', (1, 6), (2, 6)),
            ('SPAN', (1, 7), (4, 7)),
            ('SPAN', (0, 5), (0, 6)),
        )
        data = []
        data.append([
            Paragraph('<strong>Accused\'s plea</strong>', styles['Normal']),
            [
                Paragraph('I have received a prosecution notice dated' + gap(40) + 'and a court hearing notice advising me of the hearing on [date]', styles['Normal']),
                Paragraph('I understand or have had explained to me the charge(s) in the prosecution notice and the contents of the court hearing notice and I understand the effect of this written plea I am sending to the court.', styles['Normal']),
            ],
            '', '', '',
        ])
        data.append([
            [
                Paragraph('<strong>Plea of guilty</strong>', styles['Normal']),
                Paragraph('[Tick on box]', styles['Normal']),
                Spacer(0, 20*mm),
                Paragraph('[Tick on box]', styles['Normal']),
            ],
            [
                ParagraphCheckbox('I plead <u>guilty</u> to the charge(s) in the prosecution notice.', styles['Normal']),
                ParagraphCheckbox('I plead <u>guilty</u> to the following charges in the prosecution notice.', styles['Normal']),
                Paragraph('<i>[If the prosecution notice contains more than one charge and you want to plead guilty to only some of them, write the numbers of the charges here.]</i>', styles['Normal']),
                Spacer(0, 8*mm),
                Paragraph('Attendance at court:', styles['Normal']),
                ParagraphCheckbox('I will be attending the hearing on the above date.', styles['Normal']),
                ParagraphCheckbox('I will not be attending the hearing on the above date.', styles['Normal']),
                Paragraph('I would like the court to take account of the following:', styles['Normal']),
                Paragraph('<i>[If you are pleading guilty you can (but need not) explain why you committed the offence(s) and give any information that you want the court to consider when deciding what sentence to impose on you.]</i>', styles['Normal']),
                Spacer(0, 10 * mm),
            ],
            '', '', '',
        ])
        data.append([
            [
                Paragraph('<strong>Plea of not guilty</strong>', styles['Normal']),
                Paragraph('[Tick on box]', styles['Normal']),
                Spacer(0, 20 * mm),
                Paragraph('[Tick on box]', styles['Normal']),
            ],
            [
                ParagraphCheckbox('I plead not guilty to the charge(s) in the prosecution notice.', styles['Normal']),
                ParagraphCheckbox('I plead not guilty to the following charges in the prosecution notice.', styles['Normal']),
                Paragraph('<i>[If the prosecution notice contains more than one charge and you want to plead not guilty to only some of them, write the numbers of them here]</i>', styles['Normal']),
                Spacer(0, 8 * mm),
                Paragraph('Attendance at court:', styles['Normal']),
                ParagraphCheckbox('I will be attending the hearing on the above date.', styles['Normal']),
                ParagraphCheckbox('I will not be attending the hearing on the above date.', styles['Normal']),
                Paragraph('At the trial of the charge(s) I intend to call' + gap(40) + 'witnesses (including myself).', styles['Normal']),
                Paragraph('<i>[Please insert the number of witnesses to assist the court in deciding how long the trial might last]</i>', styles['Normal']),
                Paragraph('When setting a date for the trial please take account of the following:', styles['Normal']),
                Paragraph('<i>[Please provide any information that might assist the court when setting the date for the trial such as dates when you will be overseas or in hospital.]</i>', styles['Normal']), Spacer(0, 10 * mm),
            ],
            '', '', '',
        ])
        data.append([
            Paragraph('<strong>Contact details</strong>', styles['Normal']),
            [
                Paragraph('My contact details are:', styles['Normal']),
                Spacer(0, 2*mm),
                Paragraph('Address (if different to the one above):', styles['Normal']),
                Spacer(0, 2*mm),
                Paragraph('Telephone no.' + gap(40) + 'Fax no.' + gap(40) + 'Mobile no.', styles['Normal']),
            ],
            '', '', '',
        ])
        data.append([
            [
                Paragraph('<strong>Lawyer\'s details</strong>', styles['Normal']),
                Paragraph('[If a lawyer will appear for you]', styles['Normal']),
            ],
            [
                Paragraph('Name:', styles['Normal']),
                Paragraph('Firm name', styles['Normal']),
            ],
            '', '', '',
        ])
        data.append([
            Paragraph('<strong>Accused\'s signature</strong>', styles['Normal']),
            Paragraph('<i>This may be signed by the accused’s lawyer or, if the accused is a corporation, made in accordance with the Criminal Procedure Act 2004 section 154(1).</i>', styles['Normal']),
            '', '', '',
        ])
        data.append([
            '',
            '',
            '',
            Paragraph('Date', styles['Normal']),
            '',
        ])
        data.append([
            Paragraph('<strong>Court address</strong>', styles['Normal']),
            [
                Paragraph('Send this document to:', styles['Normal']),
                Spacer(0, 2*mm),
                Paragraph('at:', styles['Normal']),
                Spacer(0, 2 * mm),
            ],
            '', '', '',
        ])
        tbl_main_p2 = Table(data, style=tbl_style_p2, colWidths=col_width_p2, )

        ###
        # 3rd page
        ###
        header_small_text_p3 = ParagraphOffeset('<font size="' + str(FONT_SIZE_S) + '">Copy to be attached to accused copy of prosecution notice</font>',
                                                styles['Right'],
                                                x_offset=-3*mm, y_offset=0)

        ###
        # 4th page
        ###
        # Same as 2nd page

        ###
        # 5th page
        ###
        header_small_text_p5 = ParagraphOffeset('<font size="' + str(FONT_SIZE_S) + '">Return of service copy</font>',
                                                styles['Right'],
                                                x_offset=-3*mm, y_offset=0)

        ###
        # 6th page
        ###

        gap_between_tables = 1.5*mm
        odd_page = []
        odd_page.append(tbl_head)
        odd_page.append(tbl_accused_details)
        odd_page.append(Spacer(0, gap_between_tables))
        odd_page.append(tbl_hearing_details)
        odd_page.append(Spacer(0, gap_between_tables))
        odd_page.append(tbl_notice_to_accused)
        odd_page.append(Spacer(0, gap_between_tables))
        odd_page.append(tbl_issuing_details)
        odd_page.append(Spacer(0, gap_between_tables))
        odd_page.append(tbl_service_details)
        even_page = []
        even_page.append(tbl_head_p2)
        even_page.append(tbl_accused_details)
        even_page.append(Spacer(0, gap_between_tables))
        even_page.append(tbl_main_p2)

        # 1st page
        elements.append(header_small_text_p1)
        elements += odd_page
        elements.append(PageBreak())
        # 2nd page
        elements += even_page
        elements.append(PageBreak())
        # 3rd page
        elements.append(header_small_text_p3)
        elements += odd_page
        elements.append(PageBreak())
        # 4th page
        elements += even_page
        elements.append(PageBreak())
        # 5th page
        elements.append(header_small_text_p5)
        elements += odd_page
        elements.append(PageBreak())
        # 6th page
        elements += even_page

    doc.build(elements)
    return invoice_buffer


def create_court_hearing_notice_pdf_bytes(filename, legal_case):
    with BytesIO() as invoice_buffer:
        _create_pdf(invoice_buffer, legal_case)

        # # Get the value of the BytesIO buffer
        # value = invoice_buffer.getvalue()
        #
        # # START: Save the pdf file to the database
        # document = legal_case.documents.create(name=filename)
        # path = default_storage.save('wildlifecompliance/{}/{}/documents/{}'.format(legal_case._meta.model_name, legal_case.id, filename), invoice_buffer)
        # document._file = path
        # document.save()
        # invoice_buffer.close()
        # return document
    invoice_buffer.seek(0)

    response = HttpResponse(invoice_buffer, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="{}"'.format(filename)
    return response
