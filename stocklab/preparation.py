"""Optional full UCI workbook ETL; runtime uses the small attributed derivative."""

from pathlib import Path
import hashlib
import json

SOURCE = "https://archive.ics.uci.edu/static/public/502/online%2Bretail%2Bii.zip"
ZIP_SHA = "572e36277c2390fbfde10664750731e0a86f55e33470d91919085f0408e67bfb"
WORKBOOK_SHA = "bcbe73b35f5b7babf197fb0cb983a11f5d9ff929078d4aa53d171b1f2df2e980"
FIRST_WEEK = "2009-12-07"
LAST_WEEK = "2011-11-28"


def clean_transactions(frame):
    import numpy as np
    import pandas as pd

    f = frame.copy()
    audit = [{"stage": "raw", "rows": len(f), "removed": 0}]

    def keep(mask, stage):
        nonlocal f
        before = len(f)
        f = f.loc[mask].copy()
        audit.append({"stage": stage, "rows": len(f), "removed": before - len(f)})

    keep(~f.duplicated(), "exact_duplicate_lines_removed")
    f["InvoiceDate"] = pd.to_datetime(f["InvoiceDate"], errors="coerce")
    keep(f["InvoiceDate"].notna(), "valid_dates")
    keep(
        ~f["Invoice"].astype(str).str.upper().str.startswith("C"),
        "cancellations_excluded",
    )
    for col, name in [("Quantity", "quantity"), ("Price", "price")]:
        f[col] = pd.to_numeric(f[col], errors="coerce")
        keep(np.isfinite(f[col]) & (f[col] > 0), f"positive_finite_{name}")
    f["StockCode"] = f["StockCode"].astype(str).str.strip().str.upper()
    keep(f["StockCode"].str.fullmatch(r"\d{5}[A-Z]?"), "merchandise_code_pattern")
    keep(f["Country"].eq("United Kingdom"), "uk_scope")
    keep(
        (f["InvoiceDate"] >= FIRST_WEEK) & (f["InvoiceDate"] < "2011-12-05"),
        "complete_week_boundaries",
    )
    f["week_start"] = f["InvoiceDate"].dt.to_period("W-SUN").dt.start_time
    return f, audit


def derive_panel(clean, count=5):
    import pandas as pd

    weeks = pd.date_range(FIRST_WEEK, LAST_WEEK, freq="W-MON")
    training = clean[clean["week_start"] < weeks[52]]
    grouped = training.groupby(["StockCode", "week_start"])["Quantity"].sum()
    eligible = []
    for code in sorted(training["StockCode"].unique()):
        values = grouped.loc[code].reindex(weeks[:52], fill_value=0)
        if (values > 0).sum() >= 39 and values.std(ddof=0) / values.mean() <= 2:
            eligible.append((code, int(values.sum()), int((values > 0).sum())))
    chosen = sorted(eligible, key=lambda x: (-x[1], x[0]))[:count]
    products, panels = [], []
    for code, units, active in chosen:
        lines = training[training["StockCode"].eq(code)]
        products.append(
            {
                "stock_code": code,
                "description": str(lines["Description"].mode().iloc[0]),
                "training_units": units,
                "training_active_weeks": active,
                "reference_price_gbp": float(lines["Price"].median()),
            }
        )
        series = (
            clean[clean["StockCode"].eq(code)]
            .groupby("week_start")["Quantity"]
            .sum()
            .reindex(weeks, fill_value=0)
        )
        panels.append(
            pd.DataFrame(
                {
                    "stock_code": code,
                    "week_start": weeks.strftime("%Y-%m-%d"),
                    "units": series.to_numpy(dtype=int),
                }
            )
        )
    return pd.concat(panels, ignore_index=True), products


def prepare(workbook, destination):
    import pandas as pd

    workbook, destination = Path(workbook), Path(destination)
    if hashlib.sha256(workbook.read_bytes()).hexdigest() != WORKBOOK_SHA:
        raise ValueError("Original workbook checksum mismatch")
    sheets = pd.read_excel(workbook, sheet_name=None, engine="openpyxl")
    raw = pd.concat(sheets.values(), ignore_index=True)
    clean, audit = clean_transactions(raw)
    panel, products = derive_panel(clean)
    destination.mkdir(parents=True, exist_ok=True)
    csv = destination / "weekly_sales.csv"
    panel.to_csv(csv, index=False, lineterminator="\n")
    manifest = {
        "dataset": "UCI Online Retail II",
        "dataset_id": 502,
        "citation": "Chen, D. (2012). Online Retail II [Dataset]. UCI Machine Learning Repository. https://doi.org/10.24432/C5CG6D",
        "source_url": SOURCE,
        "source_sha256": ZIP_SHA,
        "workbook_sha256": WORKBOOK_SHA,
        "derived_sha256": hashlib.sha256(csv.read_bytes()).hexdigest(),
        "license": "CC BY 4.0",
        "license_url": "https://creativecommons.org/licenses/by/4.0/",
        "raw_rows": len(raw),
        "cleaned_rows": len(clean),
        "cleaning_audit": audit,
        "first_week": FIRST_WEEK,
        "last_week": LAST_WEEK,
        "weeks_per_product": 104,
        "train_weeks": 52,
        "validation_weeks": 13,
        "test_weeks": 39,
        "selection_rule": "Top five initial-52-week unit volume SKUs; >=39 active training weeks; CV<=2; ties by code. No holdout-based selection.",
        "products": products,
        "limitations": [
            "Sales are a demand proxy; stock availability and lost demand are unobserved.",
            "Exact duplicate removal is an assumption; repeated legitimate identical lines cannot be distinguished.",
            "Missing customer IDs are retained; identifiers are not exported.",
            "Zero sales do not prove zero demand or availability.",
            "Costs, salvage, penalties and supplier stress are assumptions.",
        ],
    }
    (destination / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest
