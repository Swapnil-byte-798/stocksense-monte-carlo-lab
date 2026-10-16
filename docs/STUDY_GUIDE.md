# Monte Carlo, from first principles to a defensible decision

## How to use this guide

This guide teaches the reasoning behind StockSense, not just the commands. Read a lesson, explain its analogy aloud, run the related code, and answer its checkpoint without looking. Mathematical fluency comes from predicting what should happen before pressing Run.

**Prerequisites:** Python variables, functions, loops, and arrays. No prior Monte Carlo knowledge is required. Currency is illustrative INR; the ideas apply to any consistent units.

**Learning route:** Foundations (lessons 1-8), model building (9-14), reliable inference (15-21), engineering (22-27), advanced extensions (28-32), then the practical exercises and interview rehearsal. Advanced extensions are learning material unless explicitly identified as implemented.

## Part I - Foundations

### 1. A decision is different from a prediction

A prediction estimates what might happen: demand may average 1,000 units. A decision chooses an action: order 975, 1,000, or 1,200 units. The best action depends on the cost of mistakes, not just the most accurate forecast. A retailer with cheap leftovers and expensive shortages should make a different decision from one with costly spoilage.

**Analogy:** A weather forecast tells you the chance of rain. Deciding to carry an umbrella also depends on the inconvenience of carrying it and the cost of getting wet. The same forecast can lead two people to different sensible actions.

**Checkpoint:** Why can two retailers with identical demand forecasts choose different quantities? Because their economic costs and preferences differ.

### 2. Random variables and outcomes

A random variable assigns a number to an uncertain outcome. Demand D is unknown when the order is chosen. One simulation world gives D a particular value, such as 850. A list of simulated outcomes is a sample, not the full population of possible outcomes.

**Analogy:** Before opening a mystery box, its weight is unknown. Each opened box reveals one observation. A warehouse full of observed boxes helps describe the pattern without making the next box certain.

**Code connection:** `worlds()` returns arrays of demand and delivered fractions, one value per simulated world.

### 3. Distributions describe shape, not just an average

A probability distribution describes possible values and their relative likelihood. Demand may be tightly clustered or have a long upper tail. Matching only the mean can hide important differences. Two distributions with average 1,000 may imply very different shortage risk.

Normal distributions allow negative values; lognormal distributions are positive and right-skewed. That makes lognormal demand a convenient educational assumption, not proof of the correct real demand model.

**Analogy:** Knowing a class's average height does not tell you whether everyone is similar or whether it mixes very short and very tall students. The distribution is the full class photograph. The mean is one caption underneath it.

### 4. Expectation: the long-run average

For equally weighted simulated profits P1,...,PN, the estimated expectation is mean(P)=sum(Pi)/N. Expected profit need not be an outcome that occurs in any single period. It summarizes the average across repeated model worlds.

Do not compute profit at average demand and call it expected profit: profit contains minimum and maximum functions, so in general E[g(D)] differs from g(E[D]).

**Analogy:** Your average commute might be 37 minutes even if no trip takes exactly 37 minutes. Some days are smooth; others are delayed. Planning only for an average day hides the difficult trips.

**Try:** Compare profit at D=1000 with average profit at D=500 and D=1500 for Q=1000. They differ even though the average demand is the same.

### 5. Variance, standard deviation, and coefficient of variation

Variance measures squared distance from the mean. Standard deviation is its square root and has the original units. The coefficient of variation, CV=SD/mean, is dimensionless. Mean demand 1,000 with CV=.35 implies SD=350.

CV makes relative variability easier to compare across items. It becomes unsuitable when the mean is zero or near zero. StockSense only supports a positive mean.

**Analogy:** A bus that usually arrives within a minute of its average time is predictable. Another with the same average but frequent 20-minute deviations is not. Standard deviation captures the spread that the average hides.

### 6. Quantiles and percentiles

