"""Pure model primitives; no filesystem, network, or global RNG state."""

from dataclasses import dataclass, asdict
import math
import numbers

import numpy as np
from scipy.stats import lognorm, norm, qmc


@dataclass(frozen=True)
class Scenario:
    demand_mean: float = 1000
    demand_cv: float = 0.35
    price: float = 50
    cost: float = 28
    salvage: float = 8
    shortage_penalty: float = 5
    disruption_probability: float = 0.08
    disrupted_fill: float = 0.65
    demand_supply_correlation: float = 0.25
    risk_weight: float = 0.20
    tail_probability: float = 0.05
    order_min: int = 400
    order_max: int = 1800
    order_step: int = 25
    baseline_order: int = 1000

    def __post_init__(self):
        for key, value in asdict(self).items():
            if isinstance(value, bool) or not isinstance(value, numbers.Real) or not math.isfinite(value):
                raise ValueError(f"{key} must be a finite number")
        for key in ("order_min", "order_max", "order_step", "baseline_order"):
            if not isinstance(getattr(self, key), numbers.Integral):
                raise ValueError(f"{key} must be an integer")
        if not 1 <= self.demand_mean <= 1e6 or not 0 <= self.demand_cv <= 2:
            raise ValueError("demand_mean must be in [1, 1000000] and demand_cv in [0, 2]")
        if not 0 <= self.salvage < self.cost < self.price <= 1e6:
            raise ValueError("require 0 <= salvage < cost < price <= 1000000")
        if not 0 <= self.shortage_penalty <= 1e6:
            raise ValueError("shortage_penalty must be in [0, 1000000]")
        for key in ("disruption_probability", "disrupted_fill", "risk_weight"):
            if not 0 <= getattr(self, key) <= 1:
                raise ValueError(f"{key} must be in [0, 1]")
        if not -0.95 <= self.demand_supply_correlation <= 0.95:
            raise ValueError("latent correlation must be in [-0.95, 0.95]")
        if not 0.01 <= self.tail_probability <= 0.25:
            raise ValueError("tail_probability must be in [0.01, 0.25]")
        if not 0 <= self.order_min < self.order_max <= 2_000_000 or self.order_step < 1:
            raise ValueError("invalid order grid")
        if (self.order_max - self.order_min) // self.order_step + 1 > 121:
            raise ValueError("order grid must contain at most 121 candidates")
        if not 0 <= self.baseline_order <= 2_000_000:
            raise ValueError("baseline_order out of range")

    @property
    def orders(self):
        """Grid upper endpoint is included only when divisible by the step."""
        return np.arange(self.order_min, self.order_max + 1, self.order_step)


def uniforms(n: int, method: str, seed: int) -> np.ndarray:
    """Two uniform dimensions. Dependence within a Sobol replicate is intentional."""
    if isinstance(n, bool) or not isinstance(n, numbers.Integral) or n < 2:
        raise ValueError("sample count must be an integer >= 2")
    if method == "mc":
        values = np.random.default_rng(seed).random((n, 2))
    elif method == "sobol":
        if n & (n - 1):
            raise ValueError("Sobol sample count must be a power of two")
        values = qmc.Sobol(d=2, scramble=True, rng=np.random.default_rng(seed)).random_base2(int(math.log2(n)))
    else:
        raise ValueError("method must be mc or sobol")
    # Avoid infinite inverse-normal values at endpoints; do not discard Sobol points.
    return np.clip(values, np.finfo(float).eps, 1 - np.finfo(float).eps)


def worlds(scenario: Scenario, u: np.ndarray):
    """Gaussian copula: positive rho couples high demand to supply disruption."""
    z = norm.ppf(u)
    sigma = math.sqrt(math.log1p(scenario.demand_cv ** 2))
    mu = math.log(scenario.demand_mean) - sigma ** 2 / 2
    demand = np.exp(mu + sigma * z[:, 0])
    rho = scenario.demand_supply_correlation
    supply_z = rho * z[:, 0] + math.sqrt(1 - rho ** 2) * z[:, 1]
    disrupted = supply_z > norm.ppf(1 - scenario.disruption_probability)
    fill = np.where(disrupted, scenario.disrupted_fill, 1.0)
    return demand, fill


def outcomes(scenario: Scenario, order: float, demand: np.ndarray, fill: np.ndarray):
    """Continuous units. Orders prepaid; undelivered units receive no refund."""
    available = order * fill
    sold = np.minimum(demand, available)
    left = np.maximum(available - demand, 0)
    unmet = np.maximum(demand - available, 0)
    profit = scenario.price * sold + scenario.salvage * left - scenario.cost * order - scenario.shortage_penalty * unmet
    return profit, sold, unmet


def lower_tail_mean(values: np.ndarray, alpha: float) -> float:
    """Exact fractional empirical lower-tail average, including boundary mass."""
    x = np.sort(np.asarray(values, dtype=float))
    if x.ndim != 1 or x.size == 0 or not np.all(np.isfinite(x)) or not 0 < alpha <= 1:
        raise ValueError("finite nonempty vector and 0 < alpha <= 1 required")
    mass = alpha * x.size
    full = int(math.floor(mass))
    total = x[:full].sum()
    if full < x.size:
        total += (mass - full) * x[full]
    return float(total / mass)


def summarize(scenario: Scenario, order: float, demand: np.ndarray, fill: np.ndarray):
    profit, sold, unmet = outcomes(scenario, order, demand, fill)
    mean = float(profit.mean())
    tail = lower_tail_mean(profit, scenario.tail_probability)
    return {
        "order": int(order), "mean_profit": mean,
        "tail_profit": tail, "loss_probability": float(np.mean(profit < 0)),
        "fill_rate": float(sold.sum() / demand.sum()),
        "stockout_probability": float(np.mean(unmet > 0)),
        "profit_p05": float(np.quantile(profit, 0.05)),
        "profit_p95": float(np.quantile(profit, 0.95)),
        "score": (1 - scenario.risk_weight) * mean + scenario.risk_weight * tail,
    }


def analytic_expected_profit(scenario: Scenario, order: float) -> float:
    """Independent analytic oracle for the no-disruption lognormal model."""
    if scenario.disruption_probability != 0:
        raise ValueError("analytic oracle requires zero disruption probability")
    sigma = math.sqrt(math.log1p(scenario.demand_cv ** 2))
    if sigma == 0:
        return float(outcomes(scenario, order, np.array([scenario.demand_mean]), np.ones(1))[0][0])
    mu = math.log(scenario.demand_mean) - sigma ** 2 / 2
    if order == 0:
        expected_sales = 0.0
    else:
        z = (math.log(order) - mu) / sigma
        expected_sales = scenario.demand_mean * norm.cdf(z - sigma) + order * norm.sf(z)
    return float((scenario.price - scenario.salvage + scenario.shortage_penalty) * expected_sales
                 + (scenario.salvage - scenario.cost) * order - scenario.shortage_penalty * scenario.demand_mean)


def analytic_order(scenario: Scenario) -> float:
    if scenario.disruption_probability != 0 or scenario.risk_weight != 0:
        raise ValueError("closed-form optimum requires no disruption and risk_weight=0")
    fractile = (scenario.price - scenario.cost + scenario.shortage_penalty) / (scenario.price - scenario.salvage + scenario.shortage_penalty)
    sigma = math.sqrt(math.log1p(scenario.demand_cv ** 2))
    if sigma == 0:
        return scenario.demand_mean
    scale = scenario.demand_mean / math.sqrt(1 + scenario.demand_cv ** 2)
    return float(lognorm.ppf(fractile, s=sigma, scale=scale))
