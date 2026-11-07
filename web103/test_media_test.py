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
        self.assertIn('currentTime=0', expressions['reset'])
        self.assertIn('.play()', expressions['play'])
        self.assertIn('.paused', expressions['paused'])
        self.assertIn('videoHeight', expressions['height'])
        self.assertEqual(expressions['time_first'], expressions['time_second'])
        for expression in expressions.values():
            for character in expression:
                self.assertTrue(module.char_keys(character), character)

    def test_incomplete_guest_run_is_not_a_successful_capture(self):
        module = importlib.import_module('media_test')
        valid = {'guest_nonroot_firefox_started': True, 'guest_ca_verified_https_probe': True,
                 'boot_cd_ejected': True, 'guest_heartbeat_continued_after_eject': True,
                 'qemu_running_at_end': True, 'errors': [],
                 'console_queries': [{'name': name} for name, _ in module.MEDIA_EXPRESSIONS],
                 'screenshots': [{'filename': 'probe_' + name + '.ppm'} for name, _ in module.MEDIA_EXPRESSIONS]
                                + [{'filename': 'frame_470.ppm'}]}
        self.assertTrue(module.capture_complete(valid))
        self.assertFalse(module.capture_complete(dict(valid, qemu_running_at_end=False)))
        self.assertFalse(module.capture_complete(dict(valid, errors=['QEMU exited'])))
        self.assertFalse(module.capture_complete(dict(valid, console_queries=[])))
        self.assertFalse(module.capture_complete(dict(valid, screenshots=[])))


if __name__ == '__main__':
    unittest.main()