The p quantile is a threshold below which approximately p of the distribution lies. The 5th percentile of profit describes a poor-outcome boundary. It is not the average of bad outcomes and not an uncertainty interval for the mean.

Empirical quantiles use a finite sample and an interpolation convention. StockSense uses NumPy's default quantile interpolation for P05 and P95. Exact numerical reproduction therefore includes library versions.

**Analogy:** The slowest 5% cutoff in a race is a boundary time. It does not tell you the average finish time among those runners. A cutoff and an average answer different questions.

### 7. Seeds and pseudorandomness

A pseudorandom generator deterministically transforms internal state into numbers with useful statistical properties. A seed initializes that state. The same algorithm, environment, call order, and seed can reproduce a sequence. Reusing a seed is useful for debugging; using one seed repeatedly is not independent replication.

StockSense creates local generators rather than changing NumPy's global state. A root SeedSequence allocates separate selection and evaluation branches. Each evaluation replicate has its own derived seed.

**Analogy:** A seed is the starting page in a very long, carefully arranged book of numbers. Starting from the same page lets a teammate follow your exact route. Reading that same route twice does not create two independent journeys.

### 8. What Monte Carlo actually does

Monte Carlo estimates a quantity by repeatedly sampling uncertain inputs, computing an outcome, and aggregating results. In this project the quantity may be expected profit, probability of a loss, or demand fulfillment. The simulation is conditional on its assumptions.

```python
import numpy as np
rng = np.random.default_rng(2026)
demand = rng.lognormal(mean=6.85, sigma=0.34, size=10000)
profit = 50*np.minimum(demand, 1000) - 28*1000
print(profit.mean())
```

This small snippet omits salvage, disruption, and shortage penalties. The full model adds them explicitly.

**Analogy:** Rehearse a shop's opening day thousands of times with different customer arrivals. Calculate what each rehearsal earns. The collection reveals plausible outcomes, while no rehearsal predicts the exact real day.

## Part II - Build the model

### 9. Write the accounting equation first

Let Q be ordered stock, D demand, and F delivered fraction. Available stock is QF. Sales=min(D,QF), leftovers=max(QF-D,0), and unmet demand=max(D-QF,0).

Profit = price×sales + salvage×leftovers - cost×Q - shortage_penalty×unmet.

The full Q is prepaid. Undelivered stock has no refund in this model. This assumption matters economically and must be stated before interpreting results.

**Analogy:** A shop's cash register has several compartments: sales money, leftover recovery, purchase bills, and shortage costs. Writing each compartment separately prevents accidentally counting money twice. A polished chart cannot fix a missing bill.

**Worked case:** Q=100, D=80, F=1, price=50, cost=28, salvage=8 gives 4,000+160-2,800=1,360. With D=120, shortage penalty=5, profit is 5,000-2,800-100=2,100.

### 10. Convert intuitive demand parameters into lognormal parameters

Users think in mean m and CV v. A lognormal generator needs normal-space mu and sigma. Use sigma²=log(1+v²) and mu=log(m)-sigma²/2; then D=exp(mu+sigma Z), Z standard normal.

For m=1,000 and v=.35, sigma is about .340 and mu about 6.850. Passing 1,000 as the generator's log-space mean would be catastrophically wrong. Test the generated sample moments against the requested moments.

**Analogy:** A recipe may specify tablespoons while your measuring tool uses milliliters. Both describe the same ingredient but require conversion. Mean demand and log-space mean are different measurement systems.

### 11. Model supply disruption

A Bernoulli event has two possibilities: disruption or no disruption. If disruption probability is .08, about 8% of generated worlds should be disrupted in a sufficiently large sample. With delivered fraction .65, a 1,000-unit order supplies 650 units in those worlds.

This is a severity assumption, not a lead-time simulation. There is no partial recovery or later replenishment. The cost of 1,000 units remains payable under the stated contract.

**Analogy:** A delivery service may occasionally arrive with only part of a parcel shipment. The event frequency describes how often that happens; the delivered fraction describes how severe it is. Mixing those two quantities would confuse frequency with impact.

