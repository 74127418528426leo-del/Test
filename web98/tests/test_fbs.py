import unittest
from fb_vs_gtk import cmd,URLS
class Test(unittest.TestCase):
 def test_basic_js_enabled(self):
  self.assertIn('--enable_javascript=1',cmd('fb',URLS['basic_js']))
 def test_native_x_framebuffer_selected(self):
  c=cmd('fb',URLS['basic_js'])
  self.assertEqual(c[c.index('-f')+1],'x')
 def test_no_insecure_certificate_option(self):
  for front in ['gtk','fb']:
   x=cmd(front,URLS['wikipedia'])
   self.assertNotIn('--ignore-certificate-errors',x)
   self.assertNotIn('--no-sandbox',x)
 def test_unknown_rejected(self):
  with self.assertRaises(ValueError):cmd('fake','https://example.com')
if __name__=='__main__':unittest.main()
