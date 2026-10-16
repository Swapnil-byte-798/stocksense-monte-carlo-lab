# Validation record

Checked in the development environment on 16 October 2026. Python 3.12.14, NumPy 2.3.5, SciPy 1.17.0. This record states what was executed, not merely what is configured.

## Executed successfully

- **20 unittest cases:** hand-calculated economics, prepaid delivery shortfall, fractional tail mass, invalid inputs, reproducible seeds, Sobol sample-size validation, distribution moments, copula direction and marginal frequency, disruption endpoints, analytic oracle, deterministic optimum, fill-rate definition, interval arithmetic, selection/evaluation provenance, request bounds, CSV import, SQLite persistence, and live HTTP integration.
- **All notebook code cells:** executed sequentially in one Python namespace, including independent analytic verification and CSV calibration.
- **Evidence generation:** default run, nine sensitivity combinations, synthetic demand CSV, and 24-replicate MC/Sobol benchmarks at three path counts.
- **CLI:** simulation, defaults, calibration, and local serving exercised.
- **Package:** editable wheel built and installed using already available pinned numerical dependencies.
- **JavaScript:** Node syntax validation of dashboard code.
- **PDF:** study guide rendered and inspected for readable typography, tables, analogy callouts, and page layout.

## Numerical evidence

For the default seed and configuration, selected order is 975 units, held-out mean profit is 14,357.7761, and worst-5% average profit is -1,093.2435. Relative to a 1,000-unit baseline, paired mean difference is -18.4318 with approximate 95% Monte Carlo interval [-18.6277, -18.2359]. Lower-tail improvement is 202.5927, while fill rate falls from 84.26% to 83.14%.

In a separate no-disruption, risk-neutral test, the analytic optimum is 1006.0665 and exact expected profit is 15657.6031. One 65,536-path scrambled Sobol run with seed 17 estimated 15657.6154, absolute error 0.01237. The automated oracle test also checks several other order quantities.

These values verify implementation behavior under synthetic assumptions. They do not establish real-world impact or universal uncertainty coverage.

## Not executed here

- **Browser rendering and UI interaction tests:** local Chromium installation failed because the downloaded browser archive was unusable. The cloud browser could not access localhost. Desktop/mobile visual verification is therefore pending. `scripts/test-browser.cjs` and a GitHub Actions browser job cover the planned check, including exports, history, error states, mobile overflow, and saved-preview behavior.
- **Docker image build:** Docker is not available in this environment. The Dockerfile is supplied but not claimed as tested.
- **GitHub Actions:** workflows are configured; a passing remote run must be confirmed after publication.
- **Python 3.11 and 3.13:** configured in the CI matrix; only Python 3.12 was executed locally.
- **Real-data validation, service-level constraint guarantees, and tail confidence intervals:** outside v1 scope.

## Repeat the checks

```bash
python -m unittest discover -s tests -v
python scripts/reproduce.py
python -m stocklab calibrate examples/synthetic-demand.csv
```

Optional browser check, in a separate terminal while `python -m stocklab serve` is running:

```bash
npm install
npx playwright install chromium
npm run test:ui
```

Review numerical or dependency changes against the analytic oracle before updating committed evidence. Do not replace this report with a generic “all tests passed” claim while listed checks remain pending.
