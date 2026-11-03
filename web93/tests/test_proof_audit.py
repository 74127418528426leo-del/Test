import json,tempfile,unittest
from pathlib import Path
from web93.proof_audit import audit
class TestKVMReview(unittest.TestCase):
 def test_missing_means_not_proven(self):
  with tempfile.TemporaryDirectory() as d:
   r=audit(d,1536)
   self.assertFalse(r['browser_network_and_boot_prerequisites_passed'])
   self.assertFalse(r['actual_external_webpage_visually_verified'])
 def test_fake_small_screenshot_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)
   (p/'result.json').write_text(json.dumps({
    'real_QMP_browser_navigation_requested':True,
    'real_guest_ca_verified_public_https':True,
    'real_nonroot_firefox_process':True,
    'boot_cd_ejected':True,
    'guest_running_at_end':True}))
   (p/'frame_300.ppm').write_bytes(b'P6\n1280 800\n255\n'+b'\0'*12)
   r=audit(p,2048)
   self.assertFalse(r['browser_network_and_boot_prerequisites_passed'])
   self.assertNotIn('frame_300.ppm',r['valid_real_qemu_frames'])
 def test_valid_frame_and_flags_still_require_review(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)
   (p/'result.json').write_text(json.dumps({
    'real_QMP_browser_navigation_requested':True,
    'real_guest_ca_verified_public_https':True,
    'real_nonroot_firefox_process':True,
    'boot_cd_ejected':True,
    'guest_running_at_end':True}))
   (p/'frame_300.ppm').write_bytes(b'P6\n640 480\n255\n'+b'\0'*(640*480*3))
   r=audit(p,2048)
   self.assertTrue(r['browser_network_and_boot_prerequisites_passed'])
   self.assertFalse(r['actual_external_webpage_visually_verified'])
if __name__=='__main__':unittest.main()
