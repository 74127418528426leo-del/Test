"""Synthetic only. These tests cannot certify Firefox memory sufficiency."""
import importlib.util
from pathlib import Path
import unittest

p=Path(__file__).resolve().parents[1]/"analyze_firefox_wait.py"
spec=importlib.util.spec_from_file_location("wait",p)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class WaitTests(unittest.TestCase):
    def test_collects_vm_and_states_without_claiming_cause(self):
        log='\n'.join([
            'PUPPY50_V52_STATE pid=87 comm=firefox-esr state=S threads=10 vmsize_kib=1200000 vmpeak_kib=1400000 wchan=futex_wait_queue',
            'PUPPY50_V52_THREAD pid=87 tid=87 wchan=futex_wait_queue',
            'PUPPY50_V52_STATE pid=87 comm=firefox-esr state=R threads=11 vmsize_kib=1220000 vmpeak_kib=1400000 wchan=0',
            'PUPPY50_V52_STATE pid=87 comm=firefox-esr state=S threads=11 vmsize_kib=1201000 vmpeak_kib=1400000 wchan=do_poll',
            'PUPPY50_V52_STATE pid=90 comm=Web Content state=S threads=4 vmsize_kib=1000000 vmpeak_kib=1100000 wchan=do_poll'
        ])
        r=m.analyze(log)
        self.assertEqual(r['observed_firefox_parent_pids'],[87])
        self.assertEqual(r['peak_firefox_threads'],11)
        self.assertEqual(r['peak_firefox_virtual_memory_mib'],round(1220000/1024,2))
        self.assertEqual(r['firefox_state_samples'],3)
        self.assertEqual(r['browser_process_samples'],4)
        self.assertFalse(r['root_cause_identified'])
        self.assertFalse(r['browser_rendered_proven'])

    def test_missing_parent_is_not_sufficient(self):
        r=m.analyze('PUPPY50_V50_PROCESS pid=12 comm=firefox-esr')
        self.assertFalse(r['has_sufficient_process_state_data'])
        self.assertEqual(r['observed_firefox_parent_pids'],[])

if __name__=='__main__':unittest.main()
