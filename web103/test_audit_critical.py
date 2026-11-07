import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class CriticalImageAuditTests(unittest.TestCase):
    def test_firmware_symlink_change_is_detected(self):
        script = Path(__file__).with_name('audit_critical.py')
        with tempfile.TemporaryDirectory() as tmp:
            left, right = Path(tmp) / 'left', Path(tmp) / 'right'
            for folder in ('usr/lib/firmware/wifi', 'usr/lib/firefox-esr', 'etc/ssl', 'proc', 'dev', 'sys'):
                (left / folder).mkdir(parents=True)
            (left / 'usr/lib/firmware/wifi/a.bin').write_bytes(b'firmware')
            (left / 'usr/lib/firmware/wifi/board.bin').symlink_to('a.bin')
            shutil.copytree(left, right, symlinks=True)
            def compare():
                return subprocess.run([sys.executable, str(script), str(left), str(right)], capture_output=True, text=True)
            equal = compare()
            self.assertEqual(equal.returncode, 0, equal.stderr)
            (right / 'usr/lib/firmware/wifi/board.bin').unlink()
            (right / 'usr/lib/firmware/wifi/board.bin').symlink_to('different.bin')
            self.assertNotEqual(compare().returncode, 0)
            (right / 'usr/lib/firmware/wifi/board.bin').unlink()
            (right / 'usr/lib/firmware/wifi/board.bin').symlink_to('a.bin')
            (right / 'proc/unexpected-host-data').write_text('unexpected')
            self.assertNotEqual(compare().returncode, 0)


if __name__ == '__main__':
    unittest.main()
