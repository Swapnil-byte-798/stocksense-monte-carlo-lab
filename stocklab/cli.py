"""Run `python -m stocklab --help`. All generated files default to output/."""

import argparse
from dataclasses import asdict
import json
from pathlib import Path

from .calibration import calibrate
from .experiment import run
from .ledger import save
from .model import Scenario


def main():
    parser = argparse.ArgumentParser(description="StockSense Monte Carlo Decision Lab")
    sub = parser.add_subparsers(dest="command", required=True)
    sim = sub.add_parser("run", help="select an order then evaluate on independent worlds")
    sim.add_argument("--config", type=Path)
    sim.add_argument("--n", type=int, default=4096)
    sim.add_argument("--replicates", type=int, default=12)
    sim.add_argument("--seed", type=int, default=2026)
    sim.add_argument("--method", choices=["mc", "sobol"], default="sobol")
    sim.add_argument("--output", type=Path, default=Path("output/run.json"))
    sim.add_argument("--database", default="output/experiments.db")
    sub.add_parser("defaults", help="print default scenario JSON")
    cal = sub.add_parser("calibrate", help="fit lognormal moments to date,demand CSV")
    cal.add_argument("csv", type=Path)
    serve = sub.add_parser("serve", help="start the local interactive dashboard")
    serve.add_argument("--port", type=int, default=8000)
    serve.add_argument("--host", default="127.0.0.1")
    args = parser.parse_args()
    try:
        if args.command == "run":
            s = Scenario(**json.loads(args.config.read_text())) if args.config else Scenario()
            result = run(s, n=args.n, replicates=args.replicates, seed=args.seed, method=args.method)
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
            row_id = save(result, args.database)
            print(json.dumps({"output": str(args.output), "ledger_id": row_id, "order": result["selected"]["order"], "mean_profit": result["selected"]["mean_profit"], "paired_delta_ci95": result["paired_delta_ci95"]}, indent=2))
        elif args.command == "defaults":
            print(json.dumps(asdict(Scenario()), indent=2))
        elif args.command == "calibrate":
            print(json.dumps(calibrate(args.csv), indent=2))
        else:
            from .server import serve
            serve(args.host, args.port)
    except (ValueError, TypeError, OSError) as exc:
        parser.exit(2, f"Error: {exc}\n")
