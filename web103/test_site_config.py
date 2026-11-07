import importlib
import subprocess
import sys
import unittest
from pathlib import Path


class WebsiteTargetTests(unittest.TestCase):
    def test_requested_pages_are_supported_and_keyboard_encodable(self):
        script = Path(__file__).with_name('site_test.py')
        run = subprocess.run([sys.executable, str(script), '--help'], text=True, capture_output=True)
        self.assertEqual(run.returncode, 0, run.stderr)
        module = importlib.import_module('site_test')
        self.assertEqual(module.SITES['pexels4k']['url'], 'https://www.pexels.com/video/riverside-27251986/')
        self.assertEqual(module.SITES['john']['url'], 'https://3dbibleonline.github.io/john/')
        for site in module.SITES.values():
            self.assertTrue(site['url'].startswith('https://'))
            for character in site['url']:
                self.assertTrue(module.char_keys(character))


if __name__ == '__main__':
    unittest.main()
