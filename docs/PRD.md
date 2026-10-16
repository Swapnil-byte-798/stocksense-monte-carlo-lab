# Product requirements: StockSense

Version 1.0 | Owner: Swapnil Dwivedi | Educational portfolio release

## Problem and intended user

A retail analyst must recommend an inventory order before demand and supply are known. A single forecast hides the range of outcomes; choosing by average profit alone hides difficult periods. The user needs a transparent experiment that compares a proposed order with the current baseline and makes the economic assumptions explicit.

## Product outcome

An analyst can configure a synthetic scenario, run an experiment, understand the profit-service-risk trade-off, and export a reproducible decision record. A technical reviewer can trace the result from the interface through Python to the equations and tests.

## User stories

1. As an analyst, I can adjust demand, costs, disruptions, and risk preference to understand how the decision changes.
2. As a manager, I can compare expected profit, worst-tail outcomes, loss probability, and service with a baseline.
3. As a reviewer, I can distinguish simulation error from model uncertainty and inspect independent evaluation results.
4. As a developer, I can reproduce an experiment from its configuration, seed, and numerical-library versions.
5. As a learner, I can move from intuitive explanations to equations, code, validation, and model extensions.

## Scope

Included: a single-period, single-item continuous inventory model; correlated demand and disruption; Monte Carlo and randomized Sobol sampling; risk-sensitive finite-grid search; independent evaluation; local dashboard, CLI, JSON API, CSV calibration, SQLite history, documented benchmarks, and teaching materials.

Excluded: production procurement, actual orders, live supplier integrations, financial forecasts, user accounts, multi-tenant hosting, continuous background automation, real-world impact claims, and guaranteed employment outcomes.

## Success criteria

| Criterion | Acceptance evidence |
|---|---|
| A new user can run the demo without secrets | Documented Python commands and no external data dependency |
| Model accounting is correct | Hand-calculation tests and deterministic limits |
| Simulation agrees with an independent reference | No-disruption analytic profit comparison within fixed tolerance |
| Evaluation avoids policy-selection reuse | Separate SeedSequence branches with recorded stream identifiers |
| Results are understandable | Visible scenario assumptions, baseline, uncertainty labels, and trade-offs |
| Results are reproducible | Identical metrics for repeated config, seed, and environment |
| Data is auditable | Full JSON result and configuration stored in SQLite; CSV SHA-256 provenance |
| Learning is practical | Runnable notebook, worked example, exercises, interview defense |

## Principal risks

- Incorrect demand distribution or contract assumptions can dominate numerical precision. Display limitations with every run.
- Tail metrics are sensitive to rare events and have no confidence intervals in v1. Label them as point estimates.
- A finite grid can miss a better quantity. Warn at boundaries and disclose step size.
- The local web server is not production-hardened. Bind to loopback by default and document the deployment gap.

## Release sequence

1. Numerical model and mathematical checks.
2. Independent experiment evaluation and SQL persistence.
3. Dashboard and reproducible evidence.
4. Learning material, operations guide, and validation report.

Future work should add a demonstrated capability, not superficial infrastructure: parameter uncertainty first, then real-data validation and multi-period decisions.
