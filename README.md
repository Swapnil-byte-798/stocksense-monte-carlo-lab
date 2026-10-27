# StockSense · Monte Carlo + Power BI

**Real retail data. Auditable Python decisions. An interactive Power BI report.**

[![CI](https://github.com/Swapnil-byte-798/stocksense-monte-carlo-lab/actions/workflows/ci.yml/badge.svg)](https://github.com/Swapnil-byte-798/stocksense-monte-carlo-lab/actions/workflows/ci.yml)

A decision-science portfolio project that connects data engineering, statistics, inventory optimization, SQL and business intelligence. **Power BI is the primary interface. No JavaScript, HTML or CSS is required.** The Python engine handles data cleaning, simulations and historical evaluation; the report explains the results.

## Start on Windows

Install Python 3.11–3.13 and a current [Power BI Desktop](https://learn.microsoft.com/en-us/power-bi/fundamentals/desktop-get-the-desktop). Download or clone this repository and open a terminal in its root:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e .
python scripts/configure_powerbi.py
```

Open **`powerbi/StockSense.pbip`**, then select **Home → Refresh**. If requested, allow the trusted local CSV sources. The project is native PBIP/PBIR, not a renamed PBIX; you can save a PBIX from Desktop after refresh. Bundled CSVs make the first report refresh independent of Kaggle accounts, raw Excel downloads, or Python integration inside Power BI. See the [complete Power BI walkthrough](powerbi/README.md), including a first-refresh checklist.

**Validation boundary:** report/project JSON has been checked against Microsoft's schemas; model references, relationships, data hashes and numerical outputs are checked in Python/CI. Power BI Desktop is unavailable in this environment, so Desktop import, DAX/M execution and visual rendering still require the documented Windows acceptance check. No rendered Desktop pass is claimed.

## Six report pages

| Page | What you can explore |
|---|---|
| Decision summary | Selected order, modeled profit, downside, service, baseline and numerical confidence interval |
| Observed sales | 104 real weekly observations per SKU, training/validation/test splits and source prices |
| Historical policy test | Four policies over 39 chronological test weeks, profit/service comparisons and forecast diagnostics |
| Scenario explorer | 27 combinations of risk preference, cost assumptions and hypothetical supplier stress per product |
| Decision curve | 106 order candidates, mean/tail profit and the blended objective |
| Data quality & learning | Sequential cleaning audit, assumptions, attribution and run provenance |

The report includes **12 tables, 25 explicit DAX measures, 135 seeded product-scenario simulations, 14,310 candidate scores and 4,860 histogram bins**. Slicers explore precomputed results; they do not execute Python. To generate fresh simulation values or another method/seed:

```powershell
python scripts/export_powerbi.py --method sobol --n 4096 --replicates 12 --seed 2026
# Then click Refresh in Power BI Desktop.
```

Products, scenarios, time history, policy comparison, distribution inspection and visual CSV exports are interactive in Power BI. New arbitrary economics require a Python run/export followed by Refresh. Local run history is retained in SQLite through the CLI. This is import-mode BI, not a real-time procurement application.

## Real data with a reproducible lineage

Source: **[UCI Online Retail II](https://archive.ics.uci.edu/dataset/502/online+retail+ii)**, Chen, D. (2012), [DOI](https://doi.org/10.24432/C5CG6D), **CC BY 4.0**. It contains transactions from a UK non-store retailer in 2009–2011. UCI provides an official download and clear attributed reuse; it is a strong fit for this retail decision problem, not a claim to target every employer.

- **1,067,371 original rows → 892,892 audited UK sale lines.**
- **5 SKUs ×104 complete weeks =520 derived observations.** Product selection and reference prices use only the initial 52 weeks.
- **52 training /13 diagnostic validation /39 sequential test weeks.** Four policies produce **780 policy-week records** over 195 product-test weeks.
- Original ZIP, workbook, derived CSV and Power BI exports have SHA-256 provenance. Customer identifiers are not exported.

Recorded sales are a **demand proxy**. Purchase costs, supplier failures, lost demand and stock availability are not observed. Prices are initial-training medians; cost, salvage, shortage penalties and weekly inventory reset are assumptions. All monetary results are **modeled profit proxies**, not actual profits or proven savings. [Read the data card](docs/DATA_CARD.md).

## Honest results, not a universal winner

Default historical replay uses cost=55% of reference price, salvage=10%, penalty=10%, full delivery, weekly reset and risk weight=.20. Mean weekly profit proxies and fulfilled-observed-unit rates over 39 test weeks:

| SKU | Risk-policy profit | Trailing-mean profit | Risk fill | Mean fill |
|---|---:|---:|---:|---:|
| 85123A | £359.35 | £273.41 | 73.8% | 84.6% |
| 84077 | £29.18 | £28.94 | 52.2% | 71.9% |
| 21212 | £56.21 | £31.13 | 78.8% | 86.0% |
| 85099B | £457.64 | £482.67 | 70.1% | 77.3% |
| 84879 | £236.49 | £228.56 | 66.9% | 76.1% |

The risk-sensitive policy beats trailing-mean modeled profit on four products but loses on jumbo bags, and fulfills fewer units on all five. Report all four policies and discuss the service requirement before recommending an order. Changing assumed costs can change rankings.

The separate default simulation refits on the latest 52 recorded weeks for the archival planning week **2011-12-05**. It selects 476 units against a 658-unit mean baseline, with about £357.53 versus £338.02 modeled mean profit and lower fill. Its paired confidence interval measures numerical integration uncertainty conditional on the empirical model; it is not a future-savings interval and is distinct from the chronological replay.

## Python commands and reproduction

### Paired policy uncertainty

`python -m stocklab compare-policies` adds a paired weekly block-bootstrap comparison of
the risk policy with trailing mean on the existing real-sales replay. Across five products
and 39 common weeks, the mean weekly modeled profit difference is **+£94.18**, with a
four-week-block 95% interval **[−£20.55, +£200.32]**. The fulfilled-unit rate falls
**11.45 percentage points**, so the illustrative profit/service gate rejects promotion.
This is an offline historical comparison, not a live randomized A/B result.
See [method and guardrails](docs/POLICY_COMPARISON.md) and the
[executed evidence](examples/policy-comparison.json).

```bash
python -m stocklab run --product 85123A
python -m stocklab backtest
python -m stocklab data
# Full rebuild from the official ~46 MB source; optional Excel dependencies:
python -m pip install -e ".[data,dev]"
python scripts/prepare_retail.py
python scripts/reproduce.py
python scripts/configure_powerbi.py
python -m unittest discover -s tests -v
python scripts/validate_powerbi.py
# Separate mathematical teaching model:
python -m stocklab run --synthetic
```

Empirical resampling preserves observed zeros and counts. MC and scrambled Sobol use independent selection/evaluation seed branches and paired common random numbers. The historical replay scores empirical policies exactly on preceding observations, avoiding Monte Carlo noise in test policy choice. The synthetic lognormal model and analytic newsvendor benchmark remain explicitly labeled teaching/reference exercises.

## Documentation and study material

| File | Purpose |
|---|---|
| [Power BI walkthrough](powerbi/README.md) | Open/refresh, report tour, DAX, model and acceptance checklist |
| [Study guide](docs/STUDY_GUIDE.md) | 44 lessons, short analogies, exercises, 14-day learning plan |
| [Notebook](notebooks/01_monte_carlo_lab.ipynb) | Executable real-data and mathematical learning lab |
| [Data card](docs/DATA_CARD.md) | Dataset choice, license, audit, time split, limits |
| [Methodology](docs/METHODOLOGY.md) | Equations, uncertainty, policies and evaluation |
| [Architecture](docs/ARCHITECTURE.md) | Python-to-Power-BI pipeline and component ownership |
| [Runbook](docs/API_AND_RUNBOOK.md) | Commands, troubleshooting and regeneration |
| [Interview kit](docs/INTERVIEW_KIT.md) | Defensible resume bullets and technical answers |
| [PRD](docs/PRD.md) / [FRD](docs/FRD.md) / [Validation](docs/VALIDATION.md) | Scope, contracts and evidence |

Code is [MIT](LICENSE). The derived data remain **CC BY 4.0**, separately credited in [stocklab/data/README.md](stocklab/data/README.md). Microsoft JSON schemas are vendored for offline validation with their source URLs; see [schema notice](powerbi/schemas/README.md).
