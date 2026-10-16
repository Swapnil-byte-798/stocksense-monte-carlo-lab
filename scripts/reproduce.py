"""Regenerate committed evidence: python scripts/reproduce.py (from repository root)."""

import csv
from dataclasses import asdict, replace
from datetime import date, timedelta
import json
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np

from stocklab.experiment import run
from stocklab.model import Scenario, analytic_expected_profit, analytic_order, outcomes, uniforms, worlds

ROOT = Path(__file__).resolve().parents[1]


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')


def main():
    output = ROOT/'examples'
    output.mkdir(exist_ok=True)
    write_json(output/'scenario.json', asdict(Scenario()))
    result = run()
    write_json(output/'default-run.json', result)
    write_json(ROOT/'stocklab/web/example.json', result)
    # A fixed-policy benchmark against a closed-form truth, not against another MC run.
    scenario = replace(Scenario(), disruption_probability=0, risk_weight=0)
    order = analytic_order(scenario)
    truth = analytic_expected_profit(scenario, order)
    rows = []
    for n in [256, 1024, 4096]:
        for method in ['mc', 'sobol']:
            start = time.perf_counter()
            estimates = []
            for seed in range(100, 124):
                demand, fill = worlds(scenario, uniforms(n, method, seed))
                estimates.append(float(outcomes(scenario, order, demand, fill)[0].mean()))
            errors = np.array(estimates) - truth
            rows.append({'method': method, 'n': n, 'replicates': 24, 'truth': truth, 'mean_estimate': float(np.mean(estimates)), 'rmse': float(np.sqrt(np.mean(errors**2))), 'replicate_sd': float(np.std(estimates, ddof=1)), 'seconds': round(time.perf_counter()-start, 4)})
    write_json(output/'benchmark.json', {'scenario': asdict(scenario), 'order': order, 'seed_range': [100,123], 'rows': rows, 'warning': 'Smooth no-disruption oracle case only. Speed and accuracy are not guaranteed for discontinuous or high-dimensional models.'})
    with (output/'benchmark.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    sensitivity=[]
    for probability in [.0,.08,.25]:
        for weight in [.0,.2,.5]:
            r=run(replace(Scenario(), disruption_probability=probability, risk_weight=weight), n=1024, replicates=8)
            sensitivity.append({'disruption_probability':probability,'risk_weight':weight,**r['selected']})
    write_json(output/'sensitivity.json', sensitivity)
    rng=np.random.default_rng(481)
    cv=.35;sig=np.sqrt(np.log1p(cv**2));mu=np.log(1000)-sig**2/2
    with (output/'synthetic-demand.csv').open('w',newline='') as f:
        writer=csv.writer(f);writer.writerow(['date','demand'])
        for i, val in enumerate(rng.lognormal(mu,sig,365)):
            writer.writerow([(date(2025,1,1)+timedelta(days=i)).isoformat(),round(val,4)])
    print(json.dumps({'selected':result['selected'],'baseline':result['baseline'],'benchmark':rows},indent=2))


if __name__=='__main__':
    main()
