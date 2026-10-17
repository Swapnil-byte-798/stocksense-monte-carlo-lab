# Runbook · Python and Power BI

The web interface/API from version 1 has been replaced by native Power BI source. No Node, JavaScript, HTML, CSS or local HTTP server is required.

## First use

Follow [powerbi/README.md](../powerbi/README.md). Install Python3.11–3.13, create/activate a venv, `pip install -e .`, run `python scripts/configure_powerbi.py`, open `powerbi/StockSense.pbip` in current Windows Power BI Desktop and Refresh. Bundled imports make raw-data download optional. If PBIP/PBIR features are disabled in your Desktop release, enable the corresponding project/enhanced-report preview options and restart. Save a PBIX locally after successful refresh if preferred.

## Python operations

```bash
python -m stocklab defaults > scenario.json
python -m stocklab run --product 85123A --config scenario.json
python -m stocklab run --product 85099B --method mc --n 4096 --replicates 12 --seed 2026
python -m stocklab backtest
python -m stocklab data
python scripts/export_powerbi.py
python scripts/configure_powerbi.py
```

`run --config` accepts scenario fields, not the complete exported result. Real mode fixes observed history/moments/grid from the selected SKU; economic/risk/supply fields are assumptions that may be overridden after validation. JSON and SQLite are written under `output/`; full contexts retain currency and source. Custom CLI runs do not automatically join the fixed BI scenario cube. To change the BI cube's economic combinations, edit the documented `SCENARIO_GRID` in exporter, regenerate and rebuild the native project, then Refresh. Changing only N/seed/method requires export then Refresh; no report rebuild.

## Reproduction and tests

```bash
python -m pip install -e ".[data,dev]"
python scripts/prepare_retail.py
python scripts/reproduce.py
python scripts/configure_powerbi.py
python -m unittest discover -s tests -v
python scripts/validate_powerbi.py
```

The original~46MB Excel rebuild checks raw hashes, creates attributed aggregates and keeps customer identifiers out of exports. Raw files go in ignored `data/raw/`. A hash mismatch requires investigation, not bypass. Reproduction also generates clearly named synthetic/reference examples and the analytic MC/Sobol benchmark. Those are not real company results.

## Troubleshooting

Power BI is Windows Desktop software; it is not rendered by Python. If CSVs are missing, rerun configuration and check DataFolder via Transform data→Manage Parameters. Choose trusted local filesystem sources and refresh after Python export. Avoid moving the data folder while Desktop is open. Blank simulation KPIs mean choose one product and one complete scenario; clearing all slicers uses the named default. Scenario slicers do not run Python or imply fresh simulations. Import-mode Service refresh would require a supported accessible data location/gateway and separate deployment work; no Service deployment is claimed.

`Power BI Desktop` must execute/validate M and DAX. CI validates JSON schemas and references, not native rendering. Use the Windows acceptance checklist before a live interview demo.