### 12. Dependence and the Gaussian copula

Independent demand and supply risks can understate joint stress. StockSense transforms two independent normal inputs into a demand factor Z1 and a supply factor Zs=rho Z1+sqrt(1-rho²)Z2. High Zs triggers disruption. Positive rho aligns high demand with higher disruption likelihood while preserving the intended marginal disruption probability.

Rho is correlation between latent normal variables. It is not automatically the correlation between observed demand and a binary disruption indicator. The model allows negative rho too, but bounds it away from ±1.

**Analogy:** Rain can increase umbrella demand while also slowing delivery vans. These problems share a cause rather than arriving independently. A copula is a way to connect their patterns without pretending they are the same variable.

### 13. Metrics answer different business questions

Expected profit measures average performance. Loss probability measures how often profit is negative. Tail profit measures how bad the worst outcomes are. Fill rate=sum(sold)/sum(demand) measures the fraction of demanded units supplied. Stockout probability measures the fraction of worlds with any shortage.

A shop may stock out on many days but miss only one unit each day, producing high fill rate and high stockout probability. Report both when service matters.

**Analogy:** A train can be late on many trips but only by one minute, or late rarely by two hours. Frequency and severity are different. Inventory service also needs more than one number.

### 14. Tail risk and the objective function

Sort profit outcomes from lowest to highest and average the bottom 5%. This is worst-5% average profit. Use fractional mass at the boundary when 5% of N is not an integer. If profits are [0,10,20], the bottom half contains 0 and half the mass at 10, so the tail mean is (0+0.5×10)/1.5=3.333.

StockSense maximizes (1-w)×mean_profit + w×tail_profit. Both terms use currency units. Setting w=.2 expresses a preference, not a 20% chance of loss. A fixed weighted score does not guarantee a minimum service level.

**Analogy:** Choosing a route by average travel time ignores occasional disastrous delays. Adding a penalty for the worst trips expresses how much you dislike being late. Different travelers can reasonably choose different weights.

## Part III - Make the result trustworthy

### 15. Law of large numbers

Under appropriate conditions, sample averages approach their population expectation as the number of samples grows. This justifies simulation averages. It does not say every larger run is closer than every smaller run, or that the modeled population matches reality.

For finite-mean independent samples the law applies broadly. Randomized Sobol has its own convergence theory; do not describe its dependent points as an IID sample merely because there are many of them.

**Analogy:** A handful of scoops may misrepresent a jar of mixed beans. More well-designed scoops usually reveal the composition more reliably. If the jar is the wrong one, additional scoops still describe the wrong jar.

### 16. Central limit theorem and standard error

For many well-behaved IID samples with finite variance, the standardized sample mean becomes approximately normal as N grows. The standard error of an ordinary sample mean is approximately SD/sqrt(N). Reducing error by half typically requires about four times as many IID samples.

Standard deviation describes variation among individual outcomes. Standard error describes variation among estimates of their mean. A business can have a precisely estimated mean while individual periods remain risky.

**Analogy:** Individual basketball shots vary widely in where they land. The estimated average landing point becomes more stable as you observe more shots. Stable knowledge of the center does not make every shot land at the center.

### 17. Confidence intervals are not outcome ranges

A frequentist 95% confidence procedure covers the fixed target in about 95% of repeated experiments under its assumptions. It does not mean 95% of future period profits fall inside the interval. An outcome interval and a confidence interval answer different questions.

StockSense reports a Student-t interval over independent replicate means: average ± t_critical×replicate_SD/sqrt(R), with R-1 degrees of freedom. The interval is approximate unless replicate means are normal. It conditions on the chosen policy and model parameters.

**Analogy:** Measuring the average depth of a lake very precisely does not mean every part of the lake has that depth. The confidence interval concerns your estimate of the average. A swimmer still needs to understand the range of depths.

### 18. Common random numbers and paired comparisons

