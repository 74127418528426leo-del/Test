import tempfile
import unittest
from pathlib import Path

import hardware_guard


class HardwareGuardTests(unittest.TestCase):
    def test_guard_restricts_only_early_display_hook(self):
        before = ('prefix\n\t# P50_V123_BEFORE_PID1: isolated QEMU-only research, unsafe for physical release.\n'
                  '\tif [ -z "${TORAM:-}" ] && [ -b /dev/mapper/p50-staged-root ]; then\n'
                  '\t    echo launch-early\n\tfi\n\t# P50_V124_POSTROOT_X11_FORENSIC\n')
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'9990-main.sh';p.write_text(before)
            hardware_guard.patch_file(p)
            s=p.read_text()
            self.assertIn('P50_FAST_GPU_GUARD',s)
            self.assertIn('0x1234:0x1111',s)
            self.assertIn('&& [ "$p50_fast_gpu" = 1 ]',s)
            self.assertEqual(s.count('echo launch-early'),1)
            self.assertIn('P50_V124_POSTROOT_X11_FORENSIC',s)
            with self.assertRaises(ValueError):hardware_guard.patch_file(p)

    def test_unexpected_source_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'9990-main.sh';p.write_text('something else\n')
            with self.assertRaises(ValueError):hardware_guard.patch_file(p)


if __name__ == '__main__':unittest.main()
