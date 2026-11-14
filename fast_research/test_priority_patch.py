import tempfile
import unittest
from pathlib import Path

import priority_patch


class PriorityPatchTests(unittest.TestCase):
    def test_changes_only_actual_nonroot_firefox_nice(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / '9990-main.sh'
            before = ('P50_V149_SOFTWARE_WEBRENDER\nP50_V127_FIREFOX_DIRECT_EXEC\n'
                      '/usr/bin/nice -n -10 setpriv --reuid=user --regid=user --init-groups\n'
                      'network and ram markers unchanged\n')
            p.write_text(before)
            priority_patch.patch_file(p)
            self.assertEqual(p.read_text(), before.replace('/usr/bin/nice -n -10', '/usr/bin/nice -n -19'))

    def test_rejects_missing_or_duplicate_launcher(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / '9990-main.sh'
            p.write_text('P50_V149_SOFTWARE_WEBRENDER\nP50_V127_FIREFOX_DIRECT_EXEC\n')
            with self.assertRaises(ValueError):
                priority_patch.patch_file(p)
            p.write_text(p.read_text() + 2 * '/usr/bin/nice -n -10 setpriv --reuid=user --regid=user --init-groups\n')
            with self.assertRaises(ValueError):
                priority_patch.patch_file(p)


if __name__ == '__main__':
    unittest.main()
