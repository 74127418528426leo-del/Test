import tempfile,unittest
from pathlib import Path
from browser_probe import BROWSERS,SITES,process_memory
class TestProbe(unittest.TestCase):
 def test_safe_commands(self):
  for command in BROWSERS.values():
   self.assertNotIn("--no-sandbox",command)
   self.assertNotIn("--ignore-certificate-errors",command)
 def test_urls(self):
  for v in SITES.values():
   self.assertTrue(v=="about:blank" or v.startswith("https://"))
 def test_real_pss_parsing(self):
  with tempfile.TemporaryDirectory() as d:
   f=Path(d)/"123";f.mkdir()
   (f/"status").write_text("Uid:\t1550\t1550\t1550\t1550\nVmRSS:\t999 kB\n")
   (f/"smaps_rollup").write_text("Pss:\t500 kB\nPrivate_Clean:\t100 kB\nPrivate_Dirty:\t250 kB\nSwap:\t20 kB\n")
   r=process_memory(1550,Path(d))
   self.assertEqual((r["process_count"],r["pss_kib"],r["uss_kib"],r["rss_kib"],r["swap_kib"]),(1,500,350,999,20))
 def test_missing_is_not_zero(self):
  with tempfile.TemporaryDirectory() as d:
   f=Path(d)/"1";f.mkdir();(f/"status").write_text("Uid:\t1550\t1550\t1550\t1550\n")
   self.assertEqual(process_memory(1550,Path(d))["pss_missing"],1)
if __name__=="__main__":unittest.main()
