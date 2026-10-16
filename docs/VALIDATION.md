# Validation record

Checked locally and in GitHub Actions on 16 October 2026. Local environment: Python 3.12.14, NumPy 2.3.5, SciPy 1.17.0. The published implementation passed all jobs in [CI run 38931946346](https://github.com/Swapnil-byte-798/stocksense-monte-carlo-lab/actions/runs/38931946346), source commit `7f25b25741b394d77fb2f72207b86630e4e8b9d4`. This record states what was executed, not merely what is configured.

## Executed successfully

- **20 unittest cases:** hand-calculated economics, prepaid delivery shortfall, fractional tail mass, invalid inputs, reproducible seeds, Sobol sample-size validation, distribution moments, copula direction and marginal frequency, disruption endpoints, analytic oracle, deterministic optimum, fill-rate definition, interval arithmetic, selection/evaluation provenance, request bounds, CSV import, SQLite persistence, and live HTTP integration.
- **All notebook code cells:** executed sequentially in one Python namespace, including independent analytic verification and CSV calibration.
- **Evidence generation:** default run, nine sensitivity combinations, synthetic demand CSV, and 24-replicate MC/Sobol benchmarks at three path counts.
- **CLI:** simulation, defaults, calibration, and local serving exercised.
- **Package:** editable wheel built and installed using already available pinned numerical dependencies.
- **JavaScript:** Node syntax validation of dashboard code.
- **PDF:** study guide rendered and inspected for readable typography, tables, analogy callouts, and page layout.
- **Python compatibility in GitHub Actions:** numerical and integration tests, CLI run, and CSV calibration all passed on Python 3.11, 3.12, and 3.13.
- **Chromium browser checks in GitHub Actions:** default rendering, scenario changes, JSON download, validation errors retaining the previous result, experiment history, learning view, 390px mobile overflow check, and disabled saved-preview controls all passed. Desktop and mobile screenshots were inspected; the verified desktop capture is included in the README.

The first browser run exposed an incorrect test assumption: Playwright did not classify the fieldset itself as a disabled interactive control. The assertion now checks the actual Run button and demand input, including inherited fieldset disabling. Reduced-motion mode makes screenshots deterministic. Charts use their rendered container size to keep mobile labels readable.

## Numerical evidence

For the default seed and configuration, selected order is 975 units, held-out mean profit is 14,357.7761, and worst-5% average profit is -1,093.2435. Relative to a 1,000-unit baseline, paired mean difference is -18.4318 with approximate 95% Monte Carlo interval [-18.6277, -18.2359]. Lower-tail improvement is 202.5927, while fill rate falls from 84.26% to 83.14%.

In a separate no-disruption, risk-neutral test, the analytic optimum is 1006.0665 and exact expected profit is 15657.6031. One 65,536-path scrambled Sobol run with seed 17 estimated 15657.6154, absolute error 0.01237. The automated oracle test also checks several other order quantities.

These values verify implementation behavior under synthetic assumptions. They do not establish real-world impact or universal uncertainty coverage.

## Remaining checks and limits

- **Docker image build:** Docker is not available in this environment. The Dockerfile is supplied but not claimed as tested.
- **Browser engines:** Chromium was checked; Firefox, WebKit, and real mobile devices were not checked.
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
