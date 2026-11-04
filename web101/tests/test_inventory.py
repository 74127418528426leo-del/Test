import unittest
from pathlib import Path
from root_inventory import parse_listing,summarize,classify
S="""-rw-r--r-- root/root 1000 2026-11-03 12:01 squashfs-root/usr/lib/firefox-esr/omni.ja
-rw-r--r-- root/root 456 2026-11-03 12:01 squashfs-root/usr/share/doc/foo/readme
lrwxrwxrwx root/root 5 2026-11-03 12:01 squashfs-root/bin/sh -> dash
-rw-r--r-- root/root 300 2026-11-03 12:01 squashfs-root/usr/lib/firmware/wifi.bin
"""
class T(unittest.TestCase):
 def test_parse_only_regular_files(self):
  x=parse_listing(S)
  self.assertEqual(len(x),3)
  self.assertEqual(sum(a["bytes"] for a in x),1756)
 def test_dont_mislabel_compressed_savings(self):
  d=summarize(parse_listing(S),2000,1000)
  self.assertTrue(d["NOT_measured_compressed_savings_from_removing_files"])
  self.assertEqual(d["size_uncompressed_regular_files_bytes"],1756)
  self.assertEqual(d["compressed_squashfs_file_size_bytes"],1000)
 def test_preserve_network_and_browser_groupings(self):
  self.assertEqual(classify("usr/lib/firmware/rtl8xxx.bin"),"network_firmware")
  self.assertEqual(classify("usr/lib/firefox-esr/omni.ja"),"firefox_runtime")
if __name__=="__main__":unittest.main()
