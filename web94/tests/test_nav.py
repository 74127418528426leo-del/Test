import tempfile, unittest
from pathlib import Path
from unittest.mock import patch
from web94 import qemu_reliable_navigation as m

class TestLowRAMNavigation(unittest.TestCase):
    def frame(self, folder, color):
        p=Path(folder)/'frame.ppm'
        p.write_bytes(b'P6\n640 480\n255\n'+bytes(color)*(640*480))
        return p
    def test_dark_homepage_does_trigger_retry(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertTrue(m.homepage_visible(self.frame(d,(7,16,32))))
    def test_light_external_page_does_not_retry(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertFalse(m.homepage_visible(self.frame(d,(238,238,238))))
    def test_missing_or_truncated_frame_is_not_proof(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertFalse(m.homepage_visible(Path(d)/'absent.ppm'))
            p=Path(d)/'bad.ppm';p.write_bytes(b'P6\n640 480\n255\n')
            self.assertFalse(m.homepage_visible(p))
    def test_paced_key_events_keep_normal_https(self):
        actions=[]
        with patch.object(m,'qmp',side_effect=lambda mon,cmd,args:actions.append((cmd,args))), patch.object(m.time,'sleep'):
            m.send_url_slow('/fake/qmp')
        self.assertEqual(len(actions),len(m.URL)+2)
        self.assertEqual(actions[0][1]['keys'][0]['data'],'ctrl')
        self.assertEqual(actions[-1][1]['keys'][0]['data'],'ret')
        self.assertTrue(all(x[1]['hold-time']==145 for x in actions))
if __name__=='__main__':unittest.main()
