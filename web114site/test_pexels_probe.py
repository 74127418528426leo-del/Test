import ast
import unittest
from pexels_probe import MARKER, patch


class PexelsProbeTests(unittest.TestCase):
    def test_adds_read_only_video_console_after_site_capture(self):
        source='def test(monitor, out, result):\n    if True:\n'+MARKER
        result=patch(source)
        ast.parse(result)
        self.assertLess(result.index('requested_site.png'),result.index('video_console(monitor, out, result)'))
        self.assertIn("result['video_console_commands'] = []",result)

    def test_rejects_missing_multiple_or_repeated_hooks(self):
        with self.assertRaises(ValueError):patch('different')
        with self.assertRaises(ValueError):patch(MARKER+MARKER)
        with self.assertRaises(ValueError):patch(patch(MARKER))


if __name__=='__main__':unittest.main()
