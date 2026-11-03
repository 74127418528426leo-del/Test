"""Offline synthetic validation: a PPM screenshot is not proof by itself."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

p=Path(__file__).resolve().parents[1]/"probe_ppm.py"
spec=importlib.util.spec_from_file_location("ppm",p)
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

def make(path,rgb):
    w,h=64,32
    path.write_bytes(f"P6\n{w} {h}\n255\n".encode()+bytes(rgb)*(w*h))

class FrameCheck(unittest.TestCase):
    def test_real_input_indicator_color_transition(self):
        with tempfile.TemporaryDirectory() as d:
            b=Path(d)/"before.ppm";a=Path(d)/"after.ppm"
            make(b,(7,16,32));make(a,(43,204,113))
            r=mod.compare(b,a)
            self.assertTrue(r["keyboard_event_visibly_changed_page"])
            self.assertFalse(r["web_security_https_network_webgl_proven"])
    def test_no_false_pass_if_both_frames_are_black(self):
        with tempfile.TemporaryDirectory() as d:
            b=Path(d)/"before.ppm";a=Path(d)/"after.ppm"
            make(b,(0,0,0));make(a,(0,0,0))
            self.assertFalse(mod.compare(b,a)["keyboard_event_visibly_changed_page"])
    def test_no_false_pass_if_green_precedes_keypress(self):
        with tempfile.TemporaryDirectory() as d:
            b=Path(d)/"before.ppm";a=Path(d)/"after.ppm"
            make(b,(43,204,113));make(a,(43,204,113))
            self.assertFalse(mod.compare(b,a)["keyboard_event_visibly_changed_page"])
    def test_corrupted_image_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"bad.ppm";p.write_bytes(b"P6\n3 3\n255\n")
            with self.assertRaises(ValueError):
                mod.inspect(p)
if __name__=="__main__":
    unittest.main()
