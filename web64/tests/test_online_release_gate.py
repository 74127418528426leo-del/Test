import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
file=Path(__file__).resolve().parents[1]/"online_release_gate.py"
spec=importlib.util.spec_from_file_location("gate64",file)
gate=importlib.util.module_from_spec(spec);spec.loader.exec_module(gate)
class OnlineAcceptanceTests(unittest.TestCase):
 def fixture(self,d):
  root=Path(d);iso=root/"test.iso"
  with iso.open("wb") as f:
   f.truncate(51*1048576);f.seek(16*2048+1);f.write(b"CD001")
  evid=root/"evidence"
  for ram in (384,1024):
   p=evid/f"ram_{ram}MiB";p.mkdir(parents=True)
   row=dict(ram_copy_complete=True,ram_root_switch=True,media_ejection_verified=True)
   if ram==1024:
    for key in ("script_ready_visually_proven","mouse_click_visually_proven","keyboard_visually_proven","qemu_e1000_early_loaded","guest_dhcp_lease","guest_default_route","guest_dns_config","guest_ca_verified_external_https","guest_online_ready","firefox_address_bar_keys_submitted"):
     row[key]=True
    (p/"frame_245.ppm").write_bytes(b"P6 dummy")
   (p/"result.json").write_text(json.dumps(row))
   (p/"serial.log").write_text("\n".join(gate.EARLY[:2]))
  return iso,evid
 def test_accept_only_right_evidence(self):
  with tempfile.TemporaryDirectory() as d:
   iso,e=self.fixture(d)
   o=gate.validate(iso,e)
   self.assertTrue(o["1024mib_guest_real_DHCP_DNS_CA_verified_external_HTTPS"])
   self.assertFalse(o["browser_actual_remote_page_content_verified_automatically"])
 def test_https_certificate_failure_is_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   iso,e=self.fixture(d);p=e/"ram_1024MiB"/"result.json"
   j=json.loads(p.read_text());j["guest_ca_verified_external_https"]=False
   p.write_text(json.dumps(j))
   with self.assertRaisesRegex(ValueError,"guest_ca_verified_external_https"):gate.validate(iso,e)
 def test_no_browser_input_is_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   iso,e=self.fixture(d);p=e/"ram_1024MiB"/"result.json"
   j=json.loads(p.read_text());j["keyboard_visually_proven"]=False
   p.write_text(json.dumps(j))
   with self.assertRaisesRegex(ValueError,"keyboard_visually_proven"):gate.validate(iso,e)
if __name__=="__main__":unittest.main()
