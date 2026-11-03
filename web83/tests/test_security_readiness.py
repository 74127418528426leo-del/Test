import json
import tempfile
import unittest
from pathlib import Path
import importlib.util

source=Path(__file__).resolve().parents[1]/"firefox_security_readiness.py"
spec=importlib.util.spec_from_file_location("security_gate83",source)
gate=importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)

def fixture(folder,version):
    p=Path(folder)/"apk_audit.json"
    p.write_text(json.dumps({
      "schema":"PUPPY50_APK_PACKAGE_COHERENCE_AUDIT_V1",
      "apk_database_present":True,
      "firefox_package_version_in_database":version,
      "owned_shared_libraries_sha1_mismatched":0,
      "shared_library_files_without_apk_owner":0,
      "package_manager_inventory_missing":False
    }))
    return p

class BrowserFreshnessTests(unittest.TestCase):
    def test_actual_140_12_known_outdated(self):
        with tempfile.TemporaryDirectory() as d:
            r=gate.audit(fixture(d,"140.12.0-r0"))
            self.assertFalse(r["browser_version_meets_published_security_baseline"])
            self.assertFalse(r["public_production_security_release_eligible"])
            self.assertTrue(r["apk_library_ownership_and_digest_coherent"])
    def test_153_6_not_automatically_security_certified(self):
        with tempfile.TemporaryDirectory() as d:
            r=gate.audit(fixture(d,"153.6.0-r0"))
            self.assertTrue(r["browser_version_meets_published_security_baseline"])
            self.assertFalse(r["public_production_security_release_eligible"])
    def test_bad_unsupported_version_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):
                gate.audit(fixture(d,"unknown"))
    def test_older_october_esr_not_sufficient(self):
        with tempfile.TemporaryDirectory() as d:
            r=gate.audit(fixture(d,"153.5.1-r0"))
            self.assertFalse(r["browser_version_meets_published_security_baseline"])

if __name__=="__main__":unittest.main()
