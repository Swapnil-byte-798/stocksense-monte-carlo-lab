import unittest
from dataclasses import replace

import numpy as np

from stocklab.model import Scenario, analytic_expected_profit, analytic_order, lower_tail_mean, outcomes, summarize, uniforms, worlds
from stocklab.experiment import run, interval


class ModelTests(unittest.TestCase):
    def test_hand_calculated_profit(self):
        s = Scenario()
        p, sold, unmet = outcomes(s, 100, np.array([80., 120.]), np.ones(2))
        np.testing.assert_allclose(p, [50*80 + 8*20 - 28*100, 50*100 - 28*100 - 5*20])
        np.testing.assert_array_equal(sold, [80, 100])
        np.testing.assert_array_equal(unmet, [0, 20])

    def test_prepaid_supply_contract(self):
        p = outcomes(Scenario(), 100, np.array([120.]), np.array([0.5]))[0][0]
        self.assertEqual(p, 50*50 - 28*100 - 5*70)

    def test_fractional_tail_boundary(self):
        self.assertEqual(lower_tail_mean(np.array([0, 10, 20]), .5), 10/3)
        self.assertEqual(lower_tail_mean(np.array([2, 2, 5, 8]), .5), 2)
        self.assertEqual(lower_tail_mean(np.array([2, 5]), .1), 2)

    def test_tail_validation(self):
        for values, alpha in [([], .1), ([1, float('nan')], .1), ([1], 0)]:
            with self.assertRaises(ValueError):
                lower_tail_mean(np.array(values), alpha)

    def test_invalid_scenarios(self):
        for changes in [{"price": 20}, {"cost": float('nan')}, {"risk_weight": 2}, {"order_step": 0}, {"order_min": 4.5}, {"demand_mean": True}, {"order_step": 1}, {"demand_supply_correlation": 1}]:
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                replace(Scenario(), **changes)

    def test_sobol_requires_power_of_two(self):
        with self.assertRaises(ValueError):
            uniforms(300, 'sobol', 1)

    def test_seed_reproducible(self):
        np.testing.assert_array_equal(uniforms(1024, 'mc', 9), uniforms(1024, 'mc', 9))
        np.testing.assert_array_equal(uniforms(1024, 'sobol', 9), uniforms(1024, 'sobol', 9))

    def test_lognormal_moments(self):
        demand, _ = worlds(Scenario(), uniforms(65536, 'sobol', 5))
        self.assertAlmostEqual(demand.mean(), 1000, delta=1)
        self.assertAlmostEqual(demand.std()/demand.mean(), .35, delta=.002)

    def test_positive_copula_couples_high_demand_and_disruption(self):
        d, f = worlds(replace(Scenario(), demand_supply_correlation=.8, disruption_probability=.2), uniforms(32768, 'sobol', 6))
        self.assertGreater(d[f < 1].mean(), d[f == 1].mean())
        self.assertAlmostEqual(np.mean(f < 1), .2, delta=.003)

    def test_disruption_extremes(self):
        for prob, expected in [(0, 1), (1, .65)]:
            _, f = worlds(replace(Scenario(), disruption_probability=prob), uniforms(256, 'mc', 1))
            np.testing.assert_array_equal(f, np.full(256, expected))

    def test_analytic_oracle(self):
        s = replace(Scenario(), disruption_probability=0, risk_weight=0)
        d, f = worlds(s, uniforms(65536, 'sobol', 17))
        for q in [0, 500, 1000, 1500]:
            observed = outcomes(s, q, d, f)[0].mean()
            self.assertAlmostEqual(observed, analytic_expected_profit(s, q), delta=2)
        q = analytic_order(s)
        self.assertGreater(analytic_expected_profit(s, q), analytic_expected_profit(s, q - 50))
        self.assertGreater(analytic_expected_profit(s, q), analytic_expected_profit(s, q + 50))

    def test_deterministic_optimum(self):
        s = replace(Scenario(), demand_cv=0, disruption_probability=0, risk_weight=0)
        result = run(s, n=256, replicates=4)
        self.assertEqual(result['selected']['order'], 1000)
        self.assertAlmostEqual(result['selected']['mean_profit'], 22000)
        self.assertEqual(result['paired_delta_ci95']['standard_error'], 0)

    def test_fill_rate_is_unit_weighted(self):
        summary = summarize(Scenario(), 100, np.array([10., 1000.]), np.ones(2))
        self.assertAlmostEqual(summary['fill_rate'], 110/1010)
        self.assertEqual(summary['stockout_probability'], .5)

    def test_interval_known_answer(self):
        ci = interval([1, 2, 3, 4])
        self.assertAlmostEqual(ci['estimate'], 2.5)
        self.assertAlmostEqual(ci['standard_error'], np.sqrt(5/3)/2)

    def test_run_provenance_and_selection(self):
        result = run(n=256, replicates=4)
        self.assertNotIn(result['provenance']['train_seed'], result['provenance']['evaluation_seeds'])
        self.assertEqual(result['selected']['order'], max(result['frontier'], key=lambda row: row['score'])['order'])
        self.assertEqual(sum(result['histogram']['counts']), 1024)
        repeated = run(n=256, replicates=4)
        self.assertEqual(result['selected'], repeated['selected'])
        self.assertEqual(result['config_id'], repeated['config_id'])

    def test_resource_validation(self):
        for options in [{"n": 10**8}, {"replicates": 1}, {"seed": -1}, {"n": True}, {"method": "oops"}]:
            with self.subTest(options=options), self.assertRaises(ValueError):
                run(**options)


if __name__ == '__main__':
    unittest.main()
