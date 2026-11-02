"""Synthetic parser tests only; not a substitute for real KVM evidence."""
import importlib.util
from pathlib import Path
import unittest

path=Path(__file__).resolve().parents[1]/"analyze_guest_memory.py"
spec=importlib.util.spec_from_file_location("p50",path)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

def sample(i, available=204800, oom=0, psi=0.0, processes=True):
    proc=("PUPPY50_V50_PROCESS pid=73 comm=firefox-esr rss_kib=98765 pss_kib=87654\n" if processes else "")
    return (f"PUPPY50_V50_SAMPLE_BEGIN index={i}\n"
       f"PUPPY50_V50_MEM MemTotal: 505123\n"
       f"PUPPY50_V50_MEM MemAvailable: {available}\n"
       f"PUPPY50_V50_MEM Shmem: 20000\n"
       f"PUPPY50_V50_MEM SwapTotal: 0\n"
       f"PUPPY50_V50_MEM SwapFree: 0\n"
       f"PUPPY50_V50_VMSTAT oom_kill {oom}\n"
       f"PUPPY50_V50_PSI some avg10=0.10 avg60=0.00 avg300=0.00 total=99\n"
       f"PUPPY50_V50_PSI full avg10={psi:.2f} avg60=0.00 avg300=0.00 total=0\n"
       f"{proc}PUPPY50_V50_SAMPLE_END index={i}\n")

class TestMemoryAnalysis(unittest.TestCase):
    def test_detects_real_counter_delta_with_three_complete_samples(self):
        text="PUPPY50_WEB_V45_FIREFOX_REQUESTED\n"+sample(0,90000)+sample(1,9000,1,8.1)+sample(2,11000,1,12.4)
        v=m.analyze(text,{"ram_allocated_mib":512,"ram_copy_complete":True})
        self.assertEqual(v["samples_complete"],3)
        self.assertEqual(v["oom_kill_counter_delta"],1)
        self.assertEqual(v["diagnosis"],"OOM_OBSERVED")
        self.assertTrue(v["firefox_process_observed"])
        self.assertAlmostEqual(v["minimum_mem_available_mib"],9000/1024,places=3)
        self.assertFalse(v["browser_interactive_proven"])

    def test_zero_oom_does_not_prove_browser_is_usable(self):
        v=m.analyze(sample(0)+sample(1)+sample(2),{"ram_allocated_mib":1024})
        self.assertEqual(v["diagnosis"],"NO_KERNEL_OOM_IN_SAMPLED_WINDOW")
        self.assertFalse(v["browser_visible_after_ejection"])
        self.assertFalse(v["browser_interactive_proven"])

    def test_incomplete_or_missing_data_fails_closed(self):
        v=m.analyze(sample(0)+"PUPPY50_V50_SAMPLE_BEGIN index=1\n")
        self.assertEqual(v["samples_complete"],1)
        self.assertFalse(v["valid_monitoring"])
        self.assertEqual(v["diagnosis"],"INSUFFICIENT_MEMORY_TELEMETRY")

    def test_no_process_does_not_imply_no_oom(self):
        v=m.analyze(sample(0,oom=0,processes=False)+sample(1,oom=1,processes=False)+sample(2,oom=1,processes=False))
        self.assertFalse(v["firefox_process_observed"])
        self.assertTrue(v["oom_observed"])

if __name__=="__main__":
    unittest.main()
