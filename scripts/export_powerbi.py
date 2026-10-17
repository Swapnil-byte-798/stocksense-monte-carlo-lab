"""Generate a complete Power BI import mart and seeded scenario cube (no web stack)."""

import argparse
import csv
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import itertools
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from stocklab.retail import catalog, product_data, retail_run, backtest_all

ROOT = Path(__file__).resolve().parents[1]
SCENARIO_GRID = {
    "risk": [0, 0.2, 0.5],
    "cost": [0.45, 0.55, 0.65],
    "stress": [0, 0.1, 0.25],
}


def write_csv(path, rows):
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def export(destination, n=4096, replicates=12, method="sobol", seed=2026):
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    m = catalog()
    replay = backtest_all()
    scenarios = []
    for risk, cost, stress in itertools.product(
        SCENARIO_GRID["risk"], SCENARIO_GRID["cost"], SCENARIO_GRID["stress"]
    ):
        key = f"R{round(risk*100)}-C{round(cost*100)}-S{round(stress*100)}"
        scenarios.append(
            {
                "scenario_key": key,
                "scenario_label": f"Risk {risk:.0%} | Cost {cost:.0%} | Supply stress {stress:.0%}",
                "risk_weight": risk,
                "cost_fraction": cost,
                "disruption_probability": stress,
            }
        )
    summary = []
    curves = []
    histograms = []
    runs = []
    for product in m["products"]:
        for setting in scenarios:
            price = product["reference_price_gbp"]
            r = retail_run(
                product["stock_code"],
                {
                    "risk_weight": setting["risk_weight"],
                    "cost": round(price * setting["cost_fraction"], 4),
                    "disruption_probability": setting["disruption_probability"],
                },
                n=n,
                replicates=replicates,
                method=method,
                seed=seed,
            )
            key = {
                "stock_code": product["stock_code"],
                "scenario_key": setting["scenario_key"],
            }
            summary.append(
                {
                    **key,
                    "config_id": r["config_id"],
                    "selected_order": r["selected"]["order"],
                    "baseline_order": r["baseline"]["order"],
                    "mean_profit_proxy_gbp": r["selected"]["mean_profit"],
                    "baseline_profit_proxy_gbp": r["baseline"]["mean_profit"],
                    "tail_profit_proxy_gbp": r["selected"]["tail_profit"],
                    "baseline_tail_profit_proxy_gbp": r["baseline"]["tail_profit"],
                    "fill_rate_proxy": r["selected"]["fill_rate"],
                    "baseline_fill_rate_proxy": r["baseline"]["fill_rate"],
                    "loss_probability": r["selected"]["loss_probability"],
                    "stockout_probability_proxy": r["selected"]["stockout_probability"],
                    "paired_delta_gbp": r["paired_delta_ci95"]["estimate"],
                    "paired_ci_low_gbp": r["paired_delta_ci95"]["low"],
                    "paired_ci_high_gbp": r["paired_delta_ci95"]["high"],
                    "mean_ci_low_gbp": r["mean_profit_ci95"]["low"],
                    "mean_ci_high_gbp": r["mean_profit_ci95"]["high"],
                    "method": method,
                    "seed": seed,
                    "selection_worlds": n,
                    "evaluation_worlds": n * replicates,
                    "replicates": replicates,
                    "history_sha256": r["config"]["history_sha256"],
                }
            )
            curves.extend(
                {
                    **key,
                    "order": f["order"],
                    "mean_profit_proxy_gbp": f["mean_profit"],
                    "tail_profit_proxy_gbp": f["tail_profit"],
                    "score_gbp": f["score"],
                    "fill_rate_proxy": f["fill_rate"],
                }
                for f in r["frontier"]
            )
            histograms.extend(
                {
                    **key,
                    "bin_index": i,
                    "bin_low_gbp": r["histogram"]["edges"][i],
                    "bin_mid_gbp": (
                        r["histogram"]["edges"][i] + r["histogram"]["edges"][i + 1]
                    )
                    / 2,
                    "bin_high_gbp": r["histogram"]["edges"][i + 1],
                    "worlds": count,
                }
                for i, count in enumerate(r["histogram"]["counts"])
            )
            runs.append(
                {
                    "scenario_key": setting["scenario_key"],
                    "stock_code": product["stock_code"],
                    **r,
                }
            )
        print(
            f"Prepared {product['stock_code']} × {len(scenarios)} scenarios", flush=True
        )
    weeks = []
    dates = []
    _, _, rows, _ = product_data()
    for i, row in enumerate(rows):
        split = "Training" if i < 52 else "Validation" if i < 65 else "Test"
        dates.append(
            {
                "week_start": row["week_start"],
                "week_index": i + 1,
                "split": split,
                "year": int(row["week_start"][:4]),
            }
        )
    for p in m["products"]:
        _, _, rows, _ = product_data(p["stock_code"])
        weeks.extend({**r, "units": int(r["units"])} for r in rows)
    policy_summary = []
    weekly = []
    forecast = []
    for p in replay["products"]:
        policy_summary.extend(
            {"stock_code": p["stock_code"], **v} for v in p["policies"]
        )
        weekly.extend({"stock_code": p["stock_code"], **v} for v in p["weekly_records"])
        for split, diagnostic in [
            ("Validation", p["validation_forecasts"]),
            ("Test", p["forecast_diagnostics"]),
        ]:
            forecast.extend(
                {
                    "stock_code": p["stock_code"],
                    "split": split,
                    "policy": name,
                    **values,
                }
                for name, values in diagnostic.items()
            )
    products = [
        {**p, "product_label": p["stock_code"] + " | " + p["description"]}
        for p in m["products"]
    ]
    notes = [
        {
            "topic": "Source",
            "explanation": m["citation"]
            + " | CC BY 4.0; filtered and aggregated derivative.",
        },
        {
            "topic": "Sales ≠ demand",
            "explanation": "Inventory availability and lost demand are absent; zero sales may reflect missing availability.",
        },
        {
            "topic": "Economics",
            "explanation": "Reference price observed in initial training. Costs 45/55/65%, salvage 10%, penalty 10% are assumptions.",
        },
        {
            "topic": "Historical test",
            "explanation": "52 initial training, 13 diagnostics, 39 rolling test weeks. Each decision sees preceding 52 weeks only.",
        },
        {
            "topic": "Numerical CI",
            "explanation": "Paired independent-replicate numerical interval; excludes history, model and economic uncertainty.",
        },
        {
            "topic": "Supply stress",
            "explanation": "Hypothetical disruption 0/10/25%; delivered fraction 65%, latent correlation 0. No observed supplier data.",
        },
        {
            "topic": "Scenario explorer",
            "explanation": "Slicers select precomputed seeded runs. New assumptions require Python export then Power BI Refresh.",
        },
        {
            "topic": "Business limit",
            "explanation": "Modeled profit/service proxies. No actual company savings, causal uplift or live procurement.",
        },
    ]
    tables = {
        "Products": products,
        "Weeks": dates,
        "WeeklySales": weeks,
        "Scenarios": scenarios,
        "SimulationSummary": summary,
        "PolicyCurve": curves,
        "ProfitHistogram": histograms,
        "ReplaySummary": policy_summary,
        "ReplayWeekly": weekly,
        "ForecastDiagnostics": forecast,
        "CleaningAudit": m["cleaning_audit"],
        "ModelNotes": notes,
    }
    for name, data in tables.items():
        write_csv(destination / (name + ".csv"), data)
    # Machine-readable schema drives native M import types and validation.
    schema = {}
    for name, data in tables.items():
        schema[name] = {}
        for col, value in data[0].items():
            schema[name][col] = (
                "dateTime"
                if col in ("week_start", "training_last_week")
                else (
                    "int64"
                    if isinstance(value, int) and not any(isinstance(row[col], float) for row in data)
                    else "double" if isinstance(value, float) else "string"
                )
            )
    files = {
        p.name: {
            "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
            "bytes": p.stat().st_size,
        }
        for p in sorted(destination.glob("*.csv"))
    }
    metadata = {
        "dataset": m["dataset"],
        "derived_sha256": m["derived_sha256"],
        "method": method,
        "seed": seed,
        "selection_worlds": n,
        "evaluation_worlds": n * replicates,
        "replicates": replicates,
        "scenario_count": len(scenarios),
        "product_scenario_count": len(summary),
        "default_scenario": "R20-C55-S0",
        "table_rows": {name: len(rows) for name, rows in tables.items()},
        "schema": schema,
        "files": files,
        "warning": "Import report. Slicers do not execute Python. Profit is an assumption-based proxy.",
    }
    (destination / "export_manifest.json").write_text(
        json.dumps(metadata, indent=2) + "\n"
    )
    (ROOT / "examples/retail-backtest.json").write_text(
        json.dumps(replay, indent=2) + "\n"
    )
    default = next(
        r
        for r in runs
        if r["stock_code"] == "85123A" and r["scenario_key"] == "R20-C55-S0"
    )
    (ROOT / "examples/default-run.json").write_text(
        json.dumps(default, indent=2) + "\n"
    )
    (ROOT / "examples/scenario.json").write_text(
        json.dumps(default["config"]["scenario"], indent=2) + "\n"
    )
    return metadata


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "powerbi/data")
    parser.add_argument("--n", type=int, default=4096)
    parser.add_argument("--replicates", type=int, default=12)
    parser.add_argument("--method", choices=["mc", "sobol"], default="sobol")
    parser.add_argument("--seed", type=int, default=2026)
    a = parser.parse_args()
    result = export(a.output, a.n, a.replicates, a.method, a.seed)
    print(
        json.dumps(
            {
                "tables": result["table_rows"],
                "scenario_runs": result["product_scenario_count"],
            },
            indent=2,
        )
    )
