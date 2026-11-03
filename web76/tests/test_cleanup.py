import importlib.util,tempfile,unittest
from pathlib import Path
p=Path(__file__).resolve().parents[1]/"clean_stock_control.py"
spec=importlib.util.spec_from_file_location("clean76",p)
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)

class SafeStockMesaCleanup(unittest.TestCase):
    def fixture(self,base):
        root=Path(base)/"output/rootfs"
        (root/"lib/apk/db").mkdir(parents=True)
        (root/"usr/lib").mkdir(parents=True)
        (root/"lib/apk/db/installed").write_text("P:mesa\nV:26.1.6-r0\nF:usr/lib\nR:libgbm.so.1.0.0\n")
        (root/"usr/lib/libgbm.so.1.0.0").write_bytes(b"stock")
        (root/"usr/lib/libgbm.so").symlink_to("libgbm.so.1.0.0")
        return root
    def test_remove_only_unowned_symlink(self):
        with tempfile.TemporaryDirectory() as d:
            root=self.fixture(d)
            obj=c.clean(root)
            self.assertIn("usr/lib/libgbm.so",obj["removed_only_unowned_known_development_aliases"])
            self.assertTrue((root/"usr/lib/libgbm.so.1.0.0").exists())
            self.assertFalse((root/"usr/lib/libgbm.so").exists())
    def test_refuse_host_root(self):
        with self.assertRaises(ValueError):c.clean(Path("/"))
    def test_refuse_regular_unowned(self):
        with tempfile.TemporaryDirectory() as d:
            root=self.fixture(d)
            (root/"usr/lib/libgbm.so").unlink()
            (root/"usr/lib/libgbm.so").write_text("unmanaged")
            with self.assertRaises(ValueError):c.clean(root)
    def test_preserve_package_owned_alias(self):
        with tempfile.TemporaryDirectory() as d:
            root=self.fixture(d)
            db=root/"lib/apk/db/installed"
            db.write_text(db.read_text()+"R:libgbm.so\n")
            result=c.clean(root)
            self.assertEqual(result["removed_only_unowned_known_development_aliases"],[])
            self.assertTrue((root/"usr/lib/libgbm.so").is_symlink())

if __name__=="__main__":unittest.main()
