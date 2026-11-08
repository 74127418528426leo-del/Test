import unittest

import ldconfig_patch


class BootCachePatchTests(unittest.TestCase):
    def test_unique_hook_is_added_before_fstab_with_a_ram_mode_guard(self):
        source = 'before\n\tFstab\n\tNetbase\nafter\n'
        patched = ldconfig_patch.patch_main(source)
        self.assertIn('P50_V110_PREBUILT_LD_CACHE', patched)
        self.assertIn('${TORAM:-}', patched)
        self.assertIn('${rootmnt}/etc/ld.so.cache', patched)
        self.assertIn('${rootmnt}/etc/systemd/system/ldconfig.service', patched)
        self.assertLess(patched.index('P50_V110_PREBUILT_LD_CACHE'), patched.index('\n\tFstab\n'))

    def test_missing_duplicate_or_already_patched_hook_is_rejected(self):
        for source in ['no hooks', '\n\tFstab\n\tNetbase\n' * 2,
                       'P50_V110_PREBUILT_LD_CACHE\n\tFstab\n\tNetbase\n']:
            with self.assertRaises(ValueError):
                ldconfig_patch.patch_main(source)

    def test_diagnostic_is_added_once_without_removing_existing_migration_delay(self):
        source = 'before\n"$B" sleep 8\nemit P50_STAGE_START\nafter\n'
        patched = ldconfig_patch.patch_migration(source)
        self.assertIn('P50_V110_CACHE_IDENTICAL', patched)
        self.assertIn('P50_V110_CACHE_DIFFERENT', patched)
        self.assertIn('"$B" sleep 8\nemit P50_STAGE_START', patched)
        with self.assertRaises(ValueError):
            ldconfig_patch.patch_migration(patched)


if __name__ == '__main__':
    unittest.main()
