import importlib.util,tempfile,unittest
from pathlib import Path
SRC=Path(__file__).resolve().parents[1]/'patch_live_root.py'
spec=importlib.util.spec_from_file_location('p91',SRC)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class TestPatch(unittest.TestCase):
 def root(self,p):
  for name in ['usr/bin/firefox-esr','usr/sbin/lightdm','usr/share/xsessions/openbox.desktop','etc/skel/.config/openbox/autostart','usr/local/sbin/puppy50-network-probe','etc/ssl/certs/ca-certificates.crt']:
   f=p/name;f.parent.mkdir(parents=True,exist_ok=True);f.write_text('untouched')
  f=p/'etc/lightdm/lightdm.conf.d/50-puppy50.conf';f.parent.mkdir(parents=True,exist_ok=True);f.write_text('[Seat:*]\nautologin-user=user\n')
 def test_preserves_browser_and_network(self):
  with tempfile.TemporaryDirectory() as d:
   r=Path(d);self.root(r);a=(r/'usr/bin/firefox-esr').read_bytes();b=(r/'usr/local/sbin/puppy50-network-probe').read_bytes()
   x=m.patch(r);self.assertTrue(x['only_live_boot_allowed'])
   self.assertEqual(a,(r/'usr/bin/firefox-esr').read_bytes())
   self.assertEqual(b,(r/'usr/local/sbin/puppy50-network-probe').read_bytes())
   self.assertIn('ExecStartPre=/usr/local/sbin/puppy50-prepare-session',(r/'etc/systemd/system/lightdm.service.d/10-puppy50-live-preflight.conf').read_text())
 def test_missing_firefox_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   r=Path(d);self.root(r);(r/'usr/bin/firefox-esr').unlink()
   with self.assertRaises(ValueError):m.patch(r)
 def test_unrecognized_source_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   r=Path(d);self.root(r);(r/'etc/lightdm/lightdm.conf.d/50-puppy50.conf').write_text('wrong')
   with self.assertRaises(ValueError):m.patch(r)
 def test_runtime_host_forbidden(self):
  with self.assertRaises(ValueError):m.patch(Path('/'))
 def test_never_disables_browser_security(self):
  self.assertIn('boot=live',m.PREFLIGHT)
  self.assertNotIn('chpasswd',m.PREFLIGHT)
  self.assertNotIn('curl -k',m.PREFLIGHT)
if __name__=='__main__':unittest.main()
