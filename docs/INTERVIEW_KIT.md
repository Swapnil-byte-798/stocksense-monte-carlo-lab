# Interview kit · Python, real data and Power BI

## Explain it in 45 seconds

I built StockSense to connect real sales with transparent inventory decisions. I processed1.067million UCI transaction rows into audited weekly observations for five training-selected products. Four policies were replayed over 39 chronological test weeks per product. A Python Monte Carlo/Sobol engine then generated135 product-scenario experiments with independent paired evaluation, and a six-page Power BI report exposes profit, downside and service trade-offs. The risk policy improves the default profit proxy versus trailing mean on four products but lowers service on all five; costs and lost demand are not observed, so these are modeled proxies rather than claimed savings.

## Resume bullets you can substantiate

- Built a Python and Power BI inventory decision project using1.067M real transaction rows, audited ETL, SHA-256 lineage and attributed CC BY data.
- Compared four policies across 195 chronological product-weeks using rolling52-week histories; reported modeled profit, downside and fulfilled-unit trade-offs without future leakage.
- Implemented empirical MC/Sobol sampling, independent paired confidence intervals, SQLite provenance and a six-page Power BI project with 12 tables and 25 DAX measures.

Use after you can run/explain/modify the project. Do not claim employer deployment, actual savings, universal policy superiority, Kaggle ranking or native Desktop testing you have not performed.

## Questions to rehearse

**Why UCI?** Actual quantities/prices, two years, clear license and reproducible download fit transaction-to-inventory analysis. Single-retailer archival observations do not generalize to every employer.

**Are sales demand?** Sales are a proxy; availability and lost demand are unobserved. Add inventory/stockout/trading-calendar data before estimating true demand.

**How do you avoid leakage?** Fix SKU ranking and reference prices from initial training. At each test week, use only prior 52 outcomes. Future-invariance tests mutate later outcomes and check earlier records remain identical.

**Why empirical resampling?** It preserves zeros/counts without imposing a continuous positive distribution. It assumes exchangeability and cannot infer unseen extremes/seasonality. Compare seasonal or covariate models chronologically before production use.

**Why exact empirical backtest but simulation in the app?** Direct averaging over 52 possible past outcomes is cheap and removes numerical noise from policy replay. Simulation teaches and evaluates uncertainty under optional supply stress. Exact empirical calculations provide a useful comparator.

**What does a narrow CI prove?** Numerical precision for a fixed policy under fixed historical/economic assumptions. It excludes data, economic and model uncertainty; it does not prove future benefit.

**What runs in Power BI?** Power Query imports typed CSVs; a star model controls filters; DAX aggregates and guards context; native visuals present results. Python performs the simulation. Slicers select precomputed runs and never launch Python.

**Why PBIP rather than an opaque PBIX?** Text-based report/model definitions are inspectable in Git. After Windows refresh, save a PBIX for convenience. Schema checks are not a substitute for Desktop execution/rendering.

**Did every policy win?** No. Default risk-policy profit loses to trailing mean on jumbo bags and fill is lower across all five. A minimum service constraint and measured costs are needed before recommending an operational policy.

**Why not sum every scenario's profit?** Scenarios are alternative worlds/assumptions for the same decision, not independent businesses. Explicit DAX requires a single product/scenario and keeps units/currency consistent.

## Five-minute demo

1. Open the data-quality page; explain one cleaning assumption and one unobserved field.
2. Inspect observed history and training-only SKU selection.
3. Compare all four historical policies, including the unfavorable jumbo-bag result.
4. Select one product/scenario; explain order, downside, service and conditional CI.
5. Inspect the decision curve, export a table, show a leakage test and describe one production extension.

Next steps should follow business need: actual availability/cost data, service constraints, seasonal forecasts, prospective evaluation and multi-period stock flow. More complex algorithms alone do not repair missing business measurements.