Compare candidate policies on the same demand and supply worlds. For each replicate compute mean(selected_profit-baseline_profit), then estimate uncertainty across replicate differences. This controls some noise from different environmental conditions.

Mathematically, Var(A-B)=Var(A)+Var(B)-2Cov(A,B). Positive covariance between policy profits can reduce comparison variance. Variance reduction is not guaranteed for every model, so it is a design choice to evaluate rather than a universal theorem about shared seeds.

**Analogy:** Test two umbrellas in the same rainstorm. Comparing one in drizzle with another in a downpour confuses the product with the weather. Paired conditions help isolate the policy difference.

### 19. Scrambled Sobol sampling

Sobol sampling covers a uniform input space with a structured, low-discrepancy pattern. Scrambling randomizes the pattern while retaining its design properties. In StockSense each replicate contains a power-of-two number of points and uses a fresh scramble.

Improvement depends on dimension and integrand structure. Sharp disruption thresholds can reduce the advantage. Benchmark against an independent truth when available, and report both error and computational cost. Do not apply an IID error formula to individual Sobol points.

**Analogy:** Inspect a field using points spread evenly across the area. This can cover the field more effectively than random clusters of inspection points. Independently moving the pattern lets you study how the estimate changes.

### 20. Selection bias and independent evaluation

Searching many policies can select one that looks unusually good because of simulation noise. Evaluating it only on that same sample overstates its apparent performance. StockSense chooses Q using selection worlds, freezes Q, and evaluates on independent worlds.

This is analogous to train/test separation but is not a historical backtest. It controls simulation-selection reuse, not distribution misspecification or parameter estimation error. Repeatedly tuning the system after viewing evaluation results can also turn a test into a development set.

**Analogy:** Memorizing practice questions can make an exam score look impressive without proving understanding. A fresh exam provides a better test. If you repeatedly revise your answers after seeing the fresh exam, it is no longer unseen.

### 21. Verification versus validation

Verification asks whether the code correctly implements the mathematical model. Validation asks whether the model adequately represents the intended real system. StockSense verifies accounting with hand examples, checks a deterministic limit, and compares simulation against an analytic no-disruption reference.

The reference optimum is Q*=F_D^-1((p-c+k)/(p-s+k)) for risk-neutral profit with no disruption. It does not apply unchanged to the risk-weighted disrupted model. Real validation would require demand records, supply observations, contract review, and out-of-time evaluation.

**Analogy:** Verification checks whether a map was printed accurately from its source. Validation checks whether the source actually describes the city you are visiting. A perfectly printed outdated map can still mislead you.

## Part IV - Engineering a project others can use

### 22. Calibration and data quality

Calibration estimates distribution parameters from observations. For positive demand, lognormal maximum likelihood uses the mean and population variance of log-demand. Transform them back to demand mean and CV. The CSV importer requires exact headers, valid unique dates, enough rows, and finite positive demand.

Thirty observations is a basic input rule, not a proof of reliable fit. Seasonality, outliers, changes over time, and censored sales require diagnostics and potentially a different model. Sales are not automatically demand: a stockout hides unmet demand.

**Analogy:** A thermometer can be calibrated using known temperatures, but it cannot infer heat it never measured. Sales during stockouts are like a thermometer that stops at a ceiling. Treating capped measurements as complete data understates extremes.

### 23. Vectorization and computational complexity

NumPy applies operations across arrays in compiled routines. StockSense computes one policy over many worlds at once, while iterating over the modest policy grid. This avoids a large K×N matrix of all policy outcomes. Tail sorting costs O(N log N) per candidate; total selection is approximately O(KN log N).

Vectorization is not automatically memory-efficient. Always account for temporary arrays and retained evaluation samples. A request cap is a product constraint that keeps the demo responsive.

**Analogy:** A conveyor belt processes many identical items efficiently. Building a separate conveyor for every possible product would waste space. The implementation reuses a practical-sized line instead of constructing an enormous factory.

