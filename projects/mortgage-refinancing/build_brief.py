"""Render the one-page banking brief from the reviewed quarterly panel."""

import csv
import json
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph

from analyze import ABS, RBA, DATA

OUTPUT = Path(__file__).resolve().parents[2] / "output/pdf/Australian_Mortgage_Refinancing_Brief.pdf"
W, H = A4
INK = colors.HexColor("#132a31")
MUTED = colors.HexColor("#485e64")
GRID = colors.HexColor("#d3dfe0")
TEAL = colors.HexColor("#00716c")
RUST = colors.HexColor("#a94d24")
MARGIN = 44
WIDTH = W - 2 * MARGIN


def text(c, value, x, y, size=10, colour=INK, bold=False):
    c.setFont("Helvetica-Bold" if bold else "Helvetica", size)
    c.setFillColor(colour)
    c.drawString(x, y, value)


def paragraph(c, value, top, size=10.4, leading=15, colour=INK):
    style = ParagraphStyle("brief", fontName="Helvetica", fontSize=size,
                           leading=leading, textColor=colour)
    block = Paragraph(value, style)
    _, height = block.wrap(WIDTH, H)
    block.drawOn(c, MARGIN, top - height)
    return top - height


def scatter(c, rows, result, segment, colour, left, bottom, width):
    low_x, high_x = -40, 40
    low_y, high_y = -30, 30
    height = 118
    x0 = left + 35
    plot_width = width - 42
    x = lambda v: x0 + (v - low_x) / (high_x - low_x) * plot_width
    y = lambda v: bottom + (v - low_y) / (high_y - low_y) * height
    text(c, segment, left, bottom + height + 14, 10.5, INK, True)
    text(c, f"r = {result['r']:+.2f}  |  n = {result['n']}", left + 99,
         bottom + height + 14, 9, MUTED)
    c.setLineWidth(0.55)
    for tick in (-30, -15, 0, 15, 30):
        c.setStrokeColor(MUTED if tick == 0 else GRID)
        c.line(x0, y(tick), x0 + plot_width, y(tick))
        text(c, f"{tick}%", left, y(tick) - 3, 8.5, MUTED)
    c.setStrokeColor(MUTED)
    c.line(x(0), bottom, x(0), bottom + height)
    for tick in (-40, -20, 0, 20, 40):
        text(c, str(tick), x(tick) - 6, bottom - 14, 8.5, MUTED)
    c.setFillColor(colour)
    for row in rows:
        if row["segment"] != segment or not row["gapChangeBp"] or not row["nextExternalGrowth"]:
            continue
        xv = float(row["gapChangeBp"])
        yv = 100 * float(row["nextExternalGrowth"])
        if not (low_x <= xv <= high_x and low_y <= yv <= high_y):
            raise ValueError(f"Chart domain excludes {row['quarter']}: {xv}, {yv}")
        c.circle(x(xv), y(yv), 2.8, stroke=0, fill=1)
    text(c, "Quarterly change in discount (bp)", x0, bottom - 28, 8.5, MUTED)


