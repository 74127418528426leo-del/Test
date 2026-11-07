import importlib
import sys
import unittest
from pathlib import Path


class PostEjectEvidenceTests(unittest.TestCase):
    def test_heartbeat_must_continue_after_ejection(self):
        script = Path(__file__).with_name('post_eject.py')
        self.assertTrue(script.exists(), 'post-ejection harness is missing')
        sys.path.insert(0, str(script.parent))
        module = importlib.import_module('post_eject')
        valid = {'boot_cd_ejected': True, 'qemu_running_at_end': True,
                 'post_eject_input_sent': True, 'heartbeat_at_eject': 4,
                 'heartbeat_at_end': 6, 'screenshots': ['frame_360.ppm']}
        self.assertTrue(module.captured_guest_progress(valid))
        stalled = dict(valid, heartbeat_at_end=4)
        self.assertFalse(module.captured_guest_progress(stalled))
        self.assertFalse(module.captured_guest_progress(dict(valid, boot_cd_ejected=False)))
        self.assertFalse(module.captured_guest_progress(dict(valid, screenshots=[])))


if __name__ == '__main__':
    unittest.main()
