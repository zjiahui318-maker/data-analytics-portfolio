"""Build comparable ABS rent and headline CPI panels without splicing frequencies."""

from datetime import datetime
from pathlib import Path

import pandas as pd
from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "data/raw"
ABS_BASE = "https://www.abs.gov.au/statistics/economy/price-indexes-and-inflation/consumer-price-index-australia"
MONTHLY_RELEASE = ABS_BASE + "/sep-2026"
QUARTERLY_RELEASE = ABS_BASE + "/sep-quarter-2025"
CITIES = ("Canberra", "Sydney", "Melbourne")
CASE_CITIES = ("Canberra", "Melbourne", "Sydney")
METRICS = ("Rents", "All groups CPI")
MONTHLY_IDS = {
    "Canberra": ("A130394392W", "A130393727V"),
    "Sydney": ("A130390458C", "A130397375X"),
    "Melbourne": ("A130390465A", "A130396086K"),
}
QUARTERLY_IDS = {
    "Canberra": ("A2326426A", "A2325841T"),
    "Sydney": ("A2326391L", "A2325806K"),
    "Melbourne": ("A2326396X", "A2325811C"),
}


def read_series(filename, requested, frequency):
    book = load_workbook(RAW / filename, read_only=True, data_only=True)
    values = {}
    try:
        for sheet in book:
            if not sheet.title.startswith("Data"):
                continue
            rows = list(sheet.values)
            if rows[9][0] != "Series ID":
                raise ValueError(f"Unexpected metadata in {sheet.title}")
            for column, code in enumerate(rows[9]):
                if code not in requested:
                    continue
                actual = tuple(part.strip() for part in rows[0][column].split(";") if part.strip())
                if actual != requested[code] or rows[2][column] != "Original":
                    raise ValueError(f"Unexpected description or adjustment for {code}")
                if rows[4][column] != frequency or code in values:
                    raise ValueError(f"Unexpected frequency or duplicate series for {code}")
                dates, numbers = zip(*[
                    (row[0], row[column]) for row in rows[10:]
                    if isinstance(row[0], datetime) and row[column] is not None
                ])
                series = pd.Series(numbers, index=pd.DatetimeIndex(dates), dtype=float).sort_index()
                if not series.index.is_unique or not series.gt(0).all():
                    raise ValueError(f"Duplicate periods or nonpositive index in {code}")
                values[code] = series
    finally:
        book.close()
    if values.keys() != requested.keys():
        raise ValueError(f"Missing series in {filename}: {requested.keys() - values.keys()}")
    return values


def build_panel(filename, ids, frequency, start, end):
    requested = {code: ("Index Numbers", metric, city)
                 for city, codes in ids.items() for metric, code in zip(METRICS, codes)}
    values = read_series(filename, requested, frequency)
    panel = pd.DataFrame({
        (city, metric): values[code] for city, codes in ids.items()
        for metric, code in zip(METRICS, codes)
    }).loc[start:end]
    panel.columns.names = ["City", "Measure"]
    expected = pd.date_range(start, end, freq="MS" if frequency == "Month" else "QS-DEC")
    if not panel.index.equals(expected) or panel.isna().any().any():
        raise ValueError(f"Incomplete {frequency.lower()} panel")
    panel.index.name = "Period"
    return panel


def load_panels():
    monthly = build_panel("abs-monthly-table-10.xlsx", MONTHLY_IDS, "Month",
                          "2024-04-01", "2026-09-01")
    quarterly = build_panel("abs-quarterly-table-9.xlsx", QUARTERLY_IDS, "Quarter",
                            "2019-12-01", "2025-09-01")
    requested = {codes[1]: ("Index Numbers", "All groups CPI", city)
                 for city, codes in MONTHLY_IDS.items()}
    headline = read_series("abs-monthly-table-1.xlsx", requested, "Month")
    for city, (_, code) in MONTHLY_IDS.items():
        pd.testing.assert_series_equal(monthly[city]["All groups CPI"], headline[code],
                                       check_names=False, check_freq=False)
    return monthly, quarterly


def growth_table(panel, start, end):
    growth = panel.loc[end].div(panel.loc[start]).sub(1).mul(100).unstack("Measure").loc[list(CITIES)]
    growth = growth.loc[:, list(METRICS)]
    growth["Rent minus CPI (pp)"] = growth["Rents"] - growth["All groups CPI"]
    return growth


def rebase(panel, base=None):
    return panel.div(panel.loc[base] if base else panel.iloc[0]).mul(100)


def rent_yoy(panel):
    return panel.xs("Rents", axis=1, level="Measure").pct_change(12).mul(100).dropna()


def city_case_notes(monthly):
    cumulative = growth_table(monthly, "2024-04-01", "2026-09-01")
    yoy = rent_yoy(monthly)
    notes = {
        "Canberra": ("Widest gap below local inflation",
                     "Rent growth lagged local CPI over both the latest year and the full monthly window."),
        "Melbourne": ("Rent inflation slowed",
                      "Rents outpaced CPI over the full monthly window, even as annual rent inflation cooled."),
        "Sydney": ("Fastest rent growth in the latest year",
                   "Sydney also posted the largest cumulative rent increase since April 2024."),
    }
    for city in CASE_CITIES:
        title, context = notes[city]
        row = cumulative.loc[city]
        yield (city, title, f"Annual rent inflation went from {yoy.loc['2025-09-01', city]:.2f}% "
               f"to {yoy.loc['2026-09-01', city]:.2f}% between September 2025 and September 2026. "
               f"Since April 2024, rents rose {row['Rents']:.2f}% and local CPI rose "
               f"{row['All groups CPI']:.2f}%. {context}")


def export_panel(monthly, quarterly):
    frames = []
    for label, panel in (("Monthly", monthly), ("Quarterly", quarterly)):
        tidy = panel.stack(["City", "Measure"]).rename("ABS index").reset_index()
        tidy.insert(0, "Frequency", label)
        tidy["Period"] = tidy["Period"].dt.strftime("%Y-%m")
        frames.append(tidy)
    pd.concat(frames, ignore_index=True).to_csv(ROOT / "data/analysis_panel.csv", index=False)


if __name__ == "__main__":
    monthly, quarterly = load_panels()
    export_panel(monthly, quarterly)
    for label, data, start, end in (
        ("Monthly since April 2024", monthly, "2024-04-01", "2026-09-01"),
        ("Year to September 2026", monthly, "2025-09-01", "2026-09-01"),
        ("Quarterly since December 2019", quarterly, "2019-12-01", "2025-09-01"),
        ("Quarterly since September 2022", quarterly, "2022-09-01", "2025-09-01"),
    ):
        print(label)
        print(growth_table(data, start, end).round(2).to_string())
    print(rent_yoy(monthly).loc[["2025-04-01", "2025-09-01", "2026-09-01"]].round(2))
