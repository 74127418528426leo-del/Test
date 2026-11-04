import importlib.util,tempfile,unittest
from pathlib import Path
SRC=Path(__file__).resolve().parents[1]/"patch_diagnostics_only.py"
spec=importlib.util.spec_from_file_location("p100",SRC)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class T(unittest.TestCase):
 def setup(self,p):
  names=["usr/bin/firefox-esr","usr/sbin/lightdm",
    "usr/local/sbin/puppy50-prepare-session",
    "usr/local/sbin/puppy50-network-probe",
    "etc/ssl/certs/ca-certificates.crt"]
  for name in names:
   f=p/name;f.parent.mkdir(parents=True,exist_ok=True)
   f.write_text("P50_V91_LIGHTDM_AUTOLOGIN_PREPARED" if "prepare-session" in name else name)
  return names
 def test_only_readonly_guest_telemetry(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);files=self.setup(root)
   baseline={n:(root/n).read_bytes() for n in files}
   x=m.patch(root)
   self.assertEqual({n:(root/n).read_bytes() for n in files},baseline)
   self.assertFalse(x["adds_zram_or_swap"])
   self.assertFalse(x["modifies_browser_network_or_TLS"])
   self.assertFalse((root/"etc/systemd/system/puppy50-zram-live.service").exists())
 def test_do_not_patch_local_system(self):
  with self.assertRaises(ValueError):m.patch("/")
 def test_guest_memory_pressure_included(self):
  self.assertIn("/proc/pressure/memory",m.TELEMETRY)
  self.assertIn("P50_V99_RAM_SAMPLE",m.TELEMETRY)
  self.assertNotIn("swapon -p",m.TELEMETRY)
 def test_missing_live_root_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   with self.assertRaises(ValueError):m.patch(d)
if __name__=="__main__":unittest.main()
