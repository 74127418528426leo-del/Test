import importlib.util
import tempfile
import unittest
from pathlib import Path

p=Path(__file__).resolve().parents[1]/"qemu_real_mozilla_click.py"
spec=importlib.util.spec_from_file_location("site72",p)
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class RealBrowserImageTests(unittest.TestCase):
    def ppm(self,path,color):
        path.write_bytes(b"P6\n640 480\n255\n"+bytes(color)*640*480)
    def test_homepage_color_present_and_absent(self):
        with tempfile.TemporaryDirectory() as temp:
            base=Path(temp)
            before=base/"home.ppm"
            after=base/"external.ppm"
            self.ppm(before,(9,198,206))
            self.ppm(after,(250,250,250))
            self.assertGreater(module.cyan_fraction(before)["fraction"],0.025)
            self.assertLess(module.cyan_fraction(after)["fraction"],0.01)
    def test_no_browser_frame_not_considered_success(self):
        with tempfile.TemporaryDirectory() as temp:
            frame=Path(temp)/"bad.ppm"
            frame.write_bytes(b"P6\n10 10\n255\n")
            with self.assertRaises(ValueError):
                module.cyan_fraction(frame)
    def test_hmp_monitor_commands_have_no_website_success_proxy(self):
        script=p.read_text()
        self.assertIn('sendkey tab',script)
        self.assertIn('sendkey ret',script)
        self.assertIn('keyboard_tab_count_proven',script)
        self.assertNotIn('mouse_move 220 0',script)
        self.assertIn('Mozilla_public_page_visually_confirmed"]=False',script)

if __name__=="__main__":
    unittest.main()
