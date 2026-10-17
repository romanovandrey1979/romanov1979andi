"""Мини-построитель документов: один набор блоков → PDF (reportlab) и HTML (для Google Docs)."""
import html as _h
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image,
                                PageBreak, KeepTogether)

pdfmetrics.registerFont(TTFont("DV", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"))
pdfmetrics.registerFont(TTFont("DVB", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"))

ST = {
    "title": ParagraphStyle("t", fontName="DVB", fontSize=16, leading=20, spaceAfter=6),
    "h1": ParagraphStyle("h1", fontName="DVB", fontSize=12.5, leading=16, spaceBefore=10,
                         spaceAfter=5),
    "h2": ParagraphStyle("h2", fontName="DVB", fontSize=10.5, leading=14, spaceBefore=7,
                         spaceAfter=4),
    "p": ParagraphStyle("p", fontName="DV", fontSize=9, leading=12.5, spaceAfter=4),
    "small": ParagraphStyle("s", fontName="DV", fontSize=7.8, leading=10.5, spaceAfter=3,
                            textColor=colors.HexColor("#444444")),
    "cell": ParagraphStyle("c", fontName="DV", fontSize=7.8, leading=10),
    "cellb": ParagraphStyle("cb", fontName="DVB", fontSize=7.8, leading=10),
}


class Doc:
    def __init__(self, title, subtitle=""):
        self.title, self.subtitle, self.blocks = title, subtitle, []

    def h1(self, t): self.blocks.append(("h1", t))
    def h2(self, t): self.blocks.append(("h2", t))
    def p(self, t): self.blocks.append(("p", t))
    def small(self, t): self.blocks.append(("small", t))
    def items(self, lst, numbered=False): self.blocks.append(("list", lst, numbered))
    def table(self, rows, widths=None, bold_last=False, highlight=None):
        self.blocks.append(("table", rows, widths, bold_last, highlight or {}))
    def image(self, path, width_mm): self.blocks.append(("img", path, width_mm))
    def pagebreak(self): self.blocks.append(("pb",))

    # ------------------------------------------------------------------ PDF
    def pdf(self, path, land=False, footer=""):
        size = landscape(A4) if land else A4
        doc = SimpleDocTemplate(path, pagesize=size, leftMargin=15 * mm, rightMargin=15 * mm,
                                topMargin=14 * mm, bottomMargin=16 * mm, title=self.title)
        avail = size[0] - 30 * mm
        s = [Paragraph(_h.escape(self.title), ST["title"])]
        if self.subtitle:
            s.append(Paragraph(_h.escape(self.subtitle), ST["p"]))
        for b in self.blocks:
            k = b[0]
            if k in ("h1", "h2", "p", "small"):
                s.append(Paragraph(b[1] if "<b>" in b[1] else _h.escape(b[1]), ST[k]))
            elif k == "list":
                for i, t in enumerate(b[1], 1):
                    s.append(Paragraph(("%d. " % i if b[2] else "• ") + _h.escape(t), ST["p"]))
            elif k == "table":
                rows, widths, bold_last, hl = b[1:]
                data = []
                for ri, r in enumerate(rows):
                    st = ST["cellb"] if ri == 0 or (bold_last and ri == len(rows) - 1) else ST["cell"]
                    data.append([Paragraph(_h.escape(str(c)), st) for c in r])
                if widths:
                    tot = sum(widths)
                    cw = [avail * w / tot for w in widths]
                else:
                    cw = None
                t = Table(data, colWidths=cw, repeatRows=1)
                style = [("BOX", (0, 0), (-1, -1), 0.5, colors.grey),
                         ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.grey),
                         ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8e8e8")),
                         ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                         ("TOPPADDING", (0, 0), (-1, -1), 2.5),
                         ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5)]
                if bold_last:
                    style.append(("BACKGROUND", (0, len(rows) - 1), (-1, len(rows) - 1),
                                  colors.HexColor("#f3f3f3")))
                for (ri, ci), col in hl.items():
                    style.append(("BACKGROUND", (ci, ri), (ci, ri), colors.HexColor(col)))
                t.setStyle(TableStyle(style))
                s.append(t)
                s.append(Spacer(1, 5))
            elif k == "img":
                from PIL import Image as PI
                w, h = PI.open(b[1]).size
                wmm = min(b[2] * mm, avail)
                hmax = size[1] - 30 * mm - 30 * mm
                if wmm * h / w > hmax:
                    wmm = hmax * w / h
                s.append(Image(b[1], width=wmm, height=wmm * h / w))
                s.append(Spacer(1, 4))
            elif k == "pb":
                s.append(PageBreak())

        def fn(canvas, d):
            canvas.saveState()
            canvas.setFont("DV", 7.5)
            canvas.setFillColor(colors.grey)
            canvas.drawString(15 * mm, 9 * mm, footer or self.title)
            canvas.drawRightString(size[0] - 15 * mm, 9 * mm, f"стр. {d.page}")
            canvas.restoreState()
        doc.build(s, onFirstPage=fn, onLaterPages=fn)

    # ------------------------------------------------------------------ HTML
    def html(self):
        e = _h.escape
        out = [f"<h1>{e(self.title)}</h1>"]
        if self.subtitle:
            out.append(f"<p>{e(self.subtitle)}</p>")
        for b in self.blocks:
            k = b[0]
            if k == "h1":
                out.append(f"<h2>{e(b[1])}</h2>")
            elif k == "h2":
                out.append(f"<h3>{e(b[1])}</h3>")
            elif k in ("p", "small"):
                out.append(f"<p>{b[1] if '<b>' in b[1] else e(b[1])}</p>")
            elif k == "list":
                tag = "ol" if b[2] else "ul"
                out.append(f"<{tag}>" + "".join(f"<li>{e(t)}</li>" for t in b[1]) + f"</{tag}>")
            elif k == "table":
                rows = b[1]
                h = "<table border=1>"
                for ri, r in enumerate(rows):
                    c = "th" if ri == 0 else "td"
                    h += "<tr>" + "".join(f"<{c}>{e(str(x))}</{c}>" for x in r) + "</tr>"
                out.append(h + "</table>")
            elif k == "img":
                out.append("<p><i>[диаграмма — см. PDF]</i></p>")
        return "<html><body>" + "\n".join(out) + "</body></html>"
