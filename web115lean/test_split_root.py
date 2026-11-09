import os,shutil,tempfile,unittest
from pathlib import Path
from split_root import split_root

class SplitRootTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.base=Path(self.tmp.name);self.root=self.base/'root';self.root.mkdir();self.extra=self.base/'extra'
  for n,data in [('usr/lib/firmware/netronome/a.bin',b'firmware'),('usr/share/doc/readme',b'docs'),('usr/lib/firefox-esr/libxul.so',b'browser'),('usr/lib/firmware/iwlwifi.ucode',b'wifi')]:
   p=self.root/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
  (self.root/'usr/share/doc/link').symlink_to('readme')
 def tearDown(self):self.tmp.cleanup()
 def test_aggressive_profile_preserves_browser_and_moves_all_firmware_to_fallback(self):
  (self.root/'usr/share/man').mkdir(parents=True)
  (self.root/'usr/share/man/manual').write_text('manual')
  report=split_root(self.root,self.extra)
  self.assertFalse((self.root/'usr/lib/firmware').exists())
  self.assertEqual((self.extra/'usr/lib/firmware/netronome/a.bin').read_bytes(),b'firmware')
  self.assertEqual((self.extra/'usr/lib/firmware/iwlwifi.ucode').read_bytes(),b'wifi')
  self.assertEqual((self.root/'usr/lib/firefox-esr/libxul.so').read_bytes(),b'browser')
  self.assertEqual(report['moved_subtrees'],['usr/lib/firmware','usr/share/doc','usr/share/man'])
 def test_moves_only_selected_subtrees_and_preserves_links(self):
  report=split_root(self.root,self.extra,('usr/lib/firmware/netronome','usr/share/doc'))
  self.assertEqual(self.extra.stat().st_mode & 0o777,self.root.stat().st_mode & 0o777)
  self.assertFalse((self.root/'usr/lib/firmware/netronome').exists());self.assertFalse((self.root/'usr/share/doc').exists())
  self.assertEqual((self.extra/'usr/lib/firmware/netronome/a.bin').read_bytes(),b'firmware')
  self.assertTrue((self.extra/'usr/share/doc/link').is_symlink());self.assertEqual(os.readlink(self.extra/'usr/share/doc/link'),'readme')
  self.assertEqual((self.root/'usr/lib/firefox-esr/libxul.so').read_bytes(),b'browser');self.assertTrue((self.root/'usr/lib/firmware/iwlwifi.ucode').exists())
  self.assertEqual(report['moved_subtrees'],['usr/lib/firmware/netronome','usr/share/doc'])
 def test_cross_layer_hardlink_aborts_without_removal(self):
  os.link(self.root/'usr/share/doc/readme',self.root/'usr/lib/firefox-esr/shared')
  with self.assertRaises(ValueError):split_root(self.root,self.extra,('usr/share/doc',))
  self.assertTrue((self.root/'usr/share/doc/readme').exists());self.assertFalse(self.extra.exists())
 def test_rejects_symlink_and_traversal_sources_and_overlapping_roots(self):
  (self.root/'usr/share/escape').symlink_to('/tmp')
  for items in [('usr/share/escape',),('../outside',),('usr/share/doc','usr/share')]:
   with self.subTest(items=items):
    with self.assertRaises(ValueError):split_root(self.root,self.extra,items)
  with self.assertRaises(ValueError):split_root(self.root,self.root/'nested',('usr/share/doc',))
  self.assertTrue((self.root/'usr/share/doc/readme').exists())
 def test_missing_source_and_existing_destination_do_not_remove_input(self):
  with self.assertRaises(ValueError):split_root(self.root,self.extra,('usr/share/missing',))
  self.extra.mkdir()
  with self.assertRaises(ValueError):split_root(self.root,self.extra,('usr/share/doc',))
  self.assertTrue((self.root/'usr/share/doc/readme').exists())

if __name__=='__main__':unittest.main()
