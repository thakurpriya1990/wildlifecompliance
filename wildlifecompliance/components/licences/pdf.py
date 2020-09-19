import os
from io import BytesIO
from bs4 import BeautifulSoup

from reportlab.lib import enums, colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    BaseDocTemplate,
    PageTemplate,
    Frame,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    ListFlowable,
    KeepTogether,
    PageBreak
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.utils import ImageReader

from django.core.files import File
from django.conf import settings

from wildlifecompliance.components.applications.utils import ActivitySchemaUtil

from wildlifecompliance.components.licences.models import LicenceDocument
from wildlifecompliance.components.licences.models import LicenceSpecies
from wildlifecompliance.components.applications.models import (
    ApplicationSelectedActivityPurpose,
)

import logging
logger = logging.getLogger(__name__)

BW_DPAW_HEADER_LOGO = os.path.join(
    settings.BASE_DIR,
    'wildlifecompliance',
    'static',
    'wildlifecompliance',
    'img',
    'bw_dpaw_header_logo.png')

COLOUR_DPAW_HEADER_LOGO = os.path.join(
    settings.BASE_DIR,
    'wildlifecompliance',
    'static',
    'wildlifecompliance',
    'img',
    'colour_dpaw_header_logo.png')

LICENCE_HEADER_IMAGE_WIDTH = 170
LICENCE_HEADER_IMAGE_HEIGHT = 42

PAGE_WIDTH, PAGE_HEIGHT = A4

DEFAULT_FONTNAME = 'Helvetica'
BOLD_FONTNAME = 'Helvetica-Bold'
ITALIC_FONTNAME = 'Helvetica-Oblique'
BOLD_ITALIC_FONTNAME = 'Helvetica-BoldOblique'

VERY_LARGE_FONTSIZE = 14
LARGE_FONTSIZE = 12
MEDIUM_FONTSIZE = 10
SMALL_FONTSIZE = 8

PARAGRAPH_BOTTOM_MARGIN = 5

SECTION_BUFFER_HEIGHT = 10

DATE_FORMAT = '%d/%m/%Y'

HEADER_MARGIN = 10
HEADER_SMALL_BUFFER = 3

PAGE_MARGIN = 20
PAGE_TOP_MARGIN = 200

LETTER_HEADER_MARGIN = 30
LETTER_PAGE_MARGIN = 60
LETTER_IMAGE_WIDTH = 242
LETTER_IMAGE_HEIGHT = 55
LETTER_HEADER_RIGHT_LABEL_OFFSET = 400
LETTER_HEADER_RIGHT_INFO_OFFSET = 450
LETTER_HEADER_SMALL_BUFFER = 5
LETTER_ADDRESS_BUFFER_HEIGHT = 40
LETTER_BLUE_FONT = 0x045690

styles = getSampleStyleSheet()
styles.add(
    ParagraphStyle(
        name='InfoTitleLargeCenter',
        fontName=BOLD_FONTNAME,
        fontSize=LARGE_FONTSIZE,
        spaceAfter=PARAGRAPH_BOTTOM_MARGIN,
        alignment=enums.TA_CENTER))
styles.add(
    ParagraphStyle(
        name='InfoTitleVeryLargeCenter',
        fontName=BOLD_FONTNAME,
        fontSize=VERY_LARGE_FONTSIZE,
        spaceAfter=PARAGRAPH_BOTTOM_MARGIN * 2,
        alignment=enums.TA_CENTER))
styles.add(
    ParagraphStyle(
        name='InfoTitleLargeLeft',
        fontName=BOLD_FONTNAME,
        fontSize=LARGE_FONTSIZE,
        spaceAfter=PARAGRAPH_BOTTOM_MARGIN,
        alignment=enums.TA_LEFT,
        leftIndent=PAGE_WIDTH / 10,
        rightIndent=PAGE_WIDTH / 10))
styles.add(
    ParagraphStyle(
        name='InfoTitleLargeRight',
        fontName=BOLD_FONTNAME,
        fontSize=LARGE_FONTSIZE,
        spaceAfter=PARAGRAPH_BOTTOM_MARGIN,
        alignment=enums.TA_RIGHT,
        rightIndent=PAGE_WIDTH / 10))
