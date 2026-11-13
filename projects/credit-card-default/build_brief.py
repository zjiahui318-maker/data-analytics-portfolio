"""Generate the one-page validation brief from the same experiment as the notebook."""

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

from analysis import (
    MODEL, RULE, SOURCE, TARGET, load_data, paired_bootstrap, plot_capacity,
    ranking_metrics, run_experiment,
)

OUTPUT = Path(__file__).resolve().parents[2] / "output/pdf/Credit_Card_Default_Model_Validation.pdf"
W, H = A4
M = 43
WIDTH = W - 2 * M
INK = colors.HexColor("#17313a")
MUTED = colors.HexColor("#496168")
TEAL = colors.HexColor("#126e71")
GRID = colors.HexColor("#d9e4e5")
TINT = colors.HexColor("#edf5f4")


def line(c, text, x, y, size=11, colour=INK, bold=False):
    c.setFillColor(colour)
    c.setFont("Helvetica-Bold" if bold else "Helvetica", size)
    c.drawString(x, y, text)


def paragraph(c, text, top, size=10.2, leading=14.1, colour=INK):
    style = ParagraphStyle("brief", fontName="Helvetica", fontSize=size, leading=leading,
                           textColor=colour)
    block = Paragraph(text, style)
    _, height = block.wrap(WIDTH, H)
    block.drawOn(c, M, top - height)
    return top - height


def main():
    raw = load_data()
    train, test, _, scores, orders, results = run_experiment(raw)
    actual = test[TARGET].to_numpy()
    size = int(results.loc[MODEL, "Reviewed"])
    low, high = paired_bootstrap(actual, orders, size)
    ranking = ranking_metrics(train, test, scores)
    rule, model = (results.loc[name] for name in (RULE, MODEL))

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(OUTPUT), pagesize=A4)
    c.setTitle("Credit card default early warning")
    c.setAuthor("Jiahui Zhang")
    line(c, "MODEL VALIDATION BRIEF", M, H - 49, 9.5, TEAL, True)
    line(c, "Credit card default early warning", M, H - 81, 27, INK, True)
    line(c, "Jiahui Zhang  |  Taiwan 2005  |  Independent portfolio project", M, H - 103, 10, MUTED)
    c.setStrokeColor(GRID)
    c.line(M, H - 118, W - M, H - 118)

    y = paragraph(c,
                  f"<b>Keep the delinquency rule as the benchmark at 10% review capacity.</b> "
                  f"On {len(test):,} held-out clients, the rule found {rule['Defaults found']:.0f} defaults "
                  f"and logistic regression found {model['Defaults found']:.0f} across {size} reviews each. "
                  f"The paired 95% interval for the model's difference spans {low:+.0f} to {high:+.0f} defaults.",
                  H - 132)

    table = [["Queue", "Found", "Missed", "Precision", "Recall", "ROC AUC"]]
    for name, row in ((RULE, rule), (MODEL, model)):
        table.append([name, f"{row['Defaults found']:.0f}", f"{row['Defaults missed']:.0f}",
                      f"{row['Precision']:.1%}", f"{row['Recall']:.1%}", f"{ranking.loc[name, 'ROC AUC']:.3f}"])
    comparison = Table(table, colWidths=[147, 68, 68, 75, 70, WIDTH - 428],
                       rowHeights=[25, 25, 25])
    comparison.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), TINT),
        ("TEXTCOLOR", (0, 0), (-1, -1), INK),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LINEBELOW", (0, 1), (-1, -1), 0.5, GRID),
    ]))
    comparison.wrapOn(c, WIDTH, H)
    comparison.drawOn(c, M, y - 89)

    fig = plot_capacity(actual, orders)
    image = BytesIO()
    fig.savefig(image, format="png", dpi=160, facecolor="white")
    plt.close(fig)
    chart_width = WIDTH - 18
    chart_height = chart_width * 4.2 / 7.5
    chart_bottom = y - 105 - chart_height
    c.drawImage(ImageReader(image), M + 9, chart_bottom, chart_width, chart_height)

    y = paragraph(c, "<b>Decision at the cutoff.</b> The logistic model has higher ROC AUC on the held-out sample. "
                  "Its top 600 accounts yield almost the same coverage. Compare queues at the actual review "
                  "budget before changing the rule.", chart_bottom - 11)
    y = paragraph(c, "<b>Validation design.</b> Stratified 80/20 holdout. The model uses repayment, bill, payment "
                  "and limit information available before the outcome month. Demographics and IDs are excluded. "
                  "The interval resamples test clients and reselects both queues with the fitted scores.", y - 9, 9.5, 13)
    y = paragraph(c, "<b>Scope.</b> One historical Taiwan cohort. A later lender cohort would be needed to "
                  "verify performance, calibration and subgroup outcomes before any operational use.", y - 9, 9.5, 13)
    if y < 64:
        raise ValueError("Brief content does not fit above the source footer")

    c.setStrokeColor(GRID)
    c.line(M, 56, W - M, 56)
    line(c, "Source  |  UCI Default of Credit Card Clients (Yeh, 2016)", M, 38, 8.8, TEAL, True)
    c.linkURL(SOURCE, (M, 36, M + 248, 49), relative=0)
    c.showPage()
    c.save()
    print(OUTPUT)


if __name__ == "__main__":
    main()
