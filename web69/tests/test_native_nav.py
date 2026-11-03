import importlib.util,tempfile,unittest
from pathlib import Path
p=Path(__file__).resolve().parents[1]/"patch_native_nav.py"
spec=importlib.util.spec_from_file_location("nav69",p)
n=importlib.util.module_from_spec(spec);spec.loader.exec_module(n)
class NativeNavigationPatchTests(unittest.TestCase):
 def test_patches_existing_firefox_once(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);x=root/"usr/local/bin/puppy50-web-launch"
   x.parent.mkdir(parents=True)
   x.write_text("#!/bin/sh\n"+n.ANCHOR+"\n")
   result=n.patch(root)
   c=x.read_text()
   self.assertTrue(result["native_firefox_navigation_scheduled"])
   self.assertIn("sleep 205",c)
   self.assertIn("firefox-esr --new-tab https://example.com/",c)
   self.assertIn(n.ANCHOR,c)
   with self.assertRaises(ValueError):n.patch(root)
 def test_missing_launcher_rejected(self):
  with tempfile.TemporaryDirectory() as td:
   with self.assertRaises(ValueError):n.patch(Path(td))
if __name__=="__main__":unittest.main()
