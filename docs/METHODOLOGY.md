# Statistical specification

## 1. Economic model

Let Q be ordered quantity, D demand, F the delivered fraction, p unit selling price, c purchase cost, s salvage value, and k shortage penalty.

Available stock A = QF; sold units S = min(D,A); leftovers L = max(A-D,0); unmet demand U = max(D-A,0).

**Profit: P = pS + sL - cQ - kU.**

The full order is prepaid, even if a disruption reduces delivery. This is a deliberate stress-contract assumption, not a universal supply contract. Changing to payment for delivered units requires changing the accounting equation and revalidating it. Unsold delivered units have salvage value. The model excludes taxes, fixed costs, replenishment, and time discounting.

## 2. Distribution and dependence

For desired mean m and coefficient of variation v, set sigma = sqrt(log(1+v²)) and mu = log(m) - sigma²/2. Generate independent standard-normal coordinates Z1 and Z2 from uniform inputs. Demand is D = exp(mu + sigma Z1), which has mean m and coefficient of variation v. The v=0 case is deterministic.

Define Zs = rho Z1 + sqrt(1-rho²) Z2. A disruption occurs when Zs > Phi^-1(1-pd), where pd is the marginal disruption probability. The delivered fraction is fd when disrupted and 1 otherwise. Positive rho makes high-demand worlds more likely to coincide with disruption. Rho is a **latent Gaussian correlation**, not the observed Pearson correlation between demand and a binary event.

Demand and delivered units are continuous. For indivisible goods, a discrete model must be specified; silently rounding changes both moments and the analytic benchmark.

## 3. Risk preference

Let T_alpha be the empirical average of the lowest alpha fraction of profit observations. The score is:

**Score(Q) = (1-w) E[P(Q)] + w T_alpha(P(Q)).**

Both terms have the same monetary units. A larger w expresses greater preference for downside protection. It is neither the probability of a bad event nor a fitted model coefficient. This is a weighted objective, not a hard service-level constraint.

For sorted profits x1 <= ... <= xn and mass a=alpha*n, define j=floor(a), r=a-j. The lower-tail mean is (sum(x1...xj) + r*x(j+1))/a. This fractional boundary rule handles ties and noninteger tail sizes without changing the target tail mass. At alpha=.05 it is the worst-5% average profit. The fifth percentile is a different statistic. A conventional loss CVaR would use loss=-profit and the upper loss tail; the application deliberately displays the profit convention.

## 4. Selection and evaluation

Generate N selection worlds once. Every candidate faces these same worlds. Choose the maximum empirical score; ordered-grid ties choose the lower quantity. Then freeze the chosen order. Use a separate SeedSequence branch to generate R independent evaluation replicates of N worlds each. Selected and baseline policies share worlds within each evaluation replicate.

The independent evaluation estimates the performance of the selected, now fixed policy. It does not quantify uncertainty in which policy would be selected on a different training sample, prove global optimality, or validate the underlying distribution.

## 5. Confidence intervals

For replicate means M1,...,MR, report mean(M) ± t(.975,R-1) × sd(M)/sqrt(R). For comparison, first compute the within-replicate average difference between selected and baseline profit, then apply the same interval to those R paired differences.

The t interval is an approximation for independent replicate means. It is exact under normal replicate means and otherwise depends on approximate normality. Individual Sobol points within a replicate are not independent; using their raw sample standard deviation divided by sqrt(N) would give the wrong inference basis. Mean intervals describe simulation error conditional on parameters. Tail, quantile, stockout, fill-rate, and loss-chance metrics are point estimates in this release. A wider set of uncertainty methods belongs in future work.

## 6. Sampling methods

Ordinary Monte Carlo uses NumPy's local Generator with a supplied seed. Randomized quasi-Monte Carlo uses independent scrambled two-dimensional Sobol sequences. Each replicate uses exactly 2^m points through `random_base2`, preserving sequence balance. No Sobol points are skipped or thinned. Inverse-normal endpoints are clipped to floating-point epsilon to avoid infinity; this is a negligible numerical endpoint approximation rather than a model for extreme tails. See the [SciPy Sobol documentation](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.qmc.Sobol.html).

## 7. Independent analytic oracle

When disruption is zero and w=0, the newsvendor critical fractile is (p-c+k)/(p-s+k). The unrestricted optimal quantity is the corresponding demand quantile. This follows by differentiating expected profit with respect to Q; the shortage penalty increases the opportunity cost of under-ordering.

For lognormal demand with parameters mu and sigma and Q>0, define z=(log(Q)-mu)/sigma. Expected sold units are m Phi(z-sigma) + Q[1-Phi(z)]. Substitute this into:

E[P] = (p-s+k) E[S] + (s-c)Q - km.

The implementation separately handles Q=0 and sigma=0. Tests compare simulated profits with this analytic reference at multiple order quantities, then verify that the analytic optimum beats nearby quantities. This oracle applies only to the simplified model, not to the correlated disruption scenario. For the underlying inventory formulation, see [MIT OpenCourseWare's newsvendor notes](https://ocw.mit.edu/courses/15-772j-d-lab-supply-chains-fall-2014/6952be57b43aa185119c6f114908bcc5_MIT15_772JF14_Newsboy.pdf).

## 8. Metric definitions

| Metric | Definition | Interpretation |
|---|---|---|
| Mean profit | Average of all profit outcomes | Long-run model average |
| Worst-tail profit | Fractional lower-tail average | Severity of bad outcomes; higher is better |
| Loss probability | Mean of indicator(P<0) | Frequency of negative profit |
| Fill rate | Sum(sold) / Sum(demand) | Unit-weighted demand fulfilled |
| Stockout probability | Mean of indicator(unmet>0) | Fraction of worlds with any shortage |
| P05 / P95 | Empirical profit quantiles | Outcome range boundaries, not confidence bounds |
| Paired delta | Average(selected profit - baseline profit) | Expected profit difference under shared conditions |

## 9. What must be validated before real use

Demand distribution, seasonality, censorship from stockouts, item substitutability, supplier economics, disruption frequency, dependence, and parameter stability. Historical validation and stakeholder review are separate from numerical verification. Finite-grid search, synthetic experiments, and highly precise numerical estimates do not establish business impact.
