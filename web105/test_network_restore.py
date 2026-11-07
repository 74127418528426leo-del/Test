from pathlib import Path
import tempfile
import threading
import time
import unittest

from boot_bench import request_network_restore


class NetworkRestoreHandshakeTests(unittest.TestCase):
    def test_waits_for_a_separate_restoration_acknowledgement(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            def acknowledge():
                while not (out / 'network_restore_requested').exists():
                    time.sleep(0.01)
                (out / 'network_restored').touch()
            worker = threading.Thread(target=acknowledge)
            worker.start()
            try:
                self.assertTrue(request_network_restore(out, timeout=2, interval=.01))
            finally:
                worker.join(timeout=2)

    def test_missing_acknowledgement_is_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            self.assertFalse(request_network_restore(out, timeout=.05, interval=.01))
            self.assertTrue((out / 'network_restore_requested').exists())


if __name__ == '__main__':
    unittest.main()
