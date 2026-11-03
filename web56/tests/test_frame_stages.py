import importlib.util,tempfile,unittest
from pathlib import Path
p=Path(__file__).resolve().parents[1]/"frame_stages.py"
spec=importlib.util.spec_from_file_location("stages",p)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def ppm(path,color):
    path.write_bytes(b"P6\n128 128\n255\n"+bytes(color)*16384)
class StageTests(unittest.TestCase):
    def test_separate_visible_stages(self):
        with tempfile.TemporaryDirectory() as d:
            files=[Path(d)/str(i) for i in range(3)]
            for p,c in zip(files,[(255,192,68),(212,140,39),(43,204,113)]):ppm(p,c)
            r=m.compare_stages(*files)
            self.assertTrue(r['full_input_proof'])
            self.assertFalse(r['network_https_real_hardware_proven'])
    def test_unchanged_or_blank_is_failure(self):
        with tempfile.TemporaryDirectory() as d:
            paths=[Path(d)/str(i) for i in range(3)]
            for p in paths:ppm(p,(0,0,0))
            r=m.compare_stages(*paths)
            self.assertFalse(r['script_ready'])
            self.assertFalse(r['click_confirmed'])
            self.assertFalse(r['key_confirmed'])
            self.assertFalse(r['full_input_proof'])
    def test_script_and_click_without_keyboard_are_not_full_success(self):
        with tempfile.TemporaryDirectory() as d:
            files=[Path(d)/str(i) for i in range(3)]
            for p,c in zip(files,[(255,192,68),(212,140,39),(212,140,39)]):ppm(p,c)
            r=m.compare_stages(*files)
            self.assertTrue(r['script_ready'])
            self.assertTrue(r['click_confirmed'])
            self.assertFalse(r['key_confirmed'])
            self.assertFalse(r['full_input_proof'])
if __name__=="__main__":unittest.main()
