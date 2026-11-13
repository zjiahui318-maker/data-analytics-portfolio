"""Render three named APRA bank cases and the combined comparison."""

from pathlib import Path

from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.platypus import Table, TableStyle

from bank_cases import APRA, load_balances, summarize
from build_brief import GRID, H, INK, MARGIN, MUTED, RUST, TEAL, W, WIDTH, paragraph, text

OUTPUT = Path(__file__).resolve().parents[2] / "output/pdf/Australian_Bank_Mortgage_Cases.pdf"


def comparison(c, cases, combined, top):
    rows = [["Bank", "Sep 2026 balance", "Annual growth", "Investor share", "Share of growth"]]
    for name, row in [*cases.items(), ("Three banks", combined)]:
        rows.append([name, f"A${row['balance']:,.1f}bn", f"{row['growth']:+.2f}%",
                     f"{row['investor_share']:.2f}%", f"{row.get('growth_share', 100):.1f}%"])
    table = Table(rows, colWidths=[91, 110, 102, 102, WIDTH - 405], rowHeights=21)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eaf4f2")),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#f3f6f7")),
        ("TEXTCOLOR", (0, 0), (-1, -1), INK),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9.5),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LINEBELOW", (0, 1), (-1, -2), 0.45, GRID),
    ]))
    _, height = table.wrapOn(c, WIDTH, H)
    table.drawOn(c, MARGIN, top - height)
    return top - height


def change_chart(c, cases, top):
    text(c, "Where each bank's balance growth came from", MARGIN, top, 12, INK, True)
    text(c, "September 2025 to September 2026 | A$ billion", MARGIN, top - 15, 9, MUTED)
    for x, label, fill in ((MARGIN + 289, "Owner-occupied", TEAL), (MARGIN + 404, "Investment", RUST)):
        c.setFillColor(fill)
        c.rect(x, top - 16, 9, 8, stroke=0, fill=1)
        text(c, label, x + 13, top - 15, 8.8, MUTED)

    start, scale = MARGIN + 67, (WIDTH - 85) / 40
    for tick in range(0, 41, 10):
        x = start + tick * scale
        c.setStrokeColor(GRID)
        c.setLineWidth(.5)
        c.line(x, top - 116, x, top - 25)
        text(c, str(tick), x - 4, top - 128, 8, MUTED)
    for i, (name, row) in enumerate(cases.items()):
        y = top - 49 - i * 28
        text(c, name, MARGIN, y + 5, 10, INK, True)
        x = start
        for value, fill in ((row["owner_delta"], TEAL), (row["investor_delta"], RUST)):
            c.setFillColor(fill)
            c.rect(x, y, value * scale, 16, stroke=0, fill=1)
            x += value * scale
    return top - 128


def main():
    cases, combined = summarize(load_balances())
    cba, nab, westpac = (cases[name] for name in ("CBA", "NAB", "Westpac"))
    net = combined["owner_delta"] + combined["investor_delta"]
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(OUTPUT), pagesize=(W, H))
    c.setTitle("Three Australian bank mortgage cases")
    c.setAuthor("Jiahui Zhang")
    text(c, "BANKING ANALYTICS", MARGIN, H - 49, 9, TEAL, True)
    text(c, "Three Australian bank mortgage cases", MARGIN, H - 82, 25, INK, True)
    text(c, "Jiahui Zhang  |  CBA, NAB and Westpac  |  September 2026", MARGIN, H - 104, 10, MUTED)
    c.setStrokeColor(GRID)
    c.line(MARGIN, H - 118, W - MARGIN, H - 118)
    y = paragraph(c, f"<b>Housing loan balances rose {combined['growth']:.2f}% across the three banks.</b> "
                  f"They added A${net:.1f}bn in the year to September 2026, with CBA accounting for "
                  f"{cba['growth_share']:.1f}% of the increase. The three banks showed different growth patterns "
                  "by loan purpose.", H - 134)
    y = change_chart(c, cases, y - 24)
    for case in (
        f"<b>CBA | Fastest growth.</b> Investor balances rose {cba['investor_growth']:.2f}%, faster than "
        f"owner-occupied balances ({cba['owner_growth']:.2f}%). CBA added A${cba['investor_delta']:.1f}bn "
        "of investor loans on a net balance basis, the largest increase of the three.",
        f"<b>NAB | Owner-occupied growth dominated.</b> Owner-occupied balances rose "
        f"{nab['owner_growth']:.2f}%, versus {nab['investor_growth']:.2f}% for investor balances. "
        f"The investor share fell {abs(nab['share_change']):.2f} percentage points.",
        f"<b>Westpac | Similar growth across purposes.</b> Owner-occupied balances rose "
        f"{westpac['owner_growth']:.2f}% and investor balances rose {westpac['investor_growth']:.2f}%. "
        "The investor share changed by less than 0.1 percentage point.",
    ):
        y = paragraph(c, case, y - 13, 10.1, 14)
    text(c, "Cross-bank comparison", MARGIN, y - 20, 12, INK, True)
    y = comparison(c, cases, combined, y - 29)
    y = paragraph(c, f"<b>Combined.</b> Owner-occupied balances added A${combined['owner_delta']:.1f}bn "
                  f"and investor balances added A${combined['investor_delta']:.1f}bn. Each segment grew about "
                  f"{combined['owner_growth']:.1f}%, leaving the combined investor share nearly unchanged.",
                  y - 10, 10.1, 14)
    y = paragraph(c, "<b>Scope.</b> APRA domestic books for the three named legal entities, not their consolidated "
                  "groups or the full market. Growth uses starting balances as weights in the combined row. "
                  "Share of growth uses the three banks' net increase as the denominator. Balances are stocks: "
                  "they do not identify originations, refinancing flows or borrower switching.",
                  y - 8, 9.2, 12.4, MUTED)
    if y < 65:
        raise ValueError("Content does not fit above the source footer")
    c.setStrokeColor(GRID)
    c.line(MARGIN, 56, W - MARGIN, 56)
    label = "APRA MADIS | Sep 2026 back series, Table 1 and monthly issue, Table 2"
    text(c, label, MARGIN, 39, 8.8, TEAL, True)
    c.linkURL(APRA, (MARGIN, 37, MARGIN + 310, 49), relative=0)
    c.showPage()
    c.save()
    print(OUTPUT)


if __name__ == "__main__":
    main()
