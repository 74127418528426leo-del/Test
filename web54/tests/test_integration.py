"""Safety invariants for staged-only Mesa integration. No hardware claims."""
import importlib.util
from pathlib import Path
import io
import tarfile
import tempfile
import unittest

SRC=Path(__file__).resolve().parents[1]/"integrate_softpipe.py"
spec=importlib.util.spec_from_file_location("softpipe",SRC)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class SoftpipeSafetyTests(unittest.TestCase):
    def fixture(self,base):
        root=Path(base)/"output"/"rootfs"
        (root/"etc/apk").mkdir(parents=True)
        (root/"etc/apk/repositories").write_text("test\n")
        (root/"usr/share/puppy50web").mkdir(parents=True)
        (root/"usr/share/puppy50web/index.html").write_text("test")
        (root/"usr/lib").mkdir(parents=True)
        (root/"usr/lib/libgallium-26.1.6.so").write_bytes(b"test")
        return root

    def test_refuses_other_root(self):
        with tempfile.TemporaryDirectory() as d:
            self.fixture(d)
            with self.assertRaises(ValueError):
                m.validate_root(Path(d))

    def test_rejects_tar_path_traversal(self):
        with tempfile.TemporaryDirectory() as d:
            root=self.fixture(d)
            buf=io.BytesIO()
            with tarfile.open(fileobj=buf,mode="w:gz") as t:
                payload=b"unsafe"
                info=tarfile.TarInfo("../escape")
                info.size=len(payload)
                t.addfile(info,io.BytesIO(payload))
            buf.seek(0)
            with tarfile.open(fileobj=buf,mode="r:gz") as t:
                with self.assertRaises(ValueError):
                    m.validate_tar(t,root)

    def test_rejects_absolute_symlink(self):
        with tempfile.TemporaryDirectory() as d:
            root=self.fixture(d)
            buf=io.BytesIO()
            with tarfile.open(fileobj=buf,mode="w:gz") as t:
                info=tarfile.TarInfo("./usr/lib/libbad.so")
                info.type=tarfile.SYMTYPE
                info.linkname="/etc/passwd"
                t.addfile(info)
            buf.seek(0)
            with tarfile.open(fileobj=buf,mode="r:gz") as t:
                with self.assertRaises(ValueError):
                    m.validate_tar(t,root)

if __name__=="__main__":
    unittest.main()
