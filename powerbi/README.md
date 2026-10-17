# Power BI: open, understand and refresh StockSense

## First refresh on Windows

1. Install current Power BI Desktop and Python3.11–3.13. Clone/download the whole repository; keep its folder structure.
2. In a terminal at the repository root, create/activate a venv and run `python -m pip install -e .`.
3. Run `python scripts/configure_powerbi.py`. This sets the DataFolder parameter to your local `powerbi/data` directory; it performs no simulation and needs no dataset download.
4. Open `powerbi/StockSense.pbip`. If your Desktop release requires it, enable project/enhanced PBIR preview features and restart.
5. Click Home→Refresh. If the local CSV paths are blocked, open Transform data→Manage Parameters, verify DataFolder, and approve the trusted local data source.
6. Explore the six pages. With no product/scenario filter, simulation measures default to SKU85123A and R20-C55-S0. Select exactly one product and scenario for comparisons; incompatible multi-selections deliberately blank the simulation KPIs.
7. Save a local PBIX using File→Save As after successful refresh if you prefer a single Desktop file. PBIP/PBIR is the Git-reviewable source supplied here.

The report has no HTML/JavaScript/CSS dependency and needs no Python visual or Python installation configured inside Desktop. All visuals are native Power BI visuals. A separate `StockSense-theme.json` is available under View→Themes→Browse for themes for the evergreen/amber palette.

## Report tour

| Page | Interpretation |
|---|---|
|01 Decision summary | Default/focused simulation metrics and a separate chronological policy comparison |
|02 Observed sales | Complete104-week panel and 52/13/39 split; zero sales may reflect unavailable stock |
|03 Historical policy test |39 test weeks, four policies, fixed declared economics and service metrics |
|04 Scenario explorer |135 precomputed runs; histogram bins and numerical uncertainty |
|05 Decision curve |Mean/tail/score across 106 quantities from selection worlds, not evaluation worlds |
|06 Data quality & learning |Cleaning audit, attribution, assumptions and seed/history hashes |

Scenario slicers affect final-refit simulations, not the historical replay's fixed assumptions. Date filtering affects weekly sale/replay facts; fixed whole-test summaries and final-refit simulations do not become newly backtested models when dates are filtered. Forecast MAE/WAPE columns are for mean/seasonal forecasts, not inventory-order accuracy.

## What happens when you click a slicer?

The slicer filters imported rows through one-direction dimension-to-fact relationships. DAX retrieves the appropriate already-computed metrics. It does not sample random values or call Python. Python owns random streams, policy selection, independent evaluation and confidence intervals. This separation makes the report repeatable and explainable.

27 scenario combinations cover risk0/20/50%, purchase cost 45/55/65% of observed reference price and hypothetical failure0/10/25%. Salvage/penalty stay10%, disrupted fill65%, latent correlation0. The default is R20-C55-S0. Sales and reference prices are observed; these ratios are assumptions.

## Generate fresh simulations

```powershell
python scripts/export_powerbi.py --method sobol --n 4096 --replicates 12 --seed 2026
```

Then Refresh Desktop. To compare MC, regenerate with `--method mc` and save the previous export elsewhere if needed. To change the preset economic grid, edit `SCENARIO_GRID` in `scripts/export_powerbi.py`, keep the documented default key if using default DAX, regenerate, run `python scripts/build_powerbi.py`, then `python scripts/configure_powerbi.py` and validate. Do not overwrite unsaved report edits when rebuilding; the builder recreates generated report/model source. For a single arbitrary custom run, use CLI `run --config`; that run remains in JSON/SQLite and is not automatically added to this fixed mart.

## Model and DAX

Products, Weeks and Scenarios are dimensions. WeeklySales, SimulationSummary, PolicyCurve, ProfitHistogram, ReplayWeekly and ForecastDiagnostics are facts; ReplaySummary provides whole-test tail summaries. CleaningAudit/ModelNotes are descriptive independent tables. Relationships filter in one direction to avoid fact-to-fact ambiguity. Model source is TMSL `StockSense.SemanticModel/model.bim`; Power Query M imports explicit types from CSV with en-GB conversion.

The25 measures are included in the native model and mirrored in `measures.dax`. Profit proxies use GBP. Replay fill uses DIVIDE(SUM(fulfilled),SUM(observed_sales)), preserving unit-weighted service. Simulation measures use a named default when dimensions are unfiltered, blank on incompatible multi-selection, and KEEPFILTERS to respect selected contexts. Never sum alternative scenario profits into one claimed benefit.

## Export and provenance

Use a visual's More options→Export data when available to save its displayed table. Filters affect that export. Full input/output CSVs and export_manifest.json are already in `data/`; the CLI also writes full result JSON and SQLite provenance. The report's bins carry bounds/counts; numerical CI bounds are simulation-only uncertainty, not a future profit prediction interval.

## Windows acceptance checklist

These native checks cannot be completed without Power BI Desktop and are not represented as passed by CI:

- Open PBIP with no load errors; set DataFolder and Refresh all12 tables with zero refresh errors.
- Confirm no DAX compilation/visual query errors on all six pages; import the optional theme.
- Clear selections: order476, mean modeled profit about£357.53, baseline658 with default 4096×12 Sobol export.
- Select SKU85099B and another scenario; confirm simulation KPIs change and history/policy comparison reflect product selection.
- Confirm multiple incompatible scenario/product selections blank simulation KPIs; clearing restores default values.
- On historical policy page, compare all four policies; risk-policy profit for jumbo bags is below trailing mean under declared replay assumptions.
- Inspect history dates/splits, curve order sorting, histogram bin counts, text wrapping and export a filtered CSV.
- Save/reopen a PBIX/PBIP, refresh again and record Desktop version and outcome before presenting the live demo.

Schema validation is an additional engineering check, not proof that Desktop opened/rendered the report. Source docs: [PBIP](https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-overview), [PBIR](https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-report), [semantic model](https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-dataset).