### 24. Reproducibility and provenance

Save the full scenario, sample size, method, root and child seeds, software versions, execution time, and results. The configuration ID is a hash of the request. Identical configuration IDs do not prove identical software environments; the version metadata provides that additional context.

The CSV hash records which exact source bytes were used. A timestamp distinguishes executions, while a SQL run ID provides a local unique identifier. Timing results can vary even when numerical outputs match.

**Analogy:** A recipe needs ingredients, quantities, oven settings, and method. Saying only 'I used seed 2026' is like recording the oven temperature but omitting the ingredients. Provenance is the complete recipe card.

### 25. SQL as an experiment memory

SQLite stores typed summary columns for quick queries and a complete JSON result for audit. Parameterized SQL separates values from query code. An index on configuration ID speeds lookup; a window function selects the latest run per configuration without deleting history.

Repeated identical configurations are legitimate records, not necessarily data duplicates. An append-only history supports comparison and debugging. It is still a local file, so backup and concurrency requirements change for shared production use.

**Analogy:** A laboratory notebook records every experiment, even repeated ones. A neat summary table helps you find the experiment; the detailed page explains how it was performed. SQLite supplies both the index and the notebook.

### 26. API and interface contracts

The API validates inputs, runs the same engine as the CLI, and returns structured results. The interface should clearly distinguish editable inputs, running status, successful outputs, and errors. A changed input must not silently relabel an old result as current.

StockSense marks pending changes, keeps previous results after errors, and disables simulation when displaying a static saved preview. Unknown routes do not expose arbitrary files. The local server remains a demo, not a production security boundary.

**Analogy:** A restaurant menu states what can be ordered, the kitchen prepares it, and the waiter reports what arrived. If the kitchen rejects a request, the waiter must not invent a meal. A good API and interface preserve the same honest contract.

### 27. Tests that provide evidence

Useful tests have an independent reason to expect an answer. Examples include exact accounting, known limiting cases, analytic references, invalid input rejection, seed replay, and actual HTTP requests. A test that recomputes the same formula in the same way may repeat the same bug.

Numerical tests use tolerances justified by their reference and sample design. Avoid probabilistic tests that fail unpredictably; fixed seeds and sensible tolerances make the signal stable. Passing tests supports specific claims, not a guarantee of zero defects.

**Analogy:** Checking a calculator by pressing the same buttons twice only proves consistency. Comparing it with a hand calculation checks correctness independently. Tests should bring a second source of reasoning.

## Part V - Advanced extensions and when to use them

### 28. Parameter uncertainty and bootstrap - extension

The current model treats demand parameters as known. To reflect estimation uncertainty, resample historical observations, refit parameters, and rerun the decision experiment. This creates an outer parameter loop and an inner simulation loop. Preserve separate random streams for each layer.

An ordinary IID bootstrap assumes exchangeable observations. Seasonal or serially dependent demand may require block resampling or an explicit time-series model. Distinguish numerical Monte Carlo error from variation caused by refitted parameters.

**Analogy:** You are unsure both about tomorrow's weather and about how accurate your weather model is. Repeating tomorrow under one fixed model explores the first uncertainty. Refitting plausible models explores the second.

### 29. Importance sampling - extension

Rare losses may be poorly represented in ordinary samples. Importance sampling draws from a proposal distribution that visits important regions more often, then weights outcomes by target density divided by proposal density. For expectation E_f[g(X)], use average(g(X)f(X)/q(X)) with X drawn from q.

The proposal must cover relevant target support, and unstable weights can increase variance. Tail quantiles and tail means need carefully designed weighted estimators. This is not implemented in v1 and should not be claimed as a feature.

**Analogy:** Inspect more houses in flood-prone areas to understand rare flood damage. Because those areas were oversampled, adjust their contribution before estimating the whole city's average. Sampling more danger without weighting would exaggerate overall risk.

### 30. Antithetic variates and control variates - extensions

