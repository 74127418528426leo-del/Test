import sys,unittest,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from report_ram_budget_v44 import summarize
class Budget(unittest.TestCase):
 def test_mock_real_file_metadata(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);(p/'rootfs/usr').mkdir(parents=True);(p/'reports').mkdir()
   (p/'rootfs/usr/zz').write_bytes(b'a'*100)
   (p/'reports/installed-packages.txt').write_text('firefox-esr\nxorg-server\n')
   (p/'puppy50-web-v44-root.sfs').write_bytes(b'b'*90)
   v=summarize(p)
   self.assertEqual(v['compressed_root_bytes'],90)
   self.assertEqual(v['installed_package_count'],2)
   self.assertFalse(v['actual_full_ram_boot_and_webpage_render_proven'])
   self.assertFalse(v['physical_ram_384mib_verified'])
 def test_missing_file_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   with self.assertRaises(ValueError):summarize(Path(d))
 def test_no_optimistic_memory_usage(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);(p/'rootfs').mkdir();(p/'reports').mkdir()
   (p/'reports/installed-packages.txt').write_text('test\n')
   (p/'puppy50-web-v44-root.sfs').write_bytes(b'a')
   self.assertIsNone(summarize(p)['kernel_graphics_browser_xorg_and_network_runtime_memory_measured_mib'])
