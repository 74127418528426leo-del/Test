import base64
import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

p=Path(__file__).resolve().parents[1]/"audit_apk_root.py"
spec=importlib.util.spec_from_file_location("apk73",p)
audit=importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)

def record(name, version, folder, filename, data):
    checksum="Q1"+base64.b64encode(hashlib.sha1(data).digest()).decode().rstrip("=")
    return "\n".join(("P:"+name,"V:"+version,"F:"+folder,"R:"+filename,"Z:"+checksum))+"\n"

class ApkAuditTests(unittest.TestCase):
    def fixture(self,base):
        root=Path(base)
        db=root/"lib/apk/db/installed"
        db.parent.mkdir(parents=True,exist_ok=True)
        lib=root/"usr/lib"
        lib.mkdir(parents=True,exist_ok=True)
        (lib/"libgood.so.1").write_bytes(b"baseline")
        (lib/"libtampered.so.1").write_bytes(b"unmanaged overlay")
        (lib/"libuntracked.so.1").write_bytes(b"untracked")
        db.write_text(
            record("good","1.2","usr/lib","libgood.so.1",b"baseline")+
            "\n"+
            record("mesa","3.4","usr/lib","libtampered.so.1",b"original"))
        return root
    def test_audit_detects_mismatched_or_unowned_shared_libraries(self):
        with tempfile.TemporaryDirectory() as d:
            root=self.fixture(d)
            report=audit.audit(root)
            self.assertTrue(report["apk_database_present"])
            self.assertEqual(report["owned_shared_libraries_sha1_checked"],2)
            self.assertEqual(report["owned_shared_libraries_sha1_mismatched"],1)
            self.assertEqual(report["shared_library_files_without_apk_owner"],1)
            self.assertIn("usr/lib/libuntracked.so.1",report["unowned_lib_examples"])
            self.assertFalse(report["security_updates_certified"])
    def test_original_digest_is_decoded(self):
        digest=hashlib.sha1(b"hello").digest()
        token="Q1"+base64.b64encode(digest).decode().rstrip("=")
        self.assertEqual(audit.expected_sha1(token),digest)
        self.assertIsNone(audit.expected_sha1("Q2unknown"))
        self.assertIsNone(audit.expected_sha1("Q1%%%"))
    def test_no_apk_database_cannot_be_claimed_verified(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):
                audit.audit(Path(d))
    def test_unsafe_root_path_not_accepted(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            for path in ("../etc/passwd","/etc/passwd"):
                with self.assertRaises(ValueError):
                    audit.safe_path(root,path)
if __name__=="__main__":unittest.main()
