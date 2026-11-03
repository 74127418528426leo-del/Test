import importlib.util
import tempfile
import unittest
from pathlib import Path
p=Path(__file__).resolve().parents[1]/"remote_pixels.py"
spec=importlib.util.spec_from_file_location("remote_pixels",p)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def ppm(path,rgb):
    path.write_bytes(b"P6\n256 256\n255\n"+bytes(rgb)*65536)
class BrowserWebsiteProof(unittest.TestCase):
    def test_color_is_unique_to_real_remote_site(self):
        with tempfile.TemporaryDirectory() as d:
            a=Path(d)/"before.ppm";b=Path(d)/"after.ppm"
            ppm(a,(7,16,32));ppm(b,(203,45,145))
            r=m.remote_page_proof(a,b)
            self.assertTrue(r['page_color_transition'])
            self.assertGreater(r['after']['fraction'],0.9)
    def test_blank_screen_never_passes(self):
        with tempfile.TemporaryDirectory() as d:
            a=Path(d)/"a.ppm";b=Path(d)/"b.ppm"
            ppm(a,(0,0,0));ppm(b,(0,0,0))
            self.assertFalse(m.remote_page_proof(a,b)['page_color_transition'])
    def test_premature_page_color_is_not_proof(self):
        with tempfile.TemporaryDirectory() as d:
            a=Path(d)/"a.ppm";b=Path(d)/"b.ppm"
            ppm(a,(203,45,145));ppm(b,(203,45,145))
            self.assertFalse(m.remote_page_proof(a,b)['page_color_transition'])
    def test_invalid_ppm_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            a=Path(d)/"invalid.ppm";a.write_bytes(b"P6\n12 12\n255\n")
            with self.assertRaises(ValueError):
                m.color_fraction(a)
if __name__=="__main__":unittest.main()
