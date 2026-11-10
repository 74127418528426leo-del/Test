import unittest
from verify_probe import verify

H='a'*64
J='b'*64
MANIFEST=f'{H}  one-le64.cache-9\n{J}  two-le64.cache-9\n'
DIRS='/usr/share/fonts\n/usr/share/fonts/truetype/dejavu\n'
SERIAL=(f'P50_FONT_BEFORE_INIT_BEGIN\nP50_FONT_BEFORE one-le64.cache-9 {H} {H}\n'
        f'P50_FONT_BEFORE two-le64.cache-9 {J} {J}\nP50_FONT_VALIDITY_BEGIN\n'
        '/usr/share/fonts: skipping, existing cache is valid: 0 fonts, 1 dirs\n'
        '/usr/share/fonts/truetype/dejavu: skipping, existing cache is valid: 8 fonts, 0 dirs\n'
        'P50_FONT_VALIDITY_RC 0\nP50_FONT_VALIDITY_END\n'
        f'P50_FONT_AFTER one-le64.cache-9 {H} {H}\nP50_FONT_AFTER two-le64.cache-9 {J} {J}\n'
        'P50_FONT_BEFORE_INIT_END\nP50_FONT_TRACE_READY\n'
        'P50_FONT_ACCESS\t9000\t200\t1000\tXorg\t/var/cache/fontconfig/one-le64.cache-9\n'
        'P50_FONT_ACCESS\t9001\t201\t1000\tfirefox-esr\t/var/cache/fontconfig/two-le64.cache-9\n'
        'P50_FONT_FIREFOX_CACHE_OPEN\nP50_FONT_TRACE_END 2 0 0\n')
RESULT={'first_home_seen_seconds':15.0,'serial_marker_first_seen_seconds':{'P50_FONT_FIREFOX_CACHE_OPEN':14.7}}

class ProbeTests(unittest.TestCase):
 def test_accepts_verified_manifest_validity_and_nonroot_firefox_open(self):
  out=verify(SERIAL,MANIFEST,DIRS,RESULT)
  self.assertEqual(out['expected_cache_files'],2);self.assertEqual(out['firefox_cache_opens'],1)
 def test_rejects_missing_or_changed_cache_before_and_after(self):
  for s in (SERIAL.replace('P50_FONT_BEFORE two-le64.cache-9','P50_FONT_BAD two-le64.cache-9'),SERIAL.replace(f'P50_FONT_AFTER one-le64.cache-9 {H} {H}',f'P50_FONT_AFTER one-le64.cache-9 {H} {J}')):
   with self.assertRaises(ValueError):verify(s,MANIFEST,DIRS,RESULT)
 def test_rejects_stale_regenerated_and_missing_expected_directory(self):
  for s in (SERIAL.replace('skipping, existing cache is valid','caching, new cache contents',1),SERIAL.replace('/usr/share/fonts/truetype/dejavu: skipping','/different: skipping')):
   with self.assertRaises(ValueError):verify(s,MANIFEST,DIRS,RESULT)
 def test_rejects_xorg_only_late_open_and_incomplete_trace(self):
  for s,r in ((SERIAL.replace('firefox-esr','Xorg'),RESULT),(SERIAL,{**RESULT,'serial_marker_first_seen_seconds':{'P50_FONT_FIREFOX_CACHE_OPEN':15.5}}),(SERIAL.replace('P50_FONT_TRACE_END 2 0 0','P50_FONT_TRACE_END 2 1 0'),RESULT)):
   with self.assertRaises(ValueError):verify(s,MANIFEST,DIRS,r)

if __name__=='__main__':unittest.main()
