"""Paired historical policy comparison; this is not a randomized customer A/B test."""

from datetime import date
import math

import numpy as np


def block_indices(n, block_length, replicates, seed):
    """Circular moving-block bootstrap; retain weekly alignment across all products."""
    if not (2 <= n and 1 <= block_length <= n and replicates >= 100):
        raise ValueError("Invalid week count, block length or replicate count")
    rng = np.random.default_rng(seed)
    starts = rng.integers(0, n, size=(replicates, math.ceil(n / block_length)))
    return ((starts[:, :, None] + np.arange(block_length)) % n).reshape(replicates, -1)[
        :, :n
    ]


def paired_panel(report, candidate="empirical_risk", baseline="trailing_mean"):
    if candidate == baseline:
        raise ValueError("Candidate and baseline must differ")
    products = report["products"]
    if not products:
        raise ValueError("No products")
    panels, codes, calendar = [], [], None
    for product in products:
        code = product["stock_code"]
        if code in codes:
            raise ValueError("Duplicate product")
        records = {}
        for row in product["weekly_records"]:
            if row["policy"] not in [candidate, baseline]:
                continue
            key = (row["week_start"], row["policy"])
            if key in records:
                raise ValueError("Duplicate product-week-policy observation")
            if row["training_last_week"] >= row["week_start"]:
                raise ValueError("Forecast uses same/future week")
            records[key] = row
        weeks = sorted({key[0] for key in records})
        if len(weeks) < 12:
            raise ValueError("At least 12 paired weeks required")
        if any(
            (date.fromisoformat(b) - date.fromisoformat(a)).days != 7
            for a, b in zip(weeks, weeks[1:])
        ):
            raise ValueError("Calendar contains missing weeks")
        if calendar is not None and weeks != calendar:
            raise ValueError("Products must share an identical weekly calendar")
        calendar = weeks
        paired = []
        for week in weeks:
            try:
                a, b = records[(week, candidate)], records[(week, baseline)]
            except KeyError as exc:
                raise ValueError("Missing candidate/baseline pair") from exc
            if a["observed_sales"] != b["observed_sales"]:
                raise ValueError("Paired policies must see identical observed sales")
            if a["training_last_week"] != b["training_last_week"]:
                raise ValueError("Paired policies must share a forecast origin")
            values = [
                a["profit_proxy_gbp"] - b["profit_proxy_gbp"],
                a["fulfilled_units"] - b["fulfilled_units"],
                a["observed_sales"],
            ]
            if not np.isfinite(values).all() or values[2] < 0:
                raise ValueError("Non-finite outcome or negative sales")
            paired.append(values)
        panels.append(paired)
        codes.append(code)
    return calendar, codes, np.asarray(panels).transpose(1, 0, 2)


def summarize(values, indices):
    if values[:, 2].sum() <= 0:
        raise ValueError("Positive observed sales required")
    samples = values[indices]
    profit = samples[:, :, 0].mean(axis=1)
    denom = samples[:, :, 2].sum(axis=1)
    if (denom <= 0).any():
        raise ValueError("Bootstrap sample has zero sales; cannot estimate fill rate")
    fill = samples[:, :, 1].sum(axis=1) / denom
    return {
        "mean_weekly_profit_proxy_delta_gbp": float(values[:, 0].mean()),
        "profit_proxy_ci95_gbp": np.quantile(profit, [0.025, 0.975]).tolist(),
        "fulfilled_observed_unit_rate_delta": float(
            values[:, 1].sum() / values[:, 2].sum()
        ),
        "fill_delta_ci95": np.quantile(fill, [0.025, 0.975]).tolist(),
    }


def compare_policies(
    report,
    candidate="empirical_risk",
    baseline="trailing_mean",
    replicates=20000,
    seed=2026,
    service_margin=0.02,
):
    if not 0 <= service_margin <= 1:
        raise ValueError("Service margin must be in [0,1]")
    weeks, codes, panel = paired_panel(report, candidate, baseline)
    results = []
    for length in [2, 4, 8]:
        indices = block_indices(len(weeks), length, replicates, seed)
        for scope, values in [("portfolio", panel.sum(axis=1))] + [
            (code, panel[:, i, :]) for i, code in enumerate(codes)
        ]:
            results.append(
                {
                    "scope": scope,
                    "block_length_weeks": length,
                    "primary": scope == "portfolio" and length == 4,
                    **summarize(values, indices),
                }
            )
    primary = next(row for row in results if row["primary"])
    passed = (
        primary["profit_proxy_ci95_gbp"][0] > 0
        and primary["fill_delta_ci95"][0] >= -service_margin
    )
    return {
        "comparison_type": "paired historical replay, not randomized A/B",
        "candidate": candidate,
        "baseline": baseline,
        "weeks": len(weeks),
        "products": codes,
        "first_week": weeks[0],
        "last_week": weeks[-1],
        "bootstrap": {
            "method": "circular moving blocks",
            "replicates": replicates,
            "seed": seed,
            "primary_block_length_weeks": 4,
            "sensitivity_block_lengths": [2, 8],
        },
        "illustrative_gate": {
            "profit_lower_bound_above_zero": True,
            "maximum_fill_rate_drop": service_margin,
            "passes_both": bool(passed),
            "decision": "further prospective validation"
            if passed
            else "do not promote on this evidence",
            "note": "Retrospective gate defined after prior project results; not a preregistered decision.",
        },
        "results": results,
        "limitations": [
            "Real observed sales; profit depends on assumed costs and weekly reset, not actual realized profit.",
            "Resample the same weeks for both policies and every SKU; retain local serial and cross-product dependence.",
            "39 historical weeks are short; trend/seasonality can violate approximate block stationarity.",
            "Pointwise percentile intervals; product and block-length sensitivity rows are exploratory, not multiple confirmed wins.",
            "No customer randomization, intervention, live A/B result, future-savings guarantee, or automatic operational change.",
        ],
    }
