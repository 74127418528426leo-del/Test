import importlib.util
import tempfile
import unittest
from pathlib import Path

source=Path(__file__).resolve().parents[1]/"patch_normal_browser.py"
spec=importlib.util.spec_from_file_location("patch70",source)
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class NormalBrowserTests(unittest.TestCase):
    def fixture(self,base):
        root=Path(base)
        session=root/"usr/local/bin/puppy50-web-launch"
        session.parent.mkdir(parents=True,exist_ok=True)
        session.write_text(
            "#!/bin/sh\n/usr/local/bin/puppy50-network-probe || true\n"+
            mod.NAV_START+"\n(\n  sleep 205\n"+
            "  echo 'PUPPY50_V69_NATIVE_FIREFOX_NAV_REQUESTED=https://example.com/'\n"+
            ") &\n"+mod.FIREFOX_COMMAND+"\n")
        probe=root/"usr/local/bin/puppy50-network-probe"
        probe.write_text("#!/bin/sh\necho PUPPY50_V67_EXTERNAL_TLS_CA_VERIFIED=PASS\n")
        html=root/"usr/share/puppy50web/index.html"
        html.parent.mkdir(parents=True,exist_ok=True)
        html.write_text("<h1>old test page</h1>")
        ca=root/"etc/ssl/certs/ca-certificates.crt"
        ca.parent.mkdir(parents=True,exist_ok=True)
        ca.write_text("trusted test roots")
        (root/"usr/lib/firefox-esr").mkdir(parents=True,exist_ok=True)
        return root

    def test_replaces_demo_with_normal_browser(self):
        with tempfile.TemporaryDirectory() as folder:
            root=self.fixture(folder)
            proof=mod.patch(root)
            self.assertTrue(proof["automated_external_site_navigation_removed"])
            self.assertTrue(proof["original_CA_bundle_preserved"])
            launch=(root/"usr/local/bin/puppy50-web-launch").read_text()
            self.assertEqual(launch.count(mod.FIREFOX_COMMAND),1)
            self.assertNotIn("sleep 205",launch)
            self.assertNotIn("PUPPY50_V69_NATIVE_FIREFOX_NAV_REQUESTED",launch)
            self.assertIn("PUPPY50_V70_NETWORK_STATUS_PAGE_WRITTEN=PASS",
                          (root/"usr/local/bin/puppy50-network-probe").read_text())
            self.assertIn("PUPPY50_V67_EXTERNAL_TLS_CA_VERIFIED=PASS",
                          (root/"usr/local/libexec/puppy50-network-probe-core").read_text())
            page=(root/"usr/share/puppy50web/index.html").read_text()
            self.assertIn("https://www.wikipedia.org/",page)
            self.assertIn("file:///run/puppy50-network-status.html",page)
            self.assertNotIn("window.location=",page)
            self.assertEqual((root/"etc/ssl/certs/ca-certificates.crt").read_text(),"trusted test roots")

    def test_reject_missing_original_demo(self):
        with tempfile.TemporaryDirectory() as folder:
            root=self.fixture(folder)
            session=root/"usr/local/bin/puppy50-web-launch"
            session.write_text(mod.FIREFOX_COMMAND)
            with self.assertRaises(ValueError):mod.patch(root)

    def test_dont_repatch_root(self):
        with tempfile.TemporaryDirectory() as folder:
            root=self.fixture(folder)
            mod.patch(root)
            with self.assertRaises(ValueError):mod.patch(root)

    def test_no_insecure_network_or_browser_overrides(self):
        wrapper=(source.parent/"network_status_wrapper.sh").read_text()
        for bad in ("curl -k", "--insecure", "MOZ_DISABLE_CONTENT_SANDBOX"):
            self.assertNotIn(bad,wrapper)
        self.assertIn("mv \"$TMP\" \"$PAGE\"",wrapper)
if __name__=="__main__":unittest.main()
