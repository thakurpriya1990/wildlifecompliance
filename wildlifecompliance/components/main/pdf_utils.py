from uuid import uuid4

from reportlab.lib import colors
from reportlab.lib.colors import Color, blue, red, green, black, white
from reportlab.lib.styles import StyleSheet1, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import Table, Paragraph, Flowable, Image, TableStyle, Spacer


def gap(num):
    ret = ''
    for i in range(num):
        ret = ret + '&nbsp;'
    return ret


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


class ParagraphOffeset(Paragraph, object):

    def __init__(self, text, style, bulletText=None, frags=None, caseSensitive=1, encoding='utf8', x_offset=0, y_offset=0):
        self.x_offset = x_offset
        self.y_offset = y_offset
        super(ParagraphOffeset, self).__init__(text, style, bulletText, frags, caseSensitive, encoding)

    def drawOn(self, canvas, x, y, _sW=0):
        x = x + self.x_offset
        y = y + self.y_offset
        super(ParagraphOffeset, self).drawOn(canvas, x, y, _sW)


class ParagraphCheckbox(Paragraph, object):

    def __init__(self, text, style, checked=False, name='', gap=6, checkboxSize=11, bulletText=None, frags=None, caseSensitive=1, encoding='utf8', x_offset=0, y_offset=0):
        self.x_offset = x_offset
        self.y_offset = y_offset
        self.checked = checked
        self.checkboxSize = checkboxSize
        self.gap = gap
        if not name:
            self.name = str(uuid4())
        super(ParagraphCheckbox, self).__init__(text, style, bulletText, frags, caseSensitive, encoding)

    def drawOn(self, canvas, x, y, _sW=0):
        # test
        ret = canvas.absolutePosition(x, y)
        form = canvas.acroForm
        form.checkbox(
            name=self.name,
            tooltip='',
            size=self.checkboxSize,
            checked=self.checked,
            x=ret[0]+self.x_offset,  # the horizontal position on the page (absolute coordinates)
            y=ret[1]+self.y_offset,  # the vertical position on the page (absolute coordinates)
            buttonStyle='check',
            borderStyle='solid',
            borderWidth=1,
            borderColor=black,
            fillColor=white,
            fieldFlags='readOnly',
            # textColor=blue,
            forceBorder=True,
        )
        # test: end

        x = x + self.x_offset + self.checkboxSize + self.gap
        y = y + self.y_offset
        # canvas.restoreState()
        super(ParagraphCheckbox, self).drawOn(canvas, x, y, _sW)


class YesNoCheckbox(Flowable):
    def __init__(self, width, height, checkboxSize=11, checkedYes=False, checkedNo=False, x_offset=0, y_offset=0, fontName='Times-Roman'):
        Flowable.__init__(self)
        self.width = width
        self.height = height
        self.checkboxSize = checkboxSize
        self.checkedYes = checkedYes
        self.checkedNo = checkedNo
        self.x_offset = x_offset
        self.y_offset = y_offset
        self.fontName = fontName

    def draw(self):
        form = self.canv.acroForm
        self.canv.setFont(self.fontName, 12)
        self.canv.drawString(0, 5, 'Yes')
        # self.canv.rect(23, 4, self.width, self.height, fill=0)
        self.canv.drawString(47, 5, 'No')
        # self.canv.rect(67, 4, self.width, self.height, fill=0)
        ret = self.canv.absolutePosition(23, 4)
        form.checkbox(
            name='yes',
            tooltip='',
            size=self.checkboxSize,
            checked=self.checkedYes,
            x=ret[0]+self.x_offset,  # the horizontal position on the page (absolute coordinates)
            y=ret[1]+self.y_offset,  # the vertical position on the page (absolute coordinates)
            buttonStyle='check',
            borderStyle='solid',
            borderWidth=1,
            borderColor=black,
            fieldFlags='readOnly',
            fillColor=white,
            forceBorder=True,
        )
        ret = self.canv.absolutePosition(64, 4)
        form.checkbox(
            name='no',
            tooltip='',
            size=self.checkboxSize,
            checked=self.checkedNo,
            x=ret[0]+self.x_offset,  # the horizontal position on the page (absolute coordinates)
            y=ret[1]+self.y_offset,  # the vertical position on the page (absolute coordinates)
            buttonStyle='check',
            borderStyle='solid',
            borderWidth=1,
            borderColor=black,
            fieldFlags='readOnly',
            fillColor=white,
            forceBorder=True,
        )

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
        self.canv.setDash(3, 3)
        self.canv.line(0, self.height, self.width, self.height)


class SolidLine(Flowable):

    def __init__(self, width, height=0, dashed=False, wrap_height=25):
        Flowable.__init__(self)
        self.width = width
        self.height = height
        self.dashed = dashed
        self.wrap_height = wrap_height

    def wrap(self, *args):
        return 0, self.wrap_height

    def __repr__(self):
        return 'Line {}'.format(self.width)

    def draw(self):
        if self.dashed:
            self.canv.setDash(3, 3)
        self.canv.line(5, self.height + 5, self.width, self.height + 5)


