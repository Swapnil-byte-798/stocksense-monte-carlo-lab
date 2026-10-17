# Methodology · real sales and conditional decisions

## Data and time

See [data card](DATA_CARD.md). SKU choice and median reference prices use initial 52 weeks only. Thirteen weeks provide forecast diagnostics without automated tuning. At every one of the final 39 test weeks, orders use the preceding 52 observations. Previously revealed outcomes may enter later windows. The report's default simulation is a separate final refit on the latest 52 historical weeks for planning week 2011-12-05.

## Empirical simulation

Sort n observed weekly counts and map a uniform U to zero-based index floor(nU). This inverse empirical CDF preserves recorded zeros/integer values. It assumes exchangeability, cannot exceed historical support, and does not infer latent demand. MC supplies pseudo-random uniforms; Sobol supplies scrambled base-2 points with power-of-two N. Hypothetical supply stress uses a Gaussian-copula latent construction. Discreteness means latent correlation is not a promised observed Pearson correlation. Default disruption is zero, because supplier performance is not measured.

## Accounting and decision

```
sold = min(D, Q*F)
left = max(Q*F-D, 0)
unmet = max(D-Q*F, 0)
profit_proxy = price*sold + salvage*left - cost*Q - penalty*unmet
score = (1-w)*mean(profit_proxy) + w*lower_tail_mean(profit_proxy, .05)
```

D is observed-sales proxy, Q ordered units, F delivered fraction. Entire Q is paid even if not delivered. Weekly reset/no carryover is assumed. Lower-tail mean integrates exactly 5% empirical mass with fractional boundary weight. Fill is total fulfilled proxy units / total observed proxy units, not average of weekly fill ratios.

Default cost=.55price, salvage=.10price, penalty=.10price, w=.20, full delivery. The scenario cube varies cost .45/.55/.65, risk0/.20/.50 and hypothetical failure0/.10/.25 (65% fill when disrupted, latent correlation0). The order grid has step max(1,ceil(history.max()/100)) and 106 quantities0..105step. Rounded trailing mean is a separate baseline and need not lie on the grid. Optimality is limited to this finite candidate set and chosen objective; service is not constrained.

## Chronological replay

Risk-sensitive and profit-only empirical policies score the previous 52 observations exactly for each grid quantity, with no simulation selection noise. Compare trailing mean and same-week-last-year against the same observed test week. Across5 SKUs×39 weeks×4 policies there are 780 records, not 780 independent business experiments. Export last-training date for audit. Report all policies/products, including unfavorable results. MAE/WAPE apply to mean/seasonal forecast baselines; order decisions are not treated as demand forecasts.

## Independent simulation evaluation

A selection SeedSequence branch chooses Q using N worlds. Independent branches generate randomized evaluation replicates for the fixed Q and fixed baseline, using common worlds within each pair. Student-t intervals across independent replicate paired differences estimate numerical error. Sobol points within one replicate are dependent; an IID pointwise standard-error formula is inappropriate. Defaults:4096 selection worlds,12×4096 evaluation worlds. Selection curves and evaluation KPIs describe different samples.

CIs condition on empirical history and economic assumptions. They exclude finite-history, censored-sales, cost, seasonality and model uncertainty. Historical replay is another evidence layer, not causal uplift. No actual business savings are estimated.

## Teaching/reference mathematics

`run --synthetic` retains positive lognormal demand: sigma²=log(1+CV²), mu=log(mean)-sigma²/2. Positive-only CSV calibration and its strict importer are separate from zero-inclusive UCI ETL. With no disruption and no risk weight, the newsvendor critical fractile is (price+penalty-cost)/(price+penalty-salvage). Analytic lognormal truncated moments give a known expected-profit reference. Equal-N repeated-seed MC/Sobol RMSE comparisons verify that mathematical case; they do not establish universal speed or real-data validity.

Primary sources: [UCI](https://doi.org/10.24432/C5CG6D), [SciPy Sobol](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.qmc.Sobol.html), [NumPy Generator](https://numpy.org/doc/stable/reference/random/generator.html), [Microsoft PBIP](https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-overview).
