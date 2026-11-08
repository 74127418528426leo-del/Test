import unittest
import boot_experiments as p

class BootPatchTests(unittest.TestCase):
    def test_prefetch_variants_only_read_expected_existing_browser_files(self):
        source='before\n\tFstab\n\tNetbase\nafter\n'
        for mode in ('xul', 'browser'):
            result=p.patch_main(source,mode)
            self.assertIn('P50_V113_PREFETCH',result)
            self.assertIn('${rootmnt}/usr/lib/firefox-esr/libxul.so',result)
            self.assertIn('[ -z "${TORAM:-}" ]',result)
            self.assertLess(result.index('P50_V113_PREFETCH'),result.index('\n\tFstab\n'))
            self.assertEqual('browser/omni.ja' in result, mode=='browser')
            self.assertNotIn('rm -',result)

    def test_no_settle_keeps_device_node_check_and_rejects_ambiguous_source(self):
        source=p.DEVICE_MARKER+'\n            p50_actual="$(stat -c x /dev/mapper/p50-staged-root)"\n'
        output=p.patch_helper(source,'no-settle')
        self.assertNotIn('udevadm settle',output)
        self.assertIn('p50_actual=',output)
        for bad in ('absent', source+source):
            with self.assertRaises(ValueError):p.patch_helper(bad,'no-settle')

    def test_profile_preserves_wait_and_records_guest_timestamps(self):
        output=p.patch_helper(p.DEVICE_MARKER,'profile')
        self.assertIn('udevadm settle',output)
        self.assertIn('P50_V113_SETTLE_BEGIN',output)
        self.assertIn('P50_V113_SETTLE_END',output)

    def test_rejects_missing_duplicate_and_previously_patched_main_hooks(self):
        marker='\n\tFstab\n\tNetbase\n'
        for source in ('missing',marker+marker,'P50_V113_PREFETCH'+marker):
            with self.assertRaises(ValueError):p.patch_main(source,'xul')

if __name__=='__main__':unittest.main()
