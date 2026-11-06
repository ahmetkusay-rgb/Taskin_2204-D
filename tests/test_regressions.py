import asyncio
import importlib.util
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
def module(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    obj = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(obj)
    return obj

tri = module('tri', 'analysis/tri_score.py')
bridge = module('bridge', 'software/server.py')

class AnalysisTests(unittest.TestCase):
    def test_mixed_formats_and_session_boundaries(self):
        with tempfile.TemporaryDirectory() as folder:
            Path(folder, 'a.csv').write_text('timestamp,node_id,doluluk_pct\n2026-02-09 11:00:00,1,10\n2026-02-09 11:00:01,1,10\n')
            Path(folder, 'b.csv').write_text('zaman_ms,node_id,doluluk,alarm\n0,1,90,1\n2000,1,90,1\n')
            df = tri.load_all_csv(folder)
            self.assertEqual(len(df), 4)
            metrics = tri.compute_metrics(df)[1]
            self.assertEqual(metrics['E'], 2)
            self.assertEqual(metrics['F'], 0)

    def test_dropouts_do_not_create_exposure_or_crossings(self):
        df = tri.pd.DataFrame({'node_id':[1]*4, 'doluluk':[0,90,90,90], 'zaman_ms':[0,10000,12000,14000]})
        result = tri.compute_metrics(df)[1]
        self.assertEqual(result['E'], 4)
        self.assertEqual(result['F'], 0)

    def test_empty_measurements_raise_clear_error(self):
        with tempfile.TemporaryDirectory() as folder:
            Path(folder, 'a.csv').write_text('zaman_ms,node_id,doluluk\n0,1,nan\n')
            with self.assertRaisesRegex(ValueError, 'No valid measurements'):
                tri.load_all_csv(folder)

    def test_sample_ranking(self):
        scores = tri.compute_tri(tri.compute_metrics(tri.load_all_csv(ROOT/'data/samples')))
        self.assertEqual(sorted(scores, key=scores.get, reverse=True), [1,2,3])
        for node, expected in {1:91.3, 2:48.6, 3:9.4}.items():
            self.assertAlmostEqual(scores[node], expected, delta=0.15)

class BridgeTests(unittest.IsolatedAsyncioTestCase):
    def test_no_unrelated_port_fallback(self):
        with patch.object(bridge.serial.tools.list_ports, 'comports', return_value=[SimpleNamespace(device='COM1',description='Bluetooth')]):
            self.assertIsNone(bridge.find_esp_port())

    async def test_invalid_packets_and_serial_cleanup(self):
        lines = iter([b'1,nan,0\n',b'1,50,9\n',b'1,50,0\n'])
        class Serial:
            closed = False
            def readline(self):
                return next(lines, b'')
            def close(self):
                self.closed = True
        serial = Serial()
        received = []
        async def broadcast(message):
            payload = bridge.json.loads(message)
            received.append(payload)
            if payload['type'] == 'data':
                raise asyncio.CancelledError()
        with patch.object(bridge.serial, 'Serial', return_value=serial), patch.object(bridge, 'broadcast', broadcast):
            with self.assertRaises(asyncio.CancelledError):
                await asyncio.wait_for(bridge.serial_reader('test',115200), timeout=5)
        self.assertTrue(serial.closed)
        self.assertEqual([p['doluluk_pct'] for p in received if p['type']=='data'], [50])

if __name__ == '__main__':
    unittest.main()
