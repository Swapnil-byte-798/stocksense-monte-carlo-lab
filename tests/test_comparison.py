import copy
import json
from pathlib import Path
import unittest

import numpy as np

from stocklab.comparison import block_indices, compare_policies, paired_panel, summarize

ROOT = Path(__file__).resolve().parents[1]


class PolicyComparisonTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads((ROOT / "examples/retail-backtest.json").read_text())

    def test_real_pairs_and_point_estimate_reconcile(self):
        weeks, products, panel = paired_panel(self.report)
        self.assertEqual(panel.shape, (39, 5, 3))
        self.assertEqual(len(weeks), 39)
        self.assertEqual(len(products), 5)
        rows = self.report["products"][0]["weekly_records"]
        expected = np.mean(
            [r["profit_proxy_gbp"] for r in rows if r["policy"] == "empirical_risk"]
        ) - np.mean(
            [r["profit_proxy_gbp"] for r in rows if r["policy"] == "trailing_mean"]
        )
        self.assertAlmostEqual(panel[:, 0, 0].mean(), expected)

    def test_zero_paired_difference_has_zero_uncertainty(self):
        values = np.column_stack([np.zeros(20), np.zeros(20), np.ones(20)])
        result = summarize(values, block_indices(20, 4, 100, 5))
        self.assertEqual(result["profit_proxy_ci95_gbp"], [0, 0])
        self.assertEqual(result["fill_delta_ci95"], [0, 0])

    def test_blocks_are_contiguous_and_reproducible(self):
        a = block_indices(39, 4, 100, 5)
        np.testing.assert_array_equal(a, block_indices(39, 4, 100, 5))
        for offset in [0, 4, 8, 12, 16, 20, 24, 28, 32]:
            np.testing.assert_array_equal(
                np.diff(a[:, offset : offset + 4], axis=1) % 39,
                np.ones((100, 3), dtype=int),
            )

    def test_reject_missing_pair_duplicate_and_different_sales(self):
        for change in ["missing", "duplicate", "sales", "future"]:
            report = copy.deepcopy(self.report)
            rows = report["products"][0]["weekly_records"]
            if change == "missing":
                rows.pop(0)
            elif change == "duplicate":
                rows.append(copy.deepcopy(rows[0]))
            elif change == "sales":
                rows[0]["observed_sales"] += 1
            else:
                rows[0]["training_last_week"] = rows[0]["week_start"]
            with self.subTest(change=change), self.assertRaises(ValueError):
                paired_panel(report)

    def test_reject_product_calendar_mismatch(self):
        report = copy.deepcopy(self.report)
        report["products"][0]["weekly_records"] = report["products"][0][
            "weekly_records"
        ][4:]
        with self.assertRaises(ValueError):
            paired_panel(report)

    def test_gate_catches_service_tradeoff_on_real_data(self):
        result = compare_policies(self.report, replicates=1000)
        self.assertFalse(result["illustrative_gate"]["passes_both"])
        self.assertEqual(len(result["results"]), 18)
        primary = next(r for r in result["results"] if r["primary"])
        self.assertLess(primary["fulfilled_observed_unit_rate_delta"], 0)

    def test_invalid_bootstrap_configuration(self):
        for args in [(1, 1, 100, 5), (20, 0, 100, 5), (20, 21, 100, 5), (20, 4, 2, 5)]:
            with self.subTest(args=args), self.assertRaises(ValueError):
                block_indices(*args)
