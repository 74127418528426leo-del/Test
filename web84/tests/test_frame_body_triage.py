import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

p=Path(__file__).resolve().parents[1]/"frame_body_triage.py"
spec=importlib.util.spec_from_file_location("v84",p)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class FrameTriageTests(unittest.TestCase):
    def ppm(self,path,body_color=(255,255,255),black_lines=False):
        w,h=1600,900
        pixels=bytearray(bytes((255,255,255))*w*h)
        for y in range(175,860):
            for x in range(350,1550):
                dark=black_lines and y%30<3 and x%80<40
                i=(y*w+x)*3
                pixels[i:i+3]=bytes((40,40,40)) if dark else bytes(body_color)
        path.write_bytes(b"P6\n1600 900\n255\n"+pixels)
    def test_blank_frame_rejected_as_web_content(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);self.ppm(root/"frame_405.ppm")
            (root/"result.json").write_text(json.dumps({"ram_root_copy":True,"ram_root_switch":True}))
            r=m.assess(root,"test",1024)
            self.assertTrue(r["body_blank_at_final_screenshot"])
            self.assertFalse(r["body_nonblank_content_candidate"])
            self.assertFalse(r["Wikipedia_site_visually_confirmed"])
    def test_textured_frame_is_only_candidate_not_proof(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);self.ppm(root/"frame_405.ppm",black_lines=True)
            r=m.assess(root,"test",2048)
            self.assertTrue(r["body_nonblank_content_candidate"])
            self.assertFalse(r["Wikipedia_site_visually_confirmed"])
    def test_truncated_frame_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/"frame_405.ppm").write_bytes(b"P6\n1600 900\n255\n")
            with self.assertRaises(ValueError):m.central_pixels(root/"frame_405.ppm")
if __name__=="__main__":unittest.main()
