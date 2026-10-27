# Paired policy comparison on real historical sales

The existing replay evaluates four inventory policies on real UCI Online Retail II sales.
This addition measures uncertainty in the **same-week difference** between `empirical_risk`
and `trailing_mean`. It is a historical policy replay, not a randomized online A/B test.

```bash
python -m stocklab compare-policies
# Exact recorded evidence:
python -m stocklab compare-policies --output examples/policy-comparison.json
```

The command regenerates the replay from packaged, attributed real-sales histories. No raw
download or key is required. Each run matches candidate and baseline by product/week,
rejects duplicate/missing pairs, requires equal observed sales and forecast origins, and
checks that each training origin precedes its test week.

## Recorded result

Five products, 39 common chronological test weeks, 20,000 bootstrap replicates, seed 2026.
The primary summary aggregates products within each week, then resamples **four-week
circular blocks**. Both policies and all products use the same resampled weeks.

| Portfolio metric | Candidate minus baseline | Pointwise 95% interval |
|---|---:|---:|
| Mean weekly modeled profit proxy | +£94.18 | [−£20.55, +£200.32] |
| Fulfilled observed-unit rate | −11.45 pp | [−12.69, −10.00] pp |

The modeled profit interval includes zero, and the service loss exceeds an illustrative
two-percentage-point tolerance. The gate says **do not promote on this evidence**.
The gate was defined retrospectively after earlier project outputs existed; it is not
a preregistered business acceptance criterion or automatic procurement decision.

Two- and eight-week sensitivity blocks retain the same conclusion. Product-specific and
block-sensitivity intervals are exploratory pointwise intervals; they do not establish
multiple independently confirmed product wins. See the complete JSON for all 18 rows.

## Why pairing and blocks matter

Policies face the same realized sales in a week, so compare their differences directly.
Shuffling their outcomes independently would throw away that pairing. Products can share
calendar shocks, so all products travel together in each resample. Contiguous week blocks
retain short-range serial dependence, unlike independent weekly resampling.

Circular blocks join the end to the beginning when required. This is an approximation,
not a cure for nonstationarity; 39 weeks give little evidence about seasonality or future
conditions. Report block-length sensitivity instead of choosing the most favorable interval.

The fulfilled-unit statistic is `sum(candidate fulfilled - baseline fulfilled) / sum(observed sales)`;
it is not an unweighted average of weekly percentages. Portfolio profit is the mean of the
weekly sum across products, not a mean over unrelated product-week observations.

Real observed sales are still a demand proxy. Purchase costs, inventory reset, stockouts,
salvage and penalties remain modeled assumptions. These intervals measure variability in
the historical replay, separately from Monte Carlo numerical integration intervals. They
do not prove causal business profit, customer impact, or future savings.

## Next experiment if deployed

Before a live test, agree on the decision unit, interference constraints, service floor,
eligible SKUs, inventory carryover, duration, MDE, allocation and stopping rule. A physical
inventory policy may need store/warehouse clusters or a planned switchback design; splitting
individual orders that consume shared stock can contaminate treatment and control.
No assignment or customer intervention has been performed by this change.

Validation: existing 35-test suite passes, including 7 new comparison tests. Native Power BI
structure/data checks pass. Desktop execution remains outside the Linux validation boundary.
