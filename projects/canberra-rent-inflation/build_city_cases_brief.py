"""Render the three-city rent and inflation comparison."""

from io import BytesIO
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from reportlab.platypus import Table, TableStyle

from analysis import CASE_CITIES, MONTHLY_RELEASE, QUARTERLY_RELEASE, city_case_notes, growth_table, load_panels
from build_brief import H, INK, M, MUTED, RULE, TEAL, TINT, W, WIDTH, draw_text, paragraph
from figures import BLUE, plot_city_panels

OUTPUT = Path(__file__).resolve().parents[2] / "output/pdf/Canberra_Melbourne_Sydney_Rent_Cases.pdf"


def comparison(c, annual, recent, top):
    rows = [["City", "Rent YoY", "CPI YoY", "YoY gap", "Gap since Apr 2024"]]
    for city in CASE_CITIES:
        row = annual.loc[city]
        rows.append([city, f"{row['Rents']:.2f}%", f"{row['All groups CPI']:.2f}%",
                     f"{row['Rent minus CPI (pp)']:+.2f} pp",
                     f"{recent.loc[city, 'Rent minus CPI (pp)']:+.2f} pp"])
    table = Table(rows, colWidths=[112, 87, 87, 87, WIDTH - 373], rowHeights=20)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), TINT),
        ("TEXTCOLOR", (0, 0), (-1, -1), INK),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9.5),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LINEBELOW", (0, 1), (-1, -1), .5, RULE),
    ]))
    _, height = table.wrapOn(c, WIDTH, H)
    table.drawOn(c, M, top - height)
    return top - height


def chart(c, monthly, top):
    draw_text(c, "Rent and headline CPI | April 2024 = 100", M, top, 11.5, bold=True)
    for x, label, color, dash in ((M + 326, "Rents", TEAL, ()), (M + 398, "Headline CPI", colors.HexColor(BLUE), (4, 2))):
        c.setStrokeColor(color)
        c.setLineWidth(1.6)
        c.setDash(dash)
        c.line(x, top + 2, x + 20, top + 2)
        draw_text(c, label, x + 25, top - 1, 9, colour=MUTED)
    c.setDash()
    fig = plot_city_panels(monthly)
    image = BytesIO()
    fig.savefig(image, format="png", dpi=210, facecolor="white")
    plt.close(fig)
    height = WIDTH * 2.22 / 8.5
    bottom = top - 9 - height
    c.drawImage(ImageReader(image), M, bottom, WIDTH, height)
    return bottom


def main():
    monthly, quarterly = load_panels()
    annual = growth_table(monthly, "2025-09-01", "2026-09-01")
    recent = growth_table(monthly, "2024-04-01", "2026-09-01")
    later = growth_table(quarterly, "2022-09-01", "2025-09-01")["Rent minus CPI (pp)"]
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(OUTPUT), pagesize=(W, H))
    c.setTitle("Rent and inflation across three cities")
    c.setAuthor("Jiahui Zhang")
    draw_text(c, "APPLIED ECONOMICS", M, H - 49, 9.5, bold=True, colour=TEAL)
    draw_text(c, "Rent and inflation across three cities", M, H - 82, 25, bold=True)
    draw_text(c, "Jiahui Zhang  |  Canberra, Melbourne and Sydney  |  September 2026",
              M, H - 104, 10, colour=MUTED)
    c.setStrokeColor(RULE)
    c.line(M, H - 118, W - M, H - 118)
    y = paragraph(c, "<b>Rent growth trailed local inflation in all three cities in the latest year.</b> "
                  "Over the full monthly window starting in April 2024, rents outpaced headline CPI in "
                  "Melbourne and Sydney. Canberra's rents lagged CPI over both windows.", H - 134)
    y = chart(c, monthly, y - 24)
    for city, title, detail in city_case_notes(monthly):
        y = paragraph(c, f"<b>{city} | {title}.</b> {detail}", y - 10, 10, 13.5)
    draw_text(c, "Cross-city comparison | September 2026", M, y - 19, 12, bold=True)
    y = comparison(c, annual, recent, y - 28)
    y = paragraph(c, "<b>Historical check.</b> In separate quarterly data, rents lagged CPI in all three cities "
                  "from December 2019 to September 2025. Starting in September 2022, rents outpaced CPI in "
                  f"Melbourne (+{later['Melbourne']:.2f} pp) and Sydney (+{later['Sydney']:.2f} pp).",
                  y - 10, 9.6, 13.2)
    y = paragraph(c, "<b>Measurement.</b> Gaps are rent growth minus local all-groups CPI growth. Rent indexes "
                  "track prices paid by new and existing tenants. They do not compare weekly rent levels or "
                  "affordability. All-groups CPI includes rents. ABS changed its rent data source in July 2022.",
                  y - 8, 9.2, 12.4, MUTED)
    if y < 65:
        raise ValueError("Content does not fit above the source footer")
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