Antithetic sampling pairs U with 1-U to create compensating outcomes when the response has suitable monotonic structure. Control variates use a correlated quantity with known expectation: adjusted estimate Y-b(X-E[X]). A good coefficient can reduce variance without changing the expectation.

The dependence created by these methods must be reflected in uncertainty estimates. Estimate coefficients carefully, ideally on separate or properly accounted-for data. Neither method guarantees improvement for arbitrary nonlinear models.

**Analogy:** Two people carrying opposite ends of a plank can balance each other's movement. That is the intuition behind antithetic pairs. A familiar ruler placed beside an unfamiliar object acts like a control variate: a known reference helps refine measurement.

### 31. Bayesian modeling and MCMC - extension

Monte Carlo broadly means estimation using simulation. Markov chain Monte Carlo is a specific family for sampling difficult target distributions using dependent chains. A Bayesian extension could place priors on demand parameters, update them with data, and simulate posterior predictive demand.

MCMC requires chain diagnostics, effective sample size, convergence assessment, and attention to autocorrelation. StockSense uses direct sampling and randomized Sobol; it does not run MCMC. Using a sophisticated name without its diagnostics weakens an interview answer.

**Analogy:** Direct sampling is like drawing independent tickets from a known box. MCMC is like walking through connected rooms to explore a building you cannot sample directly. You must check whether the walk explored the building rather than circling one hallway.

### 32. Multi-period decisions and constrained optimization - extension

A multi-period model tracks inventory state over time, replenishment lead times, backlogs, and policy rules such as reorder points. Multiple items introduce budget, warehouse, or service constraints. These change both the simulator and the optimization problem; they are not solved by increasing N.

Before adding reinforcement learning or complex solvers, define states, actions, transition logic, constraints, and simple baselines. Validate conservation of units and cash across time. For real operations, measure decision quality out of time and against existing policies.

**Analogy:** Packing lunch for one day is a single-period decision. Planning a kitchen for a month requires tracking leftovers, deliveries, expiry, and tomorrow's needs. The problem gains memory, so the model must gain state.

## Guided practical exercises

### Exercise A: predict the deterministic result

Set demand CV=0, disruption probability=0, risk weight=0, and mean demand=1,000. Keep the default economics and ensure the grid includes 1,000. Before running, predict the best order and profit.

**Answer:** Q=1,000 and profit=(50-28)×1,000=22,000. There are no leftovers or shortages. A larger Q loses 20 per unused unit; a smaller Q gives up 27 per missing unit including shortage penalty.

### Exercise B: explain the default policy

Read `examples/default-run.json`. Why does the selected quantity have lower mean profit than the baseline? Does this mean the optimizer failed?

**Answer:** The objective blends mean and lower-tail profit. The 975-unit order gives up approximately 18.43 of expected profit while improving worst-5% average profit by approximately 202.59. At w=.2 this raises the weighted score. It reduces fill rate, so the trade-off must be accepted rather than hidden.

### Exercise C: distinguish three uncertainties

Write one sentence each for outcome uncertainty, Monte Carlo estimation uncertainty, and parameter uncertainty.

**Answer:** Outcome uncertainty is which demand and supply world occurs. Estimation uncertainty is how the finite simulation differs from the model expectation. Parameter uncertainty is not knowing the correct demand and supply parameters. The current confidence intervals address only the second.

### Exercise D: improve the search responsibly

Use a narrower grid step near the selected quantity. Keep the evaluation stream independent. Explain why a higher in-sample score does not automatically prove a meaningful improvement.

**Answer:** More candidates can exploit selection-sample noise. Fine grid spacing also has diminishing practical value. Compare the frozen policies on a fresh evaluation sample and inspect both the magnitude and paired uncertainty of the difference.

### Exercise E: challenge the supplier contract

Change the model to pay only for delivered units: replace cost×Q with cost×QF. Add a hand-calculated shortfall test. Explain why comparing this new result with the old result is a model-change experiment, not a faster algorithm.

