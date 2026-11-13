"""Build a reproducible quarterly panel from the retained RBA and ABS releases."""

import csv
import json
from calendar import monthrange
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path
from statistics import correlation, mean

from lxml import html

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
RBA = "https://www.rba.gov.au/statistics/tables/#interest-rates"
RBA_CSV = "https://www.rba.gov.au/statistics/tables/csv/f6-data.csv"
ABS = "https://www.abs.gov.au/statistics/economy/finance/lending-indicators/sep-quarter-2026"
PURPOSES = {
    "Owner occupier": ("FLRHOOTA", "FLRHOFTA", "FLRHOOVA", "FLRHOFVA"),
    "Investor": ("FLRHIOTA", "FLRHIFTA", "FLRHIOVA", "FLRHIFVA"),
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def quarter_end(day):
    month = (day.month + 2) // 3 * 3
    return date(day.year, month, monthrange(day.year, month)[1])


def quarter_number(day):
    return day.year * 4 + (day.month - 1) // 3


def read_rates():
    path = DATA / "raw/rba-f6-2026-11-06.csv"
    with path.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.reader(stream))
    metadata = {row[0]: row for row in rows[1:11] if row}
    index = {series: col for col, series in enumerate(metadata["Series ID"])}
    for ids in PURPOSES.values():
        for series in ids:
            col = index[series]
            require(metadata["Units"][col] == "Per cent per annum", series)
            require(metadata["Frequency"][col] == "Monthly", series)
            require(metadata["Publication date"][col] == "06-Nov-2026", series)
    monthly = defaultdict(list)
    seen = set()
    for row in rows[11:]:
        if not row or not row[0]:
            continue
        day = datetime.strptime(row[0], "%d/%m/%Y").date()
        require(day not in seen, f"Duplicate RBA month: {day}")
        seen.add(day)
        monthly[quarter_end(day)].append(row)

    rates = {}
    for quarter, records in sorted(monthly.items()):
        if len(records) != 3:
            continue
        for segment, ids in PURPOSES.items():
            values = [[row[index[series]] for row in records] for series in ids]
            require(all(all(group) for group in values), f"Missing F6 data: {quarter} {segment}")
            rates[quarter, segment] = tuple(mean(map(float, group)) for group in values)
    return rates


def read_counts():
    path = DATA / "raw/abs-lending-2026-q3.html"
    document = html.fromstring(path.read_bytes())
    fields = [
        f"{segment}, {channel} refinancing (seasadj) (no.)"
        for segment in PURPOSES
        for channel in ("external", "internal")
    ]
    matches = []
    for table in document.xpath("//table"):
        rows = [
            [" ".join(cell.text_content().split()) for cell in row.xpath("./th|./td")]
            for row in table.xpath(".//tr")
        ]
        if rows and set(fields).issubset(rows[0]):
            matches.append(rows)
    require(len(matches) == 1, "Expected one ABS national refinancing counts table")
    header, *body = matches[0]
    counts = {}
    for row in body:
        quarter = quarter_end(datetime.strptime(row[0], "%b-%y").date())
        for segment in PURPOSES:
            values = [row[header.index(f"{segment}, {channel} refinancing (seasadj) (no.)")]
                      for channel in ("external", "internal")]
            if "NA" in values:
                continue
            key = (quarter, segment)
            require(key not in counts, f"Duplicate ABS quarter: {key}")
            counts[key] = tuple(int(value.replace(",", "")) for value in values)
    return counts


def build_panel(rates, counts):
    panel = []
    for segment in PURPOSES:
        keys = sorted(key for key in rates.keys() & counts.keys() if key[1] == segment)
        previous = None
        for quarter, _ in keys:
            outstanding, new, variable_outstanding, variable_new = rates[quarter, segment]
            external, internal = counts[quarter, segment]
            require(external > 0 and internal > 0, f"Unexpected count: {quarter} {segment}")
            row = {
                "date": quarter.isoformat(),
                "quarter": f"{quarter.year} Q{(quarter.month + 2) // 3}",
                "segment": segment,
                "outstandingRate": round(outstanding, 6),
                "newRate": round(new, 6),
                "gapBp": round((outstanding - new) * 100, 6),
                "variableGapBp": round((variable_outstanding - variable_new) * 100, 6),
                "external": external,
                "internal": internal,
                "externalShare": round(external / (external + internal), 8),
                "gapChangeBp": None,
                "variableGapChangeBp": None,
                "externalGrowth": None,
                "nextExternalGrowth": None,
            }
            if previous:
                require(quarter_number(quarter) - quarter_number(date.fromisoformat(previous["date"])) == 1,
                        f"Nonconsecutive quarters before {quarter}")
                row["gapChangeBp"] = round(row["gapBp"] - previous["gapBp"], 6)
                row["variableGapChangeBp"] = round(row["variableGapBp"] - previous["variableGapBp"], 6)
                row["externalGrowth"] = round(external / previous["external"] - 1, 8)
                previous["nextExternalGrowth"] = row["externalGrowth"]
            previous = row
            panel.append(row)
    return panel


