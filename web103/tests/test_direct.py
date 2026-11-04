import unittest
from web103.direct_4k import DIRECT_MP4,HTML,DATA_URL
from web101.site_test import char_keys
class T(unittest.TestCase):
 def test_exact_official_pexels_native_media(self):
  self.assertEqual(DIRECT_MP4, "https://videos.pexels.com/video-files/27251986/12102943_3840_2160_30fps.mp4")
  self.assertIn(DIRECT_MP4,HTML)
 def test_html5_native_media_overlay(self):
  for term in ['<video','autoplay','muted','videoHeight','videoWidth','totalVideoFrames','droppedVideoFrames','currentTime']:
   self.assertIn(term,HTML)
 def test_user_entered_data_url_characters(self):
  self.assertTrue(DATA_URL.startswith('data:text/html;base64,'))
  self.assertLess(len(DATA_URL),2000)
  for c in DATA_URL:self.assertTrue(char_keys(c))
 def test_no_browser_security_bypass(self):
  for s in ['--no-sandbox','ignore-certificate-errors','disable-web-security']:
   self.assertNotIn(s,HTML)
if __name__=='__main__':unittest.main()
