"""Strict import of positive, uncensored demand observations, fitted by log moments."""

import csv
from datetime import date
import hashlib
from pathlib import Path

import numpy as np


def calibrate(path):
    path = Path(path)
    if path.stat().st_size > 5_000_000:
        raise ValueError("CSV must be smaller than 5 MB")
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != ["date", "demand"]:
            raise ValueError("CSV columns must be exactly date,demand")
        observations, dates = [], []
        for row in reader:
            dates.append(date.fromisoformat(row["date"]))
            value = float(row["demand"])
            if not np.isfinite(value) or value <= 0:
                raise ValueError("demand must be positive and finite; zero-demand data needs a different model")
            observations.append(value)
    if len(observations) < 30 or len(set(dates)) != len(dates):
        raise ValueError("need >=30 observations with unique dates")
    log_values = np.log(observations)
    mu, variance = float(log_values.mean()), float(log_values.var(ddof=0))
    mean = float(np.exp(mu + variance / 2))
    cv = float(np.sqrt(np.expm1(variance)))
    if not np.isfinite(mean) or not np.isfinite(cv) or not 1 <= mean <= 1e6 or cv > 2:
        raise ValueError("fitted moments exceed supported scenario bounds")
    return {"demand_mean": mean, "demand_cv": cv, "observations": len(observations), "first_date": min(dates).isoformat(), "last_date": max(dates).isoformat(), "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "method": "lognormal maximum likelihood, positive demand only", "warning": "No seasonality, censoring correction, or parameter-uncertainty intervals; validate fit before use."}
