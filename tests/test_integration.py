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
from stocklab.server import create_server


class IntegrationTests(unittest.TestCase):
    def test_ledger_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'runs.db'
            result = run(n=256, replicates=4)
            first = save(result, path)
            second = save(result, path)
            self.assertNotEqual(first, second)
            self.assertEqual(len(recent(path)), 2)
            self.assertEqual(recent(path)[0]['config_id'], result['config_id'])

    def test_csv_calibration(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'demand.csv'
            with path.open('w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['date', 'demand'])
                for day in range(1, 31):
                    writer.writerow([f'2025-01-{day:02}', 100])
            result = calibrate(path)
            self.assertAlmostEqual(result['demand_mean'], 100)
            self.assertAlmostEqual(result['demand_cv'], 0)
            self.assertEqual(result['observations'], 30)

    def test_bad_csv_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'bad.csv'
            for content in ['day,units\n2025-01-01,10', 'date,demand\n2025-01-01,0', 'date,demand\n2025-01-01,nan']:
                path.write_text(content)
                with self.assertRaises(ValueError):
                    calibrate(path)

    def test_http_end_to_end(self):
        with tempfile.TemporaryDirectory() as tmp:
            server = create_server(port=0, ledger_path=str(Path(tmp)/'runs.db'))
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            base = f'http://127.0.0.1:{server.server_port}'
            try:
                with urlopen(base+'/api/health') as response:
                    self.assertEqual(json.load(response)['status'], 'ok')
                with urlopen(base+'/') as response:
                    self.assertIn(b'StockSense', response.read())
                request = Request(base+'/api/run', json.dumps({'n': 256, 'replicates': 4}).encode(), {'Content-Type': 'application/json'})
                with urlopen(request) as response:
                    result = json.load(response)
                self.assertEqual(result['evaluation_paths'], 1024)
                with urlopen(base+'/api/history') as response:
                    self.assertEqual(len(json.load(response)), 1)
                for path in ['/../pyproject.toml', '/stocklab/model.py', '/not-found']:
                    with self.assertRaises(HTTPError) as err:
                        urlopen(base+path)
                    self.assertEqual(err.exception.code, 404)
                for payload in [{'scenario': {'cost': -1}}, {'n': 999999}, {'seed': True}, []]:
                    with self.assertRaises(HTTPError) as err:
                        urlopen(Request(base+'/api/run', json.dumps(payload).encode(), {'Content-Type': 'application/json'}))
                    self.assertEqual(err.exception.code, 400)
                with self.assertRaises(HTTPError) as err:
                    urlopen(Request(base+'/api/run', b'{}', {'Content-Type': 'application/json', 'Origin': 'https://example.com'}))
                self.assertEqual(err.exception.code, 403)
            finally:
                server.shutdown()
                server.server_close()
                thread.join()
