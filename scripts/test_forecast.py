import copy
import unittest
from forecast import month_label, run, seasonal, validate


def fixture(n=60):
    return {"series_id": "SYNTHETIC_TEST_NOT_MARKET_DATA", "source": "synthetic unit test",
            "as_of": "2026-09-08", "scope": "sample", "unit": "units",
            "observations": [{"month": month_label(2021 * 12 + i),
                              "value": 100 + i % 12 * 10} for i in range(n)]}


class ForecastTests(unittest.TestCase):
    def test_horizon_and_sums(self):
        result = run(fixture(), seasonal, "seasonal")
        self.assertEqual(len(result["months"]), 18)
        self.assertEqual(result["months"][0], "2026-01")
        self.assertEqual(result["months"][-1], "2027-06")
        self.assertEqual(result["sum_months_7_18_point"], sum(result["point"][6:]))
        self.assertEqual(result["backtest"]["model"]["mae"], 0)
        self.assertIsNone(result["population"])
        self.assertFalse(result["production_approved"])

    def test_short_history_no_backtest(self):
        self.assertIsNone(run(fixture(14), seasonal, "seasonal")["backtest"])

    def test_reject_gaps_and_duplicates(self):
        for index in (0, 11):
            data = fixture()
            data["observations"][12]["month"] = data["observations"][index]["month"]
            with self.assertRaises(ValueError):
                validate(data)

    def test_reject_invalid_values(self):
        for value in (None, -1, float("nan"), float("inf"), True, "100"):
            data = fixture()
            data["observations"][0]["value"] = value
            with self.assertRaises(ValueError):
                validate(data)

    def test_reject_partial_or_future_month(self):
        data = fixture()
        data["as_of"] = "2025-12-15"
        with self.assertRaises(ValueError):
            validate(data)

    def test_require_market_coverage(self):
        data = fixture()
        data["scope"] = "market"
        with self.assertRaises(ValueError):
            validate(data)

    def test_holdout_does_not_leak(self):
        data = fixture()
        calls = []
        def spy(values):
            calls.append(copy.copy(values))
            return seasonal(values)
        run(data, spy, "test")
        self.assertEqual(len(calls[1]), 42)
        self.assertEqual(calls[1], [r["value"] for r in data["observations"][:-18]])


if __name__ == "__main__":
    unittest.main()
