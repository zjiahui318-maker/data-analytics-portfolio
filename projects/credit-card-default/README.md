# Credit Card Default Early Warning

An independent banking analytics case study by Jiahui Zhang. The question is whether a logistic regression queue finds more next-month defaults than a delinquency rule when the team can review only 10% of clients.

| Method | Reviewed | Defaults found | Defaults missed | Precision | Recall | ROC AUC |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Delinquency rule | 600 | 414 | 913 | 69.0% | 31.2% | 0.722 |
| Logistic regression | 600 | 412 | 915 | 68.7% | 31.0% | 0.766 |

The overall ranking improved, while coverage at the operating cutoff was similar. The model found two fewer defaults. A paired test-cohort bootstrap gave a 95% interval of -17 to +10 defaults per 600 reviews, conditional on the fitted scores. Keep the rule as the benchmark until a later lender cohort demonstrates a practical advantage. The data records outcomes, so this project measures potential review coverage rather than prevented defaults.

## Reproduce

From this directory with Python 3.11 or 3.12:

```sh
python -m pip install -r requirements.txt
python build_notebook.py
python build_brief.py
```

Open [the executed notebook](credit_card_default.ipynb) to see the data checks, charts, queue overlap and descriptive subgroup results. The PDF build writes to the workspace's `output/pdf` directory. The project runs offline after the dependencies are installed. The data snapshot is retained in `data/`.

## Source

Yeh, I. (2016). [Default of Credit Card Clients](https://doi.org/10.24432/C55S3H). UCI Machine Learning Repository. The 30,000-client Taiwan dataset has repayment, bill and payment histories from April to September 2005 and a next-month default flag.

The original host timed out during download. The unchanged CSV is from the [pinned scikit-learn mirror](https://huggingface.co/datasets/scikit-learn/credit-card-clients/blob/f809522/UCI_Credit_Card.csv), and its checksum is verified by the loader. The analysis checks that the dimensions and published default total match. Feature engineering is performed in `analysis.py`; original data attribution is retained.

## Suggested CV Entry

**Credit Card Default Early Warning | Independent Portfolio Project**

- Developed a scikit-learn credit-risk model using 30,000 historical credit card records and benchmarked it against a delinquency rule on 6,000 held-out clients.
- Evaluated default capture at a 10% review capacity with paired bootstrap intervals, showing that higher ROC AUC did not improve coverage at the operating cutoff.
