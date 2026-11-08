import unittest
import os
import subprocess
import tempfile
from pathlib import Path

import first_run_patch


class FirstRunPatchTests(unittest.TestCase):
    def test_adds_first_run_policy_only_to_fast_boot(self):
        src = 'before\n\tFstab\n\tNetbase\nafter\n'
        out = first_run_patch.patch_main(src)
        self.assertIn('P50_V112_FIRST_RUN_POLICY', out)
        self.assertIn('${TORAM:-}', out)
        self.assertIn('"OverrideFirstRunPage":""', out)
        self.assertIn('policies.json', out)
        self.assertLess(out.index('P50_V112_FIRST_RUN_POLICY'), out.index('\n\tFstab\n'))

    def test_debian_relative_distribution_symlink_is_supported(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root/'usr/lib/firefox-esr').mkdir(parents=True)
            (root/'usr/share/firefox-esr/distribution').mkdir(parents=True)
            (root/'usr/lib/firefox-esr/distribution').symlink_to('../../share/firefox-esr/distribution')
            hook = first_run_patch.HOOK.replace('[ -b /dev/mapper/p50-staged-root ]', '[ -d "$rootmnt" ]')
            proc = subprocess.run(['sh', '-c', 'panic() { echo "$*" >&2; exit 55; }\n'+hook],
                                  env={**os.environ, 'rootmnt': temp, 'TORAM': ''},
                                  text=True, capture_output=True)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertEqual((root/'usr/share/firefox-esr/distribution/policies.json').read_text().strip(),
                             '{"policies":{"OverrideFirstRunPage":""}}')

    def test_unexpected_distribution_symlink_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root/'usr/lib/firefox-esr').mkdir(parents=True)
            (root/'usr/share/firefox-esr/distribution').mkdir(parents=True)
            (root/'usr/lib/firefox-esr/distribution').symlink_to('/tmp/unexpected')
            hook = first_run_patch.HOOK.replace('[ -b /dev/mapper/p50-staged-root ]', '[ -d "$rootmnt" ]')
            proc = subprocess.run(['sh', '-c', 'panic() { echo "$*" >&2; exit 55; }\n'+hook],
                                  env={**os.environ, 'rootmnt': temp, 'TORAM': ''},
                                  text=True, capture_output=True)
            self.assertNotEqual(proc.returncode, 0)
            self.assertFalse((root/'usr/share/firefox-esr/distribution/policies.json').exists())

    def test_rejects_missing_duplicate_and_previously_patched_hooks(self):
        for src in ['absent', '\n\tFstab\n\tNetbase\n' * 2,
                    'P50_V112_FIRST_RUN_POLICY\n\tFstab\n\tNetbase\n']:
            with self.assertRaises(ValueError):
                first_run_patch.patch_main(src)


if __name__ == '__main__':
    unittest.main()
