import tempfile
import unittest
from pathlib import Path
from defer_payload import defer, GROUPS, HWDB

class DeferralTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();root=Path(self.tmp.name);self.main=root/'main';self.late=root/'late';self.main.mkdir();self.late.mkdir()
        for base in (self.main,self.late):
            for rel,data in ((HWDB,b'hwdb'),('usr/lib/firmware/netronome/nic/fw.bin',b'first'),('usr/lib/firmware/qed/fw.bin',b'second')):
                p=base/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
            (base/'usr/lib/firmware/qed/link.bin').symlink_to('fw.bin')
    def tearDown(self):self.tmp.cleanup()
    def call(self,mode):return defer(self.main,self.late,mode,min_firmware=2,require_all_groups=False)
    def test_firmware_only_keeps_hwdb_and_verified_late_files(self):
        report=self.call('netfw')
        self.assertEqual(report['firmware_files'],2);self.assertEqual(report['hwdb_files'],0)
        self.assertTrue((self.main/HWDB).exists());self.assertTrue((self.late/HWDB).exists())
        self.assertFalse((self.main/'usr/lib/firmware/netronome/nic/fw.bin').exists())
        self.assertTrue((self.late/'usr/lib/firmware/netronome/nic/fw.bin').exists())
        self.assertTrue((self.main/'usr/lib/firmware/qed/link.bin').is_symlink())
    def test_hwdb_only_preserves_firmware(self):
        report=self.call('hwdb');self.assertEqual(report['hwdb_files'],1)
        self.assertFalse((self.main/HWDB).exists());self.assertTrue((self.late/HWDB).exists())
        self.assertTrue((self.main/'usr/lib/firmware/netronome/nic/fw.bin').exists())
    def test_combined_preserves_every_late_file(self):
        report=self.call('combined');self.assertEqual((report['firmware_files'],report['hwdb_files']),(2,1));self.assertEqual(len(report['files']),3)
        for item in report['files']:self.assertTrue((self.late/item['path']).is_file())
    def test_mismatch_aborts_before_removing_any_file(self):
        (self.late/HWDB).write_bytes(b'different')
        with self.assertRaises(ValueError):self.call('combined')
        self.assertTrue((self.main/HWDB).exists());self.assertTrue((self.main/'usr/lib/firmware/netronome/nic/fw.bin').exists())
    def test_rejects_late_copy_symlink_outside_root(self):
        path=self.late/HWDB;path.unlink();path.symlink_to('/etc/passwd')
        with self.assertRaises(ValueError):self.call('combined')
        self.assertTrue((self.main/HWDB).exists())
    def test_rejects_unknown_mode_and_overlapping_roots(self):
        with self.assertRaises(ValueError):self.call('wrong')
        with self.assertRaises(ValueError):defer(self.main,self.main,'hwdb')

if __name__=='__main__':unittest.main()
