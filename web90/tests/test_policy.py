import importlib.util,json,tempfile,unittest
from pathlib import Path
src=Path(__file__).resolve().parents[1]/"patch_firefox_policy.py"
spec=importlib.util.spec_from_file_location("patch",src);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class Tests(unittest.TestCase):
    def guest(self,td):
        r=Path(td)
        (r/"usr/lib/firefox-esr/distribution").mkdir(parents=True)
        s=r/"usr/local/bin/puppy50-web-launch";s.parent.mkdir(parents=True)
        s.write_text("firefox-esr file:///usr/share/puppy50web/index.html\n")
        return r
    def test_preserve_proxy_and_disable_only_prelaunch(self):
        with tempfile.TemporaryDirectory() as tmp:
            r=self.guest(tmp);p=r/"usr/lib/firefox-esr/distribution/policies.json"
            p.write_text(json.dumps({"policies":{"Proxy":{"Mode":"manual","SSLProxy":"10.0.2.2:3128"}}}))
            orig=(r/"usr/local/bin/puppy50-web-launch").read_bytes()
            report=m.patch(r);data=json.loads(p.read_text())
            self.assertEqual(data["policies"]["Proxy"]["SSLProxy"],"10.0.2.2:3128")
            self.assertFalse(data["policies"]["Preferences"][m.PREF]["Value"])
            self.assertEqual(report["changed"],[m.PREF])
            self.assertEqual((r/"usr/local/bin/puppy50-web-launch").read_bytes(),orig)
    def test_malformed_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            r=self.guest(tmp);(r/"usr/lib/firefox-esr/distribution/policies.json").write_text("bad")
            with self.assertRaises(ValueError):m.patch(r)
    def test_existing_preference_not_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            r=self.guest(tmp);p=r/"usr/lib/firefox-esr/distribution/policies.json"
            p.write_text(json.dumps({"policies":{"Preferences":{m.PREF:{"Value":True}}}}))
            with self.assertRaises(ValueError):m.patch(r)
    def test_missing_firefox_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):m.patch(tmp)
    def test_created_policy_parses(self):
        with tempfile.TemporaryDirectory() as tmp:
            r=self.guest(tmp);m.patch(r)
            p=r/"usr/lib/firefox-esr/distribution/policies.json"
            self.assertEqual(json.loads(p.read_text())["policies"]["Preferences"][m.PREF]["Status"],"locked")
if __name__=="__main__":unittest.main()
