import importlib.util, tempfile, unittest
from pathlib import Path
SRC=Path(__file__).resolve().parents[1]/"patch_live_zram.py"
spec=importlib.util.spec_from_file_location("p99",SRC)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class TestV99(unittest.TestCase):
 def fake_root(self,r):
  names=["usr/bin/firefox-esr","usr/sbin/lightdm",
         "etc/systemd/system/lightdm.service.d/10-puppy50-live-preflight.conf",
         "usr/local/sbin/puppy50-prepare-session",
         "usr/local/sbin/puppy50-network-probe",
         "etc/ssl/certs/ca-certificates.crt"]
  for name in names:
   p=r/name;p.parent.mkdir(parents=True,exist_ok=True)
   p.write_text("ORIGINAL "+("P50_V91_LIGHTDM_AUTOLOGIN_PREPARED" if "prepare-session" in name else name))
  return names
 def test_patch_is_extracted_root_only(self):
  with self.assertRaises(ValueError):m.patch("/")
 def test_security_files_remain_byte_identical(self):
  with tempfile.TemporaryDirectory() as d:
   r=Path(d);names=self.fake_root(r)
   before={x:(r/x).read_bytes() for x in names}
   out=m.patch(r)
   self.assertEqual({x:(r/x).read_bytes() for x in names},before)
   self.assertFalse(out["browser_or_TLS_policies_modified"])
   self.assertTrue(out["guest_proof_required"])
 def test_swap_uses_only_compressed_memory_and_live_guard(self):
  self.assertIn("boot=live",m.ZRAM)
  self.assertIn("1024M",m.ZRAM)
  self.assertIn("swapon -p 100 /dev/zram0",m.ZRAM)
  self.assertNotIn("swapfile",m.ZRAM)
  self.assertNotIn("/dev/sda",m.ZRAM)
  self.assertNotIn("curl -k",m.ZRAM)
 def test_lightdm_waits_for_zram(self):
  self.assertIn("After=puppy50-zram-live.service",m.LIGHTDM_DROP)
  self.assertIn("Wants=puppy50-zram-live.service",m.LIGHTDM_DROP)
 def test_memory_pressure_and_real_zram_proof(self):
  self.assertIn("/proc/pressure/memory",m.TELEMETRY)
  self.assertIn("/sys/block/zram0/mm_stat",m.TELEMETRY)
  self.assertIn("P50_V99_ZRAM_ENABLED=1",m.ZRAM)
  self.assertIn("oomKill",m.TELEMETRY)
 def test_invalid_base_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   with self.assertRaises(ValueError):m.patch(d)

if __name__=="__main__":unittest.main()