def association(rows, x, y):
    pairs = [(r[x], r[y]) for r in rows if r[x] is not None and r[y] is not None]
    estimate = correlation(*zip(*pairs))
    loo = [correlation(*zip(*(pairs[:i] + pairs[i+1:]))) for i in range(len(pairs))]
    return {"n": len(pairs), "r": round(estimate, 4),
            "looMin": round(min(loo), 4), "looMax": round(max(loo), 4)}


def source_query(panel):
    return {
        "rows": panel,
        "source": {
            "label": "RBA F6 and ABS Lending Indicators",
            "files": [
                {"name": "RBA F6 CSV, 6 November 2026", "url": RBA_CSV},
                {"name": "ABS Lending Indicators, September quarter 2026", "url": ABS},
            ],
            "filters": ["Australia, owner-occupier and investor, 2019 Q3 to 2026 Q3"],
            "evidenceFlow": [
                {"title": "RBA Housing Lending Rates (F6)", "detail": "Monthly all-institution new and outstanding rates, % p.a. " +
                 "Owner occupier: FLRHOOTA, FLRHOFTA. Investor: FLRHIOTA, FLRHIFTA. Variable-rate sensitivity: FLRHOOVA, FLRHOFVA, FLRHIOVA, FLRHIFVA."},
                {"title": "ABS Lending Indicators", "detail": "National chart table for quarterly seasonally adjusted internal and external refinancing commitments (number)."},
                {"title": "Join by calendar quarter and loan purpose", "detail": "Average three monthly RBA observations per quarter with equal weights. Match to the ABS quarter and loan purpose; keep complete common quarters."},
            ],
            "metricDefinitions": [
                {"label": "New-loan discount", "definition": "Quarterly average outstanding rate minus new-loan rate. A positive value means the average new rate was lower.", "formula": "(outstandingRate - newRate) * 100"},
                {"label": "External share of refinancing", "definition": "External commitments divided by internal plus external commitments for the selected purpose.", "formula": "external / (external + internal)"},
                {"label": "External refinancing growth", "definition": "Change in external commitments versus the preceding quarter, divided by the preceding quarter's commitments."},
            ],
        },
        "methods": [
            {"language": "text", "code": "Run python analyze.py with the retained snapshots in data/raw. Rates are simple quarterly averages of 3 published monthly rates. Refinance flows are published ABS quarterly counts. Pearson r is descriptive."}
        ],
    }


def main():
    panel = build_panel(read_rates(), read_counts())
    results = {}
    expected = {
        "Owner occupier": (63475, 41905),
        "Investor": (34143, 13936),
    }
    for segment in PURPOSES:
        rows = [row for row in panel if row["segment"] == segment]
        require(len(rows) == 29 and rows[0]["quarter"] == "2019 Q3", f"Coverage changed: {segment}")
        require(rows[-1]["quarter"] == "2026 Q3", f"Unexpected endpoint: {segment}")
        require((rows[-1]["external"], rows[-1]["internal"]) == expected[segment],
                f"Latest counts do not match ABS release headline: {segment}")
        results[segment] = {
            "levels": association(rows, "gapBp", "external"),
            "sameQuarter": association(rows, "gapChangeBp", "externalGrowth"),
            "nextQuarter": association(rows, "gapChangeBp", "nextExternalGrowth"),
            "sameQuarterVariable": association(rows, "variableGapChangeBp", "externalGrowth"),
            "nextQuarterVariable": association(rows, "variableGapChangeBp", "nextExternalGrowth"),
        }
    with (DATA / "quarterly.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=panel[0].keys())
        writer.writeheader()
        writer.writerows(panel)
    (DATA / "results.json").write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    snapshot = {
        "surface": "dashboard",
        "title": "Australian mortgage refinancing",
        "generatedAt": "2026-11-13T00:00:00+11:00",
        "status": "reviewed",
        "buildStatus": "creating",
        "exportPreferences": {"selected": None, "destinations": []},
        "filters": [{"id": "purpose", "label": "Loan purpose", "field": "segment",
                     "defaultValue": "Owner occupier", "queryIds": ["mortgage_quarters"]}],
        "queries": {"mortgage_quarters": source_query(panel)},
    }
    (DATA / "snapshot.json").write_text(json.dumps(snapshot, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