styles.add(
    ParagraphStyle(
        name='BoldLeft',
        fontName=BOLD_FONTNAME,
        fontSize=MEDIUM_FONTSIZE,
        alignment=enums.TA_LEFT))
styles.add(
    ParagraphStyle(
        name='BoldRight',
        fontName=BOLD_FONTNAME,
        fontSize=MEDIUM_FONTSIZE,
        alignment=enums.TA_RIGHT))
styles.add(
    ParagraphStyle(
        name='ItalicLeft',
        fontName=ITALIC_FONTNAME,
        fontSize=MEDIUM_FONTSIZE,
        alignment=enums.TA_LEFT))
styles.add(
    ParagraphStyle(
        name='ItalifRight',
        fontName=ITALIC_FONTNAME,
        fontSize=MEDIUM_FONTSIZE,
        alignment=enums.TA_RIGHT))
styles.add(ParagraphStyle(name='Center', alignment=enums.TA_CENTER))
styles.add(ParagraphStyle(name='Left', alignment=enums.TA_LEFT))
styles.add(ParagraphStyle(name='Right', alignment=enums.TA_RIGHT))
styles.add(
    ParagraphStyle(
        name='LetterLeft',
        fontSize=LARGE_FONTSIZE,
        alignment=enums.TA_LEFT))
styles.add(
    ParagraphStyle(
        name='LetterBoldLeft',
        fontName=BOLD_FONTNAME,
        fontSize=LARGE_FONTSIZE,
        alignment=enums.TA_LEFT))


def _create_licence_header(canvas, doc, draw_page_number=True):
    canvas.setFont(BOLD_FONTNAME, LARGE_FONTSIZE)

    current_y = PAGE_HEIGHT - HEADER_MARGIN

    canvas.drawCentredString(
        PAGE_WIDTH / 2,
        current_y - LARGE_FONTSIZE,
        '{}'.format(
            settings.DEP_NAME.upper()))

    current_y -= 30

    dpaw_header_logo = ImageReader(BW_DPAW_HEADER_LOGO)
    canvas.drawImage(
        dpaw_header_logo,
        HEADER_MARGIN,
        current_y - 40,
        width=LICENCE_HEADER_IMAGE_WIDTH,
        height=LICENCE_HEADER_IMAGE_HEIGHT)

    current_x = HEADER_MARGIN + LICENCE_HEADER_IMAGE_WIDTH + 5

    canvas.setFont(DEFAULT_FONTNAME, SMALL_FONTSIZE)

    canvas.drawString(current_x, current_y -
                      (SMALL_FONTSIZE + HEADER_SMALL_BUFFER), 'Enquiries:')
    canvas.drawString(current_x, current_y -
                      (SMALL_FONTSIZE + HEADER_SMALL_BUFFER) * 2, 'Telephone:')
    canvas.drawString(current_x, current_y -
                      (SMALL_FONTSIZE + HEADER_SMALL_BUFFER) * 3, 'Facsimile:')
    canvas.drawString(current_x, current_y -
                      (SMALL_FONTSIZE + HEADER_SMALL_BUFFER) * 4, 'Web Site:')
    canvas.drawString(current_x,
                      current_y - (SMALL_FONTSIZE + HEADER_SMALL_BUFFER) * 5,
                      'Correspondence:')

    current_x += 80

    canvas.drawString(current_x,
                      current_y - (SMALL_FONTSIZE + HEADER_SMALL_BUFFER),
                      '17 DICK PERRY AVE, KENSINGTON, WESTERN AUSTRALIA')
    canvas.drawString(current_x,
                      current_y - (SMALL_FONTSIZE + HEADER_SMALL_BUFFER) * 2,
                      '08 9219 9000')
    canvas.drawString(current_x,
                      current_y - (SMALL_FONTSIZE + HEADER_SMALL_BUFFER) * 3,
                      '08 9219 8242')
    canvas.drawString(current_x, current_y -
                      (SMALL_FONTSIZE + HEADER_SMALL_BUFFER) * 4, doc.site_url)

    canvas.setFont(BOLD_FONTNAME, SMALL_FONTSIZE)
    canvas.drawString(current_x,
                      current_y - (SMALL_FONTSIZE + HEADER_SMALL_BUFFER) * 5,
                      'Locked Bag 30')
    canvas.drawString(current_x,
                      current_y - (SMALL_FONTSIZE + HEADER_SMALL_BUFFER) * 6,
                      'Bentley Delivery Centre WA 6983')

    canvas.setFont(BOLD_FONTNAME, LARGE_FONTSIZE)

    current_y -= 36
    current_x += 200

    if draw_page_number:
        canvas.drawString(current_x, current_y -
                          (LARGE_FONTSIZE + HEADER_SMALL_BUFFER), 'PAGE')

    if hasattr(doc, 'licence'):
        canvas.drawString(current_x, current_y -
                          (LARGE_FONTSIZE + HEADER_SMALL_BUFFER) * 2, 'NO.')

    canvas.setFont(DEFAULT_FONTNAME, LARGE_FONTSIZE)

    current_x += 50

    if draw_page_number:
        canvas.drawString(current_x,
                          current_y - (LARGE_FONTSIZE + HEADER_SMALL_BUFFER),
                          str(canvas.getPageNumber()))

    if hasattr(doc, 'licence'):
        canvas.drawString(current_x,
                          current_y - (LARGE_FONTSIZE + HEADER_SMALL_BUFFER)*2,
                          '{}'.format(doc.licence.licence_number))