**Answer:** The economic assumptions changed. With Q=100, F=.5, D=120 and default economics, profit becomes 2,500-1,400-350=750 instead of -650. The new contract transfers part of the disruption cost to the supplier.

### Exercise F: inspect the benchmark fairly

Run `python scripts/reproduce.py`. Compare RMSE for MC and Sobol at equal N. What prevents you from claiming the observed ratio applies to every Monte Carlo problem?

**Answer:** The benchmark uses a low-dimensional fixed policy with no disruption and a known analytic expectation. Dimension, discontinuities, tail behavior, computational overhead, and model structure can alter performance. The result is evidence for this case, not a universal speed guarantee.

### Exercise G: introduce realistic data carefully

List checks needed before fitting lognormal demand to real sales.

**Answer:** Separate true demand from censored sales; check zeros, missing periods, returns, duplicate dates, seasonality, promotion effects, trend, outliers, structural changes, and whether units and aggregation periods are consistent. Use out-of-time validation and compare alternative distributions.

## A 14-day learning plan

| Day | Focus | Concrete output |
|---|---|---|
| 1 | Lessons 1-4 | Explain prediction versus decision and compute a mean |
| 2 | Lessons 5-8 | Simulate a simple random variable and explain its spread |
| 3 | Lesson 9 | Reproduce both hand-calculated profit examples |
| 4 | Lessons 10-12 | Explain parameter conversion and latent dependence |
| 5 | Lessons 13-14 | Compare fill rate, stockout chance, quantiles, and tail average |
| 6 | Lessons 15-17 | Explain standard error and confidence interval limitations |
| 7 | Lessons 18-20 | Demonstrate paired comparisons and held-out evaluation |
| 8 | Lesson 21 | Derive the no-disruption critical fractile |
| 9 | Lessons 22-24 | Fit the synthetic CSV and inspect provenance |
| 10 | Lessons 25-27 | Query SQLite and explain three independent tests |
| 11 | Lessons 28-29 | Sketch bootstrap and importance-sampling extensions |
| 12 | Lessons 30-32 | Distinguish direct MC, variance reduction, and MCMC |
| 13 | Exercises A-G | Make one reviewed model change with a new test |
| 14 | Interview kit | Record a five-minute demo and answer limitations honestly |

## Compact glossary

| Term | Plain meaning |
|---|---|
| Scenario | A complete set of model assumptions |
| World / path | One set of simulated uncertain inputs |
| Policy | The chosen order quantity in this project |
| Replicate | A complete independently randomized batch of worlds |
| Estimator | A calculation using samples to estimate a target quantity |
| Bias | Systematic difference between an estimator's expectation and its target |
| RMSE | Square root of average squared error against a known reference |
| Copula | A construction for dependence while retaining marginal distributions |
| Tail risk | Behavior of extreme adverse outcomes |
| Aleatory uncertainty | Random variability in outcomes under a model |
| Epistemic uncertainty | Uncertainty due to incomplete knowledge of a model or its parameters |
| Calibration | Estimating model parameters from observations |
| Verification | Checking code against the specified mathematics |
| Validation | Checking the model against the real problem |

## Primary references and further reading

- [MIT OpenCourseWare: Newsvendor Inventory Problem](https://ocw.mit.edu/courses/15-772j-d-lab-supply-chains-fall-2014/6952be57b43aa185119c6f114908bcc5_MIT15_772JF14_Newsboy.pdf) - underlying inventory problem.
- [SciPy: scrambled Sobol engine](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.qmc.Sobol.html) - sequence properties and implementation contract.
- [NumPy: random Generator](https://numpy.org/doc/stable/reference/random/generator.html) - modern random-generation API.
- The project's [methodology](METHODOLOGY.md), [source](../stocklab/model.py), and [tests](../tests/test_model.py) define the specific implementation. Analogies are original teaching aids; their simplified comparisons are not substitutes for mathematical assumptions.
