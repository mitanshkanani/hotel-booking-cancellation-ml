"""Shared PDF helpers (reportlab) used by the STEP_n PDF builders from Step 2 onwards.

Notes: Helvetica cannot draw arrows or the approx sign - stick to ASCII in text.
Charts are SVG files embedded as vector drawings through svglib.
"""
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (KeepTogether, Paragraph, Preformatted, SimpleDocTemplate,
                                Spacer, Table, TableStyle)
from svglib.svglib import svg2rlg

NAVY = colors.HexColor('#1F3A5F')
_ss = getSampleStyleSheet()
BODY = ParagraphStyle('body', parent=_ss['Normal'], fontName='Helvetica', fontSize=10.5, leading=15, spaceAfter=6)
H1 = ParagraphStyle('h1', parent=_ss['Heading1'], fontName='Helvetica-Bold', fontSize=20, leading=24, spaceAfter=8, textColor=NAVY)
H2 = ParagraphStyle('h2', parent=_ss['Heading2'], fontName='Helvetica-Bold', fontSize=14, leading=18, spaceBefore=12, spaceAfter=6, textColor=NAVY)
H3 = ParagraphStyle('h3', parent=_ss['Heading3'], fontName='Helvetica-Bold', fontSize=11.5, leading=15, spaceBefore=8, spaceAfter=4)
BUL = ParagraphStyle('bul', parent=BODY, leftIndent=14, bulletIndent=2, spaceAfter=3)
CODE = ParagraphStyle('code', fontName='Courier', fontSize=8.6, leading=11, backColor=colors.HexColor('#F3F4F6'),
                      borderPadding=6, spaceBefore=4, spaceAfter=10, leftIndent=4)
NOTE = ParagraphStyle('note', parent=BODY, backColor=colors.HexColor('#FFF7E0'), borderPadding=6,
                      borderColor=colors.HexColor('#E0B400'), borderWidth=0.6, spaceBefore=6, spaceAfter=10)
SMALL = ParagraphStyle('small', parent=BODY, fontSize=9, leading=12)
CAPTION = ParagraphStyle('cap', parent=SMALL, textColor=colors.HexColor('#555555'), spaceAfter=10)
_CELL = ParagraphStyle('c', parent=SMALL, fontSize=8.6, leading=10.8)
_CELLH = ParagraphStyle('ch', parent=_CELL, textColor=colors.white, fontName='Helvetica-Bold')

VERDICT_COLORS = {'USABLE': '#D9F2DF', 'NEEDS CARE': '#FFF1C9', 'LEAKAGE': '#F7CFCF', 'TARGET': '#D3E4FA'}


class Doc:
    def __init__(self):
        self.story = []

    def P(self, t, s=BODY): self.story.append(Paragraph(t, s))
    def H1(self, t): self.P(t, H1)
    def H2(self, t): self.P(t, H2)
    def H3(self, t): self.P(t, H3)
    def NT(self, t): self.P(t, NOTE)
    def SP(self, h=6): self.story.append(Spacer(1, h))
    def C(self, t): self.story.append(Preformatted(t, CODE))

    def B(self, items):
        for t in items:
            self.story.append(Paragraph(t, BUL, bulletText='-'))

    def table(self, rows, widths, verdict_col=None, header=True):
        data = [[Paragraph(str(c), _CELLH if (i == 0 and header) else _CELL) for c in r] for i, r in enumerate(rows)]
        t = Table(data, colWidths=widths, repeatRows=1 if header else 0)
        st = [('VALIGN', (0, 0), (-1, -1), 'TOP'), ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#B8BEC8')),
              ('TOPPADDING', (0, 0), (-1, -1), 3), ('BOTTOMPADDING', (0, 0), (-1, -1), 3)]
        if header:
            st.append(('BACKGROUND', (0, 0), (-1, 0), NAVY))
        if verdict_col is not None:
            for i, r in enumerate(rows[1:], 1):
                col = VERDICT_COLORS.get(str(r[verdict_col]))
                if col:
                    st.append(('BACKGROUND', (verdict_col, i), (verdict_col, i), colors.HexColor(col)))
        t.setStyle(TableStyle(st))
        self.story.append(t)
        self.SP(8)

    def figure(self, svg_path, width_mm, caption):
        d = svg2rlg(str(svg_path))
        k = (width_mm * mm) / d.width
        d.scale(k, k)
        d.width *= k
        d.height *= k
        self.story.append(KeepTogether([d, Paragraph(caption, CAPTION)]))

    def qa(self, items):
        for i, (q, a) in enumerate(items, 1):
            self.story.append(KeepTogether([Paragraph(f'<b>Q{i}. {q}</b>', BODY),
                                            Paragraph(f'<i>Answer:</i> {a}', BODY), Spacer(1, 4)]))

    def build(self, out, title, footer_text):
        def footer(c, d):
            c.saveState(); c.setFont('Helvetica', 8); c.setFillColor(colors.grey)
            c.drawString(18 * mm, 10 * mm, footer_text)
            c.drawRightString(A4[0] - 18 * mm, 10 * mm, f'Page {d.page}')
            c.restoreState()
        SimpleDocTemplate(str(out), pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm, topMargin=16 * mm,
                          bottomMargin=18 * mm, title=title, author='Mitansh Kanani').build(
            self.story, onFirstPage=footer, onLaterPages=footer)
