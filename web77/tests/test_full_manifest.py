import importlib.util,tempfile,unittest
from pathlib import Path
p=Path(__file__).resolve().parents[1]/"full_manifest_and_elf_audit.py"
s=importlib.util.spec_from_file_location("audit77",p)
a=importlib.util.module_from_spec(s);s.loader.exec_module(a)
class FullManifestTests(unittest.TestCase):
    def test_missing_tracked_library_detected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            f=root/"lib/apk/db/installed"
            f.parent.mkdir(parents=True)
            f.write_text("P:llvm20-libs\nV:20-r0\nF:usr/lib\nR:libLLVM.so.20\n")
            o=a.audit(root)
            self.assertEqual(o["apk_recorded_paths_missing_from_actual_root"],1)
            self.assertEqual(o["packages_with_missing_tracked_files"],1)
            self.assertIn("libLLVM.so.20",o["missing_registered_library_examples"][0]["path"])
    def test_existing_file_not_misreported(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);db=root/"lib/apk/db/installed";db.parent.mkdir(parents=True)
            db.write_text("P:stock\nV:1\nF:usr/share\nR:ok\n")
            file=root/"usr/share/ok";file.parent.mkdir(parents=True)
            file.write_text("present")
            self.assertEqual(a.audit(root)["apk_recorded_paths_missing_from_actual_root"],0)
    def test_block_manifest_traversal(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);db=root/"lib/apk/db/installed";db.parent.mkdir(parents=True)
            db.write_text("P:bad\nF:usr/lib\nR:../../etc/passwd\n")
            with self.assertRaises(ValueError):a.inventory(root)
if __name__=="__main__":unittest.main()
