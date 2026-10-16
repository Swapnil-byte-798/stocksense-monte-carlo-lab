"""Independent selection/evaluation streams, paired policy comparison, and provenance."""

from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
import numbers
import platform
import time

import numpy as np
import scipy
from scipy.stats import t

from . import __version__
from .model import Scenario, uniforms, worlds, outcomes, summarize


def interval(values):
    """Approximate Student-t interval across independent replicate estimates."""
    a = np.asarray(values, dtype=float)
    if len(a) < 2:
        raise ValueError("at least two independent replicates required")
    center = float(a.mean())
    se = float(a.std(ddof=1) / np.sqrt(len(a)))
    width = float(t.ppf(0.975, len(a) - 1) * se)
    return {"estimate": center, "standard_error": se, "low": center - width, "high": center + width}


def run(scenario=None, *, n=4096, replicates=12, seed=2026, method="sobol"):
    s = scenario or Scenario()
    for name, value, low, high in (("n", n, 256, 16384), ("replicates", replicates, 4, 32), ("seed", seed, 0, 2**32 - 1)):
        if isinstance(value, bool) or not isinstance(value, numbers.Integral) or not low <= value <= high:
            raise ValueError(f"{name} must be an integer in [{low}, {high}]")
    started = time.perf_counter()
    config = {"scenario": asdict(s), "n": int(n), "replicates": int(replicates), "seed": int(seed), "method": method}
    # Streams 0 and 1 have disjoint SeedSequence children; evaluation never selects Q.
    train_root, eval_root = np.random.SeedSequence(seed).spawn(2)
    train_seed = int(train_root.generate_state(1)[0])
    train_demand, train_fill = worlds(s, uniforms(n, method, train_seed))
    frontier = [summarize(s, q, train_demand, train_fill) for q in s.orders]
    winner = max(frontier, key=lambda row: row["score"])
    order = winner["order"]
    selected_profits, baseline_profits, all_demand, all_fill = [], [], [], []
    means, deltas, replicate_seeds = [], [], []
    for child in eval_root.spawn(replicates):
        child_seed = int(child.generate_state(1)[0])
        replicate_seeds.append(child_seed)
        demand, fill = worlds(s, uniforms(n, method, child_seed))
        selected = outcomes(s, order, demand, fill)[0]
        baseline = outcomes(s, s.baseline_order, demand, fill)[0]
        means.append(float(selected.mean()))
        deltas.append(float((selected - baseline).mean()))
        selected_profits.append(selected)
        baseline_profits.append(baseline)
        all_demand.append(demand)
        all_fill.append(fill)
    demand, fill = np.concatenate(all_demand), np.concatenate(all_fill)
    profit = np.concatenate(selected_profits)
    chosen = summarize(s, order, demand, fill)
    baseline = summarize(s, s.baseline_order, demand, fill)
    counts, edges = np.histogram(profit, bins=36)
    warnings = [
        "Synthetic, single-period model; results are conditional on assumptions, not real-world savings.",
        "Mean confidence intervals measure simulation error only; tail and service metrics are point estimates.",
    ]
    if order in (int(s.orders[0]), int(s.orders[-1])):
        warnings.append("Selected order is at a grid boundary: expand the search before making a decision.")
    return {
        "schema_version": 1,
        "config_id": hashlib.sha256(json.dumps(config, sort_keys=True).encode()).hexdigest()[:16],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "config": config,
        "provenance": {"version": __version__, "python": platform.python_version(), "numpy": np.__version__, "scipy": scipy.__version__, "train_seed": train_seed, "evaluation_seeds": replicate_seeds},
        "selected": chosen, "baseline": baseline,
        "mean_profit_ci95": interval(means), "paired_delta_ci95": interval(deltas),
        "frontier": frontier,
        "histogram": {"counts": counts.tolist(), "edges": edges.tolist()},
        "replicate_mean_profits": means,
        "evaluation_paths": int(n * replicates),
        "selection_paths": int(n),
        "candidate_count": len(frontier),
        "elapsed_seconds": round(time.perf_counter() - started, 4),
        "warnings": warnings,
    }
