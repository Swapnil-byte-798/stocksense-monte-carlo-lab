# Functional requirements and acceptance map

| ID | Requirement | Acceptance | Implementation |
|---|---|---|---|
| F01 | Validate costs and uncertainty inputs | Reject NaN, booleans, invalid ranges, salvage >= cost, cost >= price | `Scenario.__post_init__` |
| F02 | Generate seeded demand/supply worlds | Same inputs reproduce worlds; marginal demand moments and disruption frequency are correct within tolerance | `uniforms`, `worlds` |
| F03 | Compute accounting outcomes | Two hand-calculated cases and prepaid supply shortfall agree exactly | `outcomes` |
| F04 | Select from a bounded grid | Highest risk-adjusted score wins; ties retain lower grid quantity | `experiment.run` |
| F05 | Evaluate independently | Evaluation seeds differ from selection seed; order remains frozen | `experiment.run` |
| F06 | Compare with common random numbers | Candidate and baseline use the same worlds; interval is based on replicate paired differences | `experiment.run` |
| F07 | Report mean confidence intervals | Student-t interval across independent replicate means with n-1 degrees of freedom | `interval` |
| F08 | Report tails correctly | Fractional empirical lower-tail mass handles noninteger alpha*n and ties | `lower_tail_mean` |
| F09 | Audit every local run | Append-only SQL insert retains full result JSON; history lists newest 20 | `ledger` |
| F10 | Import positive demand history | Exact date,demand schema, unique ISO dates, >=30 rows, no zero/negative/nonfinite demand, <5MB file | `calibration` |
| F11 | Provide an interactive dashboard | Controls trigger backend calculation; changes mark results stale; JSON/CSV export works | `web/` |
| F12 | Provide a safe static preview | When Python API is absent, load a saved run and disable simulation inputs | `web/app.js` |
| F13 | Limit API resource use | 256-16384 paths, 4-32 replicates, <=121 grid candidates, 16KB request, one active simulation | `server`, `Scenario`, `run` |
| F14 | Restrict static routes | Arbitrary file paths and traversal requests return 404 | `server.ASSETS` |
| F15 | Reproduce committed evidence | Script regenerates default run, benchmark, sensitivity cases, and synthetic demand | `scripts/reproduce.py` |

## Model input contract

All monetary fields use one consistent arbitrary currency; the UI illustrates INR. Demand and order quantities refer to one planning period. Demand is continuous rather than a count. A disruption reduces the available fraction of the order, while the full order cost remains payable.

The scenario dataclass in `stocklab/model.py` is the authoritative complete contract. The UI exposes the common parameters and automatically creates a 57-candidate grid from demand mean: approximately 0.4 to 1.8 times mean, step approximately 2.5% of mean. CLI/API callers may supply a different valid grid and tail probability.

## Output contract

Schema version 1 includes config ID, UTC creation time, complete input configuration, numerical-library versions, train/evaluation seeds, selected and baseline metrics, confidence intervals, selection frontier, evaluation histogram, elapsed time, warnings, and replicate means. `config_id` hashes configuration only; it is not a unique run ID or an environment hash. The SQL primary key identifies individual local executions.

## Failure behavior

The CLI exits with status 2 for invalid user input. The API returns 400 for validation errors, 404 for unknown routes, 413 for body size violations, 415 for wrong content type, 429 when a simulation is already running, and 500 for local I/O failures. The frontend keeps the previous completed result visible after an error and marks the failure clearly. It never replaces a failed run with fabricated data.
