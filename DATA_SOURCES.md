# Data Sources and Attribution

This register distinguishes the original data provider, the exact releases used and the files available in the portfolio. Paths are relative to the named project. All results are independent analyses by Jiahui Zhang.

## Australian mortgage market

**Rates.** Source: Reserve Bank of Australia 2026 (APRA and RBA in the CSV metadata), [Housing Lending Rates, Table F6](https://www.rba.gov.au/statistics/tables/#interest-rates), 6 November 2026 issue. The [official CSV link](https://www.rba.gov.au/statistics/tables/csv/f6-data.csv) rolls forward. The research uses national monthly all-institution rates for new and outstanding loans by purpose, averaged to 29 quarters (2019 Q3 to 2026 Q3).

The [RBA terms](https://www.rba.gov.au/copyright/) distinguish financial data and third-party content. This public package leaves out the original F6 snapshot and artifacts that expose its time series. It keeps the analysis code and calculated correlation summary. For exact reproduction, obtain the 6 November 2026 snapshot separately, verify the hash below and place it at `data/raw/rba-f6-2026-11-06.csv`. Do not rename a newer release to pass it off as the historical snapshot. Only add series-level files to a public release once the applicable redistribution terms are confirmed.

**Refinancing.** Australian Bureau of Statistics, [Lending Indicators, September quarter 2026](https://www.abs.gov.au/statistics/economy/finance/lending-indicators/sep-quarter-2026), national chart table "Number of refinanced loan commitments, seasonally adjusted and trend, Australia." The package includes only the four seasonally adjusted count columns for 2019 Q3 to 2026 Q3 in a small HTML table at `data/raw/abs-lending-2026-q3.html`. The values are unchanged; the file is an excerpt rather than the full ABS webpage. The ABS release describes commitments, not settled loans or unique customer exits. Derived results: based on ABS data and RBA F6.

**Named banks.** Copyright Australian Prudential Regulation Authority (APRA) 2024. [Monthly ADI Statistics, September 2026](https://www.apra.gov.au/news-and-publications/monthly-authorised-deposit-taking-institution-statistics), published 30 October 2026. Both workbooks specify [CC BY 3.0 Australia](https://creativecommons.org/licenses/by/3.0/au/) in the Notes sheet. Use the [back series, Table 1](https://www.apra.gov.au/system/files/2026-10/Monthly%20authorised%20deposit-taking%20institution%20statistics%20back-series%20March%202019%20-%20September%202026.xlsx) for the monthly panel, and the [September issue, Table 2](https://www.apra.gov.au/system/files/2026-10/Monthly%20authorised%20deposit-taking%20institution%20statistics%20September%202026.xlsx) to cross-check the final month. Original workbooks are included at `data/raw/apra-madis-history-sep-2026.xlsx` and `data/raw/apra-madis-sep-2026.xlsx`. Derived file: `data/bank_cases_monthly.csv`, 39 bank-month records, 13 month-ends, in AUD millions. It selects CBA, NAB and Westpac by ABN.

## Credit card default

I-Cheng Yeh, [Default of Credit Card Clients](https://doi.org/10.24432/C55S3H), UCI Machine Learning Repository, [dataset documentation](https://archive.ics.uci.edu/dataset/350/default+of+credit+card+clients), [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). The dataset covers 30,000 anonymised Taiwanese client records with repayment, bill and payment histories from April to September 2005 and a next-month default label. It does not identify a named bank.

The exact file used is `data/uci-credit-card-default.csv`, an unchanged CSV copy obtained from the [pinned scikit-learn mirror](https://huggingface.co/datasets/scikit-learn/credit-card-clients/blob/f809522/UCI_Credit_Card.csv) and validated by SHA-256. Cite UCI as the original source; the mirror is the retrieval location. The analysis code derives its own model inputs from the snapshot. Do not display record-level data on the CV website; show aggregated test outcomes.

## Rent and CPI

Source: Australian Bureau of Statistics. The public aggregate data used here are covered by the [ABS copyright and licence notice](https://www.abs.gov.au/website-privacy-copyright-and-disclaimer) and [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/), subject to the notice's exclusions. Attribute the unchanged workbooks to ABS and label derived charts or tables "Based on Australian Bureau of Statistics data."

| Snapshot | Release and table | Use |
| --- | --- | --- |
| `data/raw/abs-monthly-table-1.xlsx` | [September 2026 CPI](https://www.abs.gov.au/statistics/economy/price-indexes-and-inflation/consumer-price-index-australia/sep-2026#data-downloads), [Table 1](https://www.abs.gov.au/statistics/economy/price-indexes-and-inflation/consumer-price-index-australia/sep-2026/640101.xlsx) | Validate all-groups CPI series |
| `data/raw/abs-monthly-table-10.xlsx` | September 2026 CPI, [Table 10](https://www.abs.gov.au/statistics/economy/price-indexes-and-inflation/consumer-price-index-australia/sep-2026/6401010.xlsx) | Monthly rents and CPI by city, April 2024 to September 2026 |
| `data/raw/abs-quarterly-table-9.xlsx` | [September quarter 2025 CPI](https://www.abs.gov.au/statistics/economy/price-indexes-and-inflation/consumer-price-index-australia/sep-quarter-2025#data-downloads), [Table 9](https://www.abs.gov.au/statistics/economy/price-indexes-and-inflation/consumer-price-index-australia/sep-quarter-2025/640107.xlsx) | Separate quarterly comparisons, December 2019 to September 2025 |

Derived data: `data/analysis_panel.csv`, with frequency, period, city, measure and ABS index. [ABS rental measurement context](https://www.abs.gov.au/articles/latest-insights-rental-market) explains why the index measures changes in rents paid, not advertised weekly prices.

## Snapshot Checks

| File | SHA-256 |
| --- | --- |
| RBA F6, 6 November 2026 (not bundled) | `8baf6ac5d5fdff983db9db8614530a4d7d7ebe7de91739ca6774a034a6c3a516` |
| Original ABS Lending Indicators webpage (excerpt bundled) | `ab7dcdbd6a0a36a4146f25de446a1ad5c07a555006deee7b6da111369d26b13a` |
| APRA MADIS back series | `0aed5810a9c3827d709d0c1ebeb6a7f2dd6b384723a65339633067630ebcee2b` |
| APRA MADIS September issue | `ee26a0cc12e7c41f35294cb2f251341bb4fa7a618f804806f3f8978668d83278` |
| UCI CSV mirror snapshot | `a0f0ab49d6326671d6cd83be5c88dcf18007025fe9a53ecd699119c871176ca1` |
| ABS monthly CPI Table 1 | `756e3e5a1bf286e2edb51e20b730002c74eeca772620ac34f483359b366bf77e` |
| ABS monthly CPI Table 10 | `c07cc859771db4df41d172262287362847a3ef1e9182475dd7616932523b7460` |
| ABS quarterly CPI Table 9 | `9c17eaf6fc48c7c2de18fdcf40d1bd576f2cf284c308d07d28ac6f0b9f27ab10` |
