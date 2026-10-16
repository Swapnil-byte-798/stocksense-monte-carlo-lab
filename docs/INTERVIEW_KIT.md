# Recruiter and interview kit

## Positioning

This project demonstrates a useful combination for data science, decision science, analytics engineering, and technical business analyst roles: translate a business decision into a model, quantify uncertainty, build a usable tool, verify the mathematics, and explain limitations. It complements ETL and predictive-model projects by showing how a prediction becomes an operational decision.

The project cannot guarantee hiring. Its value depends on your ability to reproduce, modify, and defend it. Do not claim real customer impact, professional deployment, or unassisted authorship if those did not occur.

## Resume bullets you can defend after studying the project

- Built a Python Monte Carlo inventory decision lab using NumPy and SciPy, comparing 57 order policies under correlated demand and supply disruption and evaluating the selected policy on 49,152 held-out simulated outcomes.
- Implemented scrambled Sobol sampling, common random numbers, replicate-level confidence intervals, and a closed-form inventory benchmark; added numerical and API tests plus reproducible experiment exports.
- Delivered an interactive decision dashboard, strict demand-CSV calibration, and an indexed SQLite experiment ledger with analytical SQL, documenting assumptions and profit-service-risk trade-offs.

Use only bullets you can explain and reproduce. The default sample counts describe a specific configuration, not a fixed scalability limit. If you mention benchmark improvement, specify the no-disruption fixed-policy benchmark, equal path count, and observed error metric. Do not convert simulated outcomes into claims of company savings.

## A 60-second explanation

“I built StockSense to answer how much inventory a retailer should order when both demand and supplier delivery are uncertain. I modeled demand with a lognormal distribution and coupled it with supply disruption using a Gaussian copula. The tool compares order quantities using expected profit and worst-tail profit, then tests the selected quantity on independent simulated scenarios. I added paired policy comparisons, reproducible seeds, a SQL experiment ledger, and a dashboard. I verified a simplified case against an analytic inventory formula. The main limitation is that these are synthetic model results, so real use would require demand validation, realistic supplier contracts, and parameter-uncertainty analysis.”

## Five-minute demonstration

1. **0:00-0:45 - Problem:** Explain why ordering average demand is not necessarily the best economic decision.
2. **0:45-1:45 - Baseline run:** Show the selected order, mean profit, lower-tail profit, and fill rate. Explain the default trade-off without claiming every metric improves.
3. **1:45-2:30 - Scenario:** Increase disruption or downside emphasis, rerun, and describe why the order changes. If it stays on the same grid point, explain grid resolution and the objective.
4. **2:30-3:15 - Trust:** Show the independent evaluation streams, paired confidence interval, and analytic test.
5. **3:15-4:00 - Engineering:** Export JSON, inspect the SQL experiment log, and trace one API call into the pure Python engine.
6. **4:00-5:00 - Limits:** Discuss model uncertainty, censored sales, and the next meaningful extension.

## Questions and strong answer outlines

| Question | What a strong answer includes |
|---|---|
| Why Monte Carlo if a newsvendor formula exists? | The formula validates a simpler case. Correlated disruptions and a tail-sensitive objective complicate the full model; simulation offers flexibility. |
| Why lognormal? | Positive, right-skewed demand with interpretable mean/CV; a modeling assumption requiring empirical comparison, not a universal truth. |
| Why not just increase sample count? | Reduces numerical noise but cannot fix wrong assumptions or parameter estimates; cost grows with samples. |
| How did you avoid overfitting? | Independent selection and evaluation streams; no claim that this removes all model risk or selection uncertainty. |
| What does a 95% CI mean? | Repeated-experiment coverage under assumptions; for the model mean, not 95% of period outcomes. |
| Why independent scrambles? | Sobol points within a replicate are dependent; uncertainty is estimated across separately randomized replicate means. |
| Why common random numbers? | Paired worlds reduce environmental noise when policy outcomes are positively correlated; use variance-of-difference reasoning. |
| Is worst-tail profit the same as VaR? | No. VaR is a quantile boundary; tail average measures average severity beyond the boundary, with an explicit profit/loss convention. |
| Why does your recommendation earn less on average? | It optimizes a weighted mean/tail objective; the default example sacrifices a little mean for better lower-tail results. |
| How would you model stockout-censored demand? | Sales may be capped by inventory; use availability and lost-sales information, censored likelihoods, or other explicit demand-estimation methods. |
| What would you add for production? | Authentication, bounded job queue, rate limits, robust server/gateway, durable storage, monitoring, and model governance. |
| Why no React/Kubernetes/cloud stack? | The decision engine and validation are the substantive scope; the buildless local UI keeps setup reproducible. Add infrastructure when requirements justify it. |
| What is the hardest bug you guarded against? | Wrong lognormal parameterization, reused selection samples, IID inference on Sobol points, or confusing fill rate with stockout frequency. Explain a test. |
| How did AI assist? | Be candid about code/documentation assistance, then demonstrate what you understand, verified, and changed yourself. |

## Ownership exercises before listing the project

- Derive the accounting formula without reading it.
- Change the supplier refund assumption and add an independent expected-value test.
- Explain each chart, including why its data comes from selection or evaluation.
- Query the SQL ledger for the most recent run per configuration.
- Reproduce the benchmark and explain its scope.
- Read one source module end to end and explain its dependencies.
- Write down an assumption you would challenge first for a real retailer.

Completing these exercises turns a repository you can run into a project you can defend.
