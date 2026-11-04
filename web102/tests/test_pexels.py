import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pexels_kvm import URL,EXPR
from web101.site_test import char_keys
class TestPexels(unittest.TestCase):
 def test_exact_url_and_4k_metadata(self):
  self.assertEqual(URL,'https://www.pexels.com/video/riverside-27251986/')
  self.assertEqual(len(URL),len(list(URL)))
 def test_all_url_chars_supported_by_qmp(self):
  for c in URL:self.assertTrue(char_keys(c))
 def test_actual_player_resolution_and_progress_instrumented(self):
  self.assertIn('videoWidth',EXPR)
  self.assertIn('videoHeight',EXPR)
  self.assertIn('currentTime',EXPR)
  self.assertIn('totalVideoFrames',EXPR['totalFrames'])
 def test_no_production_security_disable(self):
  s=(Path(__file__).resolve().parents[1]/'pexels_kvm.py').read_text()
  for banned in ['--no-sandbox','--ignore-certificate-errors','web-security=false']:
   self.assertNotIn(banned,s)
  self.assertIn('"actual_guest_4k_playback_verified":False',s)
if __name__=="__main__":unittest.main()