def main():
    with (DATA / "quarterly.csv").open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    stats = json.loads((DATA / "results.json").read_text(encoding="utf-8"))
    owner, investor = (stats[key] for key in ("Owner occupier", "Investor"))
    latest = {row["segment"]: row for row in rows if row["quarter"] == "2026 Q3"}
    prior = {row["segment"]: row for row in rows if row["quarter"] == "2026 Q2"}

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(OUTPUT), pagesize=A4)
    c.setTitle("Australian Mortgage Refinancing")
    c.setAuthor("Jiahui Zhang")
    text(c, "AUSTRALIAN BANKING RESEARCH", MARGIN, H - 49, 9, TEAL, True)
    text(c, "Mortgage pricing and refinancing", MARGIN, H - 83, 27, INK, True)
    text(c, "Jiahui Zhang  |  Australia  |  2019 Q3 to 2026 Q3", MARGIN, H - 105, 10, MUTED)
    c.setStrokeColor(GRID)
    c.line(MARGIN, H - 118, W - MARGIN, H - 118)

    y = paragraph(c, "<b>The overall new-loan discount showed no consistent positive link to switching lenders.</b> "
                  f"Quarter-to-quarter changes were nearly uncorrelated in the same quarter "
                  f"(Pearson r = {owner['sameQuarter']['r']:+.2f} for owner occupiers and "
                  f"{investor['sameQuarter']['r']:+.2f} for investors). The next-quarter relationship "
                  "was also weak or near zero for the all-loan measure.", H - 134)
    text(c, "Discount changes and next-quarter external refinancing growth", MARGIN, y - 22, 12, INK, True)
    bottom = y - 178
    scatter(c, rows, owner["nextQuarter"], "Owner occupier", TEAL, MARGIN, bottom, WIDTH / 2 - 12)
    scatter(c, rows, investor["nextQuarter"], "Investor", RUST, MARGIN + WIDTH / 2 + 12, bottom, WIDTH / 2 - 12)

    y = paragraph(c, f"<b>Variable-rate sensitivity.</b> With the variable-rate discount, the next-quarter "
                  f"correlation was {owner['nextQuarterVariable']['r']:+.2f} for owner occupiers and "
                  f"{investor['nextQuarterVariable']['r']:+.2f} for investors. The outcome still covers "
                  "all external refinancing. This is a reason to track variable pricing separately "
                  "and validate the relationship on new quarters.",
                  bottom - 46)
    text(c, "External refinancing in 2026 Q3", MARGIN, y - 24, 12, INK, True)
    table_y = y - 47
    headers = ("Loan purpose", "External count", "Quarterly change", "External share")
    xs = (MARGIN, MARGIN + 154, MARGIN + 269, MARGIN + 392)
    for x, label in zip(xs, headers):
        text(c, label, x, table_y, 9, MUTED, True)
    c.setStrokeColor(GRID)
    c.line(MARGIN, table_y - 7, W - MARGIN, table_y - 7)
    for i, (segment, row) in enumerate(latest.items(), start=1):
        share = float(row["externalShare"])
        share_change = 100 * (share - float(prior[segment]["externalShare"]))
        values = (segment, f"{int(row['external']):,}", f"{float(row['externalGrowth']):+.1%}",
                  f"{share:.1%} ({share_change:+.1f} pp)")
        for x, value in zip(xs, values):
            text(c, value, x, table_y - i * 20, 9.5)

    y = paragraph(c, "<b>Implication for retention teams.</b> External counts fell in both groups while "
                  "the external share rose because internal counts fell faster. Track the two volumes "
                  "alongside the share. Bank-level testing would need comparable customer offers, "
                  "loan characteristics and actual exits.", table_y - 56)
    y = paragraph(c, "<b>Method and limits.</b> The discount is the outstanding rate less the new funded "
                  "rate, in basis points, after averaging three monthly observations per quarter. "
                  "External refinancing means switching lender. Counts are seasonally adjusted commitments. "
                  "Industry aggregates reflect product mix and cannot identify the causal effect of a rate offer.",
                  y - 11, 9.1, 12.5, MUTED)
    if y < 67:
        raise ValueError("Brief content does not fit above the source footer")
    c.setStrokeColor(GRID)
    c.line(MARGIN, 56, W - MARGIN, 56)
    text(c, "RBA Housing Lending Rates (F6)", MARGIN, 39, 8.8, TEAL, True)
    c.linkURL(RBA, (MARGIN, 37, MARGIN + 139, 49), relative=0)
    text(c, "ABS Lending Indicators, September quarter 2026", MARGIN + 170, 39, 8.8, TEAL, True)
    c.linkURL(ABS, (MARGIN + 170, 37, MARGIN + 385, 49), relative=0)
    c.showPage()
    c.save()
    print(OUTPUT)


if __name__ == "__main__":
    main()