def _create_licence(licence_buffer, licence, application):
    '''
    Creates licence summary and purpose details for licence.
    '''

    def _create_licence_purpose(
            elements, selected_activity, issued_purpose):
        '''
        Creates the licence purpose details per page available on the activity.
        '''


        # delegation holds the dates, licencee and issuer details.
        delegation = []
        sequence = purpose.purpose_sequence
        licence_display = '{0}-{1}-{2}'.format(
            licence.licence_number, sequence, issued_purpose.purpose.code)
        licence_purpose = issued_purpose.purpose.name
        elements.append(Paragraph(
            licence_purpose.upper(),
            styles['InfoTitleVeryLargeCenter']))
        elements.append(Paragraph(
            'Regulation 28, Biodiversity Conservation Regulations 2018',
            styles['Center']))

        # applicant details
        delegation.append(Spacer(1, SECTION_BUFFER_HEIGHT))
        if application.applicant_type \
                == application.APPLICANT_TYPE_ORGANISATION:
            address = application.org_applicant.address
            pass
        elif application.applicant_type == application.APPLICANT_TYPE_PROXY:
            address = application.proxy_applicant.residential_address
            pass
        else:
            # applic.applicant_type == application.APPLICANT_TYPE_SUBMITTER
            address = application.submitter.residential_address

        address_paragraphs = [
            Paragraph(address.line1, styles['Left']),
            Paragraph(address.line2, styles['Left']),
            Paragraph(address.line3, styles['Left']),
            Paragraph('%s %s %s' % (
                address.locality, address.state,
                address.postcode), styles['Left']),
            Paragraph(address.country.name, styles['Left'])
            ]

        delegation.append(
            Table([[[Paragraph('Licence Number', styles['BoldLeft']),
                    Paragraph('Licence Holder', styles['BoldLeft']),
                    Paragraph('Address', styles['BoldLeft'])],
                    [Paragraph(
                        licence_display,
                        styles['Left']
                        )] + [Paragraph(
                            licence.current_application.applicant,
                            styles['Left']
                        )] + address_paragraphs]], colWidths=(
                            120, PAGE_WIDTH - (
                                2 * PAGE_MARGIN) - 120
                            ), style=licence_table_style))

        # dates
        dates_licensing_officer_table_style = TableStyle([(
            'VALIGN', (0, 0), (-2, -1), 'TOP'),
            ('VALIGN', (0, 0), (-1, -1), 'BOTTOM')])

        delegation.append(Spacer(1, SECTION_BUFFER_HEIGHT))
        date_headings = [
            Paragraph(
                'Date of Issue', styles['BoldLeft']), Paragraph(
                'Date Valid From', styles['BoldLeft']), Paragraph(
                'Date of Expiry', styles['BoldLeft'])]
        date_values = [
            Paragraph(issued_purpose.issue_date.strftime('%d/%m/%Y'),
                      styles['Left']),
            Paragraph(issued_purpose.start_date.strftime('%d/%m/%Y'),
                      styles['Left']),
            Paragraph(issued_purpose.expiry_date.strftime('%d/%m/%Y'),
                      styles['Left'])
        ]

        if issued_purpose.is_reissued:
            date_headings.insert(
                0,
                Paragraph(
                    'Original Date of Issue',
                    styles['BoldLeft']))
            date_values.insert(
                0,
                Paragraph(
                    issued_purpose.original_issue_date,
                    styles['Left']))

        delegation.append(
            Table(
                [[date_headings, date_values]],
                colWidths=(120, PAGE_WIDTH - (2 * PAGE_MARGIN) - 120),
                style=dates_licensing_officer_table_style))

        delegation.append(Spacer(1, SECTION_BUFFER_HEIGHT))

        elements.append(KeepTogether(delegation))

        # species
        species_ids = issued_purpose.purpose.get_species_list
        if species_ids:
            elements.append(Spacer(1, SECTION_BUFFER_HEIGHT))
            elements.append(Paragraph('SPECIES', styles['BoldLeft']))
            elements.append(Spacer(1, SECTION_BUFFER_HEIGHT))
            species = LicenceSpecies.objects.values_list('data').filter(
                specie_id__in=species_ids
            )
            speciesList = ListFlowable(
                [Paragraph(
                    s[0][0][
                        'vernacular_names'], styles['Left']) for s in species],
                bulletFontName=BOLD_FONTNAME,
                bulletFontSize=MEDIUM_FONTSIZE)
            elements.append(speciesList)
            elements.append(Spacer(1, SECTION_BUFFER_HEIGHT))

        try:
            # copy-to-licence sections with terms and additional information.
            activity_util = ActivitySchemaUtil(selected_activity.application)
            terms = selected_activity.additional_licence_info['terms']
            for term in terms:
                header = term['header']
                if not header:
                    continue
                elements.append(Spacer(1, SECTION_BUFFER_HEIGHT))
                elements.append(Paragraph(header.upper(), styles['BoldLeft']))
                elements.append(Spacer(1, SECTION_BUFFER_HEIGHT))
                text = activity_util.get_ctl_text(term)
                elements.append(Paragraph(text, styles['Left']))
                elements.append(Spacer(1, SECTION_BUFFER_HEIGHT))

        except BaseException:
            pass

        # PurposeSpecies Section
        for s in purpose.purpose_species_json:
            if s['is_additional_info']:
                continue
            parser = HtmlParser(s['details'])

            # Get and Display Purpose Species Header
            elements.append(Spacer(1, SECTION_BUFFER_HEIGHT))
            elements.append(
                Paragraph(
                    s['header'],
                    styles['BoldLeft']
                )
            )
            elements.append(Spacer(1, SECTION_BUFFER_HEIGHT))

            purposeSpeciesList = add_parsed_details(parser, list_flowable=False)
            for info_item in purposeSpeciesList:
                elements.append(KeepTogether(info_item))
        # End PurposeSpecies Section

        # application conditions
        activity_conditions = selected_activity.application.conditions.filter(
            licence_activity_id=selected_activity.licence_activity_id,
            licence_purpose_id=issued_purpose.purpose.id)

        if activity_conditions.exists():
            elements.append(Spacer(1, SECTION_BUFFER_HEIGHT))
            elements.append(Paragraph('CONDITIONS', styles['BoldLeft']))
            #elements.append(Spacer(1, SECTION_BUFFER_HEIGHT))

            # Conditions Section
            for s in activity_conditions.order_by('order'):
                conditionList = None
                parser = HtmlParser(s.condition)
                conditionList = add_parsed_details(parser)
                elements.append(Spacer(1, SECTION_BUFFER_HEIGHT))
                elements.append(conditionList)
            # End Conditions Section

        elements += _layout_extracted_fields(licence.extracted_fields)
        elements.append(Spacer(1, SECTION_BUFFER_HEIGHT))

        # signature block
        elements.append(Spacer(1, SECTION_BUFFER_HEIGHT))

        issue_officer = '{} {}'.format(
            selected_activity.updated_by.first_name,
            selected_activity.updated_by.last_name
            )
        elements.append(Paragraph('____________________', styles['Left']))
        elements.append(Paragraph(issue_officer, styles['Left']))
        elements.append(Paragraph('LICENSING OFFICER', styles['Left']))
        elements.append(
            Paragraph('WILDLIFE PROTECTION BRANCH', styles['Left']))
        elements.append(Spacer(1, SECTION_BUFFER_HEIGHT))
        elements.append(Paragraph('Delegate of CEO', styles['ItalicLeft']))
        elements.append(Spacer(1, SECTION_BUFFER_HEIGHT))

        # additional information
        # 'is_additional_info' Section from Purposespecies
        for s in purpose.purpose_species_json:
            if not s['is_additional_info']:
                continue
            parser = HtmlParser(s['details'])

            # Get and Display Purpose Species Header
            elements.append(Spacer(1, SECTION_BUFFER_HEIGHT))
            elements.append(
                Paragraph(
                    s['header'],
                    styles['BoldLeft']
                )
            )
            elements.append(Spacer(1, SECTION_BUFFER_HEIGHT))

            purposeSpeciesInfoList = add_parsed_details(parser, list_flowable=False)
            #elements.append(purposeSpeciesInfoList)
            for info_item in purposeSpeciesInfoList:
                elements.append(KeepTogether(info_item))

        # End PurposeSpecies Section


        if licence.has_additional_information_for(selected_activity):
            elements.append(Spacer(1, SECTION_BUFFER_HEIGHT))
            elements.append(Paragraph(
                'ADDITIONAL INFORMATION', styles['BoldLeft']))
            #elements.append(Spacer(1, SECTION_BUFFER_HEIGHT))

            conditions = activity_conditions
            infos = []
            c_num = 0
            for c_id, condition in enumerate(conditions.order_by('order')):
                info = None
                if condition.standard_condition:
                    info = condition.standard_condition.additional_information
                    c_num = c_id + 1
                if info:
                    infos.append('{0} (related to condition no.{1})'.format(
                        info.encode('utf8'), c_num))

            # Conditions Section
            for s in infos:
                parser = HtmlParser(s)
                infoList = add_parsed_details(parser)
                elements.append(Spacer(1, SECTION_BUFFER_HEIGHT))
                elements.append(infoList)
        # End Conditions Section

        elements.append(PageBreak())

    # create the summary for this licence.
    site_url = settings.SITE_URL
    every_page_frame = Frame(
        PAGE_MARGIN,
        PAGE_MARGIN,
        PAGE_WIDTH - 2 * PAGE_MARGIN,
        PAGE_HEIGHT - 160,
        id='EveryPagesFrame')
    every_page_template = PageTemplate(
        id='EveryPages',
        frames=[every_page_frame],
        onPage=_create_licence_header)

    doc = BaseDocTemplate(
        licence_buffer,
        pageTemplates=[every_page_template],
        pagesize=A4)

    # this is the only way to get data into the onPage callback function
    doc.licence = licence
    doc.site_url = site_url

    licence_table_style = TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP')])

    elements = []

    elements.append(Paragraph(
        'Licence Summary', styles['InfoTitleVeryLargeCenter']))
    # elements.append(Spacer(1, SECTION_BUFFER_HEIGHT))
    # elements.append(Paragraph('Activities', styles['BoldLeft']))
    # elements.append(Spacer(1, SECTION_BUFFER_HEIGHT))

    # activityList = ListFlowable(
    #     [Paragraph("{name}".format(
    #         name=selected_activity.licence_activity.name
    #     ),
    #         styles['Left'],
    #     ) for selected_activity in licence.current_activities],
    #     bulletFontName=BOLD_FONTNAME, bulletFontSize=MEDIUM_FONTSIZE)
    # elements.append(activityList)

    elements.append(Spacer(1, SECTION_BUFFER_HEIGHT))
    elements.append(Paragraph('Purposes', styles['BoldLeft']))
    elements.append(Spacer(1, SECTION_BUFFER_HEIGHT))

    include = [
        ApplicationSelectedActivityPurpose.PURPOSE_STATUS_SUSPENDED,
        ApplicationSelectedActivityPurpose.PURPOSE_STATUS_CURRENT,
        ApplicationSelectedActivityPurpose.PURPOSE_STATUS_DEFAULT,
    ]

    licence_purposes = [
        p for p in licence.get_purposes_in_sequence()
        if p.purpose_status in include and p.is_issued
    ]

    purposeList = ListFlowable(
        [Paragraph("{name} {start} - {end} ({status})".format(
            name=p.purpose.name,
            status=p.purpose_status,
            start=p.start_date.strftime('%d/%m/%Y'),
            end=p.expiry_date.strftime('%d/%m/%Y'),
        ),
            styles['Left'],
        ) for p in licence_purposes
        ],
        bulletFontName=BOLD_FONTNAME, bulletFontSize=MEDIUM_FONTSIZE)
    elements.append(purposeList)

    elements.append(PageBreak())

    for purpose in licence_purposes:
        # if not purpose.is_issued or purpose.purpose_status not in include:
        #     # Exclude purposes that are not issued.
        #     continue
        _create_licence_purpose(elements, purpose.selected_activity, purpose)

    doc.build(elements)

    return licence_buffer


