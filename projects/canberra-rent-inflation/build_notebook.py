"""Build, execute, and optionally preview the rent inflation notebook."""

import argparse
from pathlib import Path

import nbformat as nbf
from nbclient import NotebookClient
from nbconvert import HTMLExporter

from analysis import CASE_CITIES, MONTHLY_RELEASE, QUARTERLY_RELEASE, city_case_notes, growth_table, load_panels

ROOT = Path(__file__).resolve().parent
NOTEBOOK = ROOT / "canberra_rent_inflation.ipynb"


def build_notebook():
    monthly, quarterly = load_panels()
    annual = growth_table(monthly, "2025-09-01", "2026-09-01")
    recent = growth_table(monthly, "2024-04-01", "2026-09-01")
    md, code = nbf.v4.new_markdown_cell, nbf.v4.new_code_cell
    case_cells = []
    for city, title, details in city_case_notes(monthly):
        year = annual.loc[city]
        case_cells.extend((
            md(f"""### {city} | {title}

{details} In the latest year, local headline CPI rose **{year['All groups CPI']:.2f}%**, leaving a rent-minus-CPI gap of **{year['Rent minus CPI (pp)']:+.2f} percentage points**."""),
            code(f"""fig = plot_city(monthly, {city!r})
display(fig)
plt.close(fig)"""),
        ))
    notebook = nbf.v4.new_notebook(
        metadata={"kernelspec": {"name": "python3", "display_name": "Python 3", "language": "python"}},
        cells=[
            md(f"""# Rent and inflation across three cities

Jiahui Zhang | Independent applied economics project

## Summary

Rent growth trailed local headline CPI in all three cities in the year to September 2026. Sydney had the fastest annual rent growth (**{annual.loc['Sydney', 'Rents']:.2f}%**), followed by Melbourne (**{annual.loc['Melbourne', 'Rents']:.2f}%**) and Canberra (**{annual.loc['Canberra', 'Rents']:.2f}%**). Over the full monthly window from April 2024, rent growth exceeded local CPI in Melbourne and Sydney and fell **{abs(recent.loc['Canberra', 'Rent minus CPI (pp)']):.2f} percentage points** short in Canberra."""),
            md("""## Context and methods

Compare how quickly rents and all consumer prices changed within each city, then compare the rent growth paths across cities. Use published original index levels, rebase them to 100 at the first comparable month for the trend chart, and calculate growth as 100 × (end / start − 1). Growth gaps are rent growth minus local CPI growth in percentage points.

### Key assumptions

- Monthly comparisons use April 2024 to September 2026, the complete overlap of headline CPI and rents for all three cities. The annual trend begins in April 2025 because it uses a 12-month lag.
- Historical comparisons use a separate quarterly release. Quarter labels name the last month of each quarter. The December 2019 and September 2022 starting points test how the historical comparison changes with the chosen window.
- The rent index measures price changes for rents paid by new and existing tenants. Comparing index growth across cities does not provide their weekly rents in dollars or their rent-to-income ratios. Headline CPI includes rents."""),
            md(f"""## Data

[ABS September 2026 monthly CPI release]({MONTHLY_RELEASE}#data-downloads), Tables 1 and 10. [ABS September quarter 2025 CPI release]({QUARTERLY_RELEASE}#data-downloads), Table 9. The files are retained under `data/raw/`. The loader verifies exact series IDs, descriptions, frequency and full coverage. It also reconciles all three monthly headline series against Table 1."""),
            code("""from IPython.display import display
import matplotlib.pyplot as plt
from analysis import CASE_CITIES, growth_table, load_panels
from figures import plot_city, plot_historical, plot_rent_yoy

monthly, quarterly = load_panels()
for name, panel in [("Monthly", monthly), ("Quarterly", quarterly)]:
    print(f"{name}: {len(panel)} periods, {panel.shape[1]} series, "
          f"{panel.index[0]:%b %Y} to {panel.index[-1]:%b %Y}, "
          f"{panel.isna().sum().sum()} missing values")"""),
            md("""## City cases

All charts use the same scale. Both series start at 100 in April 2024, so their separation represents a difference in cumulative percentage growth."""),
            *case_cells,
            md("""## Cross-city comparison

The lines compare each month's rent index with the same month one year earlier. The two tables use the same ending month and different starting months; this makes it possible to compare short-term inflation with the cumulative path."""),
            code("""fig = plot_rent_yoy(monthly)
display(fig)
plt.close(fig)
for label, start in [("Year to September 2026", "2025-09-01"),
                     ("April 2024 to September 2026", "2024-04-01")]:
    table = growth_table(monthly, start, "2026-09-01").loc[list(CASE_CITIES)]
    display(table.style.set_caption(label).format("{:+.2f}"))"""),
            md("""### The historical answer depends on the starting quarter

From December 2019 to September 2025, rents lagged local CPI in all three cities. Moving the start to September 2022 reverses the sign for Sydney and Melbourne. The starting quarter changes which part of the rental cycle is included. ABS also introduced a new rent data source in July 2022, so the long comparison spans a collection change."""),
            code("""fig = plot_historical(quarterly)
display(fig)
plt.close(fig)
display(growth_table(quarterly, "2022-09-01", "2025-09-01").style.format("{:+.2f}"))"""),
            md("""## Takeaways

Canberra rents rose but lagged broader inflation over both monthly windows. Sydney and Melbourne show how the choice of starting point can change the comparison. These are descriptive comparisons of published price indexes; an affordability study would need weekly rent and household income data."""),
        ],
    )
    nbf.validate(notebook)
    NotebookClient(notebook, timeout=90, kernel_name="python3",
                   resources={"metadata": {"path": str(ROOT)}}).execute()
    nbf.validate(notebook)
    nbf.write(notebook, NOTEBOOK)
    return notebook


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--preview", type=Path)
    args = parser.parse_args()
    notebook = build_notebook()
    if args.preview:
        preview, _ = HTMLExporter().from_notebook_node(notebook)
        args.preview.write_text(preview, encoding="utf-8")
    print(NOTEBOOK)
