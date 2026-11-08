import unittest
import os
import subprocess
import tempfile
from pathlib import Path
import boot_experiments as p

class BootPatchTests(unittest.TestCase):
    def test_prefetch_starts_in_real_root_and_records_outcome(self):
        source='before\n\tFstab\n\tNetbase\nafter\n'
        for mode in ('xul', 'omni', 'browser'):
            result=p.patch_main(source,mode)
            self.assertIn('P50_V113_PREFETCH',result)
            self.assertIn('[ -z "${TORAM:-}" ]',result)
            self.assertIn('p50-v113-prefetch.service',result)
            self.assertIn('Before=sysinit.target',result)
            self.assertIn('P50_V113_PREFETCH_BEGIN',result)
            self.assertIn('P50_V113_PREFETCH_END',result)
            self.assertLess(result.index('P50_V113_PREFETCH'),result.index('\n\tFstab\n'))
            self.assertEqual('libxul.so' in result,mode in ('xul','browser'))
            self.assertEqual('browser/omni.ja' in result,mode in ('omni','browser'))
            self.assertNotIn('rm -',result)

    def test_prefetch_installation_is_scoped_to_fast_boot(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            (root/'usr/local/sbin').mkdir(parents=True)
            (root/'etc/systemd/system').mkdir(parents=True)
            hook=p.patch_main(p.MAIN_MARKER,'browser').replace('[ -b /dev/mapper/p50-staged-root ]','[ -d "$rootmnt" ]')
            setup='panic() { echo "$*" >&2; exit 55; }; Fstab() { :; }; Netbase() { :; }\n'
            env={**os.environ,'rootmnt':directory,'TORAM':'1'}
            result=subprocess.run(['sh','-c',setup+hook],env=env,text=True,capture_output=True)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertFalse((root/'usr/local/sbin/p50-v113-prefetch').exists())
            env['TORAM']=''
            result=subprocess.run(['sh','-c',setup+hook],env=env,text=True,capture_output=True)
            self.assertEqual(result.returncode,0,result.stderr)
            script=root/'usr/local/sbin/p50-v113-prefetch'
            unit=root/'etc/systemd/system/p50-v113-prefetch.service'
            link=root/'etc/systemd/system/sysinit.target.wants/p50-v113-prefetch.service'
            self.assertTrue(script.is_file() and unit.is_file() and link.is_symlink())
            self.assertEqual(os.readlink(link),'../p50-v113-prefetch.service')
            self.assertEqual(subprocess.run(['sh','-n',str(script)]).returncode,0)
            self.assertIn('Before=sysinit.target',unit.read_text())

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