def _layout_extracted_fields(extracted_fields):
    elements = []

    def __children_have_data(field):
        for group in field.get('children', []):
            for child_field in group:
                if child_field.get('data'):
                    return True

        return False

    # information extracted from application
    if extracted_fields:
        for field in extracted_fields:
            if 'children' not in field:
                if 'data' in field and field['data']:
                    elements.append(Spacer(1, SECTION_BUFFER_HEIGHT))
                    elements.append(
                        Paragraph(
                            field['label'],
                            styles['BoldLeft']))

                    if field['help_text']:
                        elements.append(
                            Paragraph(
                                field['help_text'],
                                styles['ItalicLeft']))

                    elements.append(Spacer(1, SECTION_BUFFER_HEIGHT))

                    if field['type'] in ['text', 'text_area']:
                        elements += _layout_paragraphs(field['data'])
                    elif field['type'] in ['radiobuttons', 'select']:
                        elements.append(Paragraph(dict([i.values() for i in field['options']]). get(
                            field['data'], 'Not Specified'), styles['Left']))
                    else:
                        elements.append(
                            Paragraph(
                                field['data'],
                                styles['Left']))

                elif field['type'] == 'label':
                    if any([option.get('data', 'off') ==
                            'on' for option in field['options']]):
                        elements.append(Spacer(1, SECTION_BUFFER_HEIGHT))
                        elements.append(
                            Paragraph(
                                field['label'],
                                styles['BoldLeft']))

                        if field['help_text']:
                            elements.append(
                                Paragraph(
                                    field['help_text'],
                                    styles['ItalicLeft']))

                        elements.append(Spacer(1, SECTION_BUFFER_HEIGHT))

                        elements.append(
                            Paragraph(
                                ', '.join(
                                    [
                                        option['label'] for option in field['options'] if option.get(
                                            'data',
                                            'off') == 'on']),
                                styles['Left']))
            else:
                if not __children_have_data(field):
                    continue

                elements.append(Spacer(1, SECTION_BUFFER_HEIGHT))
                elements.append(Paragraph(field['label'], styles['BoldLeft']))

                if field['help_text']:
                    elements.append(
                        Paragraph(
                            field['help_text'],
                            styles['ItalicLeft']))

                table_data = []
                for index, group in enumerate(field['children']):
                    if index == 0:
                        heading_row = []
                        for child_field in group:
                            heading_row.append(
                                Paragraph(
                                    child_field['label'],
                                    styles['BoldLeft']))
                        if heading_row:
                            table_data.append(heading_row)

                    row = []
                    for child_field in group:
                        if child_field['type'] in ['radiobuttons', 'select']:
                            row.append(Paragraph(dict([i.values() for i in child_field['options']]). get(
                                child_field['data'], 'Not Specified'), styles['Left']))
                        elif child_field['type'] == 'label':
                            if any([option.get('data', 'off') ==
                                    'on' for option in child_field['options']]):
                                row.append(
                                    Paragraph(
                                        ', '.join(
                                            [
                                                option['label'] for option in child_field['options'] if option.get(
                                                    'data',
                                                    'off') == 'on']),
                                        styles['Left']))
                            else:
                                row.append(
                                    Paragraph(
                                        'Not Specified',
                                        styles['Left']))
                        else:
                            row.append(
                                Paragraph(
                                    child_field['data'],
                                    styles['Left']))

                    if row:
                        table_data.append(row)

                if table_data:
                    elements.append(Table(table_data, style=TableStyle(
                        [('VALIGN', (0, 0), (-1, -1), 'TOP')])))

    return elements


