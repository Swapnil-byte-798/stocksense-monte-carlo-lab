"""Power BI data preparation and reproducible simulation commands."""

import argparse
from dataclasses import asdict
import json
from pathlib import Path
from .calibration import calibrate
from .experiment import run
from .ledger import save
from .model import Scenario


def main():
    parser = argparse.ArgumentParser(
        description="StockSense: Python engine + Power BI decision report"
    )
    sub = parser.add_subparsers(dest="command", required=True)
    sim = sub.add_parser(
        "run", help="run empirical real-sales simulation; --synthetic for teaching"
    )
    sim.add_argument("--config", type=Path)
    sim.add_argument("--product")
    sim.add_argument("--synthetic", action="store_true")
    sim.add_argument("--n", type=int, default=4096)
    sim.add_argument("--replicates", type=int, default=12)
    sim.add_argument("--seed", type=int, default=2026)
    sim.add_argument("--method", choices=["mc", "sobol"], default="sobol")
    sim.add_argument("--output", type=Path, default=Path("output/run.json"))
    sim.add_argument("--database", default="output/experiments.db")
    defaults = sub.add_parser("defaults")
    defaults.add_argument("--synthetic", action="store_true")
    sub.add_parser("data", help="show real-data provenance and audit")
    bt = sub.add_parser("backtest")
    bt.add_argument("--output", type=Path, default=Path("output/retail-backtest.json"))
    compare = sub.add_parser(
        "compare-policies", help="paired historical policy intervals on real sales"
    )
    compare.add_argument(
        "--output", type=Path, default=Path("output/policy-comparison.json")
    )
    compare.add_argument("--replicates", type=int, default=20000)
    compare.add_argument("--seed", type=int, default=2026)
    cal = sub.add_parser("calibrate", help="positive-only synthetic teaching CSV fit")
    cal.add_argument("csv", type=Path)
    args = parser.parse_args()
    try:
        if args.command == "run":
            from .retail import retail_run

            config = json.loads(args.config.read_text()) if args.config else {}
            opts = dict(
                n=args.n, replicates=args.replicates, seed=args.seed, method=args.method
            )
            result = (
                run(Scenario(**config), **opts)
                if args.synthetic
                else retail_run(args.product, config, **opts)
            )
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
            ledger = save(result, args.database)
            print(
                json.dumps(
                    {
                        "output": str(args.output),
                        "ledger_id": ledger,
                        "order": result["selected"]["order"],
                        "mean_profit_proxy": result["selected"]["mean_profit"],
                        "paired_numerical_ci95": result["paired_delta_ci95"],
                    },
                    indent=2,
                )
            )
        elif args.command == "defaults":
            from .retail import product_data, scenario_for

            _, p, _, h = product_data()
            print(
                json.dumps(
                    asdict(
                        Scenario()
                        if args.synthetic
                        else scenario_for(h[-52:], p["reference_price_gbp"])
                    ),
                    indent=2,
                )
            )
        elif args.command == "data":
            from .retail import catalog

            print(json.dumps(catalog(), indent=2))
        elif args.command == "backtest":
            from .retail import backtest_all

            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(
                json.dumps(backtest_all(), indent=2, allow_nan=False) + "\n"
            )
            print(f"Saved replay to {args.output}")
        elif args.command == "compare-policies":
            from .comparison import compare_policies
            from .retail import backtest_all

            result = compare_policies(
                backtest_all(), replicates=args.replicates, seed=args.seed
            )
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
            print(
                json.dumps(
                    {"output": str(args.output), "gate": result["illustrative_gate"]},
                    indent=2,
                )
            )
        else:
            print(json.dumps(calibrate(args.csv), indent=2))
    except (ValueError, TypeError, OSError) as exc:
        parser.exit(2, f"Error: {exc}\n")
