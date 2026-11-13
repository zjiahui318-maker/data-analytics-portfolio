# Rent and Inflation Across Three Cities

An independent applied economics case study by Jiahui Zhang. It compares rent price growth with local headline inflation in Canberra, Sydney and Melbourne.

| City | Rent growth to Sep 2026, year on year | All-groups CPI, year on year | Annual rent minus CPI | Rent minus CPI since Apr 2024 |
| --- | ---: | ---: | ---: | ---: |
| Canberra | 1.40% | 4.65% | -3.25 pp | -5.56 pp |
| Melbourne | 2.47% | 4.01% | -1.54 pp | +1.36 pp |
| Sydney | 3.48% | 4.31% | -0.83 pp | +1.76 pp |

- **Canberra:** Rents rose 2.38% since April 2024, the slowest growth of the three, versus 7.94% for local CPI.
- **Melbourne:** Annual rent inflation fell from 3.62% in September 2025 to 2.47% in September 2026. Rents still outpaced CPI over the full monthly window.
- **Sydney:** Rents rose 3.48% over the latest year and 9.64% since April 2024, the largest increases of the three cities.

Historical quarterly comparisons also change with the start date. All three cities' rents lagged local CPI from December 2019 to September 2025. Starting in September 2022, rents outpaced local CPI in Sydney and Melbourne.

## Data and Methods

- [ABS September 2026 CPI release, Tables 1 and 10](https://www.abs.gov.au/statistics/economy/price-indexes-and-inflation/consumer-price-index-australia/sep-2026#data-downloads). Use original monthly index levels for the 30 common months from April 2024 to September 2026. The loader matches all three headline CPI series in Table 10 against Table 1.
- [ABS September quarter 2025 CPI release, Table 9](https://www.abs.gov.au/statistics/economy/price-indexes-and-inflation/consumer-price-index-australia/sep-quarter-2025#data-downloads). Use 24 quarters from December 2019 to September 2025 in a separate panel. ABS changed its rent data collection source in July 2022.
- Growth is `100 * (ending index / starting index - 1)`. Growth gaps are in percentage points, using the unrounded growth calculations from the published index levels. Rebase the monthly trend chart to April 2024 = 100. Source files and ABS series IDs are retained in `data/raw` and `analysis.py`.
- The ABS rent index tracks prices paid by new and existing renters. Headline CPI includes rent. The index does not give typical weekly rents, advertised asking rents or rent-to-income ratios. [ABS rental measurement context](https://www.abs.gov.au/articles/latest-insights-rental-market)

## Reproduce

Run these commands from this directory with Python 3.11 or 3.12:

```sh
python -m pip install -r requirements.txt
python analysis.py
python build_notebook.py
python build_city_cases_brief.py
```

The project runs offline after the dependencies are installed. Open the [three-city brief](../../output/pdf/Canberra_Melbourne_Sydney_Rent_Cases.pdf) or the [executed notebook](canberra_rent_inflation.ipynb) for separate city charts, data checks and comparisons. The analysis writes `data/analysis_panel.csv`. Run `python build_brief.py` to regenerate the original Canberra-focused brief.

## Suggested CV Entry

**Rent and Inflation Across Three Australian Cities | Independent Portfolio Project**

- Built a reproducible Python analysis of ABS rental and headline CPI series for Canberra, Sydney and Melbourne, validating index metadata and reconciling monthly CPI across official tables.
- Found that rents lagged local CPI in all three cities in the latest year, while Melbourne and Sydney outpaced CPI over the full monthly window.
