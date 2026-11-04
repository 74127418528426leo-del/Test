import unittest
from web103.direct_4k import DIRECT_MP4
class T(unittest.TestCase):
 def test_exact_pexels_native_media(self):
  self.assertTrue(DIRECT_MP4.startswith("https://videos.pexels.com/video-files/27251986/"))
  self.assertIn("3840_2160_30fps.mp4",DIRECT_MP4)
 def test_no_arbitrary_host(self):
  self.assertEqual(DIRECT_MP4.split('/')[2],"videos.pexels.com")
if __name__=="__main__":unittest.main()
