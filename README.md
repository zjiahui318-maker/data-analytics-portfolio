# Jiahui Zhang | Data Analytics Portfolio

Three independent projects in banking analytics, model evaluation and applied economics. Each project folder contains the methodology, code and reproduction commands. [Data sources and attribution](DATA_SOURCES.md) describes the inputs, the release versions and what is included.

| Project | Question and result | Work |
| --- | --- | --- |
| Australian Mortgage Market and Bank Comparison | Did a wider new-loan discount track more refinancing nationally? There was little same-quarter association. In the separate bank cases, CBA supplied 60.5% of the three banks' net housing balance increase. | [Code and methods](projects/mortgage-refinancing) / [Bank case brief](output/pdf/Australian_Bank_Mortgage_Cases.pdf) |
| Credit Card Default Early Warning | Does logistic regression beat a delinquency rule at a 10% review capacity? It ranked better overall, but captured 412 defaults versus 414 for the rule at the operating cutoff. | [Code and methods](projects/credit-card-default) / [Notebook](projects/credit-card-default/credit_card_default.ipynb) / [Brief](output/pdf/Credit_Card_Default_Model_Validation.pdf) |
| Rent and Inflation Across Three Australian Cities | How did rent growth compare with local CPI in Canberra, Melbourne and Sydney? All three trailed CPI in the latest year, but Melbourne and Sydney outpaced it from April 2024 to September 2026. | [Code and methods](projects/canberra-rent-inflation) / [Notebook](projects/canberra-rent-inflation/canberra_rent_inflation.ipynb) / [Brief](output/pdf/Canberra_Melbourne_Sydney_Rent_Cases.pdf) |

The research uses fixed public releases, not live feeds. The bank comparison covers balances on the Australian books of the named legal entities, separate from national refinancing commitments. The credit model is a historical Taiwan case, not an Australian bank model. The rent study compares price growth, not affordability or weekly dollar rents.

Use Python 3.11 or 3.12 and install each project's `requirements.txt` in its own environment. The named-bank, credit and rent projects can run from the included inputs after dependency installation. Reproducing the historical industry-level mortgage analysis requires the exact separately sourced F6 snapshot described in [Data sources](DATA_SOURCES.md).

Analysis and figures are independent and are not endorsed by the data providers. The source data retain their own terms; no code licence, if added, changes those terms.
