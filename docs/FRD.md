# Functional requirements · Python + Power BI

| Capability | Contract |
|---|---|
| Real inputs | Official UCI ZIP/workbook hashes; sequential exclusion audit; CC BY attribution |
| Derivative | Five training-selected SKUs ×104 complete weeks, integer counts including zero sales |
| Temporal replay | 52 training,13 diagnostics,39 test; every decision sees preceding 52 observations only |
| Policy comparison | Risk-sensitive empirical, profit-only empirical, trailing mean, same-week-last-year |
| Simulation | Empirical MC/scrambled Sobol, finite integer grid, independent evaluation, paired replicate CI |
| Assumptions | GBP initial-training median price; declared cost/salvage/penalty, weekly reset and hypothetical stress |
| BI data | 12 typed CSV tables; SHA-256 export manifest; 135 product-scenario runs |
| BI model | Product/scenario/week dimensions, single-direction relationships, 25 explicit DAX measures |
| Report | Six native PBIR pages, slicers, cards, trends, policy bars, distributions, tables and provenance |
| Interaction | Import-mode scenario selection; no JavaScript/HTML/CSS; no Python execution from slicers |
| Recompute | Python export command, then Desktop Refresh; CLI JSON/SQLite retains custom run provenance |
| Guardrails | Multiple selections blank simulation KPIs rather than sum incompatible policies; default archival product/scenario when unfiltered |
| Tests | Numerical/data leakage/accounting checks plus Microsoft JSON-schema/reference/data validation |
| Delivery | Git-versioned PBIP/PBIR/TMSL source; user can save PBIX after local refresh |

The Windows acceptance checklist is required before claiming Power BI Desktop import/render validation. CLI/core checks run on Python 3.11–3.13.
