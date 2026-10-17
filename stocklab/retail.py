"""Verified real observations, empirical scenarios and point-in-time policy replay."""

import csv
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import numpy as np
from .experiment import run
from .model import Scenario, outcomes, summarize, lower_tail_mean, validate_history

DATA = Path(__file__).parent / "data"


def catalog():
    manifest = json.loads((DATA / "manifest.json").read_text())
    if (
        hashlib.sha256((DATA / "weekly_sales.csv").read_bytes()).hexdigest()
        != manifest["derived_sha256"]
    ):
        raise ValueError("Derived weekly sales checksum mismatch")
    return manifest


def product_data(stock_code=None):
    manifest = catalog()
    code = stock_code or manifest["products"][0]["stock_code"]
    product = next((p for p in manifest["products"] if p["stock_code"] == code), None)
    if product is None:
        raise ValueError("Unknown product; use a stock_code from `stocksense data`")
    with (DATA / "weekly_sales.csv").open(newline="") as f:
        rows = [r for r in csv.DictReader(f) if r["stock_code"] == code]
    return manifest, product, rows, validate_history([float(r["units"]) for r in rows])


def scenario_for(history, price):
    h = validate_history(history)
    step = max(1, int(np.ceil(h.max() / 100)))
    return Scenario(
        demand_mean=float(h.mean()),
        demand_cv=float(h.std(ddof=0) / h.mean()),
        price=price,
        cost=round(price * 0.55, 4),
        salvage=round(price * 0.10, 4),
        shortage_penalty=round(price * 0.10, 4),
        disruption_probability=0,
        demand_supply_correlation=0,
        order_min=0,
        order_max=105 * step,
        order_step=step,
        baseline_order=int(round(h.mean())),
    )


def retail_run(stock_code=None, overrides=None, **options):
    m, p, rows, h = product_data(stock_code)
    window = h[-52:]
    fields = asdict(scenario_for(window, p["reference_price_gbp"]))
    supplied = dict(overrides or {})
    for key in ("demand_mean", "demand_cv", "order_min", "order_max", "order_step"):
        supplied.pop(key, None)
    fields.update(supplied)
    return run(
        Scenario(**fields),
        demand_history=window,
        data_context={
            "source": m["dataset"],
            "stock_code": p["stock_code"],
            "description": p["description"],
            "currency": "GBP",
            "license": m["license"],
            "derived_sha256": m["derived_sha256"],
            "window_start": rows[-52]["week_start"],
            "window_end": rows[-1]["week_start"],
            "planning_week": "2011-12-05",
            "observations": 52,
            "price_basis": "initial-52-week median transaction unit price",
        },
        **options,
    )


def choose_order(scenario, history):
    return max(
        (
            summarize(scenario, q, history, np.ones(len(history)))
            for q in scenario.orders
        ),
        key=lambda r: r["score"],
    )["order"]


def replay_product(values, dates, price, start=65, lookback=52):
    values = validate_history(values)
    if start < lookback or start >= len(values) or len(dates) != len(values):
        raise ValueError("Invalid replay boundaries")
    records = []
    for t in range(start, len(values)):
        past = values[t - lookback : t]
        s = scenario_for(past, price)
        orders = {
            "empirical_risk": choose_order(s, past),
            "empirical_profit": choose_order(
                Scenario(**{**asdict(s), "risk_weight": 0}), past
            ),
            "trailing_mean": int(round(past.mean())),
            "seasonal_naive": int(values[t - 52]),
        }
        for policy, q in orders.items():
            profit, sold, unmet = outcomes(s, q, np.array([values[t]]), np.ones(1))
            records.append(
                {
                    "week_start": dates[t],
                    "training_last_week": dates[t - 1],
                    "policy": policy,
                    "order": q,
                    "observed_sales": int(values[t]),
                    "profit_proxy_gbp": float(profit[0]),
                    "fulfilled_units": float(sold[0]),
                    "unmet_proxy_units": float(unmet[0]),
                }
            )
    policies = []
    forecasts = {}
    for policy in orders:
        rows = [r for r in records if r["policy"] == policy]
        profits = np.array([r["profit_proxy_gbp"] for r in rows])
        total = sum(r["observed_sales"] for r in rows)
        policies.append(
            {
                "policy": policy,
                "weeks": len(rows),
                "mean_profit_proxy_gbp": float(profits.mean()),
                "total_profit_proxy_gbp": float(profits.sum()),
                "worst_5pct_profit_proxy_gbp": lower_tail_mean(profits, 0.05),
                "fill_rate_proxy": (
                    sum(r["fulfilled_units"] for r in rows) / total if total else 1
                ),
                "stockout_probability_proxy": sum(
                    r["unmet_proxy_units"] > 0 for r in rows
                )
                / len(rows),
            }
        )
        if policy in ("trailing_mean", "seasonal_naive"):
            error = sum(abs(r["order"] - r["observed_sales"]) for r in rows)
            forecasts[policy] = {
                "mae_units": error / len(rows),
                "wape": error / total if total else None,
            }
    return {
        "policies": policies,
        "forecast_diagnostics": forecasts,
        "weekly_records": records,
    }


def backtest_all():
    m = catalog()
    report = {
        "dataset": m["dataset"],
        "derived_sha256": m["derived_sha256"],
        "split": {
            "initial_training_weeks": 52,
            "validation_weeks": 13,
            "test_weeks": 39,
            "rolling_lookback": 52,
        },
        "economic_assumptions": {
            "cost_fraction": 0.55,
            "salvage_fraction": 0.10,
            "shortage_penalty_fraction": 0.10,
            "risk_weight": 0.2,
            "supplier_fill": 1,
            "carryover": False,
        },
        "interpretation": "Chronological sales-proxy replay under assumed economics; not actual profits or causal savings.",
        "products": [],
    }
    for p in m["products"]:
        _, _, rows, h = product_data(p["stock_code"])
        dates = [r["week_start"] for r in rows]
        report["products"].append(
            {
                **p,
                "history": [
                    {"week_start": r["week_start"], "units": int(r["units"])}
                    for r in rows
                ],
                "validation_forecasts": replay_product(
                    h[:65], dates[:65], p["reference_price_gbp"], start=52
                )["forecast_diagnostics"],
                **replay_product(h, dates, p["reference_price_gbp"]),
            }
        )
    return report
