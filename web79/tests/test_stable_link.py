import importlib.util,tempfile,unittest
from pathlib import Path
p=Path(__file__).resolve().parents[1]/"qemu_stable_link_page_load.py"
spec=importlib.util.spec_from_file_location("bench79",p)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class BrowserBenchmarkAcceptance(unittest.TestCase):
 def test_no_ethernet_bounce(self):
  src=p.read_text()
  self.assertIn('QEMU_virtual_NIC_kept_online',src)
  self.assertNotIn('hmp(monitor,f"set_link',src)
  self.assertIn('Wikipedia_public_page_visually_confirmed"]=False',src)
  self.assertIn('PUPPY50_V79_NO_EXTERNAL_PAGE_TRANSITION',src)
 def test_ppm_not_a_success_without_pixels(self):
  with tempfile.TemporaryDirectory() as d:
   f=Path(d)/"bad.ppm";f.write_bytes(b"invalid")
   with self.assertRaises(ValueError):m.cyan_fraction(f)
 def test_valid_frame_home_cyan_detected(self):
  with tempfile.TemporaryDirectory() as d:
   f=Path(d)/"home.ppm"
   f.write_bytes(b"P6\n640 480\n255\n"+bytes((9,198,206))*640*480)
   self.assertGreater(m.cyan_fraction(f)["fraction"],.02)
if __name__=="__main__":unittest.main()
