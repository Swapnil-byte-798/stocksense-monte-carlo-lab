# Validation evidence · version 2

## Automated scope

`python -m unittest discover -s tests -v` checks accounting, lower-tail fractional weighting, analytic lognormal references, MC/Sobol contracts, seed/provenance independence, input limits, empirical zero mass/support, raw cleaning fixtures, source audit, weekly calendar, training-only SKU selection, future-invariance, replay accounting, context/currency and packaged data.

`python scripts/validate_powerbi.py` validates55 native project/report JSON files against12 cached official Microsoft schemas, then checks model/visual field references, relationships and unique dimension keys, CSV hashes/schema/grains, replay timing/accounting, confidence interval ordering and histogram totals. It does not execute DAX/M or render Desktop visuals.

CI runs numerical/data checks on Python3.11/3.12/3.13, CLI real-data smoke commands and the offline BI validator. A dedicated export smoke job regenerates135 scenarios at reduced sample size into temporary output, then builds/validates that mart. Full source Excel is not downloaded on every push; the verified derivative and small ETL fixtures keep CI reproducible.

See [commit-specific workflow status](https://github.com/Swapnil-byte-798/stocksense-monte-carlo-lab/actions/workflows/ci.yml). Previous green runs do not validate new changes.

## Native Power BI acceptance remains separate

Power BI Desktop is not available in the authoring environment. Import, M execution, DAX compilation, visual rendering, slicer behavior and CSV export in Desktop require the documented Windows checklist in [powerbi/README.md](../powerbi/README.md). No native Desktop validation or screenshot is claimed. This boundary must remain visible until real Desktop evidence is recorded.

## Statistical/business limits

An analytic synthetic oracle verifies mathematics, not real retail demand. Historical replay uses observed sales proxies, assumed economic ratios, weekly reset and full delivery. All four policies and all five products are retained. Default risk-sensitive profit beats trailing mean on four products but loses on one and lowers fill on all five. Numerical CIs condition on assumptions and exclude finite-history/model/cost uncertainty; no causal savings or production impact is established.
