# API and runbook

## Setup and operations

Use Python 3.11-3.13 and install the project in a fresh virtual environment with `python -m pip install -e .`. Start `python -m stocklab serve`; use `--port 8001` if port 8000 is occupied. Stop with Ctrl+C. The default listener is loopback. Avoid exposing it directly to the internet.

The numerical dependencies are pinned. To deliberately upgrade them, rerun the numerical checks, sampling benchmark, and saved evidence, then document the new versions. A fixed seed alone is not a cross-version reproducibility guarantee. See [NumPy's Generator documentation](https://numpy.org/doc/stable/reference/random/generator.html).

## Endpoints

| Method / path | Response |
|---|---|
| GET /api/health | Local server status |
| GET /api/defaults | Default scenario object |
| POST /api/run | Complete experiment; appends to SQLite |
| GET /api/history | Most recent 20 completed local runs |
| GET / | Dashboard |

Example request:

```bash
curl http://127.0.0.1:8000/api/run \
  -H 'Content-Type: application/json' \
  -d '{"scenario":{"demand_mean":1000,"demand_cv":0.35,"risk_weight":0.2},"method":"sobol","n":4096,"replicates":12,"seed":2026}'
```

Unspecified scenario values use defaults. Unknown fields are rejected. Sobol requires power-of-two N. `GET /api/defaults` or `python -m stocklab defaults` gives the complete scenario object; `examples/scenario.json` is a reusable starting point. Validate the relationship salvage < cost < selling price when changing economics.

## Export and history

The dashboard exports the complete result as JSON or a two-row comparison as CSV. The experiment log stores only completed runs. Use `sql/analysis.sql` to compare runs and inspect paired differences. The database lives at `output/experiments.db`; the CLI can choose a different database with `--database`.

For a read-only static preview, serve `stocklab/web` with a static file server. It loads `example.json`, labels itself a saved experiment, and disables simulation controls. It does not compute Monte Carlo results in the browser. Do not open index.html directly with file://; browser fetch restrictions can prevent loading the example.

## Calibration

```bash
python -m stocklab calibrate examples/synthetic-demand.csv
```

Input columns must be exactly `date,demand`. Dates are unique ISO dates. Require at least 30 positive finite observations. Output contains fitted demand mean/CV, observation count, date range, fitting method, and CSV SHA-256. Copy the fitted mean and CV into an explicitly reviewed scenario; calibration does not silently change a model. This simple lognormal fit does not handle zeros, sales censored by stockouts, or seasonal demand.

## Troubleshooting

| Symptom | Action |
|---|---|
| No module named stocklab | Run from repository root or install with `python -m pip install -e .` |
| Address already in use | Use `--port 8001` or stop the process occupying the port |
| Saved experiment preview displayed | Start the Python server and open its URL; a static server cannot run Python simulations |
| Inputs changed but charts did not | Click Run simulation; charts describe the last completed run |
| Invalid price/cost message | Keep 0 <= salvage < cost < selling price |
| Selected order at grid boundary | Expand the CLI/API grid, then repeat selection and independent evaluation |
| API returns 429 | A local simulation is still running; retry after it completes |
| Permission error writing SQLite | Choose a writable working directory or CLI `--database` path |

## Public deployment boundary

The demo uses an exact static allowlist, same-origin checks for browser POSTs, content-type and size validation, numerical workload caps, and one simulation lock. It has no authentication, authorization, request queue, production rate limiter, or database backup service. These features must be designed before public multi-user deployment. A Dockerfile is packaging, not proof of production readiness.
