import importlib
import unittest
from pathlib import Path


class MediaProbeTests(unittest.TestCase):
    def test_media_probe_encodes_video_capability_and_progress_queries(self):
        script = Path(__file__).with_name('media_test.py')
        self.assertTrue(script.exists(), 'media probe is missing')
        module = importlib.import_module('media_test')
        self.assertEqual(module.TARGETS['fixture'], 'http://10.0.2.2:8765/fixture.mp4')
        self.assertEqual(module.TARGETS['pexels'], 'https://www.pexels.com/video/riverside-27251986/')
        expressions = dict(module.MEDIA_EXPRESSIONS)
        self.assertIn('canPlayType', expressions['h264_capability'])
        self.assertIn('.play()', expressions['play'])
        self.assertIn('videoHeight', expressions['height'])
        self.assertEqual(expressions['time_first'], expressions['time_second'])
        for expression in expressions.values():
            for character in expression:
                self.assertTrue(module.char_keys(character), character)


if __name__ == '__main__':
    unittest.main()
