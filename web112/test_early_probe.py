import threading
import unittest
import urllib.error
import urllib.request

from PIL import Image

import early_fixture
import early_probe


class EarlyProbeTests(unittest.TestCase):
    def test_page_detector_requires_every_expected_pixel_and_full_frame(self):
        image = Image.new('RGB', (1280, 800), (137, 31, 89))
        self.assertTrue(early_probe.page_color_visible(image, (137, 31, 89)))
        self.assertFalse(early_probe.page_color_visible(image, (17, 169, 83)))
        image.putpixel(early_probe.SAMPLE_POINTS[0], (0, 0, 0))
        self.assertFalse(early_probe.page_color_visible(image, (137, 31, 89)))
        self.assertFalse(early_probe.page_color_visible(Image.new('RGB', (800, 600)), (0, 0, 0)))

    def test_harness_injection_is_unique_and_preserves_ram_gate(self):
        marker = '            if result[\'first_home_seen_seconds\'] is not None:\n                if args.wait_ram_ready:\n'
        result = early_probe.patch_harness('before\n' + marker + 'after\n')
        self.assertIn('run_early_probe', result)
        self.assertIn('early_js_response_seconds', result)
        self.assertIn('if args.wait_ram_ready:', result)
        with self.assertRaises(ValueError):
            early_probe.patch_harness('no matching hook')
        with self.assertRaises(ValueError):
            early_probe.patch_harness(marker + marker)
        with self.assertRaises(ValueError):
            early_probe.patch_harness(result)

    def test_fixture_serves_interactive_page_and_rejects_other_paths(self):
        server = early_fixture.make_server('127.0.0.1', 0)
        self.assertIsNotNone(server)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            url = 'http://127.0.0.1:' + str(server.server_port)
            with urllib.request.urlopen(url + '/e', timeout=3) as response:
                data = response.read().decode()
                self.assertEqual(response.status, 200)
                self.assertEqual(response.headers['Cache-Control'], 'no-store')
            self.assertIn('autofocus', data)
            self.assertIn('EARLY_JS_RESPONSE', data)
            self.assertIn('rgb(17, 169, 83)', data)
            with self.assertRaises(urllib.error.HTTPError):
                urllib.request.urlopen(url + '/missing', timeout=3)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=3)


if __name__ == '__main__':
    unittest.main()