def create_licence_doc(licence, application):
    licence_buffer = BytesIO()

    _create_licence(licence_buffer, licence, application)
    filename = 'licence-{}.pdf'.format(licence.licence_number)
    document = LicenceDocument.objects.create(name=filename)
    document._file.save(filename, File(licence_buffer), save=True)

    licence_buffer.close()

    return document


def create_licence_pdf_bytes(licence, application):
    licence_buffer = BytesIO()

    _create_licence(licence_buffer, licence, application)

    # Get the value of the BytesIO buffer
    value = licence_buffer.getvalue()
    licence_buffer.close()

    return value


class HtmlParser(object):
    ''' Usage:
        html = "<table style="width:100%" species_col='Age'>
                <tr>
                    <th>Firstname</th>
                    <th>Lastname</th>
                    <th>Age</th>
                </tr>
                <tr>
                    <td>Jill</td>
                    <td>Smith</td>
                    <td>50</td>
                </tr>
                <tr>
                    <td>Eve</td>
                    <td>Jackson</td>
                    <td>94</td>
                </tr>
            </table>

            <ul>
                <li>Coffee</li>
                <li>Tea</li>
            </ul>

            <p>
                This is some text ...
            </p>"

    from wildlifecompliance.components.licences.pdf import HtmlParser
    parser=HtmlParser(html)

    parser.tables
        [[[u'Firstname', u'Lastname', u'Age'],
        [u'Jill', u'Smith', u'50'],
        [u'Eve', u'Jackson', u'94']]]

    parser.lists
        [[u'Coffee', u'Tea'], [u'ssss']]

    parser.free_text
        [u'This is some text ...']

    parser.species
        [u'50', u'94']
    '''

    def __init__(self, raw_html):
        self.raw_html = raw_html
        self.tables = []
        self.species = []
        self.lists = []
        self.free_text = []
        self.parse()

    def parse(self):
        try:
            self.soup = BeautifulSoup(self.raw_html, "html.parser")
            self._parse_table()
            self._parse_list()
            self._parse_free_text()
            self._parse_species()
        except Exception as e:
            raise

    def _parse_table(self):
        for tbl in self.soup.findAll('table'):
            rows = []

            # add table column headers
            rows.append([row.get_text(strip=True) for row in self.soup.select("table tr > th")])

            for tr in tbl.findAll('tr'):
                cols = []
                for td in tr.findAll('td'):
                    cols.append(td.string)

                if cols:
                    rows.append(cols)

            self.tables.append(rows)

    def _parse_list(self):
        for ul in self.soup.findAll('ul'):
            self.lists.append(
                [row.get_text(strip=True) for row in ul.select("li")]
            )

    def _parse_free_text(self):
        self.free_text = [row.get_text(strip=True) for row in self.soup.select("p")]

    def _parse_species(self):
        try:
            if not self.soup.table:
                return []

            col_name = self.soup.table["species_col"]
            for tbl in self.tables:
                for i, row in enumerate(tbl):
                    if i==0:
                        idx = row.index(col_name)
                    else:
                        self.species.append(row[idx])
        except ValueError as e:
            logger.warn('Species name not found in HTML. \n{}'.format(e))
        except KeyError as e:
            logger.warn('Species attribute <species_col> not found in HTML table definition. \n{}'.format(e))

def add_parsed_details(parser, list_flowable=True):
        flow_list = []
        infoList = None
        box_table_style_hdrbold = TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOX', (0,0), (-1,-1), 0.25, colors.black),
            ('GRID', (0,0), (-1,-1), 0.25, colors.black),
            ('FONTNAME', (0,0), (-1,0), 'Courier-Bold'),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT')
        ])

        # Get and Display Purpose Species Table(s) (<table>)
        for table in parser.tables:
            flow_list.append(
                Table(
                    table,
                    style=box_table_style_hdrbold,
                    hAlign='LEFT'
                )
            )

        # Get and Display Purpose Species List(s) (<ul><li>)
        for _list in parser.lists:
            flow_list.append(
                [Paragraph(
                    li,
                    styles['Left']
                ) for li in _list ]
            )

        # Get and Display Purpose Species Free Text (<p>)
        flow_list.append(
            [Paragraph(
                text,
                styles['Left']
            ) for text in parser.free_text]
        )

        if list_flowable:
            infoList = ListFlowable(
                flow_list,
                bulletFontName=BOLD_FONTNAME, bulletFontSize=MEDIUM_FONTSIZE
            )
        else:
            infoList = flow_list

        return infoList


