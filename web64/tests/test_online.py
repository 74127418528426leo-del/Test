import importlib.util
import tempfile
import unittest
from pathlib import Path

source=Path(__file__).resolve().parents[1]/"configure_online.py"
spec=importlib.util.spec_from_file_location("online",source)
online=importlib.util.module_from_spec(spec)
spec.loader.exec_module(online)

class OnlineStageTests(unittest.TestCase):
    def fixture(self,d,curl=True):
        root=Path(d)
        launch=root/"usr/local/bin/puppy50-web-launch"
        launch.parent.mkdir(parents=True,exist_ok=True)
        launch.write_text("#!/bin/sh\n"+online.START+"\n")
        html=root/"usr/share/puppy50web/index.html"
        html.parent.mkdir(parents=True,exist_ok=True)
        html.write_text("<p>The normal Firefox address bar, tabs and downloads remain available.</p>")
        if curl:
            p=root/"usr/bin/curl"
            p.parent.mkdir(parents=True,exist_ok=True)
            p.write_text("test")
        return root
    def test_safe_install_keeps_xorg_and_online_probe(self):
        with tempfile.TemporaryDirectory() as d:
            root=self.fixture(d)
            proof=online.patch(root)
            self.assertTrue(proof["firefox_sandbox_unchanged"])
            self.assertIn("puppy50-network-probe", (root/"usr/local/bin/puppy50-web-launch").read_text())
            self.assertIn(online.START,(root/"usr/local/bin/puppy50-web-launch").read_text())
            self.assertIn("HTTPS addresses",(root/"usr/share/puppy50web/index.html").read_text())
            self.assertTrue((root/"usr/local/bin/puppy50-network-probe").stat().st_mode & 0o111)
    def test_missing_HTTPS_client_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):online.patch(self.fixture(d,curl=False))
    def test_double_injection_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=self.fixture(d)
            online.patch(root)
            with self.assertRaises(ValueError):online.patch(root)
    def test_no_tls_bypass_and_positive_certificate_check(self):
        script=(source.parent/"network_probe.sh").read_text()
        self.assertIn("--proto '=https'",script)
        self.assertIn("https://example.com/",script)
        self.assertIn("PUPPY50_V64_NETWORK_READY=PASS",script)
        for bad in ("--insecure", "curl -k", "MOZ_DISABLE_CONTENT_SANDBOX=1"):
            self.assertNotIn(bad,script)
if __name__=="__main__":unittest.main()
