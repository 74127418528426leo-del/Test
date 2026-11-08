import json
from pathlib import Path
import tempfile
import unittest
import defer_network as d

class DeferredNetworkTests(unittest.TestCase):
    def create_fixture(self,root):
        early=root/'early';main=root/'main';late=root/'late'
        for p in (early,main,late):p.mkdir()
        driver=Path(d.DRIVERS)/'ethernet/intel/e1000/e1000.ko.xz'
        for base in (early,late):
            p=base/driver;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b'network-driver')
        firmware=Path(d.FIRMWARE_BASE)/'netronome/nic/fw.bin'
        for base in (main,late):
            p=base/firmware;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b'network-firmware')
        keep=early/'usr/lib/modules/keep.ko.xz';keep.parent.mkdir(parents=True,exist_ok=True);keep.write_bytes(b'boot-storage')
        return early,main,late,driver,firmware,keep

    def test_removes_only_verified_early_network_copies(self):
        with tempfile.TemporaryDirectory() as t:
            e,m,l,drv,fw,keep=self.create_fixture(Path(t))
            link=(m/fw).parent/'fw-link.bin';link.symlink_to('fw.bin')
            report=d.defer(e,m,l,'drivers-firmware',1,1)
            self.assertFalse((e/drv).exists());self.assertFalse((m/fw).exists())
            self.assertTrue((l/drv).exists() and (l/fw).exists() and keep.exists())
            self.assertTrue(link.is_symlink())
            self.assertEqual((report['drivers'],report['firmware_files']),(1,1))

    def test_mismatched_late_copy_aborts_without_any_removal(self):
        with tempfile.TemporaryDirectory() as t:
            e,m,l,drv,fw,keep=self.create_fixture(Path(t));(l/fw).write_bytes(b'different')
            with self.assertRaises(ValueError):d.defer(e,m,l,'drivers-firmware',1,1)
            self.assertTrue((e/drv).exists() and (m/fw).exists() and keep.exists())

    def test_driver_only_leaves_firmware_and_rejects_overlapping_roots(self):
        with tempfile.TemporaryDirectory() as t:
            e,m,l,drv,fw,keep=self.create_fixture(Path(t))
            with self.assertRaises(ValueError):d.defer(e,e,l,'drivers',1,0)
            d.defer(e,m,l,'drivers',1,0)
            self.assertFalse((e/drv).exists());self.assertTrue((m/fw).exists())

if __name__=='__main__':unittest.main()
