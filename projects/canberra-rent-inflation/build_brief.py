"""Render the one-page English portfolio brief from the reviewed ABS data."""

from io import BytesIO
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph, Table, TableStyle

from analysis import MONTHLY_RELEASE, QUARTERLY_RELEASE, growth_table, load_panels
from figures import plot_canberra

OUTPUT = Path(__file__).resolve().parents[2] / "output/pdf/Canberra_Rent_and_Inflation_Brief.pdf"
W, H = A4
M = 44
WIDTH = W - 2 * M
INK = colors.HexColor("#20353d")
MUTED = colors.HexColor("#465d64")
TEAL = colors.HexColor("#086d69")
RULE = colors.HexColor("#cbdcde")
TINT = colors.HexColor("#edf5f4")


def draw_text(c, value, x, y, size, *, bold=False, colour=INK):
    c.setFillColor(colour)
    c.setFont("Helvetica-Bold" if bold else "Helvetica", size)
    c.drawString(x, y, value)


def paragraph(c, value, top, size=10.5, leading=14.7, colour=INK):
    style = ParagraphStyle("brief", fontName="Helvetica", fontSize=size,
                           leading=leading, textColor=colour)
    block = Paragraph(value, style)
    _, height = block.wrap(WIDTH, H)
    block.drawOn(c, M, top - height)
    return top - height


def annual_table(c, annual, top):
    data = [["City", "Rent growth", "All-groups CPI", "Rent minus CPI"]]
    for city, row in annual.iterrows():
        data.append([city, f"{row['Rents']:.2f}%", f"{row['All groups CPI']:.2f}%",
                     f"{row['Rent minus CPI (pp)']:+.2f} pp"])
    table = Table(data, colWidths=[137, 120, 121, WIDTH - 378], rowHeights=22)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), TINT),
        ("TEXTCOLOR", (0, 0), (-1, -1), INK),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LINEBELOW", (0, 1), (-1, -1), 0.5, RULE),
    ]))
    _, height = table.wrapOn(c, WIDTH, H)
    table.drawOn(c, M, top - height)
    return top - height


def main():
    monthly, quarterly = load_panels()
    annual = growth_table(monthly, "2025-09-01", "2026-09-01")
    recent = growth_table(monthly, "2024-04-01", "2026-09-01")
    later = growth_table(quarterly, "2022-09-01", "2025-09-01")
    year = annual.loc["Canberra"]
    cumulative = recent.loc["Canberra"]
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(OUTPUT), pagesize=A4)
    c.setTitle("Canberra rent growth and inflation")
    c.setAuthor("Jiahui Zhang")

    draw_text(c, "APPLIED ECONOMICS BRIEF", M, H - 49, 9.5, bold=True, colour=TEAL)
    draw_text(c, "Canberra rent growth and inflation", M, H - 83, 27, bold=True)
    draw_text(c, "Jiahui Zhang  |  Canberra, Sydney and Melbourne  |  September 2026",
              M, H - 106, 10, colour=MUTED)
    c.setStrokeColor(RULE)
    c.line(M, H - 119, W - M, H - 119)

    y = paragraph(c, f"<b>Canberra recorded the slowest rent growth of the three cities.</b> In the year "
                  f"to September 2026, the Canberra rent index rose {year['Rents']:.2f}% and local all-groups "
                  f"CPI rose {year['All groups CPI']:.2f}%. From April 2024, rents rose {cumulative['Rents']:.2f}% "
                  f"and local CPI rose {cumulative['All groups CPI']:.2f}%. Over that longer monthly window, "
                  "rents outpaced local CPI in Sydney and Melbourne.", H - 136)

    fig = plot_canberra(monthly)
    image = BytesIO()
    fig.savefig(image, format="png", dpi=170, facecolor="white")
    plt.close(fig)
    chart_width = WIDTH
    chart_height = chart_width * 3.4 / 7.5
    chart_bottom = y - 12 - chart_height
    c.drawImage(ImageReader(image), M, chart_bottom, chart_width, chart_height)

    draw_text(c, "Annual growth to September 2026", M, chart_bottom - 23, 12, bold=True)
    y = annual_table(c, annual, chart_bottom - 34)
    y = paragraph(c, "<b>The historical comparison depends on the start date.</b> Quarterly rents lagged local "
                  "CPI in all three cities from December 2019 to September 2025. Starting in September 2022 instead, "
                  f"rents outpaced CPI by {later.loc['Sydney', 'Rent minus CPI (pp)']:.2f} points in Sydney and "
                  f"{later.loc['Melbourne', 'Rent minus CPI (pp)']:.2f} in Melbourne. Canberra rents still lagged.",
                  y - 16)
    y = paragraph(c, "<b>Measurement.</b> ABS rent indexes reflect rents paid by new and existing tenants. "
                  "All-groups CPI includes rents. These comparisons measure price growth. Weekly rent levels "
                  "and affordability require separate data. Monthly and quarterly panels use separate releases.",
                  y - 9, 9.3, 12.6, MUTED)
    if y < 67:
        raise ValueError("Brief content does not fit above the source footer")

    c.setStrokeColor(RULE)
    c.line(M, 56, W - M, 56)
    for x, label, url in (
        (M, "ABS monthly CPI | Sep 2026 | Tables 1 and 10", MONTHLY_RELEASE),
        (M + 260, "ABS quarterly CPI | Sep 2025 | Table 9", QUARTERLY_RELEASE),
    ):
        draw_text(c, label, x, 39, 8.7, bold=True, colour=TEAL)
        c.linkURL(url + "#data-downloads", (x, 37, x + 217, 49), relative=0)
    c.showPage()
    c.save()
    print(OUTPUT)


if __name__ == "__main__":
    main()
