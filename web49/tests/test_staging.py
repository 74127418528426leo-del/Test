"""Offline staging checks; fixtures are NOT a real OS or hardware evidence."""
from pathlib import Path
import subprocess
import tempfile
import unittest

SCRIPT=Path(__file__).resolve().parents[1]/"stage_boot_outside_sfs.sh"

class StagingTests(unittest.TestCase):
    def runstage(self,root,out):
        return subprocess.run(["sh",str(SCRIPT),str(root),str(out)],
                              capture_output=True,text=True)
    def test_moves_only_staged_boot_tree(self):
        with tempfile.TemporaryDirectory() as d:
            base=Path(d)
            root=base/"stage"; out=base/"isolated-boot-assets"
            (root/"etc/apk").mkdir(parents=True)
            (root/"lib/modules").mkdir(parents=True)
            (root/"boot").mkdir()
            (root/"boot/vmlinuz-lts").write_bytes(b"kernel-bytes")
            (root/"boot/initramfs-lts").write_bytes(b"initrd-bytes")
            (root/"usr/bin").mkdir(parents=True)
            (root/"usr/bin/firefox-esr").write_bytes(b"browser-kept")
            r=self.runstage(root,out)
            self.assertEqual(r.returncode,0,r.stdout+r.stderr)
            self.assertEqual((out/"vmlinuz-lts").read_bytes(),b"kernel-bytes")
            self.assertEqual((out/"initramfs-lts").read_bytes(),b"initrd-bytes")
            self.assertEqual(list((root/"boot").iterdir()),[])
            self.assertEqual((root/"usr/bin/firefox-esr").read_bytes(),b"browser-kept")
            self.assertNotEqual(self.runstage(root,out).returncode,0)
    def test_refuses_unrecognized_root(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)/"not_a_root";root.mkdir()
            self.assertNotEqual(self.runstage(root,Path(d)/"out").returncode,0)

if __name__=="__main__":
    unittest.main()
