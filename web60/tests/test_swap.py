import importlib.util
import unittest
from pathlib import Path

p=Path(__file__).resolve().parents[1]/"analyze_swap.py"
spec=importlib.util.spec_from_file_location("swap",p)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class ZramAnalysisTests(unittest.TestCase):
    def test_actual_compressed_swap_is_distinct_from_virtual_capacity(self):
        s=("PUPPY50_V46_DIRECT_INSMOD module=zram status=0\n"
           "PUPPY50_V60_ZRAM_ACTIVE=PASS\n"
           "SwapTotal: 262140 kB\n"
           "PUPPY50_V60_ZRAM_MM_STAT 104857600 40000000 43000000 0\n"
           "PUPPY50_V60_ZRAM_MM_STAT 157286400 59000000 62000000 0\n")
        x=m.analyze(s)
        self.assertTrue(x['sufficient_evidence_of_zram_swap_setup'])
        self.assertTrue(x['zram_used_for_actual_pages'])
        self.assertLess(x['largest_sampled_physical_allocator_mib'],x['largest_reported_swap_total_mib'])
        self.assertFalse(x['384mib_browser_functionality_proven'])

    def test_configured_but_unused_not_counted_as_effective_memory_saving(self):
        x=m.analyze("PUPPY50_V60_ZRAM_ACTIVE=PASS\nPUPPY50_V60_ZRAM_MM_STAT 0 0 0\nPUPPY50_V60_ZRAM_MM_STAT 0 0 0")
        self.assertTrue(x['sufficient_evidence_of_zram_swap_setup'])
        self.assertFalse(x['zram_used_for_actual_pages'])

    def test_missing_guest_telemetry_not_passed(self):
        x=m.analyze("SwapTotal: 262140 kB\n")
        self.assertFalse(x['sufficient_evidence_of_zram_swap_setup'])
        self.assertFalse(x['zram_swap_activated_in_guest'])

    def test_scripts_no_disk_swap(self):
        setup=(Path(__file__).resolve().parents[1]/"zram_setup.sh").read_text()
        self.assertIn("/dev/zram0",setup)
        self.assertNotIn("swapfile",setup)
        self.assertNotIn("WPE_DISABLE_SANDBOX",setup)
        self.assertIn("mem_limit",setup)

if __name__=="__main__": unittest.main()
