from reportlab.lib.colors import Color, blue
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

    def __init__(self, text, style, bulletText=None, frags=None, caseSensitive=1, encoding='utf8', x_offset=0, y_offset=0):
        self.x_offset = x_offset
        self.y_offset = y_offset
        super(ParagraphCheckbox, self).__init__(text, style, bulletText, frags, caseSensitive, encoding)

    def drawOn(self, canvas, x, y, _sW=0):
        canvas.saveState()
        canvas.acroForm.checkbox(
            name='CB0',
            tooltip='Field CB0',
            checked=True,
            x=x,
            y=y,
            buttonStyle='check',
            shape='square',
            borderStyle='solid',
            borderWidth=1,
            borderColor=blue,
            forceBorder=True,
        )
        x = x + self.x_offset
        y = y + self.y_offset
        canvas.restoreState()
        super(ParagraphCheckbox, self).drawOn(canvas, x, y, _sW)
