from uuid import uuid4

from reportlab.lib.colors import Color, blue, red, green, black, white
from reportlab.platypus import Table, Paragraph


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
            y=ret[1]+self.y_offset-2,  # the vertical position on the page (absolute coordinates)
            buttonStyle='check',
            borderStyle='solid',
            borderWidth=1,
            borderColor=black,
            fillColor=white,
            # textColor=blue,
            forceBorder=True,
        )
        # test: end

        x = x + self.x_offset + self.checkboxSize + self.gap
        y = y + self.y_offset
        # canvas.restoreState()
        super(ParagraphCheckbox, self).drawOn(canvas, x, y, _sW)
