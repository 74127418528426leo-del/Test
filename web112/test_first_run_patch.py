import unittest

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

    def test_rejects_missing_duplicate_and_previously_patched_hooks(self):
        for src in ['absent', '\n\tFstab\n\tNetbase\n' * 2,
                    'P50_V112_FIRST_RUN_POLICY\n\tFstab\n\tNetbase\n']:
            with self.assertRaises(ValueError):
                first_run_patch.patch_main(src)


if __name__ == '__main__':
    unittest.main()
