import importlib.util
import tempfile
import unittest
from pathlib import Path
p=Path(__file__).resolve().parents[1]/"patch_iso_root.py"
spec=importlib.util.spec_from_file_location("patch67",p)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class RootOverlayTests(unittest.TestCase):
    def setup_root(self,d):
        root=Path(d)
        files={
         "usr/local/bin/puppy50-web-launch":"#!/bin/sh\n/usr/local/bin/puppy50-network-probe\n",
         "usr/local/bin/puppy50-network-probe":"old probe",
         "etc/ssl/certs/ca-certificates.crt":"CA bundle",
         "usr/lib/firefox-esr/firefox":"binary",
         "usr/share/puppy50web/index.html":"<script>KEYBOARD CONFIRMED</script>"}
        for name,body in files.items():
            f=root/name;f.parent.mkdir(parents=True,exist_ok=True);f.write_text(body)
        return root
    def test_preserves_firefox_launcher_and_ca(self):
        with tempfile.TemporaryDirectory() as d:
            root=self.setup_root(d)
            old=(root/"usr/local/bin/puppy50-web-launch").read_bytes()
            proof=m.patch(root)
            self.assertTrue(proof["CA_bundle_preserved"])
            self.assertFalse(proof["kernel_and_initrd_changed"])
            self.assertEqual((root/"usr/local/bin/puppy50-web-launch").read_bytes(),old)
            self.assertIn("PUPPY50_V67_EXTERNAL_TLS_VIA_HOST_CONNECT=PASS",(root/"usr/local/bin/puppy50-network-probe").read_text())
    def test_no_skipped_TLS_verification(self):
        source=(p.parent/"online_probe.sh").read_text()
        self.assertIn("--proto '=https'",source)
        self.assertIn("--proxy http://10.0.2.2:3128",source)
        self.assertIn("SSLProxy",source)
        self.assertIn("PUPPY50_V67_FIREFOX_HTTPS_PROXY_POLICY=APPLIED",source)
        for insecure in ("curl -k","--insecure","security.enterprise_roots.enabled", "MOZ_DISABLE_CONTENT_SANDBOX"):
            self.assertNotIn(insecure,source)
    def test_missing_trust_bundle_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=self.setup_root(d)
            (root/"etc/ssl/certs/ca-certificates.crt").unlink()
            with self.assertRaises(ValueError):m.patch(root)

if __name__=="__main__":unittest.main()