class DbcaLogo(Image, object):

    def __init__(self, filename, x_offset=0, y_offset=0, width=None, height=None, kind='direct', mask="auto", lazy=1, hAlign='CENTER'):
        self.x_offset = x_offset
        self.y_offset = y_offset
        super(DbcaLogo, self).__init__(filename, width, height, kind, mask, lazy, hAlign)


def get_font_str(test, fontName="Helvetica", strong=True, size=11):
    try:
        if test:
            test = test if type(test) == str else str(test)
            strong_open = '<strong>' if strong else ''
            strong_close = '</strong>' if strong else ''
            ret = '<font face="' + fontName + '" size="' + str(size) + '">' + strong_open + test + strong_close + '</font>'
            return ret
        else:
            return ''
    except Exception as e:
        return ''


def get_infringement_notice_table(sanction_outcome):
    col_width = [40*mm, 60*mm, 80*mm,]

    # SPAN (col, row)
    invoice_table_style = TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
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

    date_str = gap(10) + '/' + gap(10) + '/ 20'

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
    offender = sanction_outcome.get_offender()[0]
    offender_dob = offender.dob.strftime('%d/%m/%Y') if offender.dob else ''
    offender_postcode = offender.residential_address.postcode if offender.residential_address else ''
    data.append([Paragraph('Alleged offender', styles['Bold']), Paragraph('Name: Family name: ' + get_font_str(offender.last_name), styles['Normal']), ''])
    data.append(['', Paragraph(gap(12) + 'Given names: ' + get_font_str(offender.first_name), styles['Normal']), ''])
    data.append(['', Paragraph(gap(12) + 'Date of Birth: ' + get_font_str(offender_dob), styles['Normal']), ''])
    data.append(['', [Paragraph('<strong>or</strong><br />Body corporate name: ', styles['Normal']), Spacer(1, 22)], ''])
    data.append(['',
                 [
                    Paragraph('Address: ', styles['Normal']),
                    Paragraph(get_font_str(str(offender.residential_address)), styles['Normal']),
                    Paragraph('Postcode: ' + get_font_str(offender_postcode), styles['Normal']),
                 ],
                '',
                 ])

    # When
    offence_datetime = sanction_outcome.offence.offence_occurrence_datetime
    data.append([
        Paragraph('When', styles['Bold']),
        Paragraph('Date: ' + get_font_str(offence_datetime.strftime('%d/%m/%Y')) + gap(5) + 'Time: ' + get_font_str(offence_datetime.strftime('%I:%M %p')), styles['Normal']),
        ''
    ])

    # Where
    offence_location = sanction_outcome.offence.location
    offence_location_str = str(offence_location) if offence_location else ''
    data.append([
        Paragraph('Where', styles['Bold']),
        [
            Paragraph('Location of offence', styles['Normal']),
            Paragraph(get_font_str(offence_location_str), styles['Normal']),
            Spacer(1, 25)
        ],
        '',
    ])

    # Alleged offence
    data.append([Paragraph('Alleged offence', styles['Bold']),
                 [
                     Paragraph('Description of offence', styles['Normal']),
                     Paragraph(get_font_str(sanction_outcome.description), styles['Normal']),
                 ],
                 ''])  # row index: 8
    data.append([
        '',
        [
            Paragraph('Is this a 2nd subsequent offence?', styles['Normal']),
            YesNoCheckbox(11, 11),
        ],
        '',
    ])
    data.append(['', [Paragraph('Biodiversity Conservation Act 2016 s.', styles['Normal']),
                      Paragraph('or', styles['Normal']),
                      Paragraph('Biodiversity Conservation Regulations 2018 r.', styles['Normal'])], ''])
    data.append(['', Paragraph('Modified penalty: $', styles['Normal']), ''])

    # Officer issuing notice
    data.append([
        Paragraph('Officer issuing notice', styles['Bold']),
        Paragraph('Name: {}'.format(get_font_str(sanction_outcome.responsible_officer.get_full_name())), styles['Normal']), ''
    ])  # row index: 12
    data.append([
        '',
        Paragraph('Signature', styles['Normal']),
        '',
    ])
    data.append([
        '',
        Paragraph('Officer no.', styles['Normal']),
        '',
    ])

    # Date
    issue_date = get_font_str(sanction_outcome.date_of_issue.strftime('%d/%m/%Y'))
    issue_time = get_font_str(sanction_outcome.time_of_issue.strftime('%I:%M %p'))
    data.append([Paragraph('Date', styles['Bold']), Paragraph('Date of notice: ' + issue_date + ' ' + issue_time, styles['Normal']), ''])

    # Create 1st table
    t1 = Table(data, style=invoice_table_style, colWidths=col_width)

    return t1