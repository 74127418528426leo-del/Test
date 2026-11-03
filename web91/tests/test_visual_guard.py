import importlib.util,tempfile,unittest
from pathlib import Path
SRC=Path(__file__).resolve().parents[1]/'visual_guard.py'
spec=importlib.util.spec_from_file_location('guard',SRC);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class Tests(unittest.TestCase):
 def frame(self,root,login):
  w,h=640,480;pix=bytearray(w*h*3)
  if login:
   for y in range(int(.39*h),int(.61*h)):
    for x in range(int(.395*w),int(.605*w)):
     i=3*(y*w+x);pix[i:i+3]=b'\xff\xff\xff'
  else:pix[:]=b'\xff'*(w*h*3)
  p=Path(root)/'frame.ppm';p.write_bytes(f'P6\n{w} {h}\n255\n'.encode()+pix);return p
 def test_previous_greeter_shape(self):
  with tempfile.TemporaryDirectory() as d:self.assertTrue(m.analyze(self.frame(d,True))['previous_LightDM_login_signature'])
 def test_white_browser_page_not_greeter(self):
  with tempfile.TemporaryDirectory() as d:self.assertFalse(m.analyze(self.frame(d,False))['previous_LightDM_login_signature'])
 def test_truncated_frame_refused(self):
  with tempfile.TemporaryDirectory() as d:
   f=Path(d)/'bad.ppm';f.write_bytes(b'P6\n640 480\n255\n'+b'\0'*12)
   with self.assertRaises(ValueError):m.analyze(f)
if __name__=='__main__':unittest.main()
