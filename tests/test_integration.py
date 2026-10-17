import csv
import json
from pathlib import Path
import tempfile
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from stocklab.calibration import calibrate
from stocklab.experiment import run
from stocklab.ledger import recent, save


class IntegrationTests(unittest.TestCase):
    def test_ledger_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "runs.db"
            result = run(n=256, replicates=4)
            first = save(result, path)
            second = save(result, path)
            self.assertNotEqual(first, second)
            self.assertEqual(len(recent(path)), 2)
            self.assertEqual(recent(path)[0]["config_id"], result["config_id"])

    def test_csv_calibration(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "demand.csv"
            with path.open("w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["date", "demand"])
                for day in range(1, 31):
                    writer.writerow([f"2025-01-{day:02}", 100])
            result = calibrate(path)
            self.assertAlmostEqual(result["demand_mean"], 100)
            self.assertAlmostEqual(result["demand_cv"], 0)
            self.assertEqual(result["observations"], 30)

    def test_bad_csv_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.csv"
            for content in [
                "day,units\n2025-01-01,10",
                "date,demand\n2025-01-01,0",
                "date,demand\n2025-01-01,nan",
            ]:
                path.write_text(content)
                with self.assertRaises(ValueError):
                    calibrate(path)
