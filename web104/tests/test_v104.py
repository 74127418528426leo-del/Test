import unittest,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from web104.kvm_play import URL, VIDEO
from web101.site_test import char_keys
class T(unittest.TestCase):
 def test_host_only_player_link(self):
  self.assertEqual(URL,'http://10.0.2.2:8766/pexels.html')
 def test_actual_3840_source_https(self):
  self.assertEqual(VIDEO,'https://videos.pexels.com/video-files/27251986/12102943_3840_2160_30fps.mp4')
 def test_real_player_video_stats(self):
  html=Path('web104/pexels.html').read_text()
  for n in ['getVideoPlaybackQuality','videoWidth','videoHeight','currentTime','droppedVideoFrames','frames=']:
   self.assertIn(n,html)
 def test_url_can_be_typed_by_qmp(self):
  for ch in URL: self.assertTrue(char_keys(ch))
if __name__=='__main__':unittest.main()
