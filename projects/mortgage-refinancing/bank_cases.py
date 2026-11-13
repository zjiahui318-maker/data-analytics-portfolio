"""Compare reported Australian housing loan balances at three named banks."""

import csv
from datetime import date, datetime
from math import isclose, isfinite
from pathlib import Path

from openpyxl import load_workbook

DATA = Path(__file__).resolve().parent / "data"
APRA = "https://www.apra.gov.au/news-and-publications/monthly-authorised-deposit-taking-institution-statistics"
BANKS = {
    "CBA": (48123123124, "Commonwealth Bank of Australia"),
    "NAB": (12004044937, "National Australia Bank Limited"),
    "Westpac": (33007457141, "Westpac Banking Corporation"),
}
START, END = date(2025, 9, 30), date(2026, 9, 30)
FIELDS = ("Housing: Owner-occupied", "Housing: Investment")


def load_balances():
    """Return (owner, investor) balances in AUD millions by bank and month."""
    by_abn = {abn: bank for bank, (abn, _) in BANKS.items()}
    data = {bank: {} for bank in BANKS}
    history = load_workbook(DATA / "raw/apra-madis-history-sep-2026.xlsx", read_only=True, data_only=True)
    try:
        rows = iter(history["Table 1"].values)
        if next(rows)[0] != "($million)":
            raise ValueError("Unexpected unit in APRA back series")
        headers = next(rows)
        period, identifier, name = (headers.index(label) for label in ("Period", "ABN", "Institution Name"))
        measures = [headers.index("Loans to households: " + label) for label in FIELDS]
        for row in rows:
            when, bank = row[period], by_abn.get(row[identifier])
            if bank is None or not isinstance(when, datetime) or not START <= when.date() <= END:
                continue
            values = tuple(row[column] for column in measures)
            if (row[name] != BANKS[bank][1] or when.date() in data[bank]
                    or not all(isinstance(value, (float, int)) and isfinite(value) and value > 0
                               for value in values)):
                raise ValueError(f"Invalid or duplicate APRA row for {bank} at {when:%Y-%m}")
            data[bank][when.date()] = values
    finally:
        history.close()
    expected = {(2025, m) for m in range(9, 13)} | {(2026, m) for m in range(1, 10)}
    for bank, series in data.items():
        if len(series) != len(expected) or {(d.year, d.month) for d in series} != expected:
            raise ValueError(f"Incomplete monthly series for {bank}")

    issue = load_workbook(DATA / "raw/apra-madis-sep-2026.xlsx", read_only=True, data_only=True)
    try:
        rows = iter(issue["Table 2 "].values)
        if "($ million)" not in next(rows)[0] or next(rows)[0] != "September 2026":
            raise ValueError("Unexpected period or unit in APRA issue")
        headers = next(rows)
        measures = [headers.index(label) for label in FIELDS]
        names = {name: bank for bank, (_, name) in BANKS.items()}
        found = set()
        for row in rows:
            bank = names.get(row[0])
            if bank is None:
                continue
            if bank in found or any(not isclose(row[column], value, abs_tol=0.01, rel_tol=0)
                                    for column, value in zip(measures, data[bank][END])):
                raise ValueError(f"September 2026 Table 2 reconciliation failed for {bank}")
            found.add(bank)
        if found != set(BANKS):
            raise ValueError("Missing bank in APRA monthly release")
    finally:
        issue.close()
    return data


def metrics(start, end):
    owner0, investor0 = start
    owner1, investor1 = end
    return {
        "balance": sum(end) / 1000,
        "growth": 100 * (sum(end) / sum(start) - 1),
        "owner_delta": (owner1 - owner0) / 1000,
        "investor_delta": (investor1 - investor0) / 1000,
        "owner_growth": 100 * (owner1 / owner0 - 1),
        "investor_growth": 100 * (investor1 / investor0 - 1),
        "investor_share": 100 * investor1 / sum(end),
        "share_change": 100 * (investor1 / sum(end) - investor0 / sum(start)),
    }


def summarize(data):
    cases = {bank: metrics(series[START], series[END]) for bank, series in data.items()}
    start, end = (tuple(map(sum, zip(*(series[when] for series in data.values())))) for when in (START, END))
    combined = metrics(start, end)
    for row in cases.values():
        row["growth_share"] = 100 * (row["owner_delta"] + row["investor_delta"]) / (
            combined["owner_delta"] + combined["investor_delta"])
    return cases, combined


def main():
    data = load_balances()
    with (DATA / "bank_cases_monthly.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(("month_end", "bank", "abn", "institution_name", "owner_occupied_aud_m", "investment_aud_m"))
        for bank, series in data.items():
            for when, values in sorted(series.items()):
                writer.writerow((when, bank, *BANKS[bank], *values))
    cases, combined = summarize(data)
    for name, row in [*cases.items(), ("Combined", combined)]:
        print(name, {key: round(value, 2) for key, value in row.items()})


if __name__ == "__main__":
    main()
