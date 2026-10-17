import copy
import json
from pathlib import Path
import tempfile
import unittest
import numpy as np
import pandas as pd
from stocklab.model import Scenario, uniforms, worlds, validate_history
from stocklab.preparation import clean_transactions, derive_panel
from stocklab.retail import catalog, product_data, retail_run, replay_product
from stocklab.ledger import save, recent


class RetailTests(unittest.TestCase):
    def test_empirical_support_and_zero_mass(self):
        history = np.array([0, 0, 1, 2, 3, 4, 5, 9])
        d, _ = worlds(Scenario(), uniforms(8192, "sobol", 20), history)
        self.assertEqual(set(d), set(history))
        self.assertAlmostEqual(float(np.mean(d == 0)), 0.25, delta=0.002)
        self.assertAlmostEqual(float(d.mean()), float(history.mean()), delta=0.01)

    def test_history_validation(self):
        for data in [[1] * 7, [0] * 8, [-1] + [1] * 7, [float("nan")] * 8, [[1] * 8]]:
            with self.subTest(data=data), self.assertRaises(ValueError):
                validate_history(data)

    def test_real_calendar_and_source_audit(self):
        m = catalog()
        self.assertEqual(m["raw_rows"], 1067371)
        self.assertEqual(m["cleaned_rows"], 892892)
        self.assertEqual(
            sum(a["removed"] for a in m["cleaning_audit"]),
            m["raw_rows"] - m["cleaned_rows"],
        )
        for product in m["products"]:
            _, _, rows, values = product_data(product["stock_code"])
            dates = pd.to_datetime([r["week_start"] for r in rows])
            self.assertEqual(len(values), 104)
            self.assertTrue(
                np.all(
                    np.diff(dates).astype("timedelta64[D]") == np.timedelta64(7, "D")
                )
            )
            self.assertEqual(rows[65]["week_start"], "2011-03-07")

    def test_cleaning_counts_first_failure_and_retains_missing_identity(self):
        base = {
            "Invoice": "500001",
            "StockCode": "12345a",
            "Description": "ITEM",
            "Quantity": 10,
            "InvoiceDate": "2010-02-01",
            "Price": 2,
            "Customer ID": None,
            "Country": "United Kingdom",
        }
        rows = [base, copy.deepcopy(base)]
        for update in [
            {"Invoice": "C500001"},
            {"Quantity": -1},
            {"Price": 0},
            {"StockCode": "POST"},
            {"Country": "France"},
            {"InvoiceDate": "bad"},
        ]:
            rows.append({**base, **update})
        clean, audit = clean_transactions(pd.DataFrame(rows))
        self.assertEqual(len(clean), 1)
        self.assertTrue(clean["Customer ID"].isna().all())
        self.assertEqual(clean.iloc[0]["StockCode"], "12345A")
        self.assertEqual(sum(a["removed"] for a in audit), len(rows) - 1)

    def test_product_selection_is_training_only(self):
        weeks = pd.date_range("2009-12-07", periods=104, freq="W-MON")
        rows = []
        for i, week in enumerate(weeks):
            for code, qty in [("12345", 20), ("23456", 10 if i < 52 else 100000)]:
                rows.append(
                    {
                        "StockCode": code,
                        "Quantity": qty,
                        "week_start": week,
                        "Price": 2,
                        "Description": code,
                    }
                )
        panel, products = derive_panel(pd.DataFrame(rows), count=1)
        self.assertEqual(products[0]["stock_code"], "12345")
        self.assertEqual(len(panel), 104)

    def test_future_observation_cannot_change_prior_replay_orders(self):
        values = np.array([100 + (i % 9) * 5 for i in range(76)], dtype=float)
        dates = [
            str(d.date()) for d in pd.date_range("2009-12-07", periods=76, freq="W-MON")
        ]
        first = replay_product(values, dates, 2)
        values[-1] = 1000
        second = replay_product(values, dates, 2)
        self.assertEqual(first["weekly_records"][:-4], second["weekly_records"][:-4])
        self.assertTrue(
            all(
                r["training_last_week"] < r["week_start"]
                for r in first["weekly_records"]
            )
        )

    def test_real_run_provenance_and_observed_moments_are_fixed(self):
        first = retail_run(n=256, replicates=4)
        second = retail_run(
            overrides={"demand_mean": 99999, "demand_cv": 0.01}, n=256, replicates=4
        )
        self.assertEqual(first["selected"], second["selected"])
        self.assertEqual(first["config"]["demand_model"], "empirical_weekly_sales")
        self.assertEqual(first["config"]["data_context"]["currency"], "GBP")
        self.assertEqual(first["config"]["scenario"]["disruption_probability"], 0)
        with self.assertRaises(ValueError):
            product_data("../unknown")

    def test_legacy_and_real_history_keep_currency(self):
        result = retail_run(n=256, replicates=4)
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "runs.db"
            save(result, path)
            legacy = copy.deepcopy(result)
            legacy["config"].pop("data_context")
            save(legacy, path)
            self.assertEqual([r["currency"] for r in recent(path)], ["INR", "GBP"])

    def test_packaged_replay_matches_source_and_timing(self):
        root = Path(__file__).resolve().parents[1]
        report = json.loads((root / "examples/retail-backtest.json").read_text())
        self.assertEqual(report["derived_sha256"], catalog()["derived_sha256"])
        for p in report["products"]:
            self.assertEqual(len(p["weekly_records"]), 156)
            self.assertTrue(
                all(
                    r["training_last_week"] < r["week_start"]
                    for r in p["weekly_records"]
                )
            )
