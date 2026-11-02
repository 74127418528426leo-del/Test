"""Disposable-root safety and positive accounting tests, no VM claims."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
spec=importlib.util.spec_from_file_location("qemu_trim",Path(__file__).resolve().parents[1]/"trim_qemu_only_firmware.py")
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)

class QemuTrimTests(unittest.TestCase):
    def fixture(self,base):
        root=Path(base)/"output/rootfs"
        (root/"etc/apk").mkdir(parents=True)
        (root/"etc/apk/repositories").write_text("example.invalid\n")
        (root/"usr/share/puppy50web").mkdir(parents=True)
        (root/"usr/share/puppy50web/index.html").write_text("test")
        (root/"usr/lib/firmware/i915").mkdir(parents=True)
        (root/"usr/lib/firmware/i915/mock.bin").write_bytes(b"q"*128)
        (root/"usr/lib/firmware/wifi.bin").write_bytes(b"w"*64)
        (root/"usr/bin").mkdir(parents=True)
        (root/"usr/bin/firefox-esr").write_bytes(b"browser")
        return root

    def test_firmware_removed_but_browser_unmodified(self):
        with tempfile.TemporaryDirectory() as t:
            r=self.fixture(t)
            result=module.trim(r)
            self.assertEqual(result["uncompressed_regular_file_bytes_removed"],192)
            self.assertEqual(result["removed_file_count"],2)
            self.assertFalse((r/"usr/lib/firmware/wifi.bin").exists())
            self.assertEqual((r/"usr/bin/firefox-esr").read_bytes(),b"browser")
            self.assertFalse(result["valid_real_hardware_variant"])

    def test_non_staging_root_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            r=self.fixture(t)
            with self.assertRaises(ValueError):
                module.trim(Path(t))
            with self.assertRaises(ValueError):
                module.trim(Path(t)/"output")

    def test_symlink_outside_root_refused_without_deletion(self):
        with tempfile.TemporaryDirectory() as t:
            r=self.fixture(t)
            outside=Path(t)/"outside"
            outside.mkdir()
            p=outside/"keep"
            p.write_bytes(b"data")
            (r/"usr/lib/firmware/wifi.bin").unlink()
            (r/"usr/lib/firmware/wifi.bin").symlink_to(p)
            module.trim(r)
            self.assertEqual(p.read_bytes(),b"data")

if __name__=="__main__": unittest.main()
