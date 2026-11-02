"""Evidence limits and accounting checks for the v48 footprint tool."""
import importlib.util
import pathlib
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("audit_image", ROOT / "web48/audit_image.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class FootprintAuditTests(unittest.TestCase):
    def test_no_follow_symlink_and_real_mib_units(self):
        with tempfile.TemporaryDirectory() as t:
            root=pathlib.Path(t)/"staged"; root.mkdir()
            (root/"boot").mkdir()
            (root/"boot/vmlinuz-lts").write_bytes(b"k"*80)
            (root/"usr/lib/firefox").mkdir(parents=True)
            (root/"usr/lib/firefox/xul.so").write_bytes(b"f"*100)
            (root/"usr/lib/firefox/link").symlink_to("/etc/passwd")
            r = mod.audit(root, 100*(2**20), 384, top=3)
            self.assertEqual(r["measured_sfs_mib"],100)
            self.assertEqual(r["staged_apparent_file_bytes"],180)
            self.assertEqual(r["staged_symlink_count"],1)
            self.assertEqual(r["nonadditive_uncompressed_directory_categories"]["firefox-engine"],100)
            self.assertFalse(r["is_complete_browser_proven"])
            self.assertEqual(r["ram_budget_estimate_only"]["classification"],
                             "PASS_ESTIMATE_ONLY_NOT_REAL_VM_PROOF")

    def test_oversized_image_cannot_pass_gate(self):
        with tempfile.TemporaryDirectory() as t:
            p=pathlib.Path(t)
            r=mod.audit(p,385*(2**20),384)
            self.assertEqual(r["ram_budget_estimate_only"]["classification"],
                             "FAIL_HARD_SFS_ALONE_GE_GUEST_RAM")

if __name__ == "__main__":
    unittest.main()
