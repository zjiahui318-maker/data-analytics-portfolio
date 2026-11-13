# Australian Mortgage Market and Bank Comparison

Two related analyses at different levels. The bank cases compare outstanding loan balances at named entities. The national analysis compares industry rates with national refinancing commitments.

## Named Bank Cases

Use APRA's Monthly ADI Statistics to compare Commonwealth Bank of Australia, National Australia Bank Limited and Westpac Banking Corporation over 13 month-ends from September 2025 to September 2026. The loader matches each entity by ABN and reconciles the final month with APRA's separate monthly issue.

| Bank | Annual housing balance growth | Investor share, Sep 2026 | Share of net increase |
| --- | ---: | ---: | ---: |
| CBA | 6.60% | 34.74% | 60.5% |
| NAB | 3.72% | 32.78% | 19.1% |
| Westpac | 2.73% | 33.78% | 20.4% |
| Three banks | 4.59% | 33.96% | 100.0% |

CBA grew fastest in both loan categories, while NAB's growth was concentrated in owner-occupied balances and Westpac's categories grew at similar rates. Combined growth uses the starting balances as weights. These are the legal entities' Australian books. The balances do not identify loan originations, refinancing or borrower switching.

From this directory:

```sh
python -m pip install -r requirements.txt
python bank_cases.py
python build_bank_cases_brief.py
```

The first command after installation writes [the 39-row bank-month panel](data/bank_cases_monthly.csv). The second renders the [bank case brief](../../output/pdf/Australian_Bank_Mortgage_Cases.pdf). Data and licence details are in the [source register](../../DATA_SOURCES.md).

## National Refinancing

Across 29 quarters (2019 Q3 to 2026 Q3), compare the outstanding rate less the new funded rate with refinancing flows. Average three monthly RBA F6 observations per quarter. Match them to national, seasonally adjusted ABS refinancing commitment counts by loan purpose. Measure external growth quarter on quarter. Compare its association with changes in the rate gap in the same and following quarters, then repeat using the variable-rate gap.

| Pearson correlation | Owner occupier | Investor |
| --- | ---: | ---: |
| All-loan discount change vs same-quarter external growth | -0.02 | +0.04 |
| All-loan discount change vs next-quarter external growth | -0.22 | -0.02 |
| Variable-rate discount change vs next-quarter external growth | +0.31 | +0.61 |

The all-loan measure showed little same-quarter association. The investor variable-rate sensitivity result is exploratory. Short samples, product mix and time dependence limit inference. The ABS counts are commitments, not unique borrowers or settled loans. [Full correlation summary](data/results.json) includes sample sizes and leave-one-quarter-out ranges; those ranges are not confidence intervals.

The [source register](../../DATA_SOURCES.md) identifies the separately sourced 6 November 2026 RBA F6 snapshot required for exact reproduction. The ABS table excerpt used by the parser is included. Once the specified F6 file is available locally, run `python analyze.py` to rebuild the quarterly CSV and JSON results and `python build_brief.py` to rebuild the national PDF locally. The published repository does not redistribute the F6 snapshot, national time series or older dashboard.
