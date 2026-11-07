import importlib
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path


class FixtureServerTests(unittest.TestCase):
    def test_video_ranges_and_nonce_page(self):
        self.assertTrue(Path(__file__).with_name('fixture_server.py').exists())
        module = importlib.import_module('fixture_server')
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'fixture.mp4'
            path.write_bytes(b'0123456789')
            server = module.make_server('127.0.0.1', 0, path, 'P50-TEST-2048')
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                root = f'http://127.0.0.1:{server.server_port}'
                request = urllib.request.Request(root + '/fixture.mp4', headers={'Range': 'bytes=2-5'})
                with urllib.request.urlopen(request) as response:
                    self.assertEqual(response.status, 206)
                    self.assertEqual(response.read(), b'2345')
                    self.assertEqual(response.headers['Content-Range'], 'bytes 2-5/10')
                with urllib.request.urlopen(root + '/after.html?nonce=P50-TEST-2048') as response:
                    self.assertIn(b'AFTER EJECT P50-TEST-2048', response.read())
                with self.assertRaises(urllib.error.HTTPError):
                    urllib.request.urlopen(root + '/after.html?nonce=WRONG')
            finally:
                server.shutdown()
                server.server_close()
                thread.join()


if __name__ == '__main__':
    unittest.main()
