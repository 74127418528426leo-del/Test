import json,tempfile,unittest
from pathlib import Path
from compare import evaluate
class CompareTests(unittest.TestCase):
    def test_requires_real_js_and_usb_removal(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);r={'first_home_seen_seconds':15,'early_js_response_seconds':18,'staged_ram_ready_seconds':35,'early_media_attached_before_navigation':True,'early_media_attached_after_js_response':True,'media_ejected':True,'input_sent_after_eject':True,'qemu_running_at_end':True,'errors':[]}
            for n in ('base1','cand1','cand2','base2'):
                (root/n).mkdir();(root/n/'result.json').write_text(json.dumps(r))
            self.assertEqual(evaluate(root)['home_gain_seconds'],0)
            r['early_js_response_seconds']=None;(root/'cand1'/'result.json').write_text(json.dumps(r))
            with self.assertRaises(ValueError):evaluate(root)
if __name__=='__main__':unittest.main()
