# Data card · UCI Online Retail II

## Selection rationale

This official UCI source is well suited to a retail decision-science case: actual quantities/prices, more than a million rows for audited ETL, two years for time-aware evaluation, no account-gated download and clear attributed reuse. Kaggle M5 is a useful alternative for hierarchical multi-store forecasting; it expands the scope beyond this transaction-to-inventory project. No one dataset appeals to every industry. This project targets transferable retail, marketplace, logistics, BI and general decision-science skills; it is not a banking credit-risk dataset.

## Source and license

Chen, D. (2012). Online Retail II [Dataset]. UCI Machine Learning Repository. https://doi.org/10.24432/C5CG6D

Official page: https://archive.ics.uci.edu/dataset/502/online+retail+ii

License: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Attribute the creator/source, link the license and state that StockSense filters, subsets and aggregates the data. No endorsement is implied. MIT covers code, not a relicensing of the data.

Original transactions span 1 December 2009–9 December 2011, a UK non-store retailer with many wholesale customers. These are archival observations, not current market behavior. Both workbook sheets are concatenated.

- ZIP: `572e36277c2390fbfde10664750731e0a86f55e33470d91919085f0408e67bfb`
- Workbook: `bcbe73b35f5b7babf197fb0cb983a11f5d9ff929078d4aa53d171b1f2df2e980`
- Derived CSV: `f661b2d38b5a231a5ee99c6def06f89d997722360b18212a1ac42e25194df7ee`

## Sequential audit

| Stage | Removed | Remaining |
|---|---:|---:|
| raw | 0 | 1,067,371 |
| exact_duplicate_lines_removed | 34,335 | 1,033,036 |
| valid_dates | 0 | 1,033,036 |
| cancellations_excluded | 19,104 | 1,013,932 |
| positive_finite_quantity | 3,393 | 1,010,539 |
| positive_finite_price | 2,626 | 1,007,913 |
| merchandise_code_pattern | 5,908 | 1,002,005 |
| uk_scope | 79,639 | 922,366 |
| complete_week_boundaries | 29,474 | 892,892 |

Deduplicate across all eight original columns before other transformations. C-prefixed invoices are cancellations. Numeric quantity/price must be finite and positive. Normalize stock-code whitespace/case; merchandise codes match five digits plus an optional letter. Restrict UK and complete Monday–Sunday weeks. Missing customer IDs remain because identity is unnecessary for SKU aggregation; identifiers are absent from exports. Duplicate removal may discard genuinely repeated identical lines, an unavoidable cleaning assumption without a transaction-line key. Excluding returns means positive sales, not net revenue.

## Product selection and evaluation

Select top five initial-52-week-volume SKUs among those active in at least 39 training weeks with training CV≤2; ties by stock code. Description and median transaction-line reference price use this initial split only. Price is not unit-weighted realized revenue. Five products ×104 zero-filled complete weekly counts yield 520 rows.

| Split | Week starts | Role |
|---|---|---|
| Training 52 | 2009-12-07 through 2010-11-29 | Product choice, initial price and history |
| Validation 13 | 2010-12-06 through 2011-02-28 | Diagnostic forecast scores; no automatic tuning |
| Test 39 | 2011-03-07 through 2011-11-28 | Sequential policy replay using prior 52 weeks |

At week t only observations before t inform the order. Previously revealed test observations may enter later rolling windows. This is separate from the report's final-refit simulation of an archival planning week using the latest available 52 weeks.

## Measured versus assumed

| Item | Status |
|---|---|
| Sale date, stock code, quantity, selling price | Recorded source fields |
| Weekly sales; initial-training median unit price | Derived observations |
| Stock availability, lost sales, purchase costs, supplier performance | Unobserved |
| Cost 45/55/65%, salvage 10%, penalty 10% of reference price | Illustrative economic assumptions |
| Supply disruption 0/10/25%, disrupted fill 65%, latent correlation 0 | Hypothetical scenario assumptions |
| Weekly reset/no carryover | Simplified accounting contract |
| Modeled profit, fill and unmet units | Counterfactual sales-proxy metrics, not measured outcomes |

## Limits

Sales may be censored by stockouts. Zero sales can indicate closure, missing availability, missing records or no demand. Empirical resampling preserves recorded counts/zeros but assumes exchangeability, ignores seasonality and cannot infer unseen extremes. Windows contain only 52 actual weeks; thousands of resamples do not add real observations. The single archival, UK/wholesale-heavy retailer and five training-selected SKUs limit generalization. Fixed median prices omit promotional/price response. Weekly reset does not model inventory flows, lead times or multi-echelon replenishment. Service is reported but not constrained. Replayed profit is not causal uplift. Numerical confidence intervals exclude history/model/cost uncertainty.

Rebuild: install `.[data]`, run `python scripts/prepare_retail.py`, then `python scripts/reproduce.py`. Hash mismatches fail closed for investigation. Raw files remain in ignored `data/raw/`; the small derivative is attributed and bundled for immediate Power BI use.
