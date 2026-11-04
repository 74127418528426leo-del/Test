import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from site_test import SITES,char_keys
class T(unittest.TestCase):
 def test_exact_real_pages_and_youtube_4k_example(self):
  self.assertEqual(len(SITES),4)
  for key,site in SITES.items():
   self.assertTrue(site['url'].startswith('https://'))
   self.assertTrue(site['url'].endswith('/') or key=='youtube4k')
 def test_keyboard_encodes_all_requested_uris(self):
  for d in SITES.values():
   for c in d['url']:
    names=char_keys(c)
    self.assertTrue(names)
    self.assertTrue(all(isinstance(v,str) for v in names))
 def test_bible_uppercase(self):
  self.assertEqual(char_keys('B'),['shift','b'])
  self.assertEqual(char_keys('I'),['shift','i'])
 def test_js_console_instrumentation_without_security_disabling(self):
  s=Path(__file__).resolve().parents[1].joinpath('site_test.py').read_text()
  self.assertIn('document.querySelector',s)
  self.assertIn('videoHeight',s)
  self.assertIn('getVideoPlaybackQuality()',s)
  self.assertNotIn('ignore-certificate-errors',s)
  self.assertNotIn('--no-sandbox',s)
  self.assertIn('"youtube_2160p_proven":False',s)
 def test_unrecognized_key_refused(self):
  with self.assertRaises(ValueError):char_keys('❄')
if __name__=='__main__':unittest.main()
